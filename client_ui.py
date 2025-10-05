import asyncio
import sys
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
import json
import traceback
import re

# MCP client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI

# Get the project directory (current directory)
project_dir = Path(__file__).parent
load_dotenv(project_dir / '.env')

server_params = StdioServerParameters(
    command=sys.executable,  
    args=[str(project_dir / "src/mcpserver/__main__.py")],
)

# Configure Streamlit page
st.set_page_config(
    page_title="Precious Metals Price Checker",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #DAA520;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .price-card {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #000;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .error-card {
        background: #ff4444;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .success-card {
        background: #44ff44;
        padding: 1rem;
        border-radius: 10px;
        color: #000;
        margin: 1rem 0;
    }
    .metric-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

async def fetch_metal_price(metal):
    """Fetch price for a specific metal"""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "fetch_metal_price",
                    arguments={"metal": metal}
                )
                
                return result.content[0].text
    except Exception as e:
        return f"❌ Error fetching {metal} price: {str(e)}"

async def calculate_gold_silver_ratio():
    """Calculate gold to silver ratio"""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get both gold and silver prices
                gold_result = await session.call_tool(
                    "fetch_metal_price",
                    arguments={"metal": "gold"}
                )
                
                silver_result = await session.call_tool(
                    "fetch_metal_price", 
                    arguments={"metal": "silver"}
                )
                
                gold_text = gold_result.content[0].text
                silver_text = silver_result.content[0].text
                
                # Extract USD prices
                gold_usd = extract_usd_price(gold_text)
                silver_usd = extract_usd_price(silver_text)
                
                if gold_usd and silver_usd:
                    ratio = gold_usd / silver_usd
                    
                    return {
                        "ratio": ratio,
                        "gold_price": gold_usd,
                        "silver_price": silver_usd,
                        "gold_text": gold_text,
                        "silver_text": silver_text
                    }
                else:
                    return {
                        "error": "Could not extract prices for ratio calculation",
                        "gold_text": gold_text,
                        "silver_text": silver_text
                    }
                    
    except Exception as e:
        return {"error": f"Error fetching data for ratio calculation: {str(e)}"}

def extract_usd_price(price_text):
    """Extract USD price from the price text"""
    usd_match = re.search(r'USD:\s*\$([0-9,]+\.?[0-9]*)', price_text)
    if usd_match:
        price_str = usd_match.group(1).replace(',', '')
        return float(price_str)
    return None

async def run_openai_query(query):
    """Run a query using OpenAI integration"""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools_result = await session.list_tools()
                
                openai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                    for tool in tools_result.tools
                ]

                messages = [{"role": "user", "content": query}]

                client = OpenAI()
                response = client.chat.completions.create(
                    model='gpt-4o',
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )

                messages.append(response.choices[0].message)

                if response.choices[0].message.tool_calls:
                    for tool_execution in response.choices[0].message.tool_calls:
                        result = await session.call_tool(
                            tool_execution.function.name,
                            arguments=json.loads(tool_execution.function.arguments),
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_execution.id,
                                "content": result.content[0].text,
                            }
                        )
                    
                    # Get final response from LLM with tool results
                    response = client.chat.completions.create(
                        model='gpt-4o',
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto",
                    )

                return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error: {str(e)}"

def display_price_data(price_text, metal_type):
    """Display price data in a formatted way"""
    st.markdown(f"<div class='price-card'><h3>📊 {metal_type.title()} Price Data</h3></div>", 
                unsafe_allow_html=True)
    
    # Extract key information
    lines = price_text.split('\n')
    
    for line in lines:
        if 'USD:' in line and '$' in line:
            st.metric("💵 USD Price (Per Ounce)", line.split('USD: ')[1].strip())
        elif 'INR (Base):' in line and '₹' in line:
            st.metric("🇮🇳 INR Base Price", line.split('INR (Base): ')[1].strip())
        elif 'Market Price (GST + Duty):' in line and '₹' in line:
            st.metric("🏪 Market Price (with taxes)", line.split('Market Price (GST + Duty): ')[1].strip())
        elif 'Exchange Rate:' in line:
            st.metric("💱 Exchange Rate", line.split('Exchange Rate: ')[1].strip())
    
    # Show full details in expander
    with st.expander("📋 View Full Price Details"):
        st.text(price_text)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("<h1 class='main-header'>🏆 Precious Metals Price Checker</h1>", 
                unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Options")
    st.sidebar.markdown("---")
    
    # Option selection
    option = st.sidebar.selectbox(
        "Choose an option:",
        ["🥇 Gold Rate", "🥈 Silver Rate", "⚖️ Gold/Silver Ratio", "🤖 AI Assistant"]
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if option == "🥇 Gold Rate":
            st.subheader("🥇 Current Gold Prices")
            
            if st.button("🔄 Fetch Gold Prices", type="primary"):
                with st.spinner("Fetching current gold prices..."):
                    result = asyncio.run(fetch_metal_price("gold"))
                    
                if "❌" in result:
                    st.markdown(f"<div class='error-card'>{result}</div>", unsafe_allow_html=True)
                else:
                    display_price_data(result, "gold")
        
        elif option == "🥈 Silver Rate":
            st.subheader("🥈 Current Silver Prices")
            
            if st.button("🔄 Fetch Silver Prices", type="primary"):
                with st.spinner("Fetching current silver prices..."):
                    result = asyncio.run(fetch_metal_price("silver"))
                    
                if "❌" in result:
                    st.markdown(f"<div class='error-card'>{result}</div>", unsafe_allow_html=True)
                else:
                    display_price_data(result, "silver")
        
        elif option == "⚖️ Gold/Silver Ratio":
            st.subheader("⚖️ Gold/Silver Ratio Analysis")
            
            if st.button("📊 Calculate Ratio", type="primary"):
                with st.spinner("Calculating gold/silver ratio..."):
                    result = asyncio.run(calculate_gold_silver_ratio())
                    
                if "error" in result:
                    st.markdown(f"<div class='error-card'>{result['error']}</div>", unsafe_allow_html=True)
                    if "gold_text" in result:
                        with st.expander("Gold Data"):
                            st.text(result["gold_text"])
                        with st.expander("Silver Data"):
                            st.text(result["silver_text"])
                else:
                    # Display ratio metrics
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("🥇 Gold (USD/oz)", f"${result['gold_price']:.2f}")
                    
                    with col_b:
                        st.metric("🥈 Silver (USD/oz)", f"${result['silver_price']:.2f}")
                    
                    with col_c:
                        st.metric("⚖️ Gold/Silver Ratio", f"{result['ratio']:.2f}:1")
                    
                    # Analysis
                    historical_avg = 70
                    if result['ratio'] > historical_avg:
                        analysis = f"📈 Current ratio ({result['ratio']:.1f}:1) is **above** historical average (~{historical_avg}:1)"
                        st.success(analysis)
                    else:
                        analysis = f"📉 Current ratio ({result['ratio']:.1f}:1) is **below** historical average (~{historical_avg}:1)"
                        st.info(analysis)
                    
                    # Show detailed data
                    with st.expander("📋 Detailed Gold Data"):
                        st.text(result["gold_text"])
                    
                    with st.expander("📋 Detailed Silver Data"):
                        st.text(result["silver_text"])
        
        elif option == "🤖 AI Assistant":
            st.subheader("🤖 AI-Powered Price Assistant")
            st.markdown("Ask questions about precious metals in natural language!")
            
            # Chat interface
            user_query = st.text_input("💬 Ask about gold, silver, or market analysis:", 
                                     placeholder="e.g., 'What's the current gold price trend?'")
            
            if st.button("🚀 Ask AI", type="primary") and user_query:
                with st.spinner("AI is analyzing your question..."):
                    result = asyncio.run(run_openai_query(user_query))
                    
                if "❌" in result:
                    st.markdown(f"<div class='error-card'>{result}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='success-card'><h4>🤖 AI Response:</h4>{result}</div>", 
                              unsafe_allow_html=True)
    
    with col2:
        # Information panel
        st.markdown("### 📖 Information")
        
        st.info("""
        **💡 Features:**
        - Real-time gold & silver prices
        - USD to INR conversion
        - Tax calculations (GST + Import Duty)
        - Gold/Silver ratio analysis
        - AI-powered assistance
        
        **📊 Price Includes:**
        - Base metal prices
        - GST (3%)
        - Import Duty (6% Gold, 7.5% Silver)
        - Per ounce & per 10g rates
        """)
        
        st.markdown("### 🔄 Auto-Refresh")
        if st.checkbox("Enable auto-refresh (30s)"):
            import time
            time.sleep(30)
            st.rerun()
        
        st.markdown("### 📈 Market Info")
        st.markdown("""
        **Historical Gold/Silver Ratios:**
        - Ancient times: ~12-16:1
        - 20th century avg: ~47:1  
        - Modern avg: ~70:1
        - Current: Check ratio tab
        """)

if __name__ == "__main__":
    main()
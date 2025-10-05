import asyncio
import sys
from dotenv import load_dotenv
from pathlib import Path

# MCP client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
import json
import traceback

load_dotenv('/Users/dhruvin.shah/Documents/Projects/Learning/Learning Repos/MCP/MCP-DEPLOY/.env')

# Get the project directory
project_dir = Path("/Users/dhruvin.shah/Documents/Projects/Learning/Learning Repos/MCP/MCP-DEPLOY")

server_params = StdioServerParameters(
    command=sys.executable,  
    args=[str(project_dir / "src/mcpserver/__main__.py")],  # Path to server script
)

def display_menu():
    """Display the menu options"""
    print("\n" + "="*50)
    print("🏛️  PRECIOUS METALS PRICE CHECKER")
    print("="*50)
    print("1. 🥇 Gold Rate")
    print("2. 🥈 Silver Rate") 
    print("3. ⚖️  Gold/Silver Ratio")
    print("4. 🚪 Exit")
    print("="*50)

def get_query_for_option(option):
    """Convert menu option to appropriate query"""
    queries = {
        1: "What is the current gold price in USD and INR with all taxes?",
        2: "What is the current silver price in USD and INR with all taxes?", 
        3: "Get both gold and silver prices and calculate the gold to silver ratio"
    }
    return queries.get(option, "")

async def run(query):
    try:
        print(f"\n🔄 Processing query: {query}")
        print("Starting stdio_client...")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:

                # Initialize server
                await session.initialize()

                # Get tools
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

                # Make OpenAI LLM call
                messages = [
                    {"role": "user", "content": query}
                ]

                client = OpenAI()
                response = client.chat.completions.create(
                    model='gpt-4o',
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )

                messages.append(response.choices[0].message)

                # Handle any tool calls
                if response.choices[0].message.tool_calls:
                    for tool_execution in response.choices[0].message.tool_calls:
                        # Execute tool call
                        result = await session.call_tool(
                            tool_execution.function.name,
                            arguments=json.loads(tool_execution.function.arguments),
                        )

                        # Add tool response to conversation
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
        print(f"❌ An error occurred: {str(e)}")
        traceback.print_exc()
        return None

async def main():
    """Main function with menu loop"""
    print("🚀 Welcome to the MCP Precious Metals Client!")
    
    while True:
        try:
            display_menu()
            
            # Get user choice
            choice = input("\n💬 Please select an option (1-4): ").strip()
            
            # Validate input
            if not choice.isdigit():
                print("❌ Please enter a valid number (1-4)")
                continue
                
            option = int(choice)
            
            if option == 4:
                print("👋 Thank you for using the Precious Metals Client! Goodbye!")
                break
            elif option in [1, 2, 3]:
                # Get the appropriate query
                query = get_query_for_option(option)
                
                if option == 1:
                    print("🥇 Fetching current gold rates...")
                elif option == 2:
                    print("🥈 Fetching current silver rates...")
                elif option == 3:
                    print("⚖️  Calculating gold/silver ratio...")
                
                # Run the query
                result = await run(query)
                
                if result:
                    print("\n" + "="*60)
                    print("📊 RESULT:")
                    print("="*60)
                    print(result)
                    print("="*60)
                else:
                    print("❌ Failed to get result. Please try again.")
                    
                # Ask if user wants to continue
                continue_choice = input("\n🔄 Would you like to check another rate? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes']:
                    print("👋 Thank you for using the Precious Metals Client! Goodbye!")
                    break
                    
            else:
                print("❌ Invalid option. Please select 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            continue

if __name__ == "__main__":
    asyncio.run(main())
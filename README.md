# MCP Metal Price Server & Client

A Model Context Protocol (MCP) server that provides real-time precious metal prices with comprehensive tax calculations for the Indian market.

## Features

- 🥇 **Gold & Silver Prices**: Real-time USD and INR pricing
- 📊 **Tax Calculations**: Includes GST (3%) and Import Duty (6%/7.5%)
- ⚖️ **Multiple Units**: Per ounce and per 10 grams
- 🔄 **Live Exchange Rates**: USD to INR conversion
- 🤖 **AI Integration**: OpenAI-powered client interface

## Installation

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up OpenAI API key (for client):**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

### Running the Server

```bash
# Using uv
uv run mcp-server

# Or using Python directly
python -m mcpserver
```

The server starts on `0.0.0.0` and provides the following tool:
- `fetch_metal_price(metal: str = "gold")` - Get current gold or silver prices

### Using the Interactive Client

```bash
# Run the client
python client.py

# Or using uv
uv run python client.py
```

### Client Commands

- **Natural language**: "What's the current gold price?", "Show me silver rates"
- **Direct tool call**: `tool:fetch_metal_price:gold`
- **List tools**: `list`
- **Exit**: `exit` or `quit`

### Example Client Session

```
💬 Your request: What's the current gold price?
🤖 AI Analysis: gold
🔧 Executing tool: fetch_metal_price with arguments: {'metal': 'gold'}

📊 Tool Result:
🥇 Current Gold Price:

💱 Conversion: 1 Ounce = 31.1035 grams

📈 Per Ounce:
  USD: $2,650.30
  INR (Base): ₹2,35,476.64
  Market Price (GST + Duty): ₹2,56,690.13

⚖️ Per 10 Grams:
  USD: $852.15
  INR (Base): ₹75,691.32
  Market Price (GST + Duty): ₹82,504.14

📊 Exchange Rate: 1 USD = ₹88.80
💼 Tax Summary: GST 3% + Import Duty 6.0% = Total 9.0%
```

## API Configuration

The server can be accessed via:
- **Local**: `http://127.0.0.1:8000`
- **Network**: `http://0.0.0.0:8000` (if configured)
- **MCP Protocol**: STDIO transport

## Development

### Project Structure
```
├── src/mcpserver/
│   ├── __init__.py
│   ├── __main__.py
│   └── fetch_metal_price.py
├── client.py
├── pyproject.toml
└── README.md
```

### Adding New Tools

1. Add your tool function to `fetch_metal_price.py`:
   ```python
   @mcp.tool()
   def your_new_tool(param: str) -> str:
       """Tool description"""
       return "Tool result"
   ```

2. The client will automatically discover and use new tools.

## Requirements

- Python 3.13+
- MCP library
- Requests
- OpenAI (for client AI features)

## License

MIT License
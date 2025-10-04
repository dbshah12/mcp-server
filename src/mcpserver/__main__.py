from mcpserver.fetch_metal_price import mcp

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
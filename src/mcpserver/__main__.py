from mcpserver.deployment import mcp

def main():
    mcp.run(transport="streamable-http", host="0.0.0.0")

if __name__ == "__main__":
    main()
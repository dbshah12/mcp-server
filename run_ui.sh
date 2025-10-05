#!/bin/bash
# Script to run the Streamlit UI for the MCP Precious Metals Client

echo "🚀 Starting Precious Metals Price Checker UI..."
echo "📱 The web interface will open in your browser"
echo "🔗 URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run streamlit run client_ui.py --server.port 8501 --server.address 0.0.0.0
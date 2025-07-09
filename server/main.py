# server/__main__.py - MCP Inspector Entry Point

from mcp_server import main
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    asyncio.run(main()) 

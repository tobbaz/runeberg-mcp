"""runeberg-mcp: MCP server and CLI for searching and reading Project Runeberg."""

__version__ = "0.2.0"

from runeberg_mcp.server import mcp, run
from runeberg_mcp.cli import main

__all__ = ["mcp", "run", "main"]

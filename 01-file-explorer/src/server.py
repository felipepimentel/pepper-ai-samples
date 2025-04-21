"""File Explorer MCP Server."""

import os
from pathlib import Path
from typing import Dict, List

from mcp.server.fastmcp import Context, FastMCP

# Create an MCP server
mcp = FastMCP("File Explorer")


@mcp.tool()
def list_files(path: str = ".") -> List[Dict[str, str]]:
    """List files in a directory."""
    files = []
    for entry in os.scandir(path):
        files.append(
            {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "path": str(Path(entry.path).absolute()),
            }
        )
    return files


@mcp.tool()
async def read_file(path: str, ctx: Context) -> str:
    """Read contents of a file."""
    try:
        with open(path, "r") as f:
            content = f.read()
            await ctx.info(f"Read file: {path}")
            return content
    except Exception as e:
        await ctx.error(f"Error reading file: {e}")
        return str(e)


@mcp.resource("file://{path}")
def get_file_info(path: str) -> Dict[str, str]:
    """Get file information."""
    path_obj = Path(path)
    return {
        "name": path_obj.name,
        "extension": path_obj.suffix,
        "size": str(path_obj.stat().st_size),
        "modified": str(path_obj.stat().st_mtime),
    }


if __name__ == "__main__":
    mcp.run()

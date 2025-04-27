#!/usr/bin/env python3
"""
File Explorer MCP Server Example
Demonstrates how to create an MCP server for file system exploration.
"""

import datetime
import os
import stat
import sys
import argparse
import logging
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP as OfficialFastMCP
from pepperpymcp import PepperFastMCP, ConnectionMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Initialize MCP server
mcp = PepperFastMCP(
    name="File Explorer",
    description="MCP server for file system exploration",
    version="1.0.0"
)

# Manually set app to avoid AttributeError
if not hasattr(mcp._mcp, "app"):
    mcp._mcp.app = app


@mcp.tool()
def list_directory(path: str = ".") -> List[Dict[str, Any]]:
    """Lists files and directories in a specified path.

    Use this tool when you need to explore directory contents,
    list files or navigate the file system.

    Examples:
    - list_directory()  →  Lists files in current directory
    - list_directory("/home/user")  →  Lists files in /home/user directory
    - list_directory("../")  →  Lists files in parent directory

    Args:
        path: Directory path to list (default: current directory)

    Returns:
        List of dictionaries containing information about each file/directory

    Raises:
        FileNotFoundError: If directory doesn't exist
        PermissionError: If no permission to access directory
    """
    try:
        result = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            stats = os.stat(item_path)

            # Determine type
            item_type = "unknown"
            if os.path.isdir(item_path):
                item_type = "directory"
            elif os.path.isfile(item_path):
                item_type = "file"
            elif os.path.islink(item_path):
                item_type = "symlink"

            # Format date and permissions
            modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
            permissions = stat.filemode(stats.st_mode)

            result.append(
                {
                    "name": item,
                    "path": os.path.abspath(item_path),
                    "type": item_type,
                    "size": stats.st_size,
                    "modified": modified_time,
                    "permissions": permissions,
                }
            )

        return result
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error listing directory: {str(e)}")


@mcp.tool()
def read_file(path: str, max_size: int = 100000) -> Dict[str, Any]:
    """Reads file content.

    Use this tool when you need to read the content of a text file.
    Limited to text files with configurable maximum size.

    Examples:
    - read_file("file.txt")  →  Reads content of file.txt
    - read_file("/path/to/config.json", 5000)  →  Reads config.json limited to 5000 bytes

    Args:
        path: Path to file to read
        max_size: Maximum size to read in bytes (default: 100000)

    Returns:
        Dictionary containing file information and content

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If no permission to read file
        ValueError: If file exceeds maximum size
    """
    try:
        # Check if file exists
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File '{path}' doesn't exist")

        # Check file size
        file_size = os.path.getsize(path)
        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size} bytes (maximum: {max_size} bytes)"
            )

        # Try to determine file type
        file_type = "text"
        file_extension = os.path.splitext(path)[1].lower()
        binary_extensions = [
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".zip",
            ".exe",
            ".bin",
            ".jpg",
            ".png",
            ".gif",
        ]

        if file_extension in binary_extensions:
            file_type = "binary"
            content = "[Binary file - content not displayed]"
        else:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except UnicodeDecodeError:
                file_type = "binary"
                content = "[Unknown encoding - content not displayed]"

        # Get file stats
        stats = os.stat(path)
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()

        return {
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "size": file_size,
            "type": file_type,
            "modified": modified_time,
            "content": content,
        }
    except (FileNotFoundError, PermissionError, ValueError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error reading file: {str(e)}")


@mcp.tool()
def write_file(path: str, content: str, mode: str = "w") -> Dict[str, Any]:
    """Writes content to a file.

    Use this tool when you need to create or modify a text file.

    Examples:
    - write_file("new.txt", "File content")  →  Creates/overwrites new.txt
    - write_file("log.txt", "New line", "a")  →  Appends content to log.txt

    Args:
        path: Path to file to write
        content: Content to write to file
        mode: Write mode ('w' for overwrite, 'a' for append)

    Returns:
        Dictionary with operation information

    Raises:
        PermissionError: If no permission to write file
        ValueError: If mode is invalid
    """
    if mode not in ["w", "a"]:
        raise ValueError("Mode must be 'w' (overwrite) or 'a' (append)")

    try:
        with open(path, mode, encoding="utf-8") as file:
            file.write(content)

        file_size = os.path.getsize(path)

        return {
            "success": True,
            "path": os.path.abspath(path),
            "size": file_size,
            "mode": mode,
            "message": f"File {'overwritten' if mode == 'w' else 'updated'} successfully",
        }
    except PermissionError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error writing file: {str(e)}")


@mcp.tool()
def get_file_info(path: str) -> Dict[str, Any]:
    """Gets detailed information about a file or directory.

    Use this tool when you need to get detailed metadata about
    a file or directory without reading its content.

    Examples:
    - get_file_info("file.txt")  →  Returns metadata for file.txt
    - get_file_info("/home/user")  →  Returns metadata for /home/user directory

    Args:
        path: Path to file or directory

    Returns:
        Dictionary containing detailed information about the file/directory

    Raises:
        FileNotFoundError: If file/directory doesn't exist
        PermissionError: If no permission to access file/directory
    """
    try:
        # Check if path exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' doesn't exist")

        # Get stats
        stats = os.stat(path)

        # Determine type
        item_type = "unknown"
        if os.path.isdir(path):
            item_type = "directory"
        elif os.path.isfile(path):
            item_type = "file"
        elif os.path.islink(path):
            item_type = "symlink"

        # Format dates
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
        access_time = datetime.datetime.fromtimestamp(stats.st_atime).isoformat()
        create_time = datetime.datetime.fromtimestamp(stats.st_ctime).isoformat()

        # Permissions
        permissions = stat.filemode(stats.st_mode)

        result = {
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "type": item_type,
            "size": stats.st_size,
            "permissions": permissions,
            "owner": stats.st_uid,
            "group": stats.st_gid,
            "modified": modified_time,
            "accessed": access_time,
            "created": create_time,
        }

        # Add directory-specific info
        if item_type == "directory":
            result["contents"] = len(os.listdir(path))

        return result
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error getting file info: {str(e)}")


@mcp.tool()
def delete_item(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Deletes a file or directory.

    Use this tool when you need to delete a file or directory.
    For directories, recursive deletion must be explicitly enabled.

    Examples:
    - delete_item("file.txt")  →  Deletes file.txt
    - delete_item("empty_dir")  →  Deletes empty directory
    - delete_item("full_dir", recursive=True)  →  Deletes directory and contents

    Args:
        path: Path to file or directory to delete
        recursive: Whether to recursively delete directories (default: False)

    Returns:
        Dictionary with operation information

    Raises:
        FileNotFoundError: If path doesn't exist
        PermissionError: If no permission to delete
        OSError: If trying to delete non-empty directory without recursive=True
    """
    try:
        # Check if path exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' doesn't exist")

        # Get info before deletion
        is_dir = os.path.isdir(path)
        name = os.path.basename(path)
        abs_path = os.path.abspath(path)

        # Delete based on type
        if is_dir:
            if recursive:
                import shutil
                shutil.rmtree(path)
            else:
                os.rmdir(path)  # Will fail if directory not empty
        else:
            os.remove(path)

        return {
            "success": True,
            "name": name,
            "path": abs_path,
            "type": "directory" if is_dir else "file",
            "recursive": recursive if is_dir else None,
            "message": f"Successfully deleted {'directory' if is_dir else 'file'}"
        }
    except (FileNotFoundError, PermissionError, OSError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error deleting item: {str(e)}")


@mcp.resource("file://{path}")
def file_resource(path: str) -> str:
    """Gets file content as a resource.

    This resource provides direct access to file content through a URI.
    Only text files are supported. For binary files, use the read_file tool.

    Examples:
    - file://path/to/file.txt  →  Returns content of file.txt
    - file://config.json  →  Returns content of config.json

    Args:
        path: Path to the file

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If no permission to read file
        UnicodeDecodeError: If file is not text
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return "[Binary file - use read_file tool to access content]"


@mcp.prompt()
async def file_summary(path: str) -> str:
    """Generates a summary of a file or directory.

    Use this prompt when you need a natural language description
    of a file or directory's properties and content.

    Examples:
    - file_summary("document.txt")  →  Summary of document.txt
    - file_summary("/home/user/docs")  →  Summary of docs directory

    Args:
        path: Path to file or directory

    Returns:
        Natural language summary of the item
    """
    try:
        info = get_file_info(path)
        
        if info["type"] == "directory":
            contents = list_directory(path)
            files = sum(1 for item in contents if item["type"] == "file")
            dirs = sum(1 for item in contents if item["type"] == "directory")
            
            return mcp.get_template("directory_summary").format(
                name=info["name"],
                path=info["path"],
                files=files,
                directories=dirs,
                modified=info["modified"],
                permissions=info["permissions"]
            )
        else:
            file_data = read_file(path)
            preview = file_data["content"][:200] + "..." if len(file_data["content"]) > 200 else file_data["content"]
            
            return mcp.get_template("file_summary").format(
                name=info["name"],
                path=info["path"],
                size=info["size"],
                type=info["type"],
                modified=info["modified"],
                permissions=info["permissions"],
                preview=preview
            )
    except Exception as e:
        return f"Error generating summary: {str(e)}"


async def main():
    """Main entry point for the server."""
    if args.stdio:
        await mcp._run_stdio()
    else:
        mcp.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Explorer MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use STDIO transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.stdio:
        print("Starting File Explorer MCP Server in STDIO mode", file=sys.stderr)
        asyncio.run(main())
    else:
        print("Starting File Explorer MCP Server in HTTP mode", file=sys.stderr)
        mcp.run()

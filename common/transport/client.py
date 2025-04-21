#!/usr/bin/env python
"""
Generic MCP client for interacting with MCP servers.
Supports both HTTP and stdio modes.
"""

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

import requests


class MCPClient:
    """Generic client for interacting with MCP servers."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the client with server details."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def initialize(self) -> Dict[str, Any]:
        """Get server information."""
        return self._http_request("initialize")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get a list of available tools."""
        response = self._http_request("tools/list")
        return response.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments."""
        response = self._http_request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        if "content" in response and response["content"]:
            return response["content"][0].get("text")
        return response

    def list_resources(self) -> List[Dict[str, Any]]:
        """Get a list of available resources."""
        response = self._http_request("resources/list")
        return response.get("resources", [])

    def get_resource(self, uri: str) -> str:
        """Get a resource by URI."""
        response = self._http_request("resources/get", {"uri": uri})
        return response.get("content", "")

    def _http_request(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the server."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


class MCPStdioClient:
    """Client for interacting with MCP servers via stdio."""

    def __init__(self, server_command: List[str]):
        """Initialize the client with the server command."""
        self.server_command = server_command
        self.process = None
        self.request_id = 0

    def start(self):
        """Start the server process."""
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffering
        )

    def stop(self):
        """Stop the server process."""
        if self.process:
            self.process.terminate()
            self.process = None

    def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a request to the server and get the response."""
        if not self.process:
            return {"error": "Server not started"}

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }

        if params:
            request["params"] = params

        try:
            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            response = json.loads(response_line)

            if "result" in response:
                return response["result"]
            elif "error" in response:
                return {"error": response["error"].get("message", "Unknown error")}
            return response
        except Exception as e:
            return {"error": str(e)}

    def initialize(self) -> Dict[str, Any]:
        """Initialize the connection with the server."""
        return self._send_request("initialize")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get a list of available tools."""
        response = self._send_request("tools/list")
        return response.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments."""
        response = self._send_request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        if "content" in response and response["content"]:
            return response["content"][0].get("text")
        return response

    def list_resources(self) -> List[Dict[str, Any]]:
        """Get a list of available resources."""
        response = self._send_request("resources/list")
        return response.get("resources", [])

    def get_resource(self, uri: str) -> str:
        """Get a resource by URI."""
        response = self._send_request("resources/get", {"uri": uri})
        return response.get("content", "")


def create_interactive_session(client):
    """Create an interactive session with the MCP server."""
    try:
        # Initialize
        info = client.initialize()
        print("\n=== Server Info ===")
        print(f"Name: {info.get('name', 'Unknown')}")
        print(f"Description: {info.get('description', '')}")
        print(f"Version: {info.get('version', 'Unknown')}")

        # List tools
        tools = client.list_tools()
        print("\n=== Available Tools ===")
        for tool in tools:
            params = ", ".join(
                [f"{p['name']}: {p['type']}" for p in tool.get("parameters", [])]
            )
            print(f"- {tool['name']}({params}): {tool['description']}")

        # List resources
        resources = client.list_resources()
        print("\n=== Available Resources ===")
        for resource in resources:
            print(f"- {resource['template']}: {resource['description']}")

        # Interactive session
        while True:
            print("\n=== Actions ===")
            print("1. Call a tool")
            print("2. Get a resource")
            print("3. Exit")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                tool_name = input("Enter tool name: ").strip()

                # Get tool details
                tool_details = next((t for t in tools if t["name"] == tool_name), None)
                if not tool_details:
                    print(f"Tool '{tool_name}' not found.")
                    continue

                # Get arguments
                args = {}
                for param in tool_details.get("parameters", []):
                    param_name = param["name"]
                    param_type = param["type"]
                    value = input(f"Enter {param_name} ({param_type}): ").strip()

                    # Convert value based on type
                    if "float" in param_type:
                        args[param_name] = float(value)
                    elif "int" in param_type:
                        args[param_name] = int(value)
                    elif "bool" in param_type:
                        args[param_name] = value.lower() in ("yes", "true", "t", "1")
                    else:
                        args[param_name] = value

                # Call the tool
                result = client.call_tool(tool_name, args)
                print(f"\nResult: {result}")

            elif choice == "2":
                uri = input("Enter resource URI: ").strip()
                result = client.get_resource(uri)
                print(f"\nResource content: {result}")

            elif choice == "3":
                break

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point when running as a script."""
    parser = argparse.ArgumentParser(description="Generic MCP Client")
    parser.add_argument(
        "--host", default="localhost", help="Server host (for HTTP mode)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (for HTTP mode)"
    )
    parser.add_argument(
        "--stdio", action="store_true", help="Use stdio mode instead of HTTP"
    )
    parser.add_argument("--cmd", nargs="+", help="Server command for stdio mode")

    args = parser.parse_args()

    if args.stdio:
        if not args.cmd:
            print("Server command is required for stdio mode")
            sys.exit(1)

        # Create stdio client
        client = MCPStdioClient(args.cmd)
        client.start()
        try:
            create_interactive_session(client)
        finally:
            client.stop()
    else:
        # Create HTTP client
        client = MCPClient(args.host, args.port)
        create_interactive_session(client)


if __name__ == "__main__":
    main()

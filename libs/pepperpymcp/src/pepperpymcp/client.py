"""
MCP client implementations.
"""

from typing import Any, Dict

from .transports import Transport


class MCPClient:
    """MCP client implementation."""

    def __init__(self, transport: Transport):
        self.transport = transport

    async def connect(self) -> None:
        """Connect to the server."""
        await self.transport.connect()

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        await self.transport.disconnect()

    async def call_tool(self, name: str, **params) -> Any:
        """Call a tool on the server."""
        data = {
            "type": "tool",
            "name": name,
            "params": params,
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response["result"] if response else None

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the connection and get server info."""
        data = {
            "type": "initialize",
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response if response else {}

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools on the server."""
        data = {
            "type": "list_tools",
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response if response else {"tools": []}

    async def list_resources(self) -> Dict[str, Any]:
        """List available resources on the server."""
        data = {
            "type": "list_resources",
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response if response else {"resources": []}

    async def list_prompts(self) -> Dict[str, Any]:
        """List available prompts on the server."""
        data = {
            "type": "list_prompts",
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response if response else {"prompts": []}

    async def get_resource(self, uri: str) -> Any:
        """Get a resource from the server."""
        data = {
            "type": "resource",
            "uri": uri,
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response["content"] if response else None

    async def call_prompt(self, name: str, **params) -> Any:
        """Call a prompt on the server."""
        data = {
            "type": "prompt",
            "name": name,
            "params": params,
        }
        await self.transport.send(data)
        response = await self.transport.receive()
        return response["result"] if response else None


class MCPStdioClient(MCPClient):
    """MCP client for standard I/O."""

    pass


def create_interactive_session() -> MCPStdioClient:
    """Create an interactive MCP session."""
    from .transports import StdioTransport

    return MCPStdioClient(StdioTransport())

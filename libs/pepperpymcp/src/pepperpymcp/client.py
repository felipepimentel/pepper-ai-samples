"""
MCP client implementations.
"""

from typing import Any

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


class MCPStdioClient(MCPClient):
    """MCP client for standard I/O."""

    pass


def create_interactive_session() -> MCPStdioClient:
    """Create an interactive MCP session."""
    from .transports import StdioTransport

    return MCPStdioClient(StdioTransport())

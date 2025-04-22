"""
Transport implementations for MCP.

This module re-exports transport classes from the official MCP SDK
for backward compatibility.
"""

from enum import Enum
from typing import Any, Dict, Optional

# Import from official MCP SDK
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server


class ConnectionMode(Enum):
    """Connection mode for the MCP server."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


# Re-export official MCP transports with our naming for backward compatibility
class HTTPTransport:
    """HTTP transport from the official MCP SDK."""

    def __init__(self, url: str):
        self.url = url
        raise NotImplementedError(
            "HTTPTransport is not implemented in the official MCP SDK. "
            "Use SseServerTransport instead."
        )


class StdioTransport:
    """
    Stdio transport from the official MCP SDK.
    
    This is a compatibility wrapper around the stdio_server function.
    For new code, use mcp.server.stdio.stdio_server directly.
    """

    def __init__(self):
        self.stdio_context = None
        
    async def connect(self):
        """Connect to stdin/stdout using the official MCP SDK."""
        self.stdio_context = stdio_server()
        return await self.stdio_context.__aenter__()
        
    async def disconnect(self):
        """Disconnect from stdin/stdout."""
        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)


class SSETransport:
    """
    SSE transport from the official MCP SDK.
    
    This is a compatibility wrapper around SseServerTransport.
    For new code, use mcp.server.sse.SseServerTransport directly.
    """

    def __init__(self, request):
        self.transport = SseServerTransport("/messages")
        
    def response(self):
        """Return the SSE response."""
        return self.transport.response()


class DirectTransport:
    """Direct in-process transport."""
    
    def __init__(self):
        raise NotImplementedError(
            "DirectTransport is not implemented yet. "
            "Use stdio_server or SseServerTransport instead."
        )

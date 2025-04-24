"""
Transport implementations for MCP.

This module re-exports transport classes from the official MCP SDK
for backward compatibility.
"""

import json
import asyncio
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

# Import from official MCP SDK
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server


@runtime_checkable
class Transport(Protocol):
    """Protocol defining the interface for MCP transports."""
    
    async def connect(self) -> None:
        """Connect to the server."""
        ...
        
    async def disconnect(self) -> None:
        """Disconnect from the server."""
        ...
        
    async def send(self, data: Dict[str, Any]) -> None:
        """Send data to the server."""
        ...
        
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from the server."""
        ...


class ConnectionMode(Enum):
    """Connection mode for the MCP server."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


# Re-export official MCP transports with our naming for backward compatibility
class HTTPTransport:
    """HTTP transport for MCP client."""

    def __init__(self, url: str):
        self.url = url
        self.session = None
        
    async def connect(self) -> None:
        """Connect to the server."""
        import aiohttp
        self.session = aiohttp.ClientSession()
        
    async def disconnect(self) -> None:
        """Disconnect from the server."""
        if self.session:
            await self.session.close()
            
    async def send(self, data: Dict[str, Any]) -> None:
        """Send data to the server."""
        if not self.session:
            await self.connect()
        
        endpoint = "/mcp/request"
        if data.get("type") == "initialize":
            endpoint = "/mcp/initialize"
            
        await self.session.post(f"{self.url}{endpoint}", json=data)
        
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from the server."""
        if not self.session:
            await self.connect()
            
        # We're using the request response directly since MCP clients usually 
        # get responses from the same request they send
        async with self.session.get(f"{self.url}/mcp/result") as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                # Try the /mcp/sse endpoint as a fallback for server-sent events
                try:
                    url = f"{self.url}/mcp/sse"
                    event_source = EventSource(url, session=self.session)
                    await event_source.connect()
                    event = await event_source.get_event()
                    if event and event.data:
                        return json.loads(event.data)
                except Exception as e:
                    print(f"Error connecting to SSE: {e}")
                    pass
            return None


class StdioTransport:
    """
    Stdio transport from the official MCP SDK.
    
    This is a compatibility wrapper around the stdio_server function.
    For new code, use mcp.server.stdio.stdio_server directly.
    """

    def __init__(self):
        self.stdio_context = None
        self.read_stream = None
        self.write_stream = None
        
    async def connect(self):
        """Connect to stdin/stdout using the official MCP SDK."""
        self.stdio_context = stdio_server()
        streams = await self.stdio_context.__aenter__()
        self.read_stream, self.write_stream = streams
        return streams
        
    async def disconnect(self):
        """Disconnect from stdin/stdout."""
        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)
            
    async def send(self, data: Dict[str, Any]) -> None:
        """Send data through stdio."""
        if not self.write_stream:
            await self.connect()
        import json
        await self.write_stream.send(json.dumps(data))
        
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from stdio."""
        if not self.read_stream:
            await self.connect()
        try:
            data = await self.read_stream.receive()
            import json
            return json.loads(data)
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None


class SSETransport:
    """
    SSE transport for MCP client.
    
    This is a client-side transport that connects to an MCP server over SSE.
    """

    def __init__(self, url: str):
        self.url = url
        self.http_transport = HTTPTransport(url)
        
    async def connect(self) -> None:
        """Connect to the server."""
        await self.http_transport.connect()
        
    async def disconnect(self) -> None:
        """Disconnect from the server."""
        await self.http_transport.disconnect()
        
    async def send(self, data: Dict[str, Any]) -> None:
        """Send data to the server."""
        await self.http_transport.send(data)
        
    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from the server."""
        return await self.http_transport.receive()


class DirectTransport:
    """Direct in-process transport."""
    
    def __init__(self):
        raise NotImplementedError(
            "DirectTransport is not implemented yet. "
            "Use stdio_server or SseServerTransport instead."
        )


class EventSourceEvent:
    """A simple SSE event."""
    
    def __init__(self, event_type: str = "", data: str = "", id: str = "", retry: int = None):
        self.event_type = event_type
        self.data = data
        self.id = id
        self.retry = retry


class EventSource:
    """A simple EventSource implementation for SSE."""
    
    def __init__(self, url: str, session=None):
        self.url = url
        self.session = session
        self._response = None
        
    async def connect(self):
        """Connect to the SSE endpoint."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
            
        headers = {"Accept": "text/event-stream"}
        self._response = await self.session.get(self.url, headers=headers)
        
    async def get_event(self) -> Optional[EventSourceEvent]:
        """Parse and return the next event."""
        if not self._response:
            await self.connect()
            
        if self._response.status != 200:
            return None
            
        # Read a chunk of data
        chunk = await self._response.content.readline()
        if not chunk:
            return None
            
        lines = chunk.decode('utf-8').strip().split('\n')
        event = EventSourceEvent()
        
        for line in lines:
            if not line:
                continue
                
            if line.startswith('event:'):
                event.event_type = line[6:].strip()
            elif line.startswith('data:'):
                event.data = line[5:].strip()
            elif line.startswith('id:'):
                event.id = line[3:].strip()
            elif line.startswith('retry:'):
                try:
                    event.retry = int(line[6:].strip())
                except ValueError:
                    pass
                    
        return event
        
    async def close(self):
        """Close the connection."""
        if self._response:
            self._response.close()
            self._response = None

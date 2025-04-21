"""Transport implementations for MCP communication."""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

import httpx


class Transport(ABC):
    """Base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection with the server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection with the server."""
        pass

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message and receive response."""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """Listen for server notifications."""
        pass


class HTTPTransport(Transport):
    """Transport for HTTP/SSE communication."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient()
        self._sse_task: Optional[asyncio.Task] = None

    async def connect(self):
        await self._client.__aenter__()

    async def disconnect(self):
        if self._sse_task:
            self._sse_task.cancel()
        await self._client.__aexit__(None, None, None)

    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._client.post(f"{self.base_url}/mcp", json=message)
        return response.json()

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        async with self._client.stream(
            "GET", f"{self.base_url}/mcp/events"
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield data


class StdioTransport(Transport):
    """Transport for stdio communication with Python scripts."""

    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        self._process: Optional[asyncio.subprocess.Process] = None

    async def connect(self):
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self.script_path}")

        self._process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(self.script_path),
            "--stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def disconnect(self):
        if self._process:
            self._process.terminate()
            await self._process.wait()

    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self._process or not self._process.stdin:
            raise RuntimeError("Not connected")

        # Send message
        line = json.dumps(message) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

        # Read response
        if self._process.stdout:
            line = await self._process.stdout.readline()
            return json.loads(line.decode())
        raise RuntimeError("No stdout available")

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        if not self._process or not self._process.stdout:
            raise RuntimeError("Not connected")

        while True:
            line = await self._process.stdout.readline()
            if not line:
                break

            data = json.loads(line.decode())
            if "method" in data and data["method"] == "notify":
                yield data["params"]


class DirectTransport(Transport):
    """Transport for direct in-process communication with MCP server."""

    def __init__(self, server: Any):
        self.server = server

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        return await self.server.handle_mcp_message(message)

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        """Listen for server notifications."""
        # Direct transport doesn't support notifications yet
        # Could be implemented with asyncio.Queue if needed
        while False:
            yield {}


class MCPClient:
    """Client for connecting to MCP servers."""

    def __init__(self, transport: Transport):
        self.transport = transport

    async def __aenter__(self):
        await self.transport.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.transport.disconnect()

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with server."""
        return await self.transport.send(
            {"jsonrpc": "2.0", "method": "initialize", "params": {}}
        )

    async def list_tools(self) -> Dict[str, Any]:
        """Get list of available tools."""
        return await self.transport.send(
            {"jsonrpc": "2.0", "method": "tools/list", "params": {}}
        )

    async def call_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool with given arguments."""
        return await self.transport.send(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": name, "arguments": kwargs},
            }
        )

    async def list_resources(self) -> Dict[str, Any]:
        """Get list of available resources."""
        return await self.transport.send(
            {"jsonrpc": "2.0", "method": "resources/list", "params": {}}
        )

    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get content of a resource."""
        return await self.transport.send(
            {"jsonrpc": "2.0", "method": "resources/get", "params": {"uri": uri}}
        )

    async def subscribe(self, uri: str) -> Dict[str, Any]:
        """Subscribe to resource updates."""
        return await self.transport.send(
            {"jsonrpc": "2.0", "method": "resources/subscribe", "params": {"uri": uri}}
        )

    async def unsubscribe(self, uri: str) -> Dict[str, Any]:
        """Unsubscribe from resource updates."""
        return await self.transport.send(
            {
                "jsonrpc": "2.0",
                "method": "resources/unsubscribe",
                "params": {"uri": uri},
            }
        )

    async def listen_notifications(self):
        """Listen for server notifications."""
        async for notification in self.transport.listen():
            yield notification

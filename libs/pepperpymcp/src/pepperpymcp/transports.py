"""
Transport implementations for MCP.
"""

from typing import Any, Dict, Optional


class Transport:
    """Base transport class."""

    async def connect(self) -> None:
        """Connect to the transport."""
        pass

    async def disconnect(self) -> None:
        """Disconnect from the transport."""
        pass

    async def send(self, data: Dict[str, Any]) -> None:
        """Send data through the transport."""
        raise NotImplementedError()

    async def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from the transport."""
        raise NotImplementedError()


class HTTPTransport(Transport):
    """HTTP transport implementation."""

    def __init__(self, url: str):
        self.url = url


class StdioTransport(Transport):
    """Standard I/O transport implementation."""

    pass


class DirectTransport(Transport):
    """Direct in-process transport implementation."""

    pass

"""
Common transport utilities for MCP servers.
"""

from .client import MCPClient, MCPStdioClient, create_interactive_session
from .mcp import SimpleMCP
from .transports import DirectTransport, HTTPTransport, StdioTransport, Transport

__all__ = [
    "SimpleMCP",
    "MCPClient",
    "MCPStdioClient",
    "create_interactive_session",
    "MCPRequest",
    "MCPResponse",
    "MCPRequestHandler",
    "MCPServer",
    "Transport",
    "HTTPTransport",
    "StdioTransport",
    "DirectTransport",
]

import http.server
import json
import socketserver
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MCPRequest:
    """Model Context Protocol request."""

    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """Model Context Protocol response."""

    status: int
    body: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}


class MCPServer(http.server.HTTPServer):
    """Base MCP server implementation."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        super().__init__((host, port), MCPRequestHandler)
        self.routes = {}

    def register_route(self, path: str, handler):
        """Register a route handler."""
        self.routes[path] = handler


class MCPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handler for MCP requests."""

    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        request = MCPRequest(
            method="POST",
            path=self.path,
            headers=dict(self.headers),
            body=json.loads(body) if body else None,
        )

        handler = self.server.routes.get(self.path)
        if handler:
            response = handler(request)
            self.send_response(response.status)
            for k, v in response.headers.items():
                self.send_header(k, v)
            self.end_headers()
            if response.body:
                self.wfile.write(json.dumps(response.body).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

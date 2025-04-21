"""
Model Context Protocol (MCP) Implementation
"""

from .transport import (
    DirectTransport,
    HTTPTransport,
    MCPClient,
    MCPStdioClient,
    SimpleMCP,
    StdioTransport,
    create_interactive_session,
)
from .types import (
    JSON,
    AssistantMessage,
    JSONValue,
    Message,
    UserMessage,
)

__version__ = "0.1.0"

__all__ = [
    # Transport
    "SimpleMCP",
    "MCPClient",
    "MCPStdioClient",
    "create_interactive_session",
    "HTTPTransport",
    "StdioTransport",
    "DirectTransport",
    # Types
    "Message",
    "AssistantMessage",
    "UserMessage",
    "JSON",
    "JSONValue",
]

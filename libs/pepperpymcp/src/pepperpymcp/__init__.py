"""
Pepper Python MCP Package

This package provides extensions to the official MCP SDK, adding template support
and other utilities while ensuring strict adherence to the official implementation.
"""

__version__ = "0.1.1"

# Import from official MCP SDK
try:
    import mcp
except ImportError:
    raise ImportError(
        "The official MCP SDK is required. "
        "Please install it with: pip install mcp>=1.6.0"
    )

# Export key classes and functions from internal modules
from .mcp import (
    AssistantMessage,
    PepperFastMCP,
    SystemMessage,
    # Helper functions for message creation
    TextContent,
    UserMessage,
    create_mcp_server,
)

# Re-export transports from official MCP SDK
from .transports import (
    ConnectionMode,
    HTTPTransport,
    SSETransport,
    StdioTransport,
)

# Public exports - use these in your applications
__all__ = [
    # Core MCP classes
    "PepperFastMCP",
    "create_mcp_server",
    # Transport classes
    "ConnectionMode",
    "HTTPTransport",
    "SSETransport",
    "StdioTransport",
    # Helper functions for message creation
    "TextContent",
    "AssistantMessage",
    "UserMessage",
    "SystemMessage",
]

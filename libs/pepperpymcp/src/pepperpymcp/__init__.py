"""
PepperPyMCP - Enhanced Python SDK for the Model Context Protocol (MCP).

This package extends the official MCP SDK with additional utilities,
template support, and standardized components for building MCP
applications using the Host-Client-Server architecture.
"""

from .mcp import (
    create_mcp_server,
    PepperFastMCP,
    ConnectionMode,
    
    # Message creation utilities
    TextContent,
    AssistantRole,
    UserRole,
    SystemRole,
    CreateMessages,
    
    # Deprecated but maintained for compatibility
    AssistantMessage,
    UserMessage,
    SystemMessage,
)

from .host import (
    MCPHost,
    MCPClientWrapper,
)

from .sample_server import (
    SampleMCPServer,
    create_sample_server,
)

__version__ = "0.2.0"
__all__ = [
    # Server creation
    "create_mcp_server",
    "PepperFastMCP",
    "ConnectionMode",
    
    # Message utilities
    "TextContent",
    "AssistantRole",
    "UserRole",
    "SystemRole",
    "CreateMessages",
    "AssistantMessage",
    "UserMessage",
    "SystemMessage",
    
    # Host components
    "MCPHost",
    "MCPClientWrapper",
    
    # Sample implementations
    "SampleMCPServer",
    "create_sample_server",
]

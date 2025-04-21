"""
Common types used across MCP server examples.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Type aliases
JSON = Dict[str, Any]
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

# MCP specific types
MCPToolName = str
MCPToolDescription = str
MCPToolParameter = Dict[str, Any]
MCPToolParameters = List[MCPToolParameter]
MCPTool = Dict[str, Any]
MCPToolFunction = Callable[..., Any]

MCPResourceTemplate = str
MCPResourceDescription = str
MCPResource = Dict[str, Any]
MCPResourceFunction = Callable[..., Any]


# Existing dataclasses
@dataclass
class Tool:
    """Tool definition for MCP."""

    name: str
    description: str
    parameters: List[Dict[str, Any]]


@dataclass
class Resource:
    """Resource definition for MCP."""

    template: str
    description: str


@dataclass
class ContentItem:
    """Content item in an MCP response."""

    type: str
    text: str


@dataclass
class ToolResponse:
    """Response from an MCP tool call."""

    content: List[ContentItem]


@dataclass
class ResourceResponse:
    """Response from an MCP resource request."""

    content: str
    mimeType: str = "text/plain"


# Export all types
__all__ = [
    "JSON",
    "JSONValue",
    "MCPToolName",
    "MCPToolDescription",
    "MCPToolParameter",
    "MCPToolParameters",
    "MCPTool",
    "MCPToolFunction",
    "MCPResourceTemplate",
    "MCPResourceDescription",
    "MCPResource",
    "MCPResourceFunction",
    "Tool",
    "Resource",
    "ContentItem",
    "ToolResponse",
    "ResourceResponse",
]


@dataclass
class ModelContext:
    """Context information for model interactions."""

    workspace_path: str
    current_file: Optional[str] = None
    open_files: List[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    selection: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.open_files is None:
            self.open_files = []

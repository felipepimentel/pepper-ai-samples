"""
Common type definitions used across the MCP framework.
"""

from typing import Any, Dict, List, Union

# Type aliases
JSON = Dict[str, Any]
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

__all__ = ["JSON", "JSONValue"]

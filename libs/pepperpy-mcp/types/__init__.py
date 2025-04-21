"""
Type definitions for MCP.
"""

from .common import JSON, JSONValue
from .messages import AssistantMessage, Message, UserMessage

__all__ = ["Message", "AssistantMessage", "UserMessage", "JSON", "JSONValue"]

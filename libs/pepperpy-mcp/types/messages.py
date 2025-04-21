"""
Message type definitions for MCP.
"""

from dataclasses import dataclass


@dataclass
class Message:
    """Base class for all message types."""

    content: str
    role: str


@dataclass
class UserMessage(Message):
    """Message from a user."""

    def __init__(self, content: str):
        super().__init__(content=content, role="user")


@dataclass
class AssistantMessage(Message):
    """Message from an assistant."""

    def __init__(self, content: str):
        super().__init__(content=content, role="assistant")

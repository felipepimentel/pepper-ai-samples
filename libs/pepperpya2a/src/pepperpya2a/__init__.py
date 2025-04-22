"""
A2A (Agent-to-Agent) protocol implementation with simplified API.

This module provides a simplified interface for creating A2A-compatible agents
with a decorator-based API similar to FastAPI.
"""

from .a2a import PepperA2A, create_a2a_server

__all__ = ["create_a2a_server", "PepperA2A"]

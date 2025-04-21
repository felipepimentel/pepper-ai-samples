"""
Core MCP server implementation.
"""

from typing import Optional

import uvicorn
from fastapi import FastAPI


class SimpleMCP:
    """Simple MCP server implementation."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.app = FastAPI(title=name, description=description)
        self.tools = {}
        self.resources = {}
        self.prompts = {}

    def tool(self, name: Optional[str] = None):
        """Decorator to register a tool."""

        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func

        return decorator

    def resource(self, template: str):
        """Decorator to register a resource."""

        def decorator(func):
            self.resources[template] = func
            return func

        return decorator

    def prompt(self):
        """Decorator to register a prompt."""

        def decorator(func):
            self.prompts[func.__name__] = func
            return func

        return decorator

    def http_endpoint(self, path: str):
        """Decorator to register an HTTP endpoint."""
        return self.app.get(path)

    def get_template(self, name: str) -> str:
        """Get a template by name."""
        # TODO: Implement template loading
        return ""

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the server."""
        uvicorn.run(self.app, host=host, port=port)

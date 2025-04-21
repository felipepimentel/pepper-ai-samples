#!/usr/bin/env python
"""
SimpleMCP - A lightweight helper for creating MCP servers.
Provides a decorator-based API for both HTTP and stdio modes.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    get_type_hints,
)

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from common.types import (
    JSON,
    MCPResource,
    MCPResourceFunction,
    MCPTool,
    MCPToolFunction,
)

T = TypeVar("T")


class Message:
    """Base class for chat messages"""

    pass


class UserMessage(Message):
    """Represents a user message in a conversation"""

    def __init__(self, content: str):
        self.content = content
        self.role = "user"


class AssistantMessage(Message):
    """Represents an assistant message in a conversation"""

    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


@dataclass
class PromptResult(Generic[T]):
    """Result of a prompt execution"""

    content: T
    metadata: Dict[str, Any] = None


@dataclass
class PromptParameter:
    """Parameter definition for a prompt."""

    name: str
    type: str
    description: str = ""
    default: Any = None
    required: bool = True


class PromptSource(Enum):
    """Source type for prompt content."""

    INLINE = "inline"
    TEMPLATE = "template"
    FUNCTION = "function"


@dataclass
class PromptDefinition:
    """Complete definition of a prompt."""

    name: str
    description: str
    parameters: List[PromptParameter]
    source_type: PromptSource
    source: str
    handler: Optional[Callable] = None
    preprocessor: Optional[Callable] = None


class SimpleMCP:
    """A lightweight helper for creating MCP servers."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.http_handlers: Dict[str, Dict[str, Callable]] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # uri -> list of client_ids
        self.notifications: Dict[str, Callable] = {}  # notification_type -> handler
        self.websocket_clients: Dict[str, Set[WebSocket]] = {}
        self.prompts: Dict[str, Callable] = {}
        self.templates: Dict[str, str] = {}
        self.mounted_servers: Dict[
            str, Tuple[str, "SimpleMCP"]
        ] = {}  # prefix -> (name, server)

        # Create FastAPI app for HTTP mode
        self.app = FastAPI(title=name, description=description)
        self._setup_routes()
        self._load_templates_from_files()

    def _setup_routes(self):
        """Setup all HTTP routes."""
        # Register HTTP endpoints for MCP protocol
        self.app.post("/initialize")(self._handle_initialize)
        self.app.post("/tools/list")(self._handle_list_tools)
        self.app.post("/tools/call")(self._handle_call_tool)
        self.app.post("/resources/list")(self._handle_list_resources)
        self.app.post("/resources/get")(self._handle_get_resource)
        self.app.post("/resources/subscribe")(self._handle_resource_subscribe)
        self.app.post("/resources/unsubscribe")(self._handle_resource_unsubscribe)
        self.app.post("/prompts/list")(self._handle_list_prompts)
        self.app.post("/prompts/get")(self._handle_get_prompt)
        self.app.post("/prompts/render")(self._handle_render_prompt)

        # Add default HTTP endpoints
        self.app.get("/")(self._default_root)
        self.app.get("/help")(self._default_help)

        # Add WebSocket endpoint
        self.app.websocket("/ws/{client_id}")(self._handle_websocket)

        # Try to load default client.html if it exists
        if Path("client.html").exists():
            self.add_web_client()

    def _load_templates_from_files(self):
        """Load templates from files in the templates directory."""
        # Check for templates in current directory
        templates_dir = Path("templates")
        if not templates_dir.exists():
            return

        # Load all template files
        for template_file in templates_dir.glob("*.template"):
            try:
                template_name = template_file.stem  # filename without extension
                with open(template_file, "r") as f:
                    template_content = f.read()
                    self.templates[template_name] = template_content
                    print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Warning: Could not load template {template_file}: {e}")

        # Also check for individual template files in current directory
        for template_file in Path(".").glob("*.template"):
            try:
                template_name = template_file.stem
                with open(template_file, "r") as f:
                    template_content = f.read()
                    self.templates[template_name] = template_content
                    print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Warning: Could not load template {template_file}: {e}")

    def _default_root(self):
        """Default root endpoint."""
        return {"message": f"Welcome to {self.name}!"}

    def _default_help(self):
        """Default help endpoint."""
        return {
            "server_name": self.name,
            "description": self.description,
            "http_mode": "Access endpoints directly or use the web client at /client",
            "stdio_mode": "Run with --stdio to interact via MCP protocol",
            "available_tools": list(self.tools.keys()),
            "available_resources": list(self.resources.keys()),
        }

    def tool(self):
        """Register a function as an MCP tool."""

        def decorator(func: MCPToolFunction):
            # Get function metadata
            name = func.__name__
            doc = func.__doc__ or ""
            type_hints = get_type_hints(func)
            return_type = type_hints.pop("return", Any)

            # Register the tool
            self.tools[name] = {
                "func": func,
                "description": doc.strip(),
                "params": type_hints,
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def resource(self, template: str):
        """Register a function as an MCP resource provider."""

        def decorator(func: MCPResourceFunction):
            # Extract the URI template format
            # Example: "greeting://{name}" -> extract "name" as parameter
            params = []
            for part in template.split("/"):
                if "{" in part and "}" in part:
                    param_name = part.strip("{}")
                    params.append(param_name)

            # Register the resource
            self.resources[template] = {
                "func": func,
                "params": params,
                "description": (func.__doc__ or "").strip(),
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def http_endpoint(self, path: str, methods: List[str] = ["GET"]):
        """Register a function as an HTTP endpoint."""

        def decorator(func: Callable):
            for method in methods:
                method = method.lower()
                if method == "get":
                    self.app.get(path)(func)
                elif method == "post":
                    self.app.post(path)(func)
                elif method == "put":
                    self.app.put(path)(func)
                elif method == "delete":
                    self.app.delete(path)(func)

            return func

        return decorator

    def add_web_client(
        self, html_file: Optional[str] = None, html_content: Optional[str] = None
    ):
        """Add a web client to the server.

        Args:
            html_file: Path to an HTML file to load. If not provided, will try to load 'client.html'
            html_content: Direct HTML content string. Only used if html_file is not provided or doesn't exist
        """
        content = None

        # Try to load from file first
        if html_file:
            try:
                with open(html_file, "r") as f:
                    content = f.read()
            except Exception as e:
                print(f"Warning: Could not load web client from {html_file}: {e}")

        # Try default client.html if no file specified
        elif Path("client.html").exists():
            try:
                with open("client.html", "r") as f:
                    content = f.read()
            except Exception as e:
                print(f"Warning: Could not load default client.html: {e}")

        # Fall back to provided content or default template
        if not content:
            content = (
                html_content
                if html_content
                else """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MCP Web Client</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; }
        button { background: #4CAF50; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
        input { padding: 8px; width: 100%; box-sizing: border-box; margin-bottom: 10px; }
        pre { background: #f8f8f8; border: 1px solid #ddd; padding: 10px; overflow: auto; }
    </style>
</head>
<body>
    <h1>MCP Web Client</h1>
    <div class="card">
        <h2>Server Info</h2>
        <button onclick="fetchRoot()">Get Server Info</button>
        <pre id="rootResponse">...</pre>
    </div>
    <div id="tools" class="card">
        <h2>Tools</h2>
        <p>Loading available tools...</p>
    </div>
    <script>
        async function fetchRoot() {
            const resp = await fetch('/');
            const data = await resp.json();
            document.getElementById('rootResponse').textContent = JSON.stringify(data, null, 2);
        }
        
        async function loadTools() {
            try {
                const resp = await fetch('/tools/list', {method: 'POST'});
                const data = await resp.json();
                const toolsDiv = document.getElementById('tools');
                let html = '<h2>Available Tools</h2>';
                
                if (data.tools && data.tools.length > 0) {
                    data.tools.forEach(tool => {
                        html += `<div class="tool-card">
                            <h3>${tool.name}</h3>
                            <p>${tool.description}</p>
                        </div>`;
                    });
                } else {
                    html += '<p>No tools available</p>';
                }
                
                toolsDiv.innerHTML = html;
            } catch (e) {
                console.error('Error loading tools:', e);
            }
        }
        
        // Initialize
        fetchRoot();
        loadTools();
    </script>
</body>
</html>"""
            )

        # Add the client endpoint
        @self.app.get("/client", response_class=HTMLResponse)
        async def web_client():
            return content

    def notification(self, notification_type: str):
        """Register a function as a notification handler.

        Args:
            notification_type: Type of notification to handle (e.g. "resources/updated")
        """

        def decorator(func: Callable):
            self.notifications[notification_type] = func
            return func

        return decorator

    def prompt(self):
        """Decorator to register a prompt generator function.

        The function should have type hints for all parameters and return type.
        The docstring will be used as the prompt description.

        Example:
            @mcp.prompt()
            def code_review(code: str, focus: Optional[str] = None) -> str:
                '''Generates a code review request with optional focus area.'''
                if focus:
                    return f"Please review this code, focusing on {focus}:\\n```\\n{code}\\n```"
                return f"Please review this code:\\n```\\n{code}\\n```"
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            # Get function metadata
            sig = inspect.signature(func)
            doc = inspect.getdoc(func) or ""
            hints = get_type_hints(func)

            # Register the prompt
            self.prompts[func.__name__] = {
                "handler": func,
                "description": doc,
                "parameters": {
                    name: {
                        "type": hints.get(name, Any),
                        "default": param.default
                        if param.default != param.empty
                        else None,
                        "required": param.default == param.empty,
                    }
                    for name, param in sig.parameters.items()
                },
                "return_type": hints.get("return", Any),
            }

            @wraps(func)
            async def wrapper(*args, **kwargs) -> PromptResult[T]:
                try:
                    result = await func(*args, **kwargs)
                    return PromptResult(
                        content=result, metadata={"prompt_name": func.__name__}
                    )
                except Exception as e:
                    raise ValueError(
                        f"Error executing prompt {func.__name__}: {str(e)}"
                    )

            return wrapper

        return decorator

    def template(self, name: str, file: Optional[str] = None):
        """Register a template.

        Can be used in three ways:
        1. As a decorator for a function whose docstring is the template
        2. With a file parameter to load template from a specific file
        3. Without parameters to load from a .template file matching the name

        Args:
            name: Name of the template
            file: Optional path to template file
        """

        def decorator(func: Optional[Callable] = None) -> Optional[Callable]:
            if func is not None:
                # Used as a decorator
                self.templates[name] = func.__doc__ or ""
                return func

            # Used as a regular method
            try:
                if file:
                    # Load from specified file
                    with open(file, "r") as f:
                        self.templates[name] = f.read()
                else:
                    # Try to load from .template file
                    template_file = Path(f"{name}.template")
                    if template_file.exists():
                        with open(template_file, "r") as f:
                            self.templates[name] = f.read()
                    else:
                        print(f"Warning: Template file {template_file} not found")
            except Exception as e:
                print(f"Warning: Could not load template {name}: {e}")

            return None

        return decorator

    async def _handle_resource_subscribe(self, request: Request) -> JSON:
        """Handle resource subscription requests."""
        data = await request.json()
        uri = data.get("uri")
        client_id = data.get("client_id")

        if not uri or not client_id:
            raise HTTPException(status_code=400, detail="Missing uri or client_id")

        if uri not in self.subscriptions:
            self.subscriptions[uri] = []

        if client_id not in self.subscriptions[uri]:
            self.subscriptions[uri].append(client_id)

        return {"status": "subscribed"}

    async def _handle_resource_unsubscribe(self, request: Request) -> JSON:
        """Handle resource unsubscription requests."""
        data = await request.json()
        uri = data.get("uri")
        client_id = data.get("client_id")

        if not uri or not client_id:
            raise HTTPException(status_code=400, detail="Missing uri or client_id")

        if uri in self.subscriptions and client_id in self.subscriptions[uri]:
            self.subscriptions[uri].remove(client_id)
            if not self.subscriptions[uri]:
                del self.subscriptions[uri]

        return {"status": "unsubscribed"}

    async def notify_resource_update(self, uri: str, content: Any = None):
        """Notify subscribers about a resource update."""
        if uri in self.subscriptions:
            notification = {"type": "resources/updated", "uri": uri, "content": content}

            # Send notifications through appropriate channel
            if hasattr(self, "current_mode") and self.current_mode == "stdio":
                # Stdio mode - send through stdout
                for client_id in self.subscriptions[uri]:
                    response = {
                        "jsonrpc": "2.0",
                        "method": "notify",
                        "params": notification,
                    }
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            else:
                # HTTP mode - send through WebSocket
                for client_id in self.subscriptions[uri]:
                    if client_id in self.websocket_clients:
                        for websocket in self.websocket_clients[client_id]:
                            try:
                                await websocket.send_json(notification)
                            except WebSocketDisconnect:
                                continue

    async def _handle_initialize(self, request: Request) -> JSON:
        """Handle the initialize message."""
        # Get capabilities from all mounted servers
        mounted_capabilities = []
        for prefix, (name, server) in self.mounted_servers.items():
            mounted_capabilities.append(
                {
                    "name": name,
                    "prefix": prefix,
                    "capabilities": {
                        "resources": bool(server.resources),
                        "tools": bool(server.tools),
                        "prompts": bool(server.prompts),
                        "notifications": True,
                    },
                }
            )

        return {
            "name": self.name,
            "version": "1.0.0",
            "description": self.description,
            "capabilities": {
                "resources": True,
                "tools": True,
                "prompts": True,
                "notifications": True,
                "composition": bool(self.mounted_servers),
            },
            "mounted_servers": mounted_capabilities,
        }

    async def _handle_list_tools(self, request: Request) -> JSON:
        """Handle the tools/list message."""
        result = []

        # Add local tools
        for name, tool in self.tools.items():
            result.append(
                {
                    "name": name,
                    "description": tool["description"],
                    "parameters": [
                        {
                            "name": param_name,
                            "type": str(param_info["type"]),
                            "required": param_info["required"],
                            "default": param_info["default"],
                        }
                        for param_name, param_info in tool["params"].items()
                    ],
                }
            )

        # Add mounted server tools with prefixes
        for prefix, (_, server) in self.mounted_servers.items():
            mounted_tools = await server._handle_list_tools(request)
            for tool in mounted_tools["tools"]:
                tool["name"] = f"{prefix}/{tool['name']}"
                result.append(tool)

        return {"tools": result}

    async def _handle_call_tool(self, request: Request) -> JSON:
        """Handle the tools/call message."""
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})

        # Find appropriate server and delegate
        real_name, server = self._get_server_for_tool(tool_name)
        if server is not self:
            # Modify request for mounted server
            data["name"] = real_name
            return await server._handle_call_tool(request)

        if real_name not in self.tools:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

        tool = self.tools[real_name]
        try:
            result = await tool["func"](**arguments)
            return {"result": str(result)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def _handle_list_resources(self, request: Request) -> JSON:
        """Handle the resources/list message."""
        result = []

        # Add local resources
        for template, resource in self.resources.items():
            result.append(
                {"template": template, "description": resource["description"]}
            )

        # Add mounted server resources with prefixes
        for prefix, (_, server) in self.mounted_servers.items():
            mounted_resources = await server._handle_list_resources(request)
            for resource in mounted_resources["resources"]:
                resource["template"] = f"{prefix}+{resource['template']}"
                result.append(resource)

        return {"resources": result}

    async def _handle_get_resource(self, request: Request) -> JSON:
        """Handle the resources/get message."""
        data = await request.json()
        uri = data.get("uri", "")

        # Find appropriate server and delegate
        real_uri, server = self._get_server_for_resource(uri)
        if server is not self:
            # Modify request for mounted server
            data["uri"] = real_uri
            return await server._handle_get_resource(request)

        # Find matching resource template
        for template, resource in self.resources.items():
            # Basic template matching (can be improved)
            template_parts = template.split("/")
            uri_parts = real_uri.split("/")

            if len(template_parts) != len(uri_parts):
                continue

            is_match = True
            args = {}

            for tp, up in zip(template_parts, uri_parts):
                if tp.startswith("{") and tp.endswith("}"):
                    param_name = tp.strip("{}")
                    args[param_name] = up
                elif tp != up:
                    is_match = False
                    break

            if is_match:
                try:
                    content = await resource["func"](**args)
                    return {"content": content}
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))

        raise HTTPException(status_code=404, detail=f"Resource {uri} not found")

    async def _handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connections for real-time notifications."""
        await websocket.accept()

        try:
            # Add client to active connections
            if client_id not in self.websocket_clients:
                self.websocket_clients[client_id] = set()
            self.websocket_clients[client_id].add(websocket)

            # Keep connection alive and handle messages
            while True:
                data = await websocket.receive_json()

                # Handle subscription requests through WebSocket
                if data.get("type") == "subscribe":
                    uri = data.get("uri")
                    if uri:
                        if uri not in self.subscriptions:
                            self.subscriptions[uri] = []
                        if client_id not in self.subscriptions[uri]:
                            self.subscriptions[uri].append(client_id)
                            await websocket.send_json(
                                {"type": "subscribed", "uri": uri}
                            )

                elif data.get("type") == "unsubscribe":
                    uri = data.get("uri")
                    if (
                        uri
                        and uri in self.subscriptions
                        and client_id in self.subscriptions[uri]
                    ):
                        self.subscriptions[uri].remove(client_id)
                        if not self.subscriptions[uri]:
                            del self.subscriptions[uri]
                        await websocket.send_json({"type": "unsubscribed", "uri": uri})

        except WebSocketDisconnect:
            # Clean up on disconnect
            if client_id in self.websocket_clients:
                self.websocket_clients[client_id].remove(websocket)
                if not self.websocket_clients[client_id]:
                    del self.websocket_clients[client_id]

            # Remove from all subscriptions
            for uri in list(self.subscriptions.keys()):
                if client_id in self.subscriptions[uri]:
                    self.subscriptions[uri].remove(client_id)
                    if not self.subscriptions[uri]:
                        del self.subscriptions[uri]

    def handle_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single MCP request in stdio mode."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                result = {
                    "name": self.name,
                    "version": "1.0.0",
                    "description": self.description,
                    "capabilities": {"resources": True, "tools": True},
                }
            elif method == "tools/list":
                result = {"tools": []}
                for name, tool in self.tools.items():
                    params = []
                    for param_name, param_type in tool["params"].items():
                        params.append(
                            {
                                "name": param_name,
                                "type": str(param_type),
                                "description": "",
                                "required": True,
                            }
                        )

                    result["tools"].append(
                        {
                            "name": name,
                            "description": tool["description"],
                            "parameters": params,
                        }
                    )
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"message": f"Tool {tool_name} not found"},
                    }

                tool = self.tools[tool_name]
                try:
                    tool_result = tool["func"](**arguments)
                    result = {"content": [{"type": "text", "text": str(tool_result)}]}
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"message": str(e)},
                    }
            elif method == "resources/list":
                result = {"resources": []}
                for template, resource in self.resources.items():
                    result["resources"].append(
                        {"template": template, "description": resource["description"]}
                    )
            elif method == "resources/get":
                uri = params.get("uri", "")

                # Find matching resource template (similar to HTTP handler)
                resource_found = False
                for template, resource in self.resources.items():
                    template_parts = template.split("/")
                    uri_parts = uri.split("/")

                    if len(template_parts) != len(uri_parts):
                        continue

                    is_match = True
                    args = {}

                    for tp, up in zip(template_parts, uri_parts):
                        if tp.startswith("{") and tp.endswith("}"):
                            param_name = tp.strip("{}")
                            args[param_name] = up
                        elif tp != up:
                            is_match = False
                            break

                    if is_match:
                        try:
                            content = resource["func"](**args)
                            result = {"content": content, "mimeType": "text/plain"}
                            resource_found = True
                            break
                        except Exception as e:
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {"message": str(e)},
                            }

                if not resource_found:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"message": f"Resource {uri} not found"},
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"message": f"Unknown method: {method}"},
                }

            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"message": f"Internal error: {str(e)}"},
            }

    def handle_stdio_mode(self):
        """Handle communication in stdio mode."""
        print("Starting MCP server in stdio mode...", file=sys.stderr)
        self.current_mode = "stdio"

        while True:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                # Parse the request
                request = json.loads(line)

                # Process the request
                response = self.handle_stdio_request(request)

                # Write the response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"message": str(e)},
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

    def run(self):
        """Run the server based on command line arguments."""
        parser = argparse.ArgumentParser(description=f"{self.name} MCP Server")
        parser.add_argument(
            "--stdio", action="store_true", help="Run in stdio mode for MCP protocol"
        )
        parser.add_argument(
            "--host", default="0.0.0.0", help="Host to bind server to (HTTP mode)"
        )
        parser.add_argument(
            "--port", type=int, default=8000, help="Port to bind server to (HTTP mode)"
        )

        args = parser.parse_args()

        if args.stdio:
            self.handle_stdio_mode()
        else:
            print(f"Starting {self.name} server on http://{args.host}:{args.port}")
            uvicorn.run(self.app, host=args.host, port=args.port)

    async def _handle_list_prompts(self, request: Request) -> JSON:
        """Handle the prompts/list message."""
        result = []
        for name, prompt in self.prompts.items():
            result.append(
                {
                    "name": name,
                    "description": prompt["description"],
                    "parameters": [
                        {
                            "name": param_name,
                            "type": str(param_info["type"]),
                            "required": param_info["required"],
                            "default": param_info["default"],
                        }
                        for param_name, param_info in prompt["parameters"].items()
                    ],
                }
            )
        return {"prompts": result}

    async def _handle_get_prompt(self, request: Request) -> JSON:
        """Handle the prompts/get message."""
        data = await request.json()
        name = data.get("name")

        if name not in self.prompts:
            raise HTTPException(status_code=404, detail=f"Prompt {name} not found")

        prompt = self.prompts[name]
        return {
            "name": name,
            "description": prompt["description"],
            "parameters": [
                {
                    "name": param_name,
                    "type": str(param_info["type"]),
                    "required": param_info["required"],
                    "default": param_info["default"],
                }
                for param_name, param_info in prompt["parameters"].items()
            ],
            "return_type": prompt["return_type"],
        }

    async def _handle_render_prompt(self, request: Request) -> JSON:
        """Handle the prompts/render message."""
        data = await request.json()
        name = data.get("name")
        values = data.get("values", {})

        if name not in self.prompts:
            raise HTTPException(status_code=404, detail=f"Prompt {name} not found")

        prompt = self.prompts[name]

        # Validate parameters
        for param_name, param_info in prompt["parameters"].items():
            if param_name not in values and param_info["required"]:
                raise HTTPException(
                    status_code=400, detail=f"Missing required parameter: {param_name}"
                )

        try:
            # Execute the prompt
            result = await prompt["handler"](**values)

            # Handle different return types
            if isinstance(result.content, (str, int, float, bool)):
                content = str(result.content)
            elif isinstance(result.content, list) and all(
                isinstance(m, Message) for m in result.content
            ):
                content = [
                    {"role": m.role, "content": m.content} for m in result.content
                ]
            else:
                content = result.content

            return {"result": content, "metadata": result.metadata}

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error rendering prompt: {str(e)}"
            )

    def mount(self, prefix: str, server: "SimpleMCP", name: Optional[str] = None):
        """Mount another MCP server under a prefix.

        Args:
            prefix: URL prefix for the mounted server
            server: SimpleMCP server instance to mount
            name: Optional name override for the mounted server
        """
        if not prefix:
            raise ValueError("Prefix cannot be empty")

        if prefix in self.mounted_servers:
            raise ValueError(f"Prefix '{prefix}' already in use")

        # Store mounted server
        self.mounted_servers[prefix] = (name or server.name, server)

        # Mount FastAPI app
        self.app.mount(f"/{prefix}", server.app)

    def _get_server_for_tool(self, tool_name: str) -> Tuple[str, "SimpleMCP"]:
        """Get the appropriate server for a tool name."""
        parts = tool_name.split("/")
        if len(parts) > 1:
            prefix = parts[0]
            if prefix in self.mounted_servers:
                return parts[1], self.mounted_servers[prefix][1]
        return tool_name, self

    def _get_server_for_resource(self, uri: str) -> Tuple[str, "SimpleMCP"]:
        """Get the appropriate server for a resource URI."""
        parts = uri.split("+")
        if len(parts) > 1:
            prefix = parts[0]
            if prefix in self.mounted_servers:
                return "+".join(parts[1:]), self.mounted_servers[prefix][1]
        return uri, self

# Common Utilities

This directory contains common utilities and components shared across different examples in the Pepper AI repository.

## Transport

The `transport` module provides utilities for building MCP (Model-Controller-Protocol) servers:

### SimpleMCP

`SimpleMCP` is a lightweight helper for creating MCP servers. It provides a decorator-based API for both HTTP and stdio modes.

#### Features:
- Decorator-based API for tools and resources
- Auto-extraction of function metadata (parameters, return types, docstrings)
- Support for both HTTP and stdio modes
- Command-line argument parsing
- Error handling and protocol compliance

#### Example Usage:

```python
from common.transport import SimpleMCP

# Create server
mcp = SimpleMCP("Example Server", "Optional description")

# Add tools
@mcp.tool()
def greeting(name: str = "World") -> str:
    """Return a friendly greeting"""
    return f"Hello, {name}!"

# Add resources
@mcp.resource("quote://{category}")
def get_quote(category: str) -> str:
    """Get a quote by category"""
    quotes = {"motivation": "The best way to predict the future is to create it."}
    return quotes.get(category, "No quote found for that category.")

# Run server
if __name__ == "__main__":
    mcp.run()
```

#### Running the Server:
- HTTP mode (default): `python server.py` (serves on http://0.0.0.0:8000)
- stdio mode: `python server.py --stdio`
- Custom host/port: `python server.py --host 127.0.0.1 --port 8080`

### MCP Client

The module also provides generic clients for interacting with MCP servers:

#### MCPClient

HTTP-based client for MCP servers.

```python
from common.transport import MCPClient

# Create client
client = MCPClient(host="localhost", port=8000)

# Initialize connection
info = client.initialize()
print(f"Connected to: {info['name']}")

# List available tools
tools = client.list_tools()
for tool in tools:
    print(f"Tool: {tool['name']} - {tool['description']}")

# Call a tool
result = client.call_tool("greeting", {"name": "Alice"})
print(f"Result: {result}")

# List resources
resources = client.list_resources()
for resource in resources:
    print(f"Resource: {resource['template']}")

# Get a resource
content = client.get_resource("quote://motivation")
print(f"Content: {content}")
```

#### MCPStdioClient

Stdio-based client for MCP servers.

```python
from common.transport import MCPStdioClient

# Create client with command to start the server
client = MCPStdioClient(["python", "server.py", "--stdio"])

# Start the server
client.start()

try:
    # Same API as MCPClient
    info = client.initialize()
    tools = client.list_tools()
    result = client.call_tool("greeting", {"name": "Bob"})
    print(f"Result: {result}")
finally:
    # Stop the server
    client.stop()
```

#### Interactive Session

The module provides a helper function to create an interactive session with any MCP server:

```python
from common.transport import MCPClient, create_interactive_session

client = MCPClient()
create_interactive_session(client)
```

You can also run the client directly as a script:

```bash
# HTTP mode
python -m common.transport.client --host localhost --port 8000

# Stdio mode
python -m common.transport.client --stdio --cmd python server.py --stdio
```

## Available Modules

### MCP Server Utilities (`mcp-server.js`)

Helper functions for creating and running MCP servers with different transports:

- `createStdioServer(config, setupFn)` - Create an MCP server using standard input/output transport (for Claude Desktop)
- `createHttpServer(config, setupFn, startPort)` - Create an MCP server using HTTP transport with auto port detection

Example usage:
```javascript
import { createStdioServer } from "../common/mcp-server.js";

// Server configuration
const serverConfig = {
  name: "My MCP Server",
  version: "1.0.0",
  description: "Example MCP server"
};

// Setup function to define resources and tools
async function setupServer(server) {
  // Add resources and tools here
  // ...
}

// Start the server
createStdioServer(serverConfig, setupServer).catch(error => {
  console.error('Failed to start server:', error);
});
```

### HTTP Transport (`transport/http.js`)

HTTP transport implementation for MCP servers:

- `HttpTransport` - Class implementing HTTP transport for MCP servers
- `findFreePort(startPort)` - Utility to find an available TCP port
- `createHttpTransport(startPort)` - Create an HTTP transport on an available port

This module is used internally by `createHttpServer()` but can also be used directly if needed.

### HTTP Server Demo (`http-server-demo.js`)

A demonstration of how to use the HTTP transport for testing MCP servers without requiring Claude Desktop.

To run the demo:
```bash
node common/http-server-demo.js
```

This will start a simple HTTP-based MCP server that auto-detects an available port.

## Implementation Details

The standard approach for MCP servers is to use stdin/stdout transport for communication with Claude Desktop. However, for testing and development purposes, the HTTP transport can be useful as it allows:

1. Testing with HTTP clients
2. Auto-detection of free ports
3. Visual display of the server URL in the console 
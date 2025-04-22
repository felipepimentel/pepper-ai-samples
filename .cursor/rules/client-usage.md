# MCP Client Usage Guide

## Official MCP Client

For all new development, use the official MCP SDK client:

```python
from mcp.client import ClientSession, StdioServerParameters
from mcp import types

# Create server parameters
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            info = await session.initialize()
            print(f"Connected to: {info.server_name}")
            
            # List available tools
            tools = await session.list_tools()
            for tool in tools:
                print(f"Tool: {tool.name}")
                
            # Call tool
            result = await session.call_tool("tool_name", {"param1": "value"})
            print(result)
```

## PepperPyMCP Client (Legacy)

The `pepperpymcp` client can be used for simple utilities and legacy code:

```python
from pepperpymcp import MCPClient, HTTPTransport

# Choose appropriate transport
transport = HTTPTransport("http://localhost:8000")
client = MCPClient(transport)

# Initialize connection
info = await client.initialize()
print(f"Connected to: {info['name']}")

# List available tools
tools = await client.list_tools()
for tool in tools["tools"]:
    print(f"Tool: {tool['name']}")

# Call tools
result = await client.call_tool("tool_name", param1="value")
print(result["result"])
```

## Transport Selection

Choose the appropriate transport based on your use case:

### Official MCP SDK
```python
from mcp.client.stdio import stdio_client
from mcp.client.http import http_client

# For stdio transport
async with stdio_client(server_params) as (read, write):
    # Use the client with (read, write) streams

# For HTTP transport
async with http_client("http://localhost:8000") as (read, write):
    # Use the client with (read, write) streams
```

### PepperPyMCP (Legacy)
```python
from pepperpymcp import HTTPTransport, StdioTransport, DirectTransport

# HTTP/WebSocket transport
transport = HTTPTransport("http://localhost:8000")

# Standard I/O transport
transport = StdioTransport(["python", "server.py", "--stdio"])

# Direct in-process transport
transport = DirectTransport()
```

## Best Practices

1. **Use async context manager:**
```python
# Official SDK
async with ClientSession(read, write) as client:
    await client.initialize()

# PepperPyMCP (legacy)
async with MCPClient(transport) as client:
    await client.initialize()
```

2. **Handle errors appropriately:**
```python
# Official SDK
try:
    result = await client.call_tool("tool_name")
except Exception as e:
    print(f"Error: {e}")

# PepperPyMCP (legacy)
try:
    result = await client.call_tool("tool_name")
except Exception as e:
    print(f"Error: {e}")
```

3. **Close connections:**
```python
# Official SDK - done automatically with context manager

# PepperPyMCP (legacy)
await transport.disconnect()
```

## Migration Path

When migrating from pepperpymcp to the official MCP SDK:

1. Replace `MCPClient` with `ClientSession`
2. Update transport initialization to use `stdio_client` or `http_client`
3. Adapt response handling to match the official SDK's response format
4. Update error handling to match the official SDK's exceptions

## Example Comparisons

### Initializing Connection

```python
# Official SDK
async with ClientSession(read, write) as session:
    info = await session.initialize()
    print(f"Connected to: {info.server_name}")

# PepperPyMCP (legacy)
client = MCPClient(transport)
info = await client.initialize()
print(f"Connected to: {info['name']}")
```

### Calling Tools

```python
# Official SDK
result = await session.call_tool("greeting", {"name": "World"})
print(result)

# PepperPyMCP (legacy)
result = await client.call_tool("greeting", name="World")
print(result["result"])
```

### Accessing Resources

```python
# Official SDK
content, mime_type = await session.read_resource("data://123")
print(content)

# PepperPyMCP (legacy)
content = await client.get_resource("data://123")
print(content)
``` 
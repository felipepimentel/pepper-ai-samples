# PepperPyMCP

Enhanced Python SDK for the Model Context Protocol (MCP), providing extended functionality for building MCP applications following the Host-Client-Server architecture.

## Features

- **Complete MCP Architecture**: Implements the full Host-Client-Server model
- **Template Support**: Load and use templates for prompts and resources
- **Message Utilities**: Simplified message creation for MCP interactions
- **Graceful Shutdown**: Proper cleanup and resource management
- **Web Interface**: Built-in web interface for the Host component
- **Sample Implementations**: Ready-to-use server implementations

## Installation

```bash
pip install pepperpymcp
```

## MCP Architecture

The MCP architecture consists of three primary components:

### 1. Host

The host is responsible for:
- Creating and managing multiple clients
- Coordinating access between clients
- Aggregating context for AI interactions
- Enforcing security policies

```python
from pepperpymcp import MCPHost

# Create a host
host = MCPHost("My MCP Host")

# Create clients
data_client = await host.create_client("http://data-server:8001", "data")
search_client = await host.create_client("http://search-server:8002", "search")

# Initialize clients
await data_client.initialize()
await search_client.initialize()

# Start web interface
web_interface = await host.start_web_interface(host="0.0.0.0", port=8000)
```

### 2. Client

Each client maintains a 1:1 connection with a server:

```python
# Clients are created and managed by the host
weather_client = await host.create_client("http://weather-server:8001", "weather")

# Call a tool on the server
result = await weather_client.call_tool("get_weather", location="new_york")

# Get a resource from the server
data = await weather_client.get_resource("weather://new_york")
```

### 3. Server

Servers provide specialized capabilities through tools and resources:

```python
from pepperpymcp import create_mcp_server

# Create an MCP server
server = create_mcp_server("Weather Server", "Provides weather data")

# Register a tool
@server.tool()
async def get_weather(location: str) -> dict:
    """Get current weather for a location."""
    # Implementation...
    return {"temperature": 25, "condition": "Sunny"}

# Register a resource
@server.resource("weather://{location}")
async def weather_resource(location: str) -> bytes:
    """Get weather data as a resource."""
    # Implementation...
    return json.dumps(weather_data).encode("utf-8")

# Run the server
await server.run(host="0.0.0.0", port=8001)
```

## Quick Start

### Create and Run a Server

```python
from pepperpymcp import create_sample_server

# Create a sample server with pre-configured tools and resources
server = create_sample_server("My Server", "A sample MCP server")

# Run the server
server.run_sync(host="0.0.0.0", port=8000)
```

### Complete MCP Demo

```python
from pepperpymcp import MCPHost, create_sample_server

async def main():
    # Create the host
    host = MCPHost("Demo Host")
    
    # Start a server
    server = create_sample_server()
    server_task = asyncio.create_task(server.run(host="127.0.0.1", port=8001))
    
    # Connect a client to the server
    client = await host.create_client("http://127.0.0.1:8001", "data")
    await client.initialize()
    
    # Start web interface
    web_interface = await host.start_web_interface(host="0.0.0.0", port=8000)
    
    # Process a query
    result = await host.process_query("Get data for item_1")
    print(result)
    
    # Keep the demo running
    try:
        await server_task
    except asyncio.CancelledError:
        # Clean up
        await host.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Server Components

### Tools

Tools are functions that can be called by clients:

```python
@server.tool()
async def search_items(query: str, limit: int = 10) -> dict:
    """Search for items matching the query."""
    # Implementation...
    return {"results": results, "count": len(results)}
```

### Resources

Resources are URI-addressable data points:

```python
@server.resource("document://{id}")
async def get_document(id: str) -> bytes:
    """Get document by ID."""
    # Implementation...
    return document_content
```

### HTTP Endpoints

Custom HTTP endpoints for web access:

```python
@server.http_endpoint("/status")
async def get_status():
    """Get server status."""
    return {"status": "running", "name": server.name}
```

## License

MIT 
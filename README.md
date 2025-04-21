# Pepper AI Samples

This repository contains sample code and examples for building MCP (Model-Controller-Protocol) servers with the Pepper AI framework.

## Project Structure

- **00-hello-world**: A simple "Hello World" MCP server example
- **01-file-explorer**: MCP server example for file operations
- **02-web-search**: MCP server example for web search operations
- **03-database-query**: MCP server example for database operations
- **04-agent-system**: MCP server example for agent-based systems
- **05-fraud-detection**: MCP server example for fraud detection

## Common Utilities

The `common/` directory contains shared utilities used across all examples:

- **transport**: Utilities for MCP server creation and communication
  - `SimpleMCP`: Decorator-based API for creating MCP servers
  - `MCPClient`: Generic client for interacting with MCP servers via HTTP
  - `MCPStdioClient`: Generic client for interacting with MCP servers via stdio
- **types**: Common data types and structures

## Getting Started

Start with the hello-world example to understand the basic concepts:

```bash
cd 00-hello-world
python -m pip install -e .

# Run the server
python server.py

# In another terminal, run the client
python client.py

# Or try the stdio mode (server and client in one process)
python stdio_client.py
```

Each example has its own README with more detailed instructions.

## Development Guidelines

When contributing to this repository, follow these guidelines:

- Each example should have minimal files - generally just a single `server.py` file
- Common code should be in the `common/` directory to be reused across examples
- Examples should be simple and focused on demonstrating one concept
- Follow the MCP server pattern demonstrated in the hello-world example

## Quick Start
```bash
# Setup and activate environment
./tools/setup-env.sh && source .venv/bin/activate

# Run your first example
cd 00-hello-world && python src/server.py
```

## Running MCP Servers

There are two main ways to run and interact with MCP servers:

### 1. stdio Mode (Direct Model Integration)
Best for direct model integration (Claude, GPT-4, etc). Uses the MCP protocol over stdio:

```bash
# Using uvx (recommended)
uvx run src/server.py --stdio

# Alternative methods
python src/server.py --stdio
mcp run src/server.py
```

### 2. SSE Mode (Web/HTTP Integration)
Best for web applications and HTTP clients. Runs as a web server with Server-Sent Events:

```bash
# Default HTTP mode (port 8000)
python src/server.py

# Custom port
python src/server.py --port 3000

# With CORS enabled
python src/server.py --cors-origins "*"
```

#### SSE Integration Examples

1. Direct HTTP Client:
```html
<!-- client.html -->
<script>
const sse = new EventSource('http://localhost:8000/stream');
sse.onmessage = (event) => {
    console.log(JSON.parse(event.data));
};
</script>
```

2. FastAPI/Starlette Mount:
```python
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")
app = Starlette(routes=[Mount('/', app=mcp.sse_app())])
```

3. Custom Domain:
```python
from starlette.routing import Host
app.router.routes.append(
    Host('mcp.myapp.com', app=mcp.sse_app())
)
```

### Testing Your Server

Each example includes multiple ways to test:

1. VS Code Integration:
   - Install MCP Extension
   - Open Command Palette: "MCP: Start Server"
   - Or use the included launch config

2. API Testing:
   - Use `api.http` files
   - Test endpoints directly
   - View responses in VS Code

3. Web Client:
   - Open `client.html` in browser
   - Test server responses
   - Real-time updates via SSE

4. Command Line:
   ```bash
   # Test stdio mode
   echo '{"jsonrpc":"2.0","method":"initialize"}' | uvx run src/server.py --stdio

   # Test HTTP mode
   curl http://localhost:8000/health
   ```

## Learning Path

Each example builds upon the previous one, introducing new concepts:

### 1. Hello World MCP Server (00-hello-world)
- Basic MCP concepts and server setup
- HTTP and stdio protocols
- Simple tools and resources
- [Start Here →](00-hello-world/README.md)

### 2. File Explorer (01-file-explorer)
- File system operations
- More complex tools
- State management
- [Learn More →](01-file-explorer/README.md)

### 3. Web Search (02-web-search)
- External API integration
- Async operations
- Error handling
- [Learn More →](02-web-search/README.md)

### 4. Database Query (03-database-query)
- Database interactions
- Query building
- Data validation
- [Learn More →](03-database-query/README.md)

### 5. Agent System (04-agent-system)
- Multi-agent communication
- Complex workflows
- Event handling
- [Learn More →](04-agent-system/README.md)

### 6. Fraud Detection (05-fraud-detection)
- ML integration
- Real-time processing
- Advanced patterns
- [Learn More →](05-fraud-detection/README.md)

## Development Tips

### Running Examples
```bash
cd <example-dir>     # Go to any example
python src/server.py # Run in HTTP mode
python src/server.py --stdio  # Run in MCP mode
```

### VS Code Integration
1. Install: Python + MCP extensions
2. Open any example
3. Press F5 to run/debug

### Testing
Each example includes:
- Interactive HTML client
- API tests
- Example code

## Project Layout
```
pepper-ai-samples/
├── common/          # Shared code
├── 00-hello-world/  # Start here!
├── 01-file-explorer/
├── 02-web-search/
├── 03-database-query/
├── 04-agent-system/
└── 05-fraud-detection/
```

## Requirements
- Python 3.10+
- UV package manager 
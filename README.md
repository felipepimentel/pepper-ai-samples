# Pepper AI Samples

This repository contains progressive examples for learning and implementing the Model Context Protocol (MCP) and Agent-to-Agent (A2A) Protocol.

## Project Structure

The examples are organized into three main categories:

### MCP Examples (`examples/mcp/`)
Progressive examples for learning MCP concepts:
- `00-hello-world`: Basic MCP concepts and server setup
- `01-file-explorer`: Resource handling and management
- `02-web-search`: External service integration
- `03-database-query`: Data persistence and querying

### A2A Examples (`examples/a2a/`)
Progressive examples for learning A2A concepts:
- `00-hello-world`: Basic A2A concepts
- `01-network`: Agent communication
- `02-web`: Web integration
- `03-api-integration`: API integration

### Integration Examples (`examples/integrated/`)
Examples showing how to combine both protocols:
- `00-basic-bridge`: Basic protocol bridging
- `01-web-search`: Integrated web search
- `02-weather-insights`: Complete use case

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/pepper-ai/pepper-ai-samples.git
   cd pepper-ai-samples
   ```

2. Set up the environment:
   ```bash
   ./setup-env.sh
   source .venv/bin/activate
   ```

3. Start with basic examples:
   ```bash
   cd examples/mcp/00-hello-world
   python src/server.py
   ```

## Learning Path

1. **Start with MCP**:
   - Begin with `mcp/00-hello-world`
   - Progress through MCP examples
   - Learn core MCP concepts

2. **Move to A2A**:
   - Start with `a2a/00-hello-world`
   - Learn agent communication
   - Understand A2A patterns

3. **Explore Integration**:
   - See how protocols work together
   - Build real-world applications
   - Implement complete solutions

## Documentation

Each example includes:
- Concept explanation
- Step-by-step tutorial
- Code documentation
- Suggested exercises

## Contributing

1. Follow the project structure
2. Maintain progressive learning focus
3. Keep examples simple and focused
4. Include complete documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Configuração do Ambiente

Recomendamos o uso do gerenciador de pacotes UV para configurar o ambiente:

```bash
# Instalar UV (se ainda não estiver instalado)
curl -sSf https://astral.sh/uv/install.sh | bash

# Criar e ativar ambiente virtual
uv venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
uv pip install -e .
```

## Bibliotecas Compartilhadas

As bibliotecas comuns utilizadas pelos exemplos estão na pasta `libs/`:

- **pepperpymcp**: Implementação do protocolo MCP e utilitários comuns

## Recursos

- [Documentação do MCP](https://modelcontextprotocol.github.io/)
- [Documentação do A2A](https://google.github.io/A2A/)

## Common Utilities

The `libs/pepperpymcp` directory contains shared utilities used across all examples:

- **transport**: Utilities for MCP server creation and communication
  - `SimpleMCP`: Decorator-based API for creating MCP servers
  - `MCPClient`: Generic client for interacting with MCP servers via HTTP
  - `MCPStdioClient`: Generic client for interacting with MCP servers via stdio
- **types**: Common data types and structures

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
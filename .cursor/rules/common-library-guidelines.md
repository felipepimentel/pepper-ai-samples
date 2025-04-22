# Common Library Guidelines

## Purpose and Evolution

The `common` library serves as the foundation for all MCP server implementations. It should:
- Provide reusable components and utilities
- Standardize implementation patterns
- Reduce code duplication
- Simplify example implementations

## Official SDK vs Custom Utilities

### Official MCP SDK

O SDK oficial `mcp` é SEMPRE necessário e deve ser utilizado para toda funcionalidade principal:
```python
from mcp.server.fastmcp import FastMCP
from mcp import types

# Create an MCP server
mcp = FastMCP("Server Name", description="Description")

# Add a tool
@mcp.tool()
def example_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

### PepperPyMCP Utility

O pacote `pepperpymcp` é uma extensão do SDK oficial que:
- Requer obrigatoriamente o SDK oficial MCP como dependência
- Adiciona funcionalidades complementares como suporte a templates
- Mantém total compatibilidade com os padrões de implementação oficiais
- Encapsula (wrapper) as classes oficiais sem substituí-las ou fazer bypass

```python
# Exemplo de uso do PepperFastMCP
from pepperpymcp import PepperFastMCP
from mcp import types

# Criar server com suporte a templates
mcp = PepperFastMCP("Server Name", description="Description")

# Usar template
template = mcp.get_template("welcome_email")
email = template.format(name="User", content="Welcome!")
```

## Library Structure

```
common/
├── transport/           # Core MCP implementation
│   ├── __init__.py     # Public exports
│   ├── mcp.py          # Core MCP implementation
│   └── client.py       # Client implementations
├── types/              # Shared type definitions
│   ├── __init__.py     # Public types
│   ├── resources.py    # Resource types
│   └── tools.py        # Tool types
└── utils/              # Shared utilities
    ├── __init__.py     # Public utilities
    ├── logging.py      # Logging utilities
    └── validation.py   # Validation utilities
```

## Core Components

1. **Template Support (PepperFastMCP)**
   ```python
   from pepperpymcp import PepperFastMCP
   
   # Criar uma instância com suporte a templates
   mcp = PepperFastMCP("Server Name", description="Description")
   
   # Usar template
   @mcp.prompt()
   async def welcome_email(name: str, content: str = None) -> str:
       """Generate a welcome email"""
       if not content:
           content = "Welcome to our service!"
       return mcp.get_template("welcome_email").format(name=name, content=content)
   ```

2. **Type System**
   ```python
   from mcp import types
   
   # Create proper message content
   content = types.TextContent(type="text", text="Hello, world!")
   
   # Return formatted message
   return {
       "role": "assistant",
       "content": content
   }
   ```

3. **Client Implementations**
   ```python
   from mcp.client import ClientSession
   
   async def main():
       """Example client usage."""
       async with ClientSession() as session:
           await session.initialize()
           result = await session.call_tool("greeting")
   ```

## Enhancement Guidelines

1. **When to Add to Common**
   - Functionality used by multiple examples
   - Generic patterns that could benefit future examples
   - Infrastructure code (HTTP, FastAPI, etc.)
   - Standard client implementations

2. **When NOT to Add to Common**
   - Example-specific business logic
   - One-off implementations
   - Experimental features
   - Unstable or untested code

3. **Evolution Process**
   - Identify repeated patterns in examples
   - Extract and generalize the pattern
   - Add to appropriate common module
   - Update examples to use common implementation
   - Document the new functionality

4. **Integration Requirements**
   - Must maintain backward compatibility
   - Must be well-documented
   - Must include type hints
   - Must follow existing patterns

## Best Practices

1. **Code Organization**
   ```python
   # Official imports only
   from mcp.server.fastmcp import FastMCP
   from mcp import types
   
   # Or extended version with template support
   from pepperpymcp import PepperFastMCP
   from mcp import types
   ```

2. **Documentation**
   ```python
   class ResourceManager:
       """Manages resource lifecycle and access.
       
       This class provides a centralized way to:
       - Register resources
       - Access resource content
       - Manage resource lifecycle
       - Handle resource caching
       
       Example:
           manager = ResourceManager()
           manager.register("data", DataResource())
           content = await manager.get("data://123")
       """
   ```

3. **Testing**
   ```python
   # tests/common/test_mcp.py
   import pytest
   from mcp.server.fastmcp import FastMCP
   
   def test_tool_registration():
       """Test tool registration and lookup."""
       mcp = FastMCP("test")
       
       @mcp.tool()
       def greeting() -> str:
           return "Hello"
           
       assert "greeting" in mcp.tools
   ```

## Implementation Examples

1. **Resource Implementation**
   ```python
   from pepperpymcp import PepperFastMCP
   
   mcp = PepperFastMCP("Resource Example")
   
   @mcp.resource("data://{id}")
   def get_data(id: str) -> bytes:
       """Get file content."""
       path = f"data/{id}.json"
       with open(path, "rb") as f:
           return f.read()
   ```

2. **Tool Implementation**
   ```python
   from pepperpymcp import PepperFastMCP
   
   mcp = PepperFastMCP("Tool Example")
   
   @mcp.tool()
   async def search_tool(query: str) -> dict:
       """Perform search operation."""
       results = await perform_search(query)
       return {"results": results}
   ```

## Maintenance Guidelines

1. **Code Quality**
   - Run linters and formatters
   - Maintain test coverage
   - Update documentation
   - Check for deprecations

2. **Version Control**
   - Use semantic versioning
   - Document breaking changes
   - Maintain changelog
   - Tag releases

## Usage Example

The [00-hello-world/server.py](mdc:00-hello-world/server.py) demonstrates proper usage:
```python
from mcp import types
from pepperpymcp import PepperFastMCP

mcp = PepperFastMCP("Server Name", description="Description")

@mcp.tool()
def my_tool():
    pass

@mcp.resource("resource://{id}")
def my_resource():
    pass

@mcp.prompt()
async def welcome_email(name: str, content: str = None) -> str:
    return mcp.get_template("welcome_email").format(name=name, content=content)

async def main():
    await mcp.run()
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
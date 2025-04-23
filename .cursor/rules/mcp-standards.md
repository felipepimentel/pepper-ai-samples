# MCP Implementation Standards

## Core Principles

1. **Official SDK Usage**
   - ALWAYS use the official `mcp.server.fastmcp` SDK for all MCP server implementations
   - O SDK oficial é uma dependência **obrigatória** para todo o projeto
   - The `FastMCP` class from the official SDK is the foundational class for all MCP servers

2. **Role of pepperpymcp**
   - The `pepperpymcp` package is a **wrapper** around the official SDK
   - It REQUIRES the official MCP SDK as a mandatory dependency
   - It only extends functionality without bypassing or replacing the official implementation

3. **Template Support**
   - Para funcionalidades que exigem templates (como prompts formatados), use o `PepperFastMCP`
   - O `PepperFastMCP` é um wrapper sobre o `FastMCP` oficial que adiciona suporte a templates
   - Ele mantém a compatibilidade total com a API oficial e apenas estende suas funcionalidades

4. **Proper Import Pattern**
   ```python
   # CORRECT: Basic server without templates
   from mcp.server.fastmcp import FastMCP
   from mcp import types
   
   # CORRECT: Server with template support
   from mcp import types
   from pepperpymcp import PepperFastMCP
   
   # INCORRECT: Deprecated legacy class
   # from pepperpymcp import SimpleMCP  # Avoid this!
   ```

## Implementation Guidelines

1. **Server Creation**
   ```python
   # CORRECT: Standard MCP server without templates
   from mcp.server.fastmcp import FastMCP
   
   mcp = FastMCP("Server Name", description="Description")
   ```
   
   ```python
   # CORRECT: MCP server with template support
   from pepperpymcp import PepperFastMCP
   
   mcp = PepperFastMCP("Server Name", description="Description")
   
   # Template usage
   template = mcp.get_template("my_template")
   result = template.format(key="value")
   ```
   
   ```python
   # INCORRECT: Legacy implementation
   # from pepperpymcp import SimpleMCP
   # mcp = SimpleMCP("Server Name", "Description")  # Avoid this!
   ```

2. **Message Creation**
   ```python
   # CORRECT: Use instance methods from PepperFastMCP
   messages = [
       mcp.create_assistant_message("Hello, how can I help?"),
       mcp.create_user_message("I need assistance"),
       mcp.create_system_message("You are a helpful assistant")
   ]
   
   # DEPRECATED: Global functions (still work but will show warnings)
   # from pepperpymcp import AssistantMessage, UserMessage, SystemMessage
   # messages = [
   #     AssistantMessage("Hello, how can I help?"),
   #     UserMessage("I need assistance"),
   #     SystemMessage("You are a helpful assistant")
   # ]
   ```

3. **Server Execution**
   ```python
   # CORRECT: Use simplified run() method (UV-compatible)
   if __name__ == "__main__":
       mcp.run()
   
   # Server with cleanup
   if __name__ == "__main__":
       try:
           mcp.run()
       finally:
           # Cleanup code here
           db_connection.close()
   
   # INCORRECT: Legacy async execution pattern
   # async def main():
   #     await mcp.run()
   # 
   # if __name__ == "__main__":
   #     import asyncio
   #     asyncio.run(main())
   ```

## Migration Strategy

When encountering code that uses legacy patterns:

1. Replace `SimpleMCP` with `PepperFastMCP` from `pepperpymcp`
2. Update message handling to use instance methods like `mcp.create_assistant_message()`
3. Simplify server execution to use `mcp.run()` directly
4. For servers requiring cleanup, use a try-finally block around `mcp.run()`
5. Update dependencies in pyproject.toml to include both `mcp>=1.6.0` and `pepperpymcp`

## Dependencies Management

Always use UV for dependency management via pyproject.toml:

```toml
[project]
dependencies = [
    "mcp>=1.6.0",          # Official MCP SDK - REQUIRED
    "pepperpymcp",          # Extended functionality with template support
    "fastapi>=0.104.0",
    "uvicorn>=0.23.2",
    "pydantic>=2.4.2",
]

[tool.uv.sources]  # For local development
pepperpymcp = { path = "../libs/pepperpymcp", editable = true }
```

Do NOT use requirements.txt files. Use `uv pip install -e .` to install and `uv sync` to install from lockfile.

## Implementation Examples

See [mcp-examples/00-hello-world/server.py](mdc:mcp-examples/00-hello-world/server.py) for a reference implementation:
- Proper imports
- Tool and resource registration
- Message creation using instance methods
- UV-compatible server execution with `mcp.run()` 
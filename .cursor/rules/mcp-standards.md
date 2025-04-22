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

2. **Message Handling**
   ```python
   # CORRECT: Use official MCP types
   from mcp import types
   
   # Return proper message format
   return {
       "role": "assistant", 
       "content": types.TextContent(type="text", text="Message")
   }
   
   # INCORRECT: Legacy message format
   # from pepperpymcp import AssistantMessage
   # return AssistantMessage("Message")  # Avoid this!
   ```

3. **Server Execution**
   ```python
   # CORRECT: Use async/await pattern
   async def main():
       await mcp.run()
   
   if __name__ == "__main__":
       import asyncio
       asyncio.run(main())
   
   # INCORRECT: Synchronous execution
   # if __name__ == "__main__":
   #     mcp.run(mode=ConnectionMode.STDIO)  # Avoid this!
   ```

## Migration Strategy

When encountering code that uses the legacy SimpleMCP:

1. Replace `SimpleMCP` with `PepperFastMCP` from `pepperpymcp`
2. Ensure the official `mcp` SDK is installed
3. Update message handling to use proper dictionary format with `types.TextContent`
4. Convert to async/await pattern for server execution
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

Do NOT use requirements.txt files. 
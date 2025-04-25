# Project Structure

This document outlines the organization of the pepper-ai-samples project, which focuses on providing progressive examples for teaching MCP and A2A concepts.

## Directory Structure

```
pepper-ai-samples/
├── examples/           # All examples organized by protocol
│   ├── mcp/           # Progressive MCP examples
│   │   ├── 00-hello-world/      # Basic MCP concepts
│   │   ├── 01-file-explorer/    # Resource handling
│   │   ├── 02-web-search/       # External service integration
│   │   └── 03-database-query/   # Persistence and queries
│   │
│   ├── a2a/           # Progressive A2A examples
│   │   ├── 00-hello-world/      # Basic A2A concepts
│   │   ├── 01-network/          # Agent communication
│   │   ├── 02-web/             # Web integration
│   │   └── 03-api-integration/ # API integration
│   │
│   └── integrated/    # A2A-MCP integration examples
│       ├── 00-basic-bridge/     # Basic protocol bridge
│       ├── 01-web-search/       # Integrated web search
│       └── 02-weather-insights/ # Complete use case
│
├── libs/              # Shared libraries
│   ├── pepperpya2a/  # A2A library
│   └── pepperpymcp/  # MCP library
│
├── docs/             # Learning-focused documentation
│   ├── mcp/         # MCP concepts and tutorials
│   ├── a2a/         # A2A concepts and tutorials
│   └── integration/ # Integration guides
```

## Example Structure

Each example must follow this standard structure:

```
XX-example-name/
├── src/
│   └── server.py    # Main implementation
├── README.md        # Concept explanation and tutorial
└── pyproject.toml   # Dependencies
```

## Documentation Standards

Each example's README.md should include:
1. Concept being taught
2. Prerequisites
3. Step-by-step tutorial
4. Suggested exercises

## Progressive Learning Path

The examples are organized to provide a clear learning progression:

1. **MCP Path**:
   - Basic concepts and server setup
   - Resource handling and management
   - External service integration
   - Data persistence and querying

2. **A2A Path**:
   - Basic agent concepts
   - Agent communication
   - Web integration
   - API integration

3. **Integration Path**:
   - Basic protocol bridging
   - Real-world integrations
   - Complete use cases

## Implementation Guidelines

1. **Keep It Simple**:
   - Focus on teaching one concept at a time
   - Minimize complexity
   - Clear, well-documented code

2. **Consistency**:
   - Follow standard project structure
   - Use consistent naming conventions
   - Maintain similar README formats

3. **Dependencies**:
   - Keep dependencies minimal
   - Document all requirements
   - Use standard library when possible

## Development Workflow

1. **Adding New Examples**:
   - Place in appropriate category
   - Follow numbering convention
   - Include complete documentation
   - Ensure progressive learning

2. **Updating Examples**:
   - Maintain backward compatibility
   - Update documentation
   - Test thoroughly
   - Keep focus on teaching

3. **Documentation**:
   - Clear explanations
   - Practical examples
   - Step-by-step guides
   - Learning objectives 
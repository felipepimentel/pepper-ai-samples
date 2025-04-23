# A2A-MCP Integration Examples

This directory contains examples demonstrating the integration between the Agent-to-Agent (A2A) protocol and the Model Context Protocol (MCP). These examples show how to combine the capabilities of both protocols to create powerful agent systems that can communicate with each other and access external tools and resources.

## What's in this directory?

- **01-a2a-mcp-integration**: A basic example showing how to bridge A2A agents with MCP tools and resources

## Understanding A2A-MCP Integration

### What is A2A?

A2A (Agent-to-Agent) is a protocol designed for communication between AI agents. It enables agents to:
- Discover each other's capabilities
- Request assistance from other agents
- Share information and context
- Coordinate on complex tasks

### What is MCP?

MCP (Model Context Protocol) is a protocol that standardizes how AI models can interact with external tools and resources. It provides:
- A standardized way to define tools
- Access to structured data resources
- Mechanisms for retrieving and updating information
- Client-server communication patterns

### Why Integrate A2A and MCP?

The integration of A2A and MCP creates a powerful combination:
- A2A handles agent-to-agent communication and coordination
- MCP provides the tools and resources agents need to perform tasks
- Integration allows specialized agents to share capabilities
- Cross-protocol compatibility expands the ecosystem of available tools

## Building Your Own A2A-MCP Integration

To create your own A2A-MCP integration example, follow these steps:

1. **Set up both protocols**
   ```python
   from libs.pepperpya2a import create_a2a_server
   from libs.pepperpymcp import create_mcp_server
   
   # Create A2A server
   a2a = create_a2a_server(
       name="Your A2A Agent",
       description="Agent description"
   )
   
   # Create MCP server
   mcp = create_mcp_server(
       name="Your MCP Server",
       description="MCP server description"
   )
   ```

2. **Create a bridge between the protocols**
   ```python
   from a2a_mcp_bridge import create_a2a_mcp_bridge
   
   # Create the bridge
   bridge = create_a2a_mcp_bridge(a2a, mcp)
   ```

3. **Implement native A2A capabilities**
   ```python
   @a2a.capability(
       name="my_capability",
       description="Description of capability",
       input_schema={
           "type": "object",
           "properties": {
               "param1": {"type": "string"}
           }
       }
   )
   async def my_capability(data):
       # Implementation
       return {"result": "Success"}
   ```

4. **Implement native MCP tools and resources**
   ```python
   @mcp.tool()
   async def my_tool(param1: str) -> dict:
       # Implementation
       return {"result": "Success"}
   
   @mcp.resource("data://{id}")
   async def my_resource(id: str) -> str:
       # Implementation
       return f"Data for {id}"
   ```

5. **Run both servers**
   ```python
   import asyncio
   import uvicorn
   
   async def main():
       a2a_task = asyncio.create_task(
           uvicorn.Server(uvicorn.Config(app=a2a.app, host="0.0.0.0", port=8080)).serve()
       )
       mcp_task = asyncio.create_task(
           mcp._run_async(host="0.0.0.0", port=8000)
       )
       await asyncio.gather(a2a_task, mcp_task)
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

## Example Use Cases

1. **AI Agent Network with Specialized Tools**
   - Create multiple A2A agents, each with unique capabilities
   - Provide shared MCP tools for common tasks
   - Allow agents to discover and use each other's capabilities
   
2. **Knowledge Management System**
   - Use MCP resources to represent knowledge bases
   - Implement A2A agents for different knowledge domains
   - Allow agents to query each other's knowledge via A2A protocol
   
3. **Complex Workflow Orchestration**
   - Implement workflow steps as MCP tools
   - Create A2A agents specialized in different parts of the workflow
   - Use A2A for coordination and MCP for execution

## Best Practices

1. **Bridge Design**
   - Make your bridge bidirectional (A2A→MCP and MCP→A2A)
   - Consider namespacing when exposing capabilities across protocols
   - Handle errors gracefully across protocol boundaries

2. **Schema Translation**
   - Ensure consistent input/output schemas across protocols
   - Document expected formats for cross-protocol communication
   - Validate inputs to avoid cross-protocol data issues

3. **Resource Management**
   - Ensure efficient resource usage across both protocol servers
   - Consider connection pooling for databases or external services
   - Implement proper cleanup and shutdown procedures

## Getting Started

To run the examples in this directory:

1. Install the required dependencies
   ```bash
   pip install -e ./libs/pepperpya2a
   pip install -e ./libs/pepperpymcp
   pip install -r a2a-mcp-examples/01-a2a-mcp-integration/requirements.txt
   ```

2. Run the server
   ```bash
   cd a2a-mcp-examples/01-a2a-mcp-integration
   python server.py
   ```

3. Access the servers
   - A2A Agent Card: http://localhost:8080/agent-card
   - MCP Server Info: http://localhost:8000/info

## Next Steps

After exploring these examples, consider:

1. Creating specialized agents for different domains
2. Implementing more complex tools and resources
3. Building a multi-agent system to solve complex problems
4. Exploring integration with other systems and APIs 
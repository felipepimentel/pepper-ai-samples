# MCP Web Client and Host

This example demonstrates how to create a web-based client that can interact with MCP (Model Context Protocol) servers, providing a comprehensive view of the protocol's functionality.

## What is MCP?

The Model Context Protocol (MCP) is a standardized way for AI models to interact with external data sources and tools. It enables seamless integration between AI applications and various resources, making AI systems more capable and context-aware.

## Key Components

This implementation includes:

1. **MCP Web Client**: A browser-based client that can connect to MCP servers
2. **Protocol Flow Visualization**: A visual representation of how data flows between components
3. **Interactive UI**: Interface for discovering and interacting with server capabilities

## Features

- **Server Connection**: Connect to any MCP server by URL
- **Capability Discovery**: Automatically discover available tools, resources, and prompts
- **Tool Execution**: Execute tools with appropriate parameters
- **Resource Access**: Fetch resources using templated URIs
- **Prompt Generation**: Generate content from prompts with parameters

## How to Use

### Prerequisites

- Running MCP server(s) to connect to
- Modern web browser with JavaScript enabled

### Starting the Client

1. Clone this repository
2. Navigate to the `mcp-examples/mcp-web-client` directory
3. Open `index.html` in your browser
   - Alternatively, serve the files using a simple HTTP server:
     ```
     python -m http.server 3000
     ```
     Then navigate to `http://localhost:3000`

### Connecting to a Server

1. Select a predefined server from the dropdown or enter a custom server URL
2. Click "Connect"
3. Once connected, the server's capabilities will appear in the left panel

### Executing Tools

1. Go to the "Tools" tab
2. Select a tool from the dropdown
3. Fill in the required parameters
4. Click "Execute"
5. View the tool's response in the area below

### Accessing Resources

1. Go to the "Resources" tab
2. Select a resource pattern from the dropdown
3. Fill in the parameter values to complete the URI
4. Click "Fetch"
5. View the resource content in the area below

### Using Prompts

1. Go to the "Prompts" tab
2. Select a prompt from the dropdown
3. Fill in the required parameters
4. Click "Generate"
5. View the generated content in the area below

## Protocol Flow

The client visualizes the MCP protocol flow through a diagram showing:

1. **Host App**: The application containing the MCP client
2. **MCP Client**: The component that handles protocol communication
3. **MCP Server**: The server providing capabilities through the protocol

The flow diagram shows real-time messages being exchanged between components, helping understand how the protocol works in practice.

## Technical Implementation

This client uses:

- **Server-Sent Events (SSE)**: For real-time communication with the server
- **Fetch API**: For standard HTTP requests
- **Promises**: For asynchronous communication handling
- **JSON-RPC**: The underlying protocol format used by MCP

## Integration with Claude, Cursor, and AI Assistants

This client demonstrates how AI assistants like Claude and Cursor can leverage MCP to:

1. **Access External Data**: Connect to databases, file systems, and APIs
2. **Use Specialized Tools**: Execute domain-specific operations
3. **Maintain Context**: Preserve and recall information across sessions
4. **Generate Content**: Create structured content based on templates

## Running the Examples

To see this client in action with the included MCP examples:

1. Start one of the example MCP servers:
   ```
   cd mcp-examples/00-hello-world
   python server.py
   ```

2. Open the web client and connect to the server (default: `http://localhost:8000`)

3. Explore the server's capabilities and interact with its tools, resources, and prompts

## Understanding MCP for Course Demonstration

This implementation serves as an educational tool for understanding:

1. **Protocol Architecture**: The client-server architecture of MCP
2. **Capability Discovery**: How clients discover server capabilities
3. **Data Exchange**: How information flows between components
4. **Integration Patterns**: How MCP connects AI models with external systems

By using this client alongside the example servers, you can gain a complete understanding of how the MCP protocol works in practice.

## Contributing

Contributions to improve this client are welcome. Please follow the project's code style and submit pull requests for any enhancements.

## License

This project is available under the same license as the main repository. 
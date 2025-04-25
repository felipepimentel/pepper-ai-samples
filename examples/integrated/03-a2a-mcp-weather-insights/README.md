# Weather Insights A2A-MCP Integration

This example demonstrates the integration between Agent-to-Agent (A2A) protocol and Model Context Protocol (MCP) to create a powerful weather insights application.

## Features

- **A2A Agent**: Provides weather analysis capabilities and report generation
- **MCP Server**: Provides weather data tools for retrieving current and forecast data
- **A2A-MCP Bridge**: Connects the two protocols, allowing each to use the other's capabilities
- **Web Interface**: Simple UI for interacting with the application

## Architecture

This example implements:

1. **Direct Bridge Pattern**: A2A server and MCP server directly communicate through the bridge
2. **Capability Mapping**: MCP tools are mapped to A2A capabilities and vice versa
3. **Template-based Generation**: Weather reports are generated using templates

## Setup

1. Clone the repository and navigate to this example:
```bash
cd a2a-mcp-examples/03-a2a-mcp-weather-insights
```

2. Create a virtual environment and install dependencies with UV:
```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
# .venv\Scripts\activate   # Windows

# Install dependencies
uv sync
```

3. (Optional) Set up your OpenWeatherMap API key:
   - Create a free account at https://openweathermap.org/
   - Get your API key from your account dashboard
   - Create a `.env` file with:
   ```
   OPENWEATHER_API_KEY=your_api_key
   ```

## Running the Example

1. Start the server using UV:
```bash
uv run server.py
```

2. Access the web interface at:
```
http://localhost:8080
```

3. The A2A agent is available at port 8080 and the MCP server at port 8000.

## How It Works

### MCP Tools

The MCP server provides two main tools:

1. **get_current_weather**: Get current weather data for a location
2. **get_weather_forecast**: Get forecast data for a location

These tools are exposed to the A2A server through the bridge, allowing the A2A agent to use them as capabilities.

### A2A Capabilities

The A2A agent provides two main capabilities:

1. **analyzeWeatherTrends**: Analyze weather trends based on forecast data
2. **generateWeatherReport**: Generate comprehensive weather reports

These capabilities are exposed to the MCP server through the bridge, allowing MCP tools to use them.

### A2A-MCP Bridge

The bridge connects the two protocols by:

1. Creating A2A capability wrappers for MCP tools
2. Creating MCP tool wrappers for A2A capabilities
3. Handling parameter conversion and context management

## Example Interactions

Using the web interface, you can:

1. Get current weather for a city
2. Get a weather forecast for a city
3. Get weather trend analysis
4. Generate a comprehensive weather report

## Integration Patterns Demonstrated

This example showcases several A2A-MCP integration patterns:

1. **Capability/Tool Mapping**: A2A capabilities are mapped to MCP tools and vice versa
2. **Resource Generation**: Weather reports are generated using templates
3. **Context Propagation**: Context is maintained across protocol boundaries
4. **Error Handling**: Errors are properly handled across protocol boundaries

## Extending the Example

This example can be extended in several ways:

1. Add more weather data sources
2. Implement more sophisticated analysis
3. Add support for real-time updates using WebSockets
4. Enhance the web interface with charts and maps

## Development

To add new dependencies:
```bash
# Add a production dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest
```

To lock dependencies:
```bash
uv lock
```

## Further Reading

For more information about the A2A and MCP protocols, see:

- [A2A Protocol Documentation](https://github.com/google/generative-ai-docs/blob/main/conversations/a2a/overview/README.md)
- [Model Context Protocol Documentation](https://context-protocol.ai/)
- [A2A-MCP Integration Patterns](../../docs/a2a-mcp-integration.md) 
# A2A Weather API Integration

This example demonstrates how to build an A2A (Agent-to-Agent) server that integrates with a real external weather API to provide weather information as an agent capability.

## Features

- A2A Server implementation with weather-related capabilities
- Integration with OpenWeatherMap API for real weather data
- Interactive client for testing the A2A agent
- Well-formed agent card and capability definitions

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd a2a-examples/04-a2a-api-integration
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenWeatherMap API key:
   - Create a free account at https://openweathermap.org/
   - Get your API key from your account dashboard
   - Create a `.env` file with:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key
   ```

## Running the Example

1. Start the A2A Weather Server:
```bash
python src/server.py
```

2. In a separate terminal, run the client to interact with the agent:
```bash
python src/client.py
```

## How It Works

The A2A server exposes several weather-related capabilities:

1. `getCurrentWeather`: Get current weather for a location
2. `getWeatherForecast`: Get a multi-day forecast for a location
3. `getHistoricalWeather`: Get historical weather data for a location

The server integrates with the OpenWeatherMap API to fetch real weather data based on the location provided.

## Example Interactions

Example user queries:
- "What's the weather like in New York?"
- "Give me a 3-day forecast for Paris."
- "What was the temperature in Tokyo last week?"

## A2A Protocol

This example implements the A2A protocol specification. Key components include:

- `/.well-known/agent-card.json`: Provides metadata about the agent
- Agent capabilities with schema definitions
- Message-based interaction for capability invocation

## Project Structure

```
04-a2a-api-integration/
├── .well-known/            # Agent card directory
│   └── agent-card.json     # Agent metadata
├── src/
│   ├── server.py           # A2A server implementation
│   ├── client.py           # Interactive A2A client
│   └── weather_api.py      # OpenWeatherMap API client
├── pyproject.toml          # Project configuration
└── requirements.txt        # Dependencies
```

## Further Reading

- [A2A Protocol Specification](https://a2a.fly.dev/)
- [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 
# A2A Examples

This directory contains examples demonstrating various uses of the Agent-to-Agent (A2A) protocol, which enables autonomous agents to communicate and collaborate with each other.

## What is A2A?

The Agent-to-Agent (A2A) protocol is a standardized interface for agent-to-agent communication. It enables AI agents to:

- Discover other agents' capabilities
- Delegate tasks to specialized agents
- Share information and collaborate on complex tasks
- Form networks of agents with different specializations

## Examples

### 00-a2a-hello-world

A simple introduction to A2A with a basic agent that demonstrates the protocol fundamentals:
- Creating an A2A server
- Registering capabilities
- Handling requests
- Responding with results

### 02-a2a-network

A more complex example demonstrating a network of specialized agents:
- A coordinator agent that routes tasks
- A math specialist agent for calculations and statistics
- A text analysis agent for text processing and sentiment analysis
- Client applications that interact with the network

## Getting Started

Each example directory contains its own README.md with specific instructions. Generally, you'll need:

1. Python 3.10 or higher
2. The `pepperpya2a` library, which is included in this repository
3. Any additional dependencies listed in the example's README

To run an example:

```bash
cd [example-directory]
python server.py
```

For examples with multiple agents, you'll need to run each agent in a separate terminal.

## Key Components

### A2A Server

Creates an agent that can receive and respond to requests:

```python
from libs.pepperpya2a.src.pepperpya2a import create_a2a_server

server = create_a2a_server(
    name="Example Agent",
    description="Demonstrates A2A protocol",
    port=8080
)

# Register capabilities
server.register_capability(
    name="greeting",
    description="Returns a greeting",
    handler=greeting_handler
)

# Start the server
await server.start_server()
```

### A2A Client

Communicates with A2A agents:

```python
from libs.pepperpya2a.src.pepperpya2a import A2AClient

client = A2AClient("http://localhost:8080")

# Get agent information
agent_card = await client.get_agent_card()

# Send a task
result = await client.send_task("greeting", {"name": "World"})

# Close when done
await client.close()
```

## Requirements

- Python 3.10+
- `aiohttp` for HTTP communication
- A modern web browser for web-based examples

## Resources

- [Official A2A Documentation](https://google.github.io/A2A/)
- [A2A GitHub Repository](https://github.com/google/A2A)
- [A2A Blog Post](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) 
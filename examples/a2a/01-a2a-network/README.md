# A2A Network Example

This example demonstrates more advanced A2A protocol features, focusing on agent discovery and network communication between agents.

## Overview

This example implements a network hub agent that can:

1. Discover other A2A agents via their agent cards
2. Register and keep track of available agents and their capabilities
3. Route and delegate tasks to the most appropriate specialized agent
4. Coordinate communication between multiple agents

## Prerequisites

- Python 3.10 or higher
- uv package manager
- Running instance of the basic A2A agent (from 00-a2a-hello-world)

## Installation

```bash
# Navigate to this directory
cd a2a-examples/01-a2a-network

# Create a virtual environment with uv
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

## Running the Example

1. First, start the basic weather agent from the first example (if not already running):

```bash
# In a separate terminal
cd a2a-examples/00-a2a-hello-world
source .venv/bin/activate
uv run src/server.py  # This will run on port 8000
```

2. Then start the network hub agent:

```bash
# From the network example directory
uv run src/server.py  # This will run on port 8001
```

3. In a third terminal, run the network client:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the client to interact with the hub agent
uv run src/client.py
```

4. Using the network client console:
   - Discover the weather agent: `discover http://localhost:8000`
   - List known agents: `list`
   - Ask about weather: `chat What's the weather in Rio de Janeiro?`

## Key Concepts

This example demonstrates these advanced A2A concepts:

- **Agent Discovery**: Finding and registering other agents dynamically
- **Capability Registry**: Tracking which agents provide which capabilities
- **Task Delegation**: Routing tasks to specialized agents
- **Structured Data**: Using DataPart for complex data exchange
- **Artifacts**: Generating rich artifacts with metadata

## Network Protocol

The hub agent extends the A2A protocol with these endpoints:

- `/agents/discover`: Register a new agent by URL
- `/agents`: List all known agents

## Multi-Agent System Design

This example demonstrates a simple multi-agent system with:

1. **Specialized Agents**: Focused on specific tasks (weather information)
2. **Hub Agent**: Manages discovery and routing
3. **Client Application**: Provides user interface to the network

This architecture allows for system extension by adding new specialized agents without modifying existing code.

## Next Steps

After understanding this intermediate example, explore:
- Adding more specialized agents to the network
- Implementing authentication between agents
- Creating complex workflows spanning multiple agents
- Handling failover and load balancing across agents 
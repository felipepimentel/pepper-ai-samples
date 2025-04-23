# A2A Hello World

A simple example demonstrating the basic concepts of the Agent-to-Agent (A2A) protocol.

## Overview

This example implements a basic A2A agent that provides weather information. It demonstrates the core concepts of the A2A protocol:

- Agent discovery via AgentCard
- Task creation and management
- Basic message sending and receiving
- Simple interactive chat

## Prerequisites

- Python 3.10 or higher
- uv package manager

## Installation

```bash
# Navigate to this directory
cd a2a-examples/00-a2a-hello-world

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

1. Start the A2A server:

```bash
# From the example directory
uv run src/server.py
```

2. In a separate terminal, run the client:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the client to interact with the agent
uv run src/client.py
```

3. Chat with the agent by asking questions about the weather in different cities.

## Key Concepts

- **AgentCard**: Provides metadata about an agent, including its capabilities and skills
- **Task**: A unit of work that encapsulates a conversation or interaction
- **Message**: Communication between user and agent containing text or other content
- **Task States**: Lifecycle stages (submitted, working, input_required, completed, failed)

## A2A Protocol Structure

The A2A protocol follows these key endpoint patterns:

- `/.well-known/agent.json`: Agent discovery endpoint
- `/tasks`: Create new tasks
- `/tasks/{task_id}`: Get task status
- `/tasks/{task_id}/send`: Send messages to a task

## Next Steps

After understanding this basic example, explore more advanced features:
- Multi-turn conversations with context
- Structured data exchange with DataPart
- File handling with FilePart
- Streaming responses
- Multi-agent communication 
# A2A Web Integration Example

This example demonstrates a web-integrated agent using the Agent-to-Agent (A2A) protocol. It showcases how agents can leverage web capabilities such as search, image processing, and data visualization while maintaining a standardized A2A interface.

## Overview

The Web Integration Agent provides capabilities that integrate with various web services, allowing it to:

1. Search the web for information
2. Generate images based on text prompts
3. Analyze images and receipts
4. Convert currencies
5. Visualize data
6. Process form submissions

These capabilities are exposed through a standardized A2A interface, making them discoverable and accessible to other agents.

## Architecture

This example implements:

- **A2A Server**: Exposes agent metadata and capabilities
- **Task Management**: Handles user messages and agent responses
- **Web Service Integration**: Connects to external web services
- **File Handling**: Processes uploads and generates files
- **Stateful Interactions**: Maintains context across conversations

## Setup

### Prerequisites

- Python 3.10+
- UV package manager

### Installation

1. Create a virtual environment:

```bash
cd a2a-examples/02-a2a-web
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
uv pip install -e .
```

## Running the Server

Start the server with:

```bash
cd src
python server.py
```

The server will run on http://localhost:8002

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | Returns agent metadata |
| `/tasks` | POST | Creates a new task |
| `/tasks/{task_id}` | GET | Retrieves task status and messages |
| `/tasks/{task_id}/send` | POST | Sends a message to a task |
| `/tasks/{task_id}/upload` | POST | Uploads a file to a task |
| `/tasks/{task_id}/form` | POST | Submits a form to a task |

## Using the Client

The client script provides various ways to interact with the Web Integration Agent:

```bash
# Get the agent card (metadata)
python client.py agent_card

# Create a new task
python client.py create_task

# Get task status and messages
python client.py get_task --task_id <TASK_ID>

# Send a message to a task
python client.py send_message --task_id <TASK_ID> --message "Your message here"

# Upload a file to a task
python client.py upload_file --task_id <TASK_ID> --file path/to/file.jpg --description "Description"

# Submit a form to a task
python client.py submit_form --task_id <TASK_ID>

# Run demos for specific capabilities
python client.py web_search
python client.py image_generation
python client.py image_analysis --image path/to/image.jpg
python client.py receipt_processing --receipt path/to/receipt.jpg
python client.py currency_conversion
python client.py data_visualization
python client.py form_submission

# Run all demos
python client.py demo_all --image path/to/image.jpg --receipt path/to/receipt.jpg
```

## Agent Capabilities

The Web Integration Agent implements the following capabilities:

| Capability | Description |
|------------|-------------|
| `webSearch` | Searches the web for information |
| `generateImage` | Creates images based on text prompts |
| `analyzeImage` | Extracts information from images |
| `processReceipt` | Extracts information from receipt images |
| `convertCurrency` | Converts between currencies |
| `visualizeData` | Creates visualizations from data |
| `processForm` | Processes structured form data |

## A2A Integration

This agent complies with the A2A protocol, which means:

1. It exposes a standardized manifest at `/.well-known/agent.json`
2. Its capabilities follow consistent input/output schemas
3. It can be discovered and invoked by other A2A-compatible agents

## Example Interactions

### Web Search

```bash
python client.py send_message --task_id <TASK_ID> --message "Search for information about artificial intelligence"
```

### Image Generation

```bash
python client.py send_message --task_id <TASK_ID> --message "Generate an image of a beautiful sunset over mountains"
```

### Image Analysis

```bash
python client.py upload_file --task_id <TASK_ID> --file path/to/image.jpg --description "Please analyze this image"
```

### Data Visualization

```bash
python client.py send_message --task_id <TASK_ID> --message "Visualize the quarterly revenue data: Q1: 84, Q2: 93, Q3: 65, Q4: 120"
```

## Project Structure

```
02-a2a-web/
├── .well-known/          # A2A protocol metadata
│   └── agent.json       # Agent manifest
├── src/
│   ├── server.py        # Main server implementation
│   └── client.py        # Client for testing
├── pyproject.toml       # Project configuration
└── README.md            # This file
```

## Learning Objectives

This example demonstrates:

1. How to implement A2A protocol for web-integrated agents
2. Managing stateful conversations with tasks
3. Handling multimodal content (text, images, structured data)
4. Exposing web capabilities through standardized interfaces
5. Processing file uploads and generating file outputs

## Extension Ideas

- Implement authentication for the agent
- Add more specialized web capabilities
- Create a web-based user interface
- Integrate with real external APIs
- Add streaming responses
- Implement capability composition between multiple agents 
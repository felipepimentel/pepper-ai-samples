# PepperPyMCP

Extensions to the Model Context Protocol (MCP) Python SDK, adding template support and other utilities.

## Features

- Template support for FastMCP
- Message creation helpers (UserMessage, AssistantMessage, etc.)
- Transport wrappers around official MCP SDK

## Installation

```bash
pip install pepperpymcp
```

## Usage

```python
from pepperpymcp import PepperFastMCP, UserMessage, AssistantMessage

# Create a server
mcp = PepperFastMCP("My Server")

# Access templates
template = mcp.get_template("my_template")

# Create messages
messages = [
    UserMessage("Hello"),
    AssistantMessage("Hi there!")
]

# Run the server
mcp.run()
``` 
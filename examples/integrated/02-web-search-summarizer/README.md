# Web Search Summarizer Example

This example demonstrates how to integrate Agent-to-Agent (A2A) and Model Context Protocol (MCP) to create a powerful web search and summarization service.

## Overview

The example consists of:

1. **MCP Web Search Server**: Provides web search functionality through MCP tools
2. **A2A Summarization Agent**: Provides content summarization capabilities
3. **A2A-MCP Bridge**: Connects both protocols, allowing A2A agents to use MCP tools and vice versa
4. **Integrated Server**: Exposes a unified API that combines web search and automatic summarization

## Features

- Search the web for current information
- Automatically summarize search results
- Expose both capabilities through a unified interface
- Demonstrate how to bridge between A2A and MCP systems

## Requirements

- Python 3.10 or higher
- Dependencies from `requirements.txt`

## Setup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python server.py
   ```

3. Access the web interface at: http://localhost:8000

## Architecture

```
┌───────────────┐       ┌───────────────┐
│   MCP Web     │       │   A2A Text    │
│  Search Tool  │◄─────►│  Summarizer   │
└───────┬───────┘       └───────┬───────┘
        │                       │
        │   ┌───────────────┐   │
        └───┤  A2A-MCP      ├───┘
            │   Bridge      │
            └───────┬───────┘
                    │
            ┌───────┴───────┐
            │  Integrated   │
            │    Server     │
            └───────────────┘
```

## How It Works

1. The MCP server provides web search capabilities
2. The A2A agent provides text summarization capabilities
3. The bridge connects these two systems
4. The integrated server exposes both capabilities through a unified interface
5. When a search-and-summarize request is made:
   - Web search is performed via MCP
   - Results are summarized via A2A
   - Final results are returned to the user

## API Endpoints

- `GET /search?query={search_term}` - Search the web
- `POST /summarize` - Summarize text content
- `GET /search-and-summarize?query={search_term}` - Search and summarize in one step

## Example Usage

```python
import httpx

# Search and summarize
response = httpx.get("http://localhost:8000/search-and-summarize?query=climate change latest news")
result = response.json()

print(f"Summary: {result['summary']}")
print(f"Sources: {', '.join(result['sources'])}")
```

## Building Your Own Enhancement

Want to extend this example? Here are some ideas:

1. **Add Image Analysis**: Add MCP tools to analyze images found on web pages
2. **Add Persistent Memory**: Implement a database to remember previous searches
3. **Add Multiple Search Strategies**: Implement different search strategies based on query types
4. **Add Voice Interface**: Connect to speech-to-text and text-to-speech services

## Requirements

- Python 3.10+
- FastAPI
- httpx
- beautifulsoup4
- A2A and MCP libraries (included in the repository)

## License

This example is licensed under the MIT License. See the LICENSE file for details. 
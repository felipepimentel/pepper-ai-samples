#!/usr/bin/env python
"""
MCP Architecture Demo

This script demonstrates the complete MCP architecture with:
1. A Host that coordinates multiple clients
2. Multiple MCP Servers with different capabilities
3. Clients that connect to the servers
4. Proper interaction between components

Run with: python standalone_demo.py
"""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path to import the libraries
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.pepperpymcp.src.pepperpymcp.host import MCPHost
from libs.pepperpymcp.src.pepperpymcp.sample_server import create_sample_server
from libs.pepperpymcp.src.pepperpymcp.mcp import create_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mcp_demo.log"),
    ],
)

logger = logging.getLogger("mcp_demo")


class WeatherServer:
    """Simple weather data server for demonstration."""
    
    def __init__(self, name="Weather MCP Server", description="Provides weather data"):
        self.name = name
        self.description = description
        self.mcp = create_mcp_server(name, description=description)
        
        # Sample weather data
        self.weather_data = {
            "new_york": {"temp": 25, "condition": "Sunny", "humidity": 60},
            "london": {"temp": 18, "condition": "Cloudy", "humidity": 75},
            "tokyo": {"temp": 30, "condition": "Rainy", "humidity": 80},
            "sydney": {"temp": 22, "condition": "Partly Cloudy", "humidity": 65},
            "paris": {"temp": 20, "condition": "Clear", "humidity": 70},
        }
        
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register weather tools."""
        
        @self.mcp.tool()
        async def get_weather(location: str) -> dict:
            """Get current weather for a location."""
            logger.info(f"Weather tool called for location: {location}")
            location = location.lower()
            
            if location in self.weather_data:
                return {
                    "location": location,
                    "weather": self.weather_data[location],
                    "status": "success"
                }
            else:
                return {
                    "location": location,
                    "status": "error",
                    "message": f"No weather data available for {location}"
                }
        
        @self.mcp.tool()
        async def get_forecast(location: str, days: int = 3) -> dict:
            """Get weather forecast for a location."""
            logger.info(f"Forecast tool called for {location}, {days} days")
            location = location.lower()
            
            if location not in self.weather_data:
                return {
                    "location": location,
                    "status": "error",
                    "message": f"No forecast available for {location}"
                }
                
            # Generate fake forecast based on current weather
            current = self.weather_data[location]
            forecast = []
            for i in range(1, days + 1):
                # Simple algorithm to vary the forecast
                temp_change = (i * 2) - 3  # Will give -1, 1, 3, 5, etc.
                conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"]
                condition_idx = (conditions.index(current["condition"]) + i) % len(conditions)
                
                forecast.append({
                    "day": i,
                    "temp": current["temp"] + temp_change,
                    "condition": conditions[condition_idx],
                    "humidity": max(30, min(90, current["humidity"] + (i * 3) - 5))
                })
                
            return {
                "location": location,
                "current": current,
                "forecast": forecast,
                "days": days,
                "status": "success"
            }
    
    def _register_resources(self):
        """Register weather resources."""
        
        @self.mcp.resource("weather://{location}")
        async def weather_resource(location: str) -> bytes:
            """Get weather data as a resource."""
            logger.info(f"Weather resource requested for: {location}")
            location = location.lower()
            
            if location in self.weather_data:
                return json.dumps(self.weather_data[location]).encode("utf-8")
            else:
                raise KeyError(f"No weather data available for {location}")
    
    async def run(self, host="0.0.0.0", port=8001):
        """Run the weather server."""
        logger.info(f"Starting {self.name} on {host}:{port}")
        await self.mcp.run(host=host, port=port)
    
    def run_sync(self, host="0.0.0.0", port=8001):
        """Run the server synchronously."""
        asyncio.run(self.run(host=host, port=port))


class SearchServer:
    """Simple search server for demonstration."""
    
    def __init__(self, name="Search MCP Server", description="Provides search capabilities"):
        self.name = name
        self.description = description
        self.mcp = create_mcp_server(name, description=description)
        
        # Sample data
        self.documents = {
            "python": {
                "title": "Python Programming",
                "content": "Python is a high-level programming language...",
                "url": "https://example.com/python"
            },
            "javascript": {
                "title": "JavaScript Basics",
                "content": "JavaScript is a scripting language used for web development...",
                "url": "https://example.com/javascript"
            },
            "machine_learning": {
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a branch of artificial intelligence...",
                "url": "https://example.com/ml"
            },
            "data_science": {
                "title": "Data Science Overview",
                "content": "Data science is an interdisciplinary field...",
                "url": "https://example.com/data-science"
            }
        }
        
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register search tools."""
        
        @self.mcp.tool()
        async def search(query: str, limit: int = 5) -> dict:
            """Search for documents matching the query."""
            logger.info(f"Search tool called with query: {query}, limit: {limit}")
            
            # Simple search implementation
            results = []
            query = query.lower()
            
            for doc_id, doc in self.documents.items():
                if (query in doc_id.lower() or 
                    query in doc["title"].lower() or 
                    query in doc["content"].lower()):
                    results.append({
                        "id": doc_id,
                        "title": doc["title"],
                        "snippet": doc["content"][:100] + "...",
                        "url": doc["url"]
                    })
                    
                if len(results) >= limit:
                    break
                    
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "status": "success"
            }
    
    def _register_resources(self):
        """Register search resources."""
        
        @self.mcp.resource("document://{id}")
        async def document_resource(id: str) -> bytes:
            """Get document by ID."""
            logger.info(f"Document resource requested: {id}")
            
            if id in self.documents:
                return json.dumps(self.documents[id]).encode("utf-8")
            else:
                raise KeyError(f"Document {id} not found")
    
    async def run(self, host="0.0.0.0", port=8002):
        """Run the search server."""
        logger.info(f"Starting {self.name} on {host}:{port}")
        await self.mcp.run(host=host, port=port)
    
    def run_sync(self, host="0.0.0.0", port=8002):
        """Run the server synchronously."""
        asyncio.run(self.run(host=host, port=port))


async def run_demo():
    """Run the complete MCP architecture demo."""
    logger.info("Starting MCP Architecture Demo")
    
    # Create the host
    host = MCPHost("Demo MCP Host")
    
    # Start the data server
    data_server = create_sample_server("Data Server", "Provides data access")
    data_task = asyncio.create_task(data_server.run(host="127.0.0.1", port=8001))
    await asyncio.sleep(1)  # Give the server time to start
    
    # Start the weather server
    weather_server = WeatherServer()
    weather_task = asyncio.create_task(weather_server.run(host="127.0.0.1", port=8002))
    await asyncio.sleep(1)
    
    # Start the search server
    search_server = SearchServer()
    search_task = asyncio.create_task(search_server.run(host="127.0.0.1", port=8003))
    await asyncio.sleep(1)
    
    # Connect clients to the servers
    data_client = await host.create_client("http://127.0.0.1:8001", "data")
    weather_client = await host.create_client("http://127.0.0.1:8002", "weather")
    search_client = await host.create_client("http://127.0.0.1:8003", "search")
    
    # Initialize clients
    await data_client.initialize()
    await weather_client.initialize()
    await search_client.initialize()
    
    # Start web interface to interact with the host
    web_interface = await host.start_web_interface(
        host="0.0.0.0", 
        port=8000
    )
    
    logger.info("MCP Architecture Demo is running!")
    logger.info("Web interface available at http://localhost:8000")
    logger.info("Available clients:")
    logger.info("  - Data Server: http://localhost:8001")
    logger.info("  - Weather Server: http://localhost:8002")
    logger.info("  - Search Server: http://localhost:8003")
    logger.info("")
    logger.info("Press Ctrl+C to exit")
    
    try:
        # Keep the servers running until interrupted
        done, pending = await asyncio.wait(
            [data_task, weather_task, search_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # If any task completed, log it
        for task in done:
            try:
                result = task.result()
                logger.info(f"Task completed with result: {result}")
            except Exception as e:
                logger.error(f"Task failed with error: {e}")
                
    except asyncio.CancelledError:
        logger.info("Demo was cancelled")
    except KeyboardInterrupt:
        logger.info("Demo was interrupted")
    finally:
        # Clean up
        logger.info("Shutting down...")
        
        # Cancel all server tasks
        for task in [data_task, weather_task, search_task]:
            if not task.done():
                task.cancel()
                
        # Shutdown the host (which will disconnect all clients)
        await host.shutdown()
        
        logger.info("Demo shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.exception(f"Error in demo: {e}")
    finally:
        print("\nDemo ended")
        sys.exit(0) 
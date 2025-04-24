"""
Sample MCP server implementation demonstrating best practices.

This module provides a reference implementation of an MCP server using
the PepperFastMCP class from the pepperpymcp library.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

from .mcp import create_mcp_server, PepperFastMCP

logger = logging.getLogger(__name__)

class SampleMCPServer:
    """
    Sample MCP server implementation showcasing proper architecture.
    
    This class demonstrates:
    1. Proper resource management
    2. Tool implementation
    3. HTTP endpoint integration
    4. Graceful shutdown handling
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the sample MCP server.
        
        Args:
            name: Server name
            description: Server description
        """
        self.name = name
        self.description = description
        self.mcp = create_mcp_server(name, description=description)
        
        # Data storage for demo purposes
        self.data = {}
        self.documents = {}
        
        # Configure template paths (if templates directory exists)
        templates_dir = Path("templates")
        if templates_dir.exists() and templates_dir.is_dir():
            self.mcp.add_template_path(str(templates_dir))
        
        # Register capabilities
        self._register_tools()
        self._register_resources()
        self._register_http_endpoints()
    
    def _register_tools(self):
        """Register all tools for this server."""
        
        @self.mcp.tool()
        async def get_item(id: str) -> Dict[str, Any]:
            """
            Get an item by ID.
            
            Args:
                id: The item identifier
                
            Returns:
                The item data or an error message
            """
            logger.info(f"Tool: get_item({id})")
            
            if id in self.data:
                return {
                    "status": "success",
                    "item": self.data[id],
                    "id": id
                }
            else:
                return {
                    "status": "error",
                    "message": f"Item with ID '{id}' not found",
                    "id": id
                }
        
        @self.mcp.tool()
        async def store_item(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Store an item with the given ID.
            
            Args:
                id: The item identifier
                data: The data to store
                
            Returns:
                Success or error message
            """
            logger.info(f"Tool: store_item({id}, {data})")
            
            self.data[id] = data
            return {
                "status": "success",
                "message": f"Item with ID '{id}' stored successfully",
                "id": id
            }
        
        @self.mcp.tool()
        async def search_items(query: str, limit: int = 10) -> Dict[str, Any]:
            """
            Search for items matching the query.
            
            Args:
                query: The search query
                limit: Maximum number of results to return
                
            Returns:
                List of matching items
            """
            logger.info(f"Tool: search_items({query}, {limit})")
            
            # Simple search implementation for demo purposes
            results = []
            for item_id, item_data in self.data.items():
                # Check if query is in item ID or any string values
                if query.lower() in item_id.lower():
                    results.append({"id": item_id, "data": item_data})
                    continue
                
                for key, value in item_data.items():
                    if isinstance(value, str) and query.lower() in value.lower():
                        results.append({"id": item_id, "data": item_data})
                        break
                        
                if len(results) >= limit:
                    break
            
            return {
                "status": "success",
                "results": results[:limit],
                "count": len(results),
                "query": query
            }
    
    def _register_resources(self):
        """Register all resources for this server."""
        
        @self.mcp.resource("item://{id}")
        async def get_item_resource(id: str) -> bytes:
            """
            Get an item as a resource.
            
            Args:
                id: The item identifier
                
            Returns:
                The item data as JSON bytes
            """
            logger.info(f"Resource: item://{id}")
            
            if id in self.data:
                return json.dumps(self.data[id]).encode("utf-8")
            else:
                raise KeyError(f"Item with ID '{id}' not found")
        
        @self.mcp.resource("document://{id}")
        async def get_document_resource(id: str) -> bytes:
            """
            Get a document as a resource.
            
            Args:
                id: The document identifier
                
            Returns:
                The document content as bytes
            """
            logger.info(f"Resource: document://{id}")
            
            if id in self.documents:
                # If it's already bytes, return as is, otherwise encode
                content = self.documents[id]
                if isinstance(content, bytes):
                    return content
                elif isinstance(content, str):
                    return content.encode("utf-8")
                else:
                    return json.dumps(content).encode("utf-8")
            else:
                raise KeyError(f"Document with ID '{id}' not found")
    
    def _register_http_endpoints(self):
        """Register HTTP endpoints for this server."""
        
        @self.mcp.http_endpoint("/status")
        async def get_status():
            """Get server status."""
            return {
                "name": self.name,
                "status": "running",
                "items_count": len(self.data),
                "documents_count": len(self.documents)
            }
        
        @self.mcp.http_endpoint("/items")
        async def get_items():
            """Get all items."""
            return {
                "items": [
                    {"id": id, "data": data}
                    for id, data in self.data.items()
                ]
            }
    
    def load_sample_data(self, items_count: int = 5):
        """
        Load sample data for demonstration purposes.
        
        Args:
            items_count: Number of sample items to create
        """
        # Create sample items
        for i in range(1, items_count + 1):
            item_id = f"item_{i}"
            self.data[item_id] = {
                "name": f"Sample Item {i}",
                "description": f"This is sample item number {i}",
                "created_at": "2023-06-30T12:00:00Z",
                "tags": ["sample", f"tag_{i}"]
            }
        
        # Create sample documents
        self.documents["readme"] = "# Sample MCP Server\n\nThis is a sample document for the MCP server."
        self.documents["config"] = json.dumps({"server_name": self.name, "max_items": 100})
        self.documents["sample"] = "This is a sample text document."
        
        logger.info(f"Loaded {len(self.data)} sample items and {len(self.documents)} sample documents")
    
    def configure_cors(self, origins=None):
        """
        Configure CORS for the server.
        
        Args:
            origins: List of allowed origins (default: ["*"])
        """
        self.mcp.configure_cors(origins=origins)
    
    async def run(self, host: str = "0.0.0.0", port: int = 8000, cors: bool = True):
        """
        Run the server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            cors: Whether to enable CORS (default: True)
        """
        logger.info(f"Starting {self.name} on {host}:{port}")
        
        if cors:
            self.configure_cors()
            
        await self.mcp.run(host=host, port=port)
    
    def run_sync(self, host: str = "0.0.0.0", port: int = 8000, cors: bool = True):
        """
        Run the server synchronously.
        
        This is a convenience method for running the server in a blocking way.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            cors: Whether to enable CORS (default: True)
        """
        if cors:
            self.configure_cors()
            
        asyncio.run(self.run(host=host, port=port))


def create_sample_server(name: str = "Sample MCP Server", 
                        description: str = "A sample MCP server implementation",
                        load_data: bool = True,
                        items_count: int = 5):
    """
    Create a sample MCP server with optional sample data.
    
    Args:
        name: Server name
        description: Server description
        load_data: Whether to load sample data
        items_count: Number of sample items to create if load_data is True
        
    Returns:
        A configured SampleMCPServer instance
    """
    server = SampleMCPServer(name, description=description)
    
    if load_data:
        server.load_sample_data(items_count=items_count)
        
    return server


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run the server
    server = create_sample_server()
    server.run_sync() 
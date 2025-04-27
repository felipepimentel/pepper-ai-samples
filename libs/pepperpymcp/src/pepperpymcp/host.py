"""
MCP Host implementation that manages clients and coordinates access.

This module provides the host component of the MCP architecture, responsible for
managing client connections to MCP servers and aggregating context.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from .client import MCPClient as OfficialMCPClient
from .transports import HTTPTransport

logger = logging.getLogger(__name__)

class MCPClientWrapper:
    """Wrapper for MCP clients with additional functionality."""
    
    def __init__(self, client_id: str, url: str):
        """
        Initialize the client wrapper.
        
        Args:
            client_id: Unique identifier for this client
            url: URL of the MCP server to connect to
        """
        self.client_id = client_id
        self.url = url
        self.transport = HTTPTransport(url)
        self.client = OfficialMCPClient(self.transport)
        self.tools = []
        self.resources = []
        self.initialized = False
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the connection to the MCP server."""
        if self.initialized:
            return {"status": "already_initialized"}
            
        try:
            # Initialize the connection
            info = await self.client.initialize()
            
            # Get available tools
            tools_result = await self.client.list_tools()
            self.tools = tools_result.get("tools", [])
            
            # Get available resources
            resources_result = await self.client.list_resources()
            self.resources = resources_result.get("resources", [])
            
            self.initialized = True
            
            logger.info(f"Initialized client {self.client_id} to {self.url}")
            logger.info(f"Available tools: {[t['name'] for t in self.tools]}")
            logger.info(f"Available resources: {len(self.resources)} resources")
            
            return {
                "status": "success",
                "info": info,
                "tools": self.tools,
                "resources": self.resources
            }
        except Exception as e:
            logger.error(f"Failed to initialize client {self.client_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def call_tool(self, name: str, **params) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.initialized:
            await self.initialize()
            
        try:
            result = await self.client.call_tool(name, **params)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get a resource from the MCP server."""
        if not self.initialized:
            await self.initialize()
            
        try:
            result = await self.client.get_resource(uri)
            return result
        except Exception as e:
            logger.error(f"Error getting resource {uri}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            await self.transport.disconnect()
            self.initialized = False
            logger.info(f"Disconnected client {self.client_id}")
        except Exception as e:
            logger.error(f"Error disconnecting client {self.client_id}: {str(e)}")


class MCPHost:
    """
    Host implementation for managing MCP clients.
    
    The host is responsible for:
    1. Creating and managing client connections to MCP servers
    2. Coordinating access between clients
    3. Aggregating context for AI interactions
    4. Enforcing security policies
    """
    
    def __init__(self, name: str):
        """
        Initialize the MCP host.
        
        Args:
            name: Name of the host
        """
        self.name = name
        self.clients: Dict[str, MCPClientWrapper] = {}
        self._web_interface = None
        self._background_tasks = set()
        logger.info(f"Created MCP Host: {name}")
    
    async def create_client(self, url: str, client_id: Optional[str] = None) -> MCPClientWrapper:
        """
        Create a new client connected to an MCP server.
        
        Args:
            url: URL of the MCP server
            client_id: Optional client ID (generated if not provided)
            
        Returns:
            The created client wrapper
        """
        if client_id is None:
            client_id = f"client_{len(self.clients) + 1}"
            
        if client_id in self.clients:
            logger.warning(f"Client ID {client_id} already exists, overwriting")
            
        client = MCPClientWrapper(client_id, url)
        self.clients[client_id] = client
        logger.info(f"Created client {client_id} for {url}")
        
        # Don't initialize here - defer until needed
        return client
    
    async def remove_client(self, client_id: str) -> bool:
        """
        Remove a client by ID.
        
        Args:
            client_id: ID of the client to remove
            
        Returns:
            True if client was removed, False if not found
        """
        if client_id in self.clients:
            client = self.clients[client_id]
            await client.disconnect()
            del self.clients[client_id]
            logger.info(f"Removed client {client_id}")
            return True
            
        logger.warning(f"Client {client_id} not found for removal")
        return False
    
    async def process_query(self, query: str, client_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process a user query using available clients.
        
        Args:
            query: The user query
            client_ids: Optional list of client IDs to use (if None, uses all)
            
        Returns:
            The response from the AI model
        """
        # Determine which clients to use
        if client_ids is None:
            client_ids = list(self.clients.keys())
            
        # Collect capabilities from relevant clients
        capabilities = {}
        for client_id in client_ids:
            if client_id in self.clients:
                client = self.clients[client_id]
                
                # Initialize if needed
                if not client.initialized:
                    await client.initialize()
                    
                capabilities[client_id] = {
                    "tools": client.tools,
                    "resources": client.resources
                }
        
        # Simple implementation - in a real scenario, this would integrate with an LLM
        response = {
            "query": query,
            "available_capabilities": capabilities,
            "response": f"Processed query: {query}",
            "client_ids_used": client_ids
        }
        
        return response
    
    async def start_web_interface(self, host: str = "0.0.0.0", port: int = 8000, 
                                clients: Optional[Dict[str, MCPClientWrapper]] = None) -> Any:
        """
        Start the web interface for this host.
        
        Args:
            host: Host address to listen on
            port: Port to listen on
            clients: Optional dictionary of clients to register
            
        Returns:
            The web server instance
        """
        # Import FastAPI here to avoid circular imports
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        
        app = FastAPI(title=f"{self.name} Web Interface")
        
        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register additional clients if provided
        if clients:
            for client_id, client in clients.items():
                self.clients[client_id] = client
        
        # Define routes
        @app.get("/")
        async def get_root():
            return {
                "name": self.name,
                "clients": list(self.clients.keys()),
                "status": "running"
            }
        
        @app.get("/clients")
        async def get_clients():
            return {
                "clients": [
                    {
                        "id": client_id,
                        "url": client.url,
                        "initialized": client.initialized,
                        "tools_count": len(client.tools),
                        "resources_count": len(client.resources)
                    }
                    for client_id, client in self.clients.items()
                ]
            }
        
        @app.get("/clients/{client_id}")
        async def get_client(client_id: str):
            if client_id not in self.clients:
                raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
            
            client = self.clients[client_id]
            return {
                "id": client_id,
                "url": client.url,
                "initialized": client.initialized,
                "tools": client.tools,
                "resources": client.resources
            }
        
        @app.post("/clients/{client_id}/tools/{tool_name}")
        async def call_tool(client_id: str, tool_name: str, parameters: Dict[str, Any]):
            if client_id not in self.clients:
                raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
            
            client = self.clients[client_id]
            result = await client.call_tool(tool_name, **parameters)
            return result
        
        @app.get("/clients/{client_id}/resources/{resource_uri:path}")
        async def get_resource(client_id: str, resource_uri: str):
            if client_id not in self.clients:
                raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
            
            client = self.clients[client_id]
            result = await client.get_resource(resource_uri)
            return result
        
        @app.post("/query")
        async def process_user_query(query: Dict[str, Any]):
            result = await self.process_query(
                query["text"], 
                client_ids=query.get("client_ids")
            )
            return result
        
        # Start the server
        config = uvicorn.Config(app=app, host=host, port=port)
        server = uvicorn.Server(config)
        
        # Start server in a background task
        server_task = asyncio.create_task(server.serve())
        self._background_tasks.add(server_task)
        server_task.add_done_callback(self._background_tasks.discard)
        
        self._web_interface = server
        logger.info(f"Started web interface at http://{host}:{port}")
        
        return server
    
    async def shutdown(self):
        """Shutdown the host and all clients."""
        logger.info(f"Shutting down MCP Host: {self.name}")
        
        # Disconnect all clients
        disconnect_tasks = []
        for client_id, client in self.clients.items():
            disconnect_tasks.append(client.disconnect())
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks)
            
        # Cancel all background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete with timeout
        if self._background_tasks:
            try:
                await asyncio.wait(list(self._background_tasks), timeout=2)
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete during shutdown")
                
        logger.info(f"MCP Host {self.name} shutdown complete")
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with graceful shutdown."""
        await self.shutdown()
        return False 
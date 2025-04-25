#!/usr/bin/env python
"""
A2A and MCP Integration Example

This script demonstrates how to integrate the A2A protocol with MCP,
allowing agents to use both protocols for different purposes.
"""
import os
import uuid
import json
import logging
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response

# Tentar importar bibliotecas MCP do projeto
try:
    from libs.pepperpymcp.src.pepperpymcp import utils
    from libs.pepperpymcp.src.pepperpymcp.mcp import SimpleMCP
    HAS_MCP_LIBS = True
except ImportError:
    HAS_MCP_LIBS = False
    # Fallback se as bibliotecas não estiverem disponíveis
    class utils:
        @staticmethod
        def setup_logging():
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
    
    # Stub SimpleMCP para quando as bibliotecas não estão disponíveis
    class SimpleMCP:
        def __init__(self, name, description=None):
            self.name = name
            self.description = description
            self.tools = {}
        
        def tool(self, name=None):
            def decorator(func):
                tool_name = name or func.__name__
                self.tools[tool_name] = func
                return func
            return decorator

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
utils.setup_logging()
logger = logging.getLogger(__name__)

class A2AMCPAgent:
    """
    Agent that implements both A2A and MCP protocols.
    
    This allows the agent to:
    1. Be discovered and called by other A2A agents
    2. Use MCP tools and resources
    3. Act as an adapter between A2A and MCP
    """
    
    def __init__(self, name: str, description: str = None, version: str = "1.0.0"):
        """
        Initialize the A2A/MCP agent.
        
        Args:
            name: Agent name
            description: Agent description
            version: Agent version
        """
        self.name = name
        self.description = description or f"{name} - A2A/MCP Integration Agent"
        self.version = version
        
        # Initialize Flask for A2A endpoints
        self.app = Flask(name)
        
        # Initialize MCP for tools and resources
        self.mcp = SimpleMCP(name, description)
        
        # Setup endpoints
        self._setup_endpoints()
        
        # Register MCP tools
        self._register_tools()
        
        # Task storage for demonstration purposes
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def _setup_endpoints(self) -> None:
        """Set up A2A protocol endpoints."""
        # Agent card endpoint
        self.app.route("/.well-known/agent.json", methods=["GET"])(self.agent_card)
        
        # Task endpoints
        self.app.route("/tasks/send", methods=["POST"])(self.tasks_send)
        self.app.route("/tasks/sendSubscribe", methods=["POST"])(self.tasks_send_subscribe)
        self.app.route("/tasks/get/<task_id>", methods=["GET"])(self.tasks_get)
    
    def _register_tools(self) -> None:
        """Register MCP tools that will be used by the A2A interface."""
        @self.mcp.tool(name="web_search")
        def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
            """
            Perform a web search using MCP.
            
            Args:
                query: Search query
                num_results: Number of results to return
                
            Returns:
                Dictionary with search results
            """
            logger.info(f"MCP tool web_search called with query: '{query}'")
            
            # This would typically call an external search API
            # For demonstration, we return mock results
            results = []
            for i in range(1, min(num_results + 1, 6)):
                results.append({
                    "title": f"Example search result {i}",
                    "url": f"https://example.com/result{i}",
                    "snippet": f"This is a description of search result {i} for query: {query}"
                })
            
            return {
                "results": results,
                "query": query,
                "total": len(results)
            }
    
    def agent_card(self) -> Response:
        """Return the agent card in the well-known location."""
        card: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": ["text", "streaming"],
            "endpoints": {
                "tasks/send": "/tasks/send",
                "tasks/get": "/tasks/get/{task_id}",
                "tasks/sendSubscribe": "/tasks/sendSubscribe",
            },
            "authentication": {
                "type": "none"
            }
        }
        logger.info("Agent card requested")
        return jsonify(card)
    
    def tasks_send(self) -> Response:
        """Handle a task request using both A2A and MCP."""
        task_data = request.json
        task_id = task_data.get("id", str(uuid.uuid4()))
        
        logger.info(f"Received A2A task: {task_id}")
        
        # Extract the user's message
        user_message = self._extract_text_message(task_data)
        
        if not user_message:
            logger.warning(f"Task {task_id}: No text message provided")
            return jsonify({
                "id": task_id,
                "status": {
                    "state": "failed",
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "No text message provided."
                    }
                }
            })
        
        # Process task with MCP tool
        try:
            # Call MCP tool
            if HAS_MCP_LIBS:
                search_result = self.mcp.tools["web_search"](user_message)
            else:
                # Fallback when MCP libs aren't available
                search_result = {
                    "results": [
                        {
                            "title": "Example result 1",
                            "url": "https://example.com/result1",
                            "snippet": f"Mock result for: {user_message}"
                        }
                    ],
                    "query": user_message,
                    "total": 1
                }
            
            # Format results for A2A response
            formatted_results = self._format_search_results(search_result)
            
            # Create agent response message
            agent_message = {
                "role": "agent",
                "parts": [
                    {
                        "type": "text",
                        "text": f"Here are the search results for '{user_message}':\n\n{formatted_results}"
                    }
                ]
            }
            
            # Store task for later retrieval
            self.tasks[task_id] = {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "lastUpdateTime": self._get_timestamp()
                },
                "messages": [
                    task_data.get("message", {"role": "user", "parts": [{"type": "text", "text": user_message}]}),
                    agent_message
                ]
            }
            
            logger.info(f"Task {task_id}: Completed successfully")
            
            # Return completed task with results
            return jsonify(self.tasks[task_id])
            
        except Exception as e:
            logger.error(f"Task {task_id}: Error processing task: {str(e)}")
            error_response = {
                "id": task_id,
                "status": {
                    "state": "failed",
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": f"Error processing task: {str(e)}"
                    }
                }
            }
            self.tasks[task_id] = error_response
            return jsonify(error_response)
    
    def tasks_send_subscribe(self) -> Response:
        """Handle streaming tasks with Server-Sent Events."""
        task_data = request.json
        task_id = task_data.get("id", str(uuid.uuid4()))
        
        logger.info(f"Received streaming A2A task: {task_id}")
        
        # Extract the user's message
        user_message = self._extract_text_message(task_data)
        
        if not user_message:
            logger.warning(f"Streaming task {task_id}: No text message provided")
            return jsonify({
                "id": task_id,
                "status": {
                    "state": "failed",
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "No text message provided."
                    }
                }
            })
        
        def generate_events():
            # Send task status update: working
            logger.info(f"Streaming task {task_id}: Starting work")
            yield f"event: TaskStatusUpdateEvent\ndata: {json.dumps({'id': task_id, 'status': {'state': 'working'}})}\n\n"
            
            try:
                # Call MCP tool
                if HAS_MCP_LIBS:
                    search_result = self.mcp.tools["web_search"](user_message)
                else:
                    # Fallback when MCP libs aren't available
                    search_result = {
                        "results": [
                            {
                                "title": "Example result 1",
                                "url": "https://example.com/result1",
                                "snippet": f"Mock result for: {user_message}"
                            }
                        ],
                        "query": user_message,
                        "total": 1
                    }
                
                # Format results for A2A response
                formatted_results = self._format_search_results(search_result)
                
                # Create agent response message
                agent_message = {
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "text": f"Here are the search results for '{user_message}':\n\n{formatted_results}"
                        }
                    ]
                }
                
                # Store task for later retrieval
                self.tasks[task_id] = {
                    "id": task_id,
                    "status": {
                        "state": "completed",
                        "lastUpdateTime": self._get_timestamp()
                    },
                    "messages": [
                        task_data.get("message", {"role": "user", "parts": [{"type": "text", "text": user_message}]}),
                        agent_message
                    ]
                }
                
                # Send task artifact update with message
                logger.info(f"Streaming task {task_id}: Sending search results")
                yield f"event: TaskArtifactUpdateEvent\ndata: {json.dumps({'id': task_id, 'type': 'messages', 'messages': [agent_message]})}\n\n"
                
                # Send task status update: completed
                logger.info(f"Streaming task {task_id}: Completed")
                yield f"event: TaskStatusUpdateEvent\ndata: {json.dumps({'id': task_id, 'status': {'state': 'completed'}})}\n\n"
                
            except Exception as e:
                # Send task status update: failed
                logger.error(f"Streaming task {task_id}: Error processing task: {str(e)}")
                error_status = {
                    "id": task_id, 
                    "status": {
                        "state": "failed", 
                        "error": {
                            "code": "INTERNAL_ERROR", 
                            "message": str(e)
                        }
                    }
                }
                self.tasks[task_id] = error_status
                yield f"event: TaskStatusUpdateEvent\ndata: {json.dumps(error_status)}\n\n"
        
        return Response(generate_events(), mimetype="text/event-stream")
    
    def tasks_get(self, task_id: str) -> Response:
        """Get task status by ID."""
        logger.info(f"Task status requested: {task_id}")
        
        if task_id in self.tasks:
            return jsonify(self.tasks[task_id])
        else:
            return jsonify({
                "id": task_id,
                "status": {
                    "state": "unknown",
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Task {task_id} not found."
                    }
                }
            })
    
    def _extract_text_message(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract text message from A2A task data.
        
        Args:
            task_data: A2A task request data
            
        Returns:
            Extracted text message or None if not found
        """
        if "message" in task_data and "parts" in task_data["message"]:
            for part in task_data["message"]["parts"]:
                if part.get("type") == "text":
                    return part.get("text", "")
        return None
    
    def _format_search_results(self, search_result: Dict[str, Any]) -> str:
        """
        Format search results for display.
        
        Args:
            search_result: Raw search result from MCP tool
            
        Returns:
            Formatted results string
        """
        results = []
        for item in search_result.get("results", []):
            title = item.get("title", "No title")
            url = item.get("url", "No URL")
            snippet = item.get("snippet", "No description")
            results.append(f"- {title}\n  URL: {url}\n  {snippet}\n")
        
        return "\n".join(results)
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp string."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = True) -> None:
        """
        Run the A2A/MCP agent.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Whether to run in debug mode
        """
        logger.info(f"Starting {self.name} v{self.version} on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main() -> None:
    """Run the A2A/MCP integration example."""
    agent = A2AMCPAgent(
        name="A2AMCPIntegrationAgent",
        description="Agent that implements both A2A and MCP protocols"
    )
    agent.run()


if __name__ == "__main__":
    main() 
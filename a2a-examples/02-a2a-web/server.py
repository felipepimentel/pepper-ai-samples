#!/usr/bin/env python
"""
A2A Web Search Agent

This script implements a simple A2A-compatible agent that performs web searches.
It demonstrates how to implement the A2A protocol alongside web capabilities.
"""
import os
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Generator

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from datetime import datetime

# Tentar importar bibliotecas comuns do projeto
try:
    from libs.pepperpymcp.src.pepperpymcp import utils
except ImportError:
    # Fallback se as bibliotecas não estiverem disponíveis
    class utils:
        @staticmethod
        def setup_logging():
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
utils.setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuração
AGENT_NAME = "WebSearchAgent"
AGENT_DESCRIPTION = "A simple agent that performs web searches and returns results."
AGENT_VERSION = "1.0.0"
SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY", "")  # Set your API key as env variable
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID", "")  # Set your search engine ID as env variable

# A2A Endpoints
@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card() -> Response:
    """Return the agent card in the well-known location."""
    card: Dict[str, Any] = {
        "name": AGENT_NAME,
        "description": AGENT_DESCRIPTION,
        "version": AGENT_VERSION,
        "capabilities": ["text", "streaming", "input-required"],
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

@app.route("/tasks/send", methods=["POST"])
def tasks_send() -> Response:
    """Handle a task request."""
    task_data = request.json
    task_id = task_data.get("id", str(uuid.uuid4()))
    
    logger.info(f"Received task: {task_id}")
    
    # Extract the user's message
    user_message = None
    if "message" in task_data and "parts" in task_data["message"]:
        for part in task_data["message"]["parts"]:
            if part.get("type") == "text":
                user_message = part.get("text", "")
                break
    
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
    
    # Perform web search
    try:
        logger.info(f"Task {task_id}: Performing web search for query: '{user_message}'")
        search_results = perform_web_search(user_message)
        
        # Create agent response message with search results
        agent_message: Dict[str, Any] = {
            "role": "agent",
            "parts": [
                {
                    "type": "text",
                    "text": f"Here are the search results for '{user_message}':\n\n{search_results}"
                }
            ]
        }
        
        logger.info(f"Task {task_id}: Search completed successfully")
        
        # Return completed task with results
        return jsonify({
            "id": task_id,
            "status": {
                "state": "completed",
                "lastUpdateTime": datetime.utcnow().isoformat() + "Z"
            },
            "messages": [
                task_data.get("message", {"role": "user", "parts": [{"type": "text", "text": user_message}]}),
                agent_message
            ]
        })
    except Exception as e:
        logger.error(f"Task {task_id}: Error during web search: {str(e)}")
        return jsonify({
            "id": task_id,
            "status": {
                "state": "failed",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Error during web search: {str(e)}"
                }
            }
        })

@app.route("/tasks/sendSubscribe", methods=["POST"])
def tasks_send_subscribe() -> Response:
    """Handle streaming tasks with Server-Sent Events."""
    task_data = request.json
    task_id = task_data.get("id", str(uuid.uuid4()))
    
    logger.info(f"Received streaming task: {task_id}")
    
    # Extract the user's message (same as in tasks_send)
    user_message = None
    if "message" in task_data and "parts" in task_data["message"]:
        for part in task_data["message"]["parts"]:
            if part.get("type") == "text":
                user_message = part.get("text", "")
                break
    
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
    
    def generate_events() -> Generator[str, None, None]:
        # Send task status update: working
        logger.info(f"Streaming task {task_id}: Starting work")
        yield f"event: TaskStatusUpdateEvent\ndata: {json.dumps({'id': task_id, 'status': {'state': 'working'}})}\n\n"
        
        try:
            # Perform the web search
            logger.info(f"Streaming task {task_id}: Performing web search for query: '{user_message}'")
            search_results = perform_web_search(user_message)
            
            # Create agent response message
            agent_message: Dict[str, Any] = {
                "role": "agent",
                "parts": [
                    {
                        "type": "text",
                        "text": f"Here are the search results for '{user_message}':\n\n{search_results}"
                    }
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
            logger.error(f"Streaming task {task_id}: Error during web search: {str(e)}")
            yield f"event: TaskStatusUpdateEvent\ndata: {json.dumps({'id': task_id, 'status': {'state': 'failed', 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}})}\n\n"
    
    return Response(generate_events(), mimetype="text/event-stream")

@app.route("/tasks/get/<task_id>", methods=["GET"])
def tasks_get(task_id: str) -> Response:
    """Get task status by ID (simplified implementation)."""
    logger.info(f"Task status requested: {task_id}")
    # In a real implementation, you would store and retrieve task state
    return jsonify({
        "id": task_id,
        "status": {
            "state": "unknown",
            "message": "Task retrieval not implemented in this example."
        }
    })

def perform_web_search(query: str, num_results: int = 5) -> str:
    """
    Perform a web search for the given query.
    
    Args:
        query: The search query string
        num_results: Number of results to return
        
    Returns:
        Formatted string with search results
        
    This is a simplified implementation. In a real agent, you might use:
    - Google Custom Search API
    - Bing Search API
    - A web scraping approach with proper rate limiting
    
    For this example, we'll use a simplified approach that returns mock results
    if API keys aren't configured.
    """
    if SEARCH_API_KEY and SEARCH_ENGINE_ID:
        # Using Google Custom Search API
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": SEARCH_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": num_results
        }
        
        logger.info(f"Performing Google search for: '{query}'")
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "items" in data:
                for item in data["items"]:
                    title = item.get("title", "No title")
                    link = item.get("link", "No link")
                    snippet = item.get("snippet", "No description")
                    results.append(f"- {title}\n  URL: {link}\n  {snippet}\n")
                
                logger.info(f"Found {len(results)} search results")
                return "\n".join(results)
            else:
                logger.warning("No search results found")
                return "No results found."
        else:
            logger.error(f"Search API error: {response.status_code}")
            return f"Search API error: {response.status_code}"
    else:
        logger.info("Using mock search results (API keys not configured)")
        # Mock results for demo purposes
        return """
- Example search result 1
  URL: https://example.com/result1
  This is a description of the first search result.

- Example search result 2
  URL: https://example.com/result2
  This is a description of the second search result.

- Example search result 3
  URL: https://example.com/result3
  This is a description of the third search result.

Note: These are mock results. Configure SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables to get real results.
"""

def main() -> None:
    """Run the Flask application."""
    logger.info(f"Starting {AGENT_NAME} v{AGENT_VERSION}")
    # For development only - use a production WSGI server in production
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main() 
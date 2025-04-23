#!/usr/bin/env python
"""
A2A Web Search Client

This script demonstrates how to interact with an A2A-compatible agent
that provides web search capabilities.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

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


def discover_agent(agent_url: str) -> Dict[str, Any]:
    """
    Fetch the agent card to discover capabilities.

    Args:
        agent_url: Base URL of the agent

    Returns:
        Agent card as a dictionary

    Raises:
        Exception: If the agent card request fails
    """
    url = f"{agent_url.rstrip('/')}/.well-known/agent.json"
    logger.info(f"Discovering agent at: {url}")

    response = requests.get(url)

    if response.status_code != 200:
        error_msg = f"Failed to discover agent: {response.status_code} {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)

    logger.info("Agent discovered successfully")
    return response.json()


def send_task(agent_url: str, query: str) -> Dict[str, Any]:
    """
    Send a task to the agent and get the response.

    Args:
        agent_url: Base URL of the agent
        query: The search query to send

    Returns:
        Task response as a dictionary

    Raises:
        Exception: If the task request fails
    """
    task_id = str(uuid.uuid4())
    logger.info(f"Creating task with ID: {task_id}")

    # Create A2A task request
    task_request = {
        "id": task_id,
        "message": {"role": "user", "parts": [{"type": "text", "text": query}]},
    }

    # Send task to agent
    url = f"{agent_url.rstrip('/')}/tasks/send"
    logger.info(f"Sending task to: {url}")

    response = requests.post(url, json=task_request)

    if response.status_code != 200:
        error_msg = f"Task failed: {response.status_code} {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)

    logger.info(f"Task {task_id} completed successfully")
    return response.json()


def send_streaming_task(agent_url: str, query: str) -> None:
    """
    Send a task that uses server-sent events for streaming responses.

    Args:
        agent_url: Base URL of the agent
        query: The search query to send

    Raises:
        Exception: If the streaming task request fails
    """
    task_id = str(uuid.uuid4())
    logger.info(f"Creating streaming task with ID: {task_id}")

    # Create A2A task request (same as before)
    task_request = {
        "id": task_id,
        "message": {"role": "user", "parts": [{"type": "text", "text": query}]},
    }

    # Send streaming task to agent
    url = f"{agent_url.rstrip('/')}/tasks/sendSubscribe"
    logger.info(f"Sending streaming task to: {url}")

    response = requests.post(url, json=task_request, stream=True)

    if response.status_code != 200:
        error_msg = f"Streaming task failed: {response.status_code} {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)

    # Process SSE events
    event_type: Optional[str] = None

    logger.info(f"Processing streaming events for task {task_id}")
    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")

            # Each SSE message consists of one or more lines
            if line_str.startswith("event:"):
                event_type = line_str.split(":", 1)[1].strip()
                logger.debug(f"Received event type: {event_type}")
            elif line_str.startswith("data:"):
                data = json.loads(line_str.split(":", 1)[1].strip())

                # Process different event types
                if event_type == "TaskStatusUpdateEvent":
                    state = data.get("status", {}).get("state")
                    logger.info(f"Task status update: {state}")

                    if state == "working":
                        print("Agent is working on your request...")
                    elif state == "completed":
                        print("Task completed.")
                        logger.info(f"Task {task_id} completed successfully")
                    elif state == "failed":
                        error = data.get("status", {}).get("error", {})
                        error_msg = (
                            f"Task failed: {error.get('code')} - {error.get('message')}"
                        )
                        print(error_msg)
                        logger.error(error_msg)

                elif event_type == "TaskArtifactUpdateEvent":
                    if data.get("type") == "messages":
                        logger.info("Received message artifact")
                        for message in data.get("messages", []):
                            if message.get("role") == "agent":
                                for part in message.get("parts", []):
                                    if part.get("type") == "text":
                                        print("\nAgent response:\n")
                                        print(part.get("text"))


def main() -> None:
    """Main function to demonstrate agent interaction."""
    # Configure agent URL - change this if your agent is running elsewhere
    agent_url = "http://localhost:5000"

    try:
        # Discover agent capabilities
        agent_card = discover_agent(agent_url)
        print(f"Discovered agent: {agent_card['name']} - {agent_card['description']}")
        print(f"Version: {agent_card['version']}")
        print(f"Capabilities: {', '.join(agent_card['capabilities'])}")
        print()

        # Get user query
        query = input("Enter your search query: ")
        logger.info(f"User query: '{query}'")

        # Ask user whether to use streaming
        use_streaming = input("Use streaming? (y/n): ").lower() == "y"
        logger.info(f"Streaming mode: {use_streaming}")

        if use_streaming:
            # Send streaming task and process events
            print("\nSending streaming task...")
            send_streaming_task(agent_url, query)
        else:
            # Send regular task
            print("\nSending task...")
            response = send_task(agent_url, query)

            # Print agent's response
            print("\nAgent response:\n")
            for message in response.get("messages", []):
                if message.get("role") == "agent":
                    for part in message.get("parts", []):
                        if part.get("type") == "text":
                            print(part.get("text"))

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        logger.error(error_msg)


if __name__ == "__main__":
    main()

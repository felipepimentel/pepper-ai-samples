#!/usr/bin/env python
"""
Coordinator Agent for A2A Network

This agent coordinates tasks between specialized agents in the network,
routing requests to the appropriate agent based on task type.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a.src.pepperpya2a import A2AClient, create_a2a_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define agent addresses
MATH_AGENT_ADDRESS = "http://localhost:8081"
TEXT_AGENT_ADDRESS = "http://localhost:8082"


class CoordinatorAgent:
    """
    Coordinator Agent that routes tasks to specialized agents.

    This agent:
    1. Maintains connections to specialized agents
    2. Routes tasks based on their type and agent capabilities
    3. Returns results from the appropriate specialized agent
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        Initialize the coordinator agent.

        Args:
            host: Host to bind the server
            port: Port to run the coordinator on
        """
        self.host = host
        self.port = port
        self.server = create_a2a_server(
            name="Coordinator Agent",
            description="Routes tasks to specialized agents based on their capabilities",
            system_prompt="You are a coordinator that directs tasks to specialized agents in a network",
            port=port,
        )

        # Initialize agent clients
        self.math_client: Optional[A2AClient] = None
        self.text_client: Optional[A2AClient] = None

        # Register capabilities
        self.server.register_capability(
            name="coordinate_task",
            description="Route a task to the appropriate specialized agent",
            input_schema={
                "type": "object",
                "properties": {
                    "task_type": {
                        "type": "string",
                        "description": "Type of task (math, text, etc.)",
                    },
                    "input": {
                        "type": "object",
                        "description": "Input data for the task",
                    },
                },
                "required": ["task_type", "input"],
            },
            handler=self.coordinate_task,
        )

        self.server.register_capability(
            name="discover_agents",
            description="List all available agents and their capabilities",
            handler=self.discover_agents,
        )

    async def connect_to_agents(self):
        """Establish connections to all specialized agents."""
        logger.info("Connecting to specialized agents...")

        try:
            # Connect to math agent
            self.math_client = A2AClient(MATH_AGENT_ADDRESS)
            # No need to call connect explicitly with the updated client
            math_card = await self.math_client.get_agent_card()
            logger.info(f"Connected to math agent: {math_card.get('name', 'Unknown')}")

            # Connect to text agent
            self.text_client = A2AClient(TEXT_AGENT_ADDRESS)
            text_card = await self.text_client.get_agent_card()
            logger.info(f"Connected to text agent: {text_card.get('name', 'Unknown')}")

            logger.info("Successfully connected to all specialized agents")
        except Exception as e:
            logger.error(
                f"Failed to connect to specialized agents: {str(e)}", exc_info=True
            )
            raise

    async def start(self):
        """Start the coordinator agent server."""
        # First connect to all specialized agents
        await self.connect_to_agents()

        # Then start the server
        await self.server.start_server()
        logger.info(f"Coordinator agent started on {self.host}:{self.port}")

    async def close(self):
        """Close all connections and stop the server."""
        logger.info("Shutting down coordinator agent...")

        # Close client connections
        if self.math_client:
            await self.math_client.close()
        if self.text_client:
            await self.text_client.close()

        # Close server
        await self.server.close()
        logger.info("Coordinator agent stopped")

    async def coordinate_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the appropriate specialized agent based on its type.

        Args:
            data: Input data containing task_type and input

        Returns:
            Results from the specialized agent that handled the task
        """
        task_type = data.get("task_type", "").lower()
        input_data = data.get("input", {})

        if not task_type:
            logger.error("No task_type provided")
            return {"error": "No task_type provided"}

        logger.info(f"Received task of type: {task_type}")

        try:
            # Route to the appropriate agent based on task type
            if task_type == "math" or task_type.startswith("calc"):
                if not self.math_client:
                    return {"error": "Math agent not connected"}

                # Determine the appropriate math capability
                if "equation" in task_type:
                    capability = "solve_equation"
                elif "stats" in task_type or "statistics" in task_type:
                    capability = "stats"
                else:
                    capability = "calculate"

                logger.info(f"Routing to math agent with capability: {capability}")
                task_result = await self.math_client.send_task(capability, input_data)

                if "id" in task_result:
                    result = await self.math_client.wait_for_task_completion(
                        task_result["id"]
                    )
                    return {
                        "result": result.get("output", {}),
                        "handled_by": "math_agent",
                        "capability": capability,
                    }
                else:
                    return {
                        "error": task_result.get(
                            "error", "Unknown error with math agent"
                        )
                    }

            elif task_type.startswith("text"):
                if not self.text_client:
                    return {"error": "Text agent not connected"}

                # Determine the appropriate text capability
                if "summary" in task_type or "summarize" in task_type:
                    capability = "summarize"
                elif "sentiment" in task_type:
                    capability = "analyze_sentiment"
                else:
                    capability = "analyze_text"

                logger.info(f"Routing to text agent with capability: {capability}")
                task_result = await self.text_client.send_task(capability, input_data)

                if "id" in task_result:
                    result = await self.text_client.wait_for_task_completion(
                        task_result["id"]
                    )
                    return {
                        "result": result.get("output", {}),
                        "handled_by": "text_agent",
                        "capability": capability,
                    }
                else:
                    return {
                        "error": task_result.get(
                            "error", "Unknown error with text agent"
                        )
                    }

            else:
                logger.warning(f"Unknown task type: {task_type}")
                return {
                    "error": f"Unknown task type: {task_type}",
                    "supported_types": [
                        "math",
                        "calculate",
                        "stats",
                        "equation",
                        "text",
                        "summarize",
                        "sentiment",
                    ],
                }

        except Exception as e:
            error_msg = f"Error coordinating task: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}

    async def discover_agents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all available agents and their capabilities.

        Returns:
            Information about all connected agents and their capabilities
        """
        logger.info("Discovering agents and capabilities")

        try:
            agents = [
                {
                    "name": "Coordinator Agent",
                    "description": "Routes tasks to specialized agents based on task type",
                    "capabilities": ["coordinate_task", "discover_agents"],
                }
            ]

            # Get math agent capabilities
            if self.math_client:
                math_card = await self.math_client.get_agent_card()
                agents.append(
                    {
                        "name": math_card.get("name", "Math Agent"),
                        "description": math_card.get(
                            "description", "Math processing agent"
                        ),
                        "capabilities": [
                            c["name"] for c in math_card.get("capabilities", [])
                        ],
                    }
                )

            # Get text agent capabilities
            if self.text_client:
                text_card = await self.text_client.get_agent_card()
                agents.append(
                    {
                        "name": text_card.get("name", "Text Agent"),
                        "description": text_card.get(
                            "description", "Text processing agent"
                        ),
                        "capabilities": [
                            c["name"] for c in text_card.get("capabilities", [])
                        ],
                    }
                )

            return {"agents": agents, "count": len(agents)}
        except Exception as e:
            error_msg = f"Error discovering agents: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}


async def main():
    """Main function to run the coordinator agent."""
    parser = argparse.ArgumentParser(description="A2A Network Coordinator Agent")
    parser.add_argument("--host", default="localhost", help="Host to bind the server")
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to bind the server"
    )

    args = parser.parse_args()

    # Create and start the coordinator agent
    coordinator = CoordinatorAgent(host=args.host, port=args.port)

    try:
        await coordinator.start()

        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
    finally:
        await coordinator.close()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python
"""
A2A Network Client

This client demonstrates how to interact with the A2A network through the coordinator agent.
It sends tasks to the network and receives results.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

# Add parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a.src.pepperpya2a import create_a2a_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class A2ANetworkClient:
    """
    Client for the A2A Network that communicates with the coordinator agent
    to route tasks to specialized agents.
    """

    def __init__(self, coordinator_url: str = "http://localhost:8080"):
        """
        Initialize the A2A network client.

        Args:
            coordinator_url: URL of the coordinator agent
        """
        self.coordinator_url = coordinator_url
        self.client = create_a2a_client()
        self.connected = False

    async def connect(self):
        """Connect to the coordinator agent."""
        try:
            logger.info(f"Connecting to coordinator at {self.coordinator_url}")
            await self.client.connect(self.coordinator_url)

            # Get coordinator capabilities
            capabilities = await self.client.discover_capabilities()
            logger.info(f"Coordinator capabilities: {capabilities}")

            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to coordinator: {str(e)}", exc_info=True)
            return False

    async def close(self):
        """Close the connection to the coordinator."""
        if self.connected:
            await self.client.close()
            self.connected = False
            logger.info("Connection to coordinator closed")

    async def send_math_task(self, operation: str, numbers: list) -> Dict[str, Any]:
        """
        Send a math task to the network.

        Args:
            operation: Math operation (add, subtract, multiply, divide, etc.)
            numbers: List of numbers to perform the operation on

        Returns:
            Result of the math operation
        """
        if not self.connected:
            await self.connect()

        task_data = {"operation": operation, "numbers": numbers}

        logger.info(f"Sending math task: {task_data}")
        response = await self.client.call_capability(
            "coordinate_task", {"task_type": "math", "input": task_data}
        )

        logger.info(f"Received response: {response}")
        return response

    async def send_statistics_task(self, data_points: list) -> Dict[str, Any]:
        """
        Send a statistics task to the network.

        Args:
            data_points: List of numerical data points to analyze

        Returns:
            Statistical analysis of the data points
        """
        if not self.connected:
            await self.connect()

        task_data = {"operation": "stats", "data": data_points}

        logger.info(f"Sending statistics task: {task_data}")
        response = await self.client.call_capability(
            "coordinate_task", {"task_type": "math", "input": task_data}
        )

        logger.info(f"Received response: {response}")
        return response

    async def send_equation_task(self, equation: str) -> Dict[str, Any]:
        """
        Send an equation solving task to the network.

        Args:
            equation: Mathematical equation to solve

        Returns:
            Solution to the equation
        """
        if not self.connected:
            await self.connect()

        task_data = {"operation": "solve_equation", "equation": equation}

        logger.info(f"Sending equation task: {task_data}")
        response = await self.client.call_capability(
            "coordinate_task", {"task_type": "math", "input": task_data}
        )

        logger.info(f"Received response: {response}")
        return response

    async def send_text_analysis_task(self, text: str) -> Dict[str, Any]:
        """
        Send a text analysis task to the network.

        Args:
            text: Text to analyze

        Returns:
            Analysis of the text
        """
        if not self.connected:
            await self.connect()

        task_data = {"query": text}

        logger.info("Sending text analysis task")
        response = await self.client.call_capability(
            "coordinate_task",
            {"task_type": "text", "capability": "analyze_text", "input": task_data},
        )

        logger.info(f"Received response: {response}")
        return response

    async def send_summarization_task(self, text: str) -> Dict[str, Any]:
        """
        Send a text summarization task to the network.

        Args:
            text: Text to summarize

        Returns:
            Summary of the text
        """
        if not self.connected:
            await self.connect()

        task_data = {"query": text}

        logger.info("Sending summarization task")
        response = await self.client.call_capability(
            "coordinate_task",
            {"task_type": "text", "capability": "summarize", "input": task_data},
        )

        logger.info(f"Received response: {response}")
        return response

    async def send_sentiment_analysis_task(self, text: str) -> Dict[str, Any]:
        """
        Send a sentiment analysis task to the network.

        Args:
            text: Text to analyze for sentiment

        Returns:
            Sentiment analysis of the text
        """
        if not self.connected:
            await self.connect()

        task_data = {"query": text}

        logger.info("Sending sentiment analysis task")
        response = await self.client.call_capability(
            "coordinate_task",
            {
                "task_type": "text",
                "capability": "analyze_sentiment",
                "input": task_data,
            },
        )

        logger.info(f"Received response: {response}")
        return response

    async def discover_network_agents(self) -> Dict[str, Any]:
        """
        Discover all agents in the network and their capabilities.

        Returns:
            Dictionary of agents and their capabilities
        """
        if not self.connected:
            await self.connect()

        logger.info("Discovering network agents")
        response = await self.client.call_capability("discover_agents", {})

        logger.info(f"Discovered agents: {response}")
        return response


async def demo():
    """Run a demonstration of the A2A network client."""
    client = A2ANetworkClient()

    try:
        # Connect to the coordinator
        connected = await client.connect()
        if not connected:
            logger.error("Failed to connect to coordinator. Exiting.")
            return

        # Discover network agents
        logger.info("Discovering network agents...")
        agents = await client.discover_network_agents()
        print("\nDiscovered agents:")
        print(json.dumps(agents, indent=2))

        # Math capabilities demo
        print("\n=== Math Agent Capabilities ===")

        # Addition
        print("\nPerforming addition:")
        result = await client.send_math_task("add", [5, 3, 2])
        print(f"5 + 3 + 2 = {result.get('result', 'Error')}")

        # Multiplication
        print("\nPerforming multiplication:")
        result = await client.send_math_task("multiply", [4, 6])
        print(f"4 × 6 = {result.get('result', 'Error')}")

        # Statistics
        print("\nCalculating statistics:")
        data = [12, 15, 18, 22, 30, 35, 12]
        result = await client.send_statistics_task(data)
        print(f"Stats for {data}:")
        print(json.dumps(result, indent=2))

        # Equation solving
        print("\nSolving equation:")
        equation = "2x + 5 = 15"
        result = await client.send_equation_task(equation)
        print(f"Solution to '{equation}': {result.get('result', 'Error')}")

        # Text capabilities demo
        print("\n=== Text Agent Capabilities ===")

        # Text analysis
        print("\nAnalyzing text:")
        sample_text = "The quick brown fox jumps over the lazy dog. This sentence contains all the letters in the English alphabet. It is a pangram that has been used for testing typewriters and computer keyboards."
        result = await client.send_text_analysis_task(sample_text)
        print("Text analysis results:")
        print(json.dumps(result, indent=2))

        # Text summarization
        print("\nSummarizing text:")
        long_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to intelligence displayed by animals including humans. 
        AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
        The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving". 
        This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.
        AI applications include advanced web search engines, recommendation systems, understanding human speech, self-driving cars, generative or creative tools, and competing at the highest level in strategic game systems.
        """
        result = await client.send_summarization_task(long_text)
        print("Summary:")
        print(result.get("summary", "Error generating summary"))

        # Sentiment analysis
        print("\nAnalyzing sentiment:")
        positive_text = "I love this product! It's amazing and works perfectly. The quality is excellent and I'm very happy with my purchase."
        negative_text = "This is terrible. It broke after two days and customer service was unhelpful. I'm very disappointed and frustrated."

        print("\nPositive text sentiment:")
        result = await client.send_sentiment_analysis_task(positive_text)
        print(json.dumps(result, indent=2))

        print("\nNegative text sentiment:")
        result = await client.send_sentiment_analysis_task(negative_text)
        print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Error in demo: {str(e)}", exc_info=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(demo())

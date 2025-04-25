#!/usr/bin/env python
"""
A2A Client for communication between agents.

This module implements a client to interact with A2A servers,
allowing capability discovery, task submission, and result monitoring.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List
from urllib.parse import urljoin

# Add parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class A2AClient:
    """
    Client for interacting with A2A servers.

    Allows sending tasks, monitoring their progress, and receiving results.
    """

    def __init__(self, server_url: str):
        """
        Initialize the A2A client.

        Args:
            server_url: Base URL of the A2A server
        """
        self.server_url = server_url.rstrip("/") + "/"
        self.session = None

    async def _ensure_session(self):
        """Ensure an HTTP session is available"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Get the agent card (capabilities).

        Returns:
            Dictionary with information about the agent
        """
        await self._ensure_session()

        try:
            async with self.session.get(
                urljoin(self.server_url, ".well-known/agent-card.json")
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error getting agent card: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"HTTP error {response.status}",
                        "details": error_text,
                    }
        except Exception as e:
            logger.error(f"Exception getting agent card: {str(e)}")
            return {"error": str(e)}

    async def send_task(
        self, capability: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a task to the A2A server.

        Args:
            capability: Name of the capability to call
            input_data: Input data for the task

        Returns:
            Response from task creation, including ID
        """
        await self._ensure_session()

        endpoint = urljoin(self.server_url, f"tasks/{capability}")

        try:
            headers = {"Content-Type": "application/json"}
            payload = {"input": input_data}

            logger.info(f"Sending task to {capability} with data: {input_data}")

            async with self.session.post(
                endpoint, json=payload, headers=headers
            ) as response:
                if response.status == 202:  # Accepted
                    result = await response.json()
                    logger.info(f"Task created with ID: {result.get('id', 'unknown')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error creating task: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"HTTP error {response.status}",
                        "details": error_text,
                    }
        except Exception as e:
            logger.error(f"Exception sending task: {str(e)}")
            return {"error": str(e)}

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a task.

        Args:
            task_id: ID of the task

        Returns:
            Current status of the task
        """
        await self._ensure_session()

        endpoint = urljoin(self.server_url, f"tasks/{task_id}")

        try:
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(
                        f"Task {task_id} status: {result.get('status', 'unknown')}"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error getting status: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"HTTP error {response.status}",
                        "details": error_text,
                    }
        except Exception as e:
            logger.error(f"Exception checking status: {str(e)}")
            return {"error": str(e)}

    async def wait_for_task_completion(
        self, task_id: str, timeout: int = 60, poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Wait for task completion with polling.

        Args:
            task_id: ID of the task
            timeout: Maximum wait time in seconds
            poll_interval: Interval between checks in seconds

        Returns:
            Final result of the task
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = await self.get_task_status(task_id)

            if "error" in result:
                return result

            status = result.get("status")

            if status == "completed":
                logger.info(f"Task {task_id} completed successfully")
                return result
            elif status == "failed":
                logger.error(f"Task {task_id} failed: {result.get('error')}")
                return result
            elif status == "cancelled":
                logger.warning(f"Task {task_id} was cancelled")
                return result

            # Wait before next check
            await asyncio.sleep(poll_interval)

        logger.error(f"Timeout exceeded waiting for task {task_id}")
        return {"error": "timeout", "task_id": task_id}

    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            Result of the cancellation operation
        """
        await self._ensure_session()

        endpoint = urljoin(self.server_url, f"tasks/{task_id}/cancel")

        try:
            async with self.session.post(endpoint) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Task {task_id} cancelled")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Error cancelling task: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"HTTP error {response.status}",
                        "details": error_text,
                    }
        except Exception as e:
            logger.error(f"Exception cancelling task: {str(e)}")
            return {"error": str(e)}

    async def discover_capabilities(self) -> List[Dict[str, Any]]:
        """
        Discover the capabilities available on the agent.

        Returns:
            List of available capabilities
        """
        agent_card = await self.get_agent_card()

        if "error" in agent_card:
            return []

        return agent_card.get("capabilities", [])


if __name__ == "__main__":

    async def main():
        # Example client usage
        client = A2AClient("http://localhost:8082")

        try:
            # Discover capabilities
            capabilities = await client.discover_capabilities()
            print(f"Available capabilities: {json.dumps(capabilities, indent=2)}")

            # Send a math task
            if any(cap["name"] == "calculate" for cap in capabilities):
                task_result = await client.send_task(
                    "calculate", {"operation": "add", "numbers": [5, 7, 3]}
                )

                if "id" in task_result:
                    # Wait for result
                    result = await client.wait_for_task_completion(task_result["id"])
                    print(f"Result: {json.dumps(result, indent=2)}")
        finally:
            # Close client
            await client.close()

    asyncio.run(main())

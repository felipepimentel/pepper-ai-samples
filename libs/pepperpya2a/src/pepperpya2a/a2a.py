"""
Core A2A implementation module.

This module provides a simplified implementation of the A2A protocol with
a decorator-based API similar to FastAPI.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskInput(BaseModel):
    """A2A task input model."""

    task_id: Optional[str] = None
    skill: str
    input: Dict[str, Any] = Field(default_factory=dict)


class TaskStatus(BaseModel):
    """A2A task status model."""

    task_id: str
    status: str
    skill: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    required_input: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PepperA2A:
    """Simplified A2A server implementation with decorator-based API."""

    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        """Initialize an A2A server with agent information."""
        self.app = FastAPI()
        self.name = name
        self.description = description
        self.version = version

        # Agent capabilities and task handlers
        self._capabilities = []
        self._task_handlers = {}
        self._tasks = {}  # Task storage

        # Set up default routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up default A2A protocol routes."""
        # Agent card endpoint (discovery)
        self.app.get("/.well-known/agent.json")(self._agent_card_handler)

        # Core A2A endpoints
        self.app.post("/tasks/send")(self._tasks_send_handler)
        self.app.get("/tasks/get")(self._tasks_get_handler)
        self.app.post("/tasks/cancel")(self._tasks_cancel_handler)

    async def _agent_card_handler(self):
        """Handler for agent card requests."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self._capabilities,
        }

    async def _tasks_send_handler(self, request: Request):
        """Handler for task send requests."""
        data = await request.json()
        task_id = data.get("task_id", str(uuid.uuid4()))
        skill = data.get("skill", "default")

        if "task_id" in data and task_id in self._tasks:
            # Update existing task
            # (Handle input for multi-turn interactions)
            task = self._tasks[task_id]
            if task["status"] == "input-required":
                # Process input provided by client
                self._tasks[task_id]["status"] = "in-progress"
                self._tasks[task_id]["updated_at"] = datetime.now().isoformat()

                # Update task with new input
                new_input = data.get("input", {})
                if isinstance(new_input, dict):
                    self._tasks[task_id]["input"].update(new_input)

                # Run the task handler with the provided input
                handler = self._task_handlers.get(skill)
                if handler:
                    asyncio.create_task(
                        self._run_task_handler(task_id, handler, self._tasks[task_id])
                    )
                return {"task_id": task_id, "status": "in-progress"}
            else:
                return {"error": "Task not in input-required state"}
        else:
            # New task
            current_time = datetime.now().isoformat()
            self._tasks[task_id] = {
                "task_id": task_id,
                "status": "in-progress",
                "skill": skill,
                "input": data.get("input", {}),
                "result": None,
                "error": None,
                "required_input": None,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Find and run the matching handler
            handler = self._task_handlers.get(skill)
            if handler:
                asyncio.create_task(
                    self._run_task_handler(task_id, handler, self._tasks[task_id])
                )
                return {"task_id": task_id, "status": "in-progress"}
            else:
                self._tasks[task_id]["status"] = "error"
                self._tasks[task_id]["error"] = {
                    "message": f"No handler for skill: {skill}"
                }
                self._tasks[task_id]["updated_at"] = datetime.now().isoformat()
                return {
                    "task_id": task_id,
                    "status": "error",
                    "error": {"message": f"No handler for skill: {skill}"},
                }

    async def _run_task_handler(
        self, task_id: str, handler: Callable, task_data: Dict[str, Any]
    ):
        """Run a task handler asynchronously."""
        try:
            result = await handler(task_data)
            # Only update if task is still in-progress (might have been set to input-required)
            if self._tasks[task_id]["status"] == "in-progress":
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["result"] = result
                self._tasks[task_id]["updated_at"] = datetime.now().isoformat()
        except Exception as e:
            logger.exception(f"Error running task handler for task {task_id}")
            self._tasks[task_id]["status"] = "error"
            self._tasks[task_id]["error"] = {"message": str(e)}
            self._tasks[task_id]["updated_at"] = datetime.now().isoformat()

    async def _tasks_get_handler(self, request: Request):
        """Handler for task get requests."""
        task_id = request.query_params.get("task_id")
        if not task_id or task_id not in self._tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        return self._tasks[task_id]

    async def _tasks_cancel_handler(self, request: Request):
        """Handler for task cancellation requests."""
        data = await request.json()
        task_id = data.get("task_id")
        if not task_id or task_id not in self._tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        self._tasks[task_id]["status"] = "canceled"
        self._tasks[task_id]["updated_at"] = datetime.now().isoformat()
        return {"task_id": task_id, "status": "canceled"}

    def capability(
        self,
        name: str,
        description: str = "",
        input_schema: Dict = None,
        output_schema: Dict = None,
    ):
        """
        Decorator to register an agent capability.

        Args:
            name: The name of the capability/skill
            description: A human-readable description
            input_schema: JSON Schema describing expected input
            output_schema: JSON Schema describing expected output

        Returns:
            Decorator function
        """

        def decorator(func):
            capability_info = {
                "name": name,
                "description": description,
                "input_schema": input_schema or {},
                "output_schema": output_schema or {},
            }
            self._capabilities.append(capability_info)
            self._task_handlers[name] = func
            return func

        return decorator

    def require_input(
        self, task_id: str, description: str, schema: Dict[str, Any] = None
    ):
        """
        Helper to request additional input from the client.

        Args:
            task_id: The task ID requesting input
            description: Why input is needed
            schema: JSON Schema for the required input
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")

        self._tasks[task_id]["status"] = "input-required"
        self._tasks[task_id]["required_input"] = {
            "description": description,
            "schema": schema or {},
        }
        self._tasks[task_id]["updated_at"] = datetime.now().isoformat()

    def enable_cors(self, origins: List[str] = None):
        """
        Enable CORS middleware for the FastAPI app.

        Args:
            origins: List of allowed origins, defaults to ["*"]
        """
        if origins is None:
            origins = ["*"]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the A2A server.

        Args:
            host: Host address to bind
            port: Port to listen on
        """
        import uvicorn

        logger.info(f"Starting A2A server '{self.name}' on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# Factory function to create an A2A server
def create_a2a_server(name: str, description: str = "", version: str = "1.0.0"):
    """
    Create an A2A server instance.

    Args:
        name: Server name
        description: Server description
        version: Server version

    Returns:
        PepperA2A instance
    """
    return PepperA2A(name, description, version)

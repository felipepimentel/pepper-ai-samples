#!/usr/bin/env python
"""
Basic A2A protocol server implementation.
Shows how to create a simple weather assistant agent.
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# A2A protocol type definitions
class AgentCapabilities:
    """Agent capabilities definition."""
    def __init__(self, streaming: bool = False, push_notifications: bool = False):
        self.streaming = streaming
        self.push_notifications = push_notifications
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "streaming": self.streaming,
            "pushNotifications": self.push_notifications
        }

class AgentSkill:
    """Agent skill definition."""
    def __init__(self, id: str, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

class AgentCard:
    """Agent card definition containing metadata about the agent."""
    def __init__(
        self,
        name: str,
        description: str,
        url: str,
        version: str,
        capabilities: AgentCapabilities,
        skills: List[AgentSkill]
    ):
        self.name = name
        self.description = description
        self.url = url
        self.version = version
        self.capabilities = capabilities
        self.skills = skills
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": self.capabilities.to_dict(),
            "skills": [skill.to_dict() for skill in self.skills]
        }

class TextPart:
    """Text message part."""
    def __init__(self, text: str):
        self.text = text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "text": self.text
        }

class Message:
    """Message with one or more parts."""
    def __init__(self, role: str, parts: List[Any]):
        self.role = role
        self.parts = parts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "parts": [part.to_dict() for part in self.parts]
        }

class TaskStatus:
    """Task status information."""
    def __init__(self, state: str, message: Optional[Message] = None, timestamp: Optional[str] = None):
        self.state = state
        self.message = message
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "state": self.state,
            "timestamp": self.timestamp
        }
        if self.message:
            result["message"] = self.message.to_dict()
        return result

class Task:
    """Task object representing a unit of work."""
    def __init__(self, id: str, session_id: Optional[str] = None, status: Optional[TaskStatus] = None):
        self.id = id
        self.session_id = session_id
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id
        }
        if self.session_id:
            result["sessionId"] = self.session_id
        if self.status:
            result["status"] = self.status.to_dict()
        return result

# Task state constants
class TaskState:
    """Task state constants."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"

# In-memory task storage
tasks: Dict[str, Task] = {}

# Create a FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define our agent card
agent_card = AgentCard(
    name="Weather Assistant",
    description="Provides information about weather and forecasts",
    url="http://localhost:8000",
    version="1.0.0",
    capabilities=AgentCapabilities(
        streaming=True,
        push_notifications=False
    ),
    skills=[
        AgentSkill(
            id="weather_forecast",
            name="Weather Forecast",
            description="Provides weather forecasts for different cities"
        ),
        AgentSkill(
            id="historical_weather",
            name="Historical Weather",
            description="Provides historical weather data"
        )
    ]
)

# Define agent card endpoint
@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Returns the agent card in the A2A protocol format."""
    return agent_card.to_dict()

# Task creation endpoint
@app.post("/tasks")
async def create_task(task_data: Dict[str, Any]):
    """Creates a new task."""
    task_id = task_data.get("id")
    if not task_id:
        raise HTTPException(status_code=400, detail="Task ID is required")
    
    session_id = task_data.get("sessionId")
    
    # Create a new task with submitted status
    task = Task(
        id=task_id,
        session_id=session_id,
        status=TaskStatus(
            state=TaskState.SUBMITTED,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    )
    
    # Store the task
    tasks[task_id] = task
    
    return task.to_dict()

# Send message to a task
@app.post("/tasks/{task_id}/send")
async def send_message(task_id: str, request: Request):
    """Sends a message to a task."""
    # Check if task exists
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Get the message from request
    message_data = await request.json()
    
    # Process the message
    task = await process_message(task_id, message_data)
    
    return task.to_dict()

# Get task status
@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Gets the current state of a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return tasks[task_id].to_dict()

async def process_message(task_id: str, message_data: Dict[str, Any]) -> Task:
    """Process a message and update the task."""
    # Get the existing task
    task = tasks[task_id]
    
    # Update task status to working
    task.status = TaskStatus(
        state=TaskState.WORKING,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    # Extract message text
    text = ""
    if "parts" in message_data and len(message_data["parts"]) > 0:
        part = message_data["parts"][0]
        if part.get("type") == "text":
            text = part.get("text", "")
    
    # Simple weather information based on city
    response_text = ""
    if "tempo em São Paulo" in text.lower():
        response_text = "Em São Paulo hoje está ensolarado com temperatura de 28°C."
    elif "tempo em Rio de Janeiro" in text.lower():
        response_text = "No Rio de Janeiro hoje está parcialmente nublado com temperatura de 32°C."
    elif "tempo em " in text.lower():
        city = text.lower().split("tempo em ")[1].split("?")[0].strip()
        response_text = f"Não tenho informações específicas sobre {city}, mas posso pesquisar para você."
    else:
        response_text = "Olá! Posso fornecer informações sobre o clima. Pergunte-me sobre o tempo em uma cidade específica."
    
    # Create response message
    response_message = Message(
        role="agent",
        parts=[TextPart(text=response_text)]
    )
    
    # Update task with completed status and response
    task.status = TaskStatus(
        state=TaskState.COMPLETED,
        message=response_message,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    # Store updated task
    tasks[task_id] = task
    
    return task

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
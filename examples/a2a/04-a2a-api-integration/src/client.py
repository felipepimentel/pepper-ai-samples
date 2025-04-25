#!/usr/bin/env python
"""
Cliente A2A para interagir com o servidor meteorológico com integração de API.

Este exemplo demonstra como criar um cliente que se conecta a um servidor A2A
e envia mensagens para obter informações meteorológicas de uma API real.
"""

import asyncio
import sys
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import aiohttp

class TextPart:
    """Text message part."""
    def __init__(self, text: str):
        self.text = text
        self.type = "text"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text
        }

class DataPart:
    """Structured data message part."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.type = "data"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data
        }

class Message:
    """Message with one or more parts."""
    def __init__(self, role: str, parts: List[Union[TextPart, DataPart]]):
        self.role = role
        self.parts = parts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "parts": [part.to_dict() for part in self.parts]
        }

class A2AClient:
    """Simple A2A protocol client to interact with A2A agents."""
    
    def __init__(self, agent_url: str):
        """Initialize the A2A client with the agent URL.
        
        Args:
            agent_url: Base URL of the A2A agent
        """
        self.agent_url = agent_url.rstrip("/")
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """Retrieve the agent card to discover agent capabilities."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/.well-known/agent.json") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get agent card: {response.status}")
                return await response.json()
    
    async def create_task(self, task_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task on the agent.
        
        Args:
            task_id: Unique identifier for the task
            session_id: Optional session ID for related tasks
            
        Returns:
            Dict containing the created task information
        """
        payload = {"id": task_id}
        if session_id:
            payload["sessionId"] = session_id
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.agent_url}/tasks",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to create task: {response.status}")
                return await response.json()
    
    async def send_message(self, task_id: str, text: str, role: str = "user") -> Dict[str, Any]:
        """Send a text message to a task.
        
        Args:
            task_id: ID of the task to send the message to
            text: Text content of the message
            role: Role of the message sender (default: user)
            
        Returns:
            Dict containing the updated task information
        """
        message = Message(
            role=role,
            parts=[TextPart(text=text)]
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.agent_url}/tasks/{task_id}/send",
                json=message.to_dict()
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send message: {response.status}")
                return await response.json()
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get the current state of a task.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Dict containing the task information
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/tasks/{task_id}") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get task: {response.status}")
                return await response.json()

def format_message_response(task_result: Dict[str, Any]) -> None:
    """Format and print a message response from the agent."""
    if "status" in task_result and "message" in task_result["status"]:
        response = task_result["status"]["message"]
        
        if "parts" in response:
            # Print text parts
            for part in response["parts"]:
                if part["type"] == "text":
                    print(f"\nAgente: {part['text']}")
        
        # Print artifacts if any
        if "artifacts" in task_result and task_result["artifacts"]:
            print("\nArtefatos:")
            for artifact in task_result["artifacts"]:
                print(f"- {artifact['name']}: {artifact['description']}")
                
                # If we want to show artifact data (commented out to avoid too much output)
                # for part in artifact["parts"]:
                #     if part["type"] == "data":
                #         print(json.dumps(part["data"], indent=2, ensure_ascii=False))
    else:
        print("\nAgente: [Sem resposta]")

async def chat_with_agent(agent_url: str):
    """Interactive chat session with an A2A agent."""
    client = A2AClient(agent_url)
    
    # Get agent card to discover capabilities
    print("Conectando ao agente...")
    agent_card = await client.get_agent_card()
    print(f"Conectado a {agent_card['name']}: {agent_card['description']}")
    
    # Print agent skills
    print("\nHabilidades do agente:")
    for skill in agent_card["skills"]:
        print(f"- {skill['name']}: {skill['description']}")
    
    # Create a new task for this conversation
    task_id = f"task_{int(datetime.now().timestamp())}"
    await client.create_task(task_id)
    
    # Interactive chat loop
    print("\nConversa com o agente (digite 'sair' para encerrar):")
    print("\nDicas de perguntas:")
    print("- Como está o tempo em São Paulo?")
    print("- Qual a previsão para os próximos dias em Rio de Janeiro?")
    print("- Como está o clima em Nova York?")
    print("- Previsão do tempo para Tóquio")
    
    while True:
        user_input = input("\nVocê: ")
        if user_input.lower() == "sair":
            break
        
        # Send user message to the agent
        task_result = await client.send_message(task_id, user_input)
        
        # Check if task is in INPUT_REQUIRED state
        while task_result.get("status", {}).get("state") == "input_required":
            # Display the agent's request for input
            format_message_response(task_result)
            
            # Get user input for the required information
            additional_input = input("\nVocê: ")
            if additional_input.lower() == "sair":
                return
            
            # Send additional input
            task_result = await client.send_message(task_id, additional_input)
        
        # Display final response
        format_message_response(task_result)

def main():
    """Main entry point for the A2A client."""
    # Default to localhost:8000 if no argument is provided
    agent_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Run the chat function
    asyncio.run(chat_with_agent(agent_url))

if __name__ == "__main__":
    main() 
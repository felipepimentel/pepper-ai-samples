#!/usr/bin/env python
"""
Cliente A2A básico para interagir com o servidor de previsão do tempo.

Este exemplo demonstra como criar um cliente que se conecta a um servidor A2A
e envia mensagens para obter informações sobre o clima.
"""

import asyncio
import sys
import json
from typing import Dict, List, Any, Optional

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
    task_id = f"task_{hash(str(asyncio.get_event_loop().time()))}"[:16]
    await client.create_task(task_id)
    
    # Interactive chat loop
    print("\nConversa com o agente (digite 'sair' para encerrar):")
    while True:
        user_input = input("\nVocê: ")
        if user_input.lower() == "sair":
            break
        
        # Send user message to the agent
        task_result = await client.send_message(task_id, user_input)
        
        # Display agent response
        if "status" in task_result and "message" in task_result["status"]:
            response = task_result["status"]["message"]
            if "parts" in response and len(response["parts"]) > 0:
                print(f"\nAgente: {response['parts'][0]['text']}")
        else:
            print("\nAgente: [Sem resposta]")

def main():
    """Main entry point for the A2A client."""
    # Default to localhost:8000 if no argument is provided
    agent_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Run the chat function
    asyncio.run(chat_with_agent(agent_url))

if __name__ == "__main__":
    main() 
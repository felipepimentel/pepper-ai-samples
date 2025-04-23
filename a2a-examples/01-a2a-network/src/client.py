#!/usr/bin/env python
"""
A2A Network client implementation.
Shows how to interact with a network of A2A agents.
"""
import sys
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union

class A2AClient:
    """Advanced A2A protocol client with network capabilities."""
    
    def __init__(self, agent_url: str):
        """Initialize the A2A client with the agent URL."""
        self.agent_url = agent_url.rstrip("/")
        self.agent_card = None
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """Retrieve the agent card to discover agent capabilities."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/.well-known/agent.json") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get agent card: {response.status}")
                self.agent_card = await response.json()
                return self.agent_card
    
    async def create_task(self, task_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task on the agent."""
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
        """Send a text message to a task."""
        message = {
            "role": role,
            "parts": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.agent_url}/tasks/{task_id}/send",
                json=message
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send message: {response.status}")
                return await response.json()
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get the current state of a task."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/tasks/{task_id}") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get task: {response.status}")
                return await response.json()
    
    async def discover_agent(self, target_agent_url: str) -> Dict[str, Any]:
        """Discover another agent using this agent's discovery capability."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.agent_url}/agents/discover",
                json={"url": target_agent_url}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to discover agent: {response.status}")
                return await response.json()
    
    async def list_agents(self) -> Dict[str, Any]:
        """List known agents registered with this agent."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/agents") as response:
                if response.status != 200:
                    raise Exception(f"Failed to list agents: {response.status}")
                return await response.json()

async def network_console(hub_url: str):
    """Interactive console for A2A network operations."""
    client = A2AClient(hub_url)
    
    try:
        # Connect to hub agent
        print("Connecting to A2A network hub...")
        agent_card = await client.get_agent_card()
        print(f"Connected to {agent_card['name']}: {agent_card['description']}")
        
        # Print agent skills
        print("\nHub agent skills:")
        for skill in agent_card["skills"]:
            print(f"- {skill['name']}: {skill['description']}")
        
        # Create a new session for this conversation
        session_id = f"session_{asyncio.get_event_loop().time()}"
        task_id = f"task_{asyncio.get_event_loop().time()}"
        await client.create_task(task_id, session_id)
        
        # Print help message
        print("\nA2A Network Console")
        print("=================")
        print("Commands:")
        print("  help - Show this help message")
        print("  discover <url> - Discover an agent at the specified URL")
        print("  list - List known agents")
        print("  chat <message> - Send a chat message to the hub agent")
        print("  exit - Exit the console")
        
        while True:
            # Get user input
            command = input("\n> ")
            
            if command.lower() == "exit":
                print("Exiting...")
                break
            
            elif command.lower() == "help":
                print("Commands:")
                print("  help - Show this help message")
                print("  discover <url> - Discover an agent at the specified URL")
                print("  list - List known agents")
                print("  chat <message> - Send a chat message to the hub agent")
                print("  exit - Exit the console")
            
            elif command.lower().startswith("discover "):
                # Extract URL
                url = command[9:].strip()
                if not url.startswith("http://"):
                    url = f"http://{url}"
                
                print(f"Discovering agent at {url}...")
                try:
                    result = await client.discover_agent(url)
                    print(f"Successfully discovered agent: {result['agent_id']}")
                    print(f"Agent details: {json.dumps(result['agent_card'], indent=2)}")
                except Exception as e:
                    print(f"Error discovering agent: {str(e)}")
            
            elif command.lower() == "list":
                try:
                    result = await client.list_agents()
                    print("Known agents:")
                    for i, agent in enumerate(result["agents"]):
                        print(f"{i+1}. {agent['name']} - {agent['description']}")
                        print(f"   URL: {agent['url']}")
                        if "skills" in agent:
                            print(f"   Skills: {', '.join([s['name'] for s in agent['skills']])}")
                        print()
                except Exception as e:
                    print(f"Error listing agents: {str(e)}")
            
            elif command.lower().startswith("chat "):
                message = command[5:].strip()
                if message:
                    print(f"Sending: {message}")
                    try:
                        result = await client.send_message(task_id, message)
                        
                        if "status" in result and "message" in result["status"]:
                            response = result["status"]["message"]
                            if "parts" in response and len(response["parts"]) > 0:
                                print(f"\nAgent: {response['parts'][0]['text']}")
                        
                        # Check for artifacts
                        if "artifacts" in result and result["artifacts"]:
                            for artifact in result["artifacts"]:
                                print(f"\nArtifact: {artifact['name']} - {artifact['description']}")
                                for part in artifact["parts"]:
                                    if part["type"] == "data":
                                        print(f"Data: {json.dumps(part['data'], indent=2)}")
                    except Exception as e:
                        print(f"Error sending message: {str(e)}")
                else:
                    print("Please provide a message to send.")
            
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")
    
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Main entry point for the A2A network client."""
    # Default to localhost:8001 if no argument is provided
    hub_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    # Run the network console
    asyncio.run(network_console(hub_url))

if __name__ == "__main__":
    main() 
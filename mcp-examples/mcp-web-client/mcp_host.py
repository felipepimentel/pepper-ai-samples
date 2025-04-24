#!/usr/bin/env python
"""
MCP Host Example

This script demonstrates how an AI assistant (like Claude or an IDE like Cursor)
would use MCP clients to interact with MCP servers.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union, Tuple

from pepperpymcp import MCPClient
from pepperpymcp.transports import ConnectionMode, SSETransport, StdioTransport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("host.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp_host")

class MCPHost:
    """
    Simulates an AI assistant host that interacts with MCP servers.
    
    This class demonstrates how an application like Claude Desktop or Cursor
    would use MCP clients to access external tools and resources.
    """
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.server_capabilities: Dict[str, Dict[str, Any]] = {}
    
    async def connect_to_server(self, server_url: str, name: Optional[str] = None, connection_type: str = "http") -> str:
        """Connect to an MCP server and return its assigned name."""
        try:
            # Choose the transport based on connection type
            if connection_type.lower() == "stdio":
                logger.info("Using stdio transport...")
                transport = StdioTransport()
                # For stdio, use a default name if not provided
                if not name:
                    name = "stdio-server"
            else:
                # Use SSE transport for HTTP connections
                logger.info(f"Using HTTP transport for {server_url}...")
                transport = SSETransport(server_url)
            
            client = MCPClient(transport)
            
            # Initialize the connection
            await client.connect()
            server_info = await client.initialize()
            
            # Generate a name for this server connection if not provided
            if not name:
                name = server_info.get("name", "unnamed-server").lower().replace(" ", "-")
                
                # Make sure the name is unique
                if name in self.clients:
                    i = 1
                    while f"{name}-{i}" in self.clients:
                        i += 1
                    name = f"{name}-{i}"
            
            # Store the client and server info
            self.clients[name] = client
            self.server_capabilities[name] = {
                "info": server_info,
                "tools": await client.list_tools(),
                "resources": await client.list_resources(),
                "prompts": await client.list_prompts()
            }
            
            if connection_type.lower() == "stdio":
                logger.info(f"Connected to server '{name}' via stdio")
            else:
                logger.info(f"Connected to server '{name}' at {server_url}")
                
            logger.info(f"Server description: {server_info.get('description', 'No description')}")
            return name
            
        except Exception as e:
            if connection_type.lower() == "stdio":
                logger.error(f"Error connecting to server via stdio: {str(e)}")
            else:
                logger.error(f"Error connecting to server at {server_url}: {str(e)}")
            raise
    
    async def disconnect_from_server(self, server_name: str) -> bool:
        """Disconnect from a specific MCP server."""
        if server_name in self.clients:
            try:
                await self.clients[server_name].disconnect()
                del self.clients[server_name]
                del self.server_capabilities[server_name]
                logger.info(f"Disconnected from server '{server_name}'")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from server '{server_name}': {str(e)}")
                return False
        else:
            logger.warning(f"No connection found for server '{server_name}'")
            return False
    
    async def list_connected_servers(self) -> List[Dict[str, Any]]:
        """List all connected MCP servers and their capabilities."""
        servers = []
        for name, capabilities in self.server_capabilities.items():
            servers.append({
                "name": name,
                "server_info": capabilities["info"],
                "tools_count": len(capabilities["tools"].get("tools", [])),
                "resources_count": len(capabilities["resources"].get("resources", [])),
                "prompts_count": len(capabilities["prompts"].get("prompts", []))
            })
        return servers
    
    async def list_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """List detailed capabilities of a specific server."""
        if server_name not in self.server_capabilities:
            logger.error(f"No server found with name '{server_name}'")
            raise ValueError(f"No server found with name '{server_name}'")
        
        return self.server_capabilities[server_name]
    
    async def call_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool on a specific MCP server."""
        if server_name not in self.clients:
            logger.error(f"No connection found for server '{server_name}'")
            raise ValueError(f"No connection found for server '{server_name}'")
        
        # Add to conversation history
        self.conversation_history.append({
            "type": "tool_call",
            "server": server_name,
            "tool": tool_name,
            "params": params
        })
        
        try:
            # Call the tool
            logger.info(f"Calling tool '{tool_name}' on server '{server_name}' with params: {params}")
            result = await self.clients[server_name].call_tool(tool_name, **params)
            
            # Add the result to conversation history
            self.conversation_history.append({
                "type": "tool_result",
                "server": server_name,
                "tool": tool_name,
                "result": result
            })
            
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on server '{server_name}': {str(e)}")
            # Add the error to conversation history
            self.conversation_history.append({
                "type": "tool_error",
                "server": server_name,
                "tool": tool_name,
                "error": str(e)
            })
            raise
    
    async def get_resource(self, server_name: str, uri: str) -> Any:
        """Get a resource from a specific MCP server."""
        if server_name not in self.clients:
            logger.error(f"No connection found for server '{server_name}'")
            raise ValueError(f"No connection found for server '{server_name}'")
        
        # Add to conversation history
        self.conversation_history.append({
            "type": "resource_request",
            "server": server_name,
            "uri": uri
        })
        
        try:
            # Get the resource
            logger.info(f"Getting resource '{uri}' from server '{server_name}'")
            result = await self.clients[server_name].get_resource(uri)
            
            # Add the result to conversation history
            self.conversation_history.append({
                "type": "resource_result",
                "server": server_name,
                "uri": uri,
                "result": result
            })
            
            return result
        except Exception as e:
            logger.error(f"Error getting resource '{uri}' from server '{server_name}': {str(e)}")
            # Add the error to conversation history
            self.conversation_history.append({
                "type": "resource_error",
                "server": server_name,
                "uri": uri,
                "error": str(e)
            })
            raise
    
    async def call_prompt(self, server_name: str, prompt_name: str, params: Dict[str, Any]) -> Any:
        """Call a prompt on a specific MCP server."""
        if server_name not in self.clients:
            logger.error(f"No connection found for server '{server_name}'")
            raise ValueError(f"No connection found for server '{server_name}'")
        
        # Add to conversation history
        self.conversation_history.append({
            "type": "prompt_request",
            "server": server_name,
            "prompt": prompt_name,
            "params": params
        })
        
        try:
            # Call the prompt
            logger.info(f"Calling prompt '{prompt_name}' on server '{server_name}' with params: {params}")
            result = await self.clients[server_name].call_prompt(prompt_name, **params)
            
            # Add the result to conversation history
            self.conversation_history.append({
                "type": "prompt_result",
                "server": server_name,
                "prompt": prompt_name,
                "result": result
            })
            
            return result
        except Exception as e:
            logger.error(f"Error calling prompt '{prompt_name}' on server '{server_name}': {str(e)}")
            # Add the error to conversation history
            self.conversation_history.append({
                "type": "prompt_error",
                "server": server_name,
                "prompt": prompt_name,
                "error": str(e)
            })
            raise
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation history."""
        self.conversation_history.append({
            "type": "message",
            "role": "user",
            "content": content
        })
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation history."""
        self.conversation_history.append({
            "type": "message",
            "role": "assistant",
            "content": content
        })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history."""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

async def interactive_mode():
    """Run the MCP host in interactive mode."""
    host = MCPHost()
    print("\n" + "="*50)
    print("🤖 MCP Host Interactive Mode")
    print("="*50)
    
    while True:
        print("\nOptions:")
        print("1. Connect to an MCP server")
        print("2. List connected servers")
        print("3. List server capabilities")
        print("4. Call tool")
        print("5. Get resource")
        print("6. Call prompt")
        print("7. View conversation history")
        print("8. Clear conversation history")
        print("9. Disconnect from server")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-9): ")
        
        if choice == "0":
            # Disconnect from all servers before exiting
            for server_name in list(host.clients.keys()):
                await host.disconnect_from_server(server_name)
            print("Exiting interactive mode. Goodbye!")
            break
            
        elif choice == "1":
            # Connect to a server
            conn_type = input("Connection type (http/stdio) [http]: ").strip().lower() or "http"
            
            if conn_type == "http":
                server_url = input("Server URL [http://localhost:8000]: ").strip() or "http://localhost:8000"
                server_name = input("Server name (optional): ").strip() or None
                
                try:
                    name = await host.connect_to_server(server_url, server_name, "http")
                    print(f"✅ Connected to server '{name}'")
                except Exception as e:
                    print(f"❌ Failed to connect: {e}")
            
            elif conn_type == "stdio":
                server_name = input("Server name (optional): ").strip() or None
                
                try:
                    name = await host.connect_to_server("", server_name, "stdio")
                    print(f"✅ Connected to server '{name}'")
                except Exception as e:
                    print(f"❌ Failed to connect: {e}")
            
            else:
                print(f"❌ Unknown connection type: {conn_type}")
        
        elif choice == "2":
            # List connected servers
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
            else:
                print("\nConnected servers:")
                for i, server in enumerate(servers, 1):
                    print(f"{i}. {server['name']} - {server['server_info'].get('description', 'No description')}")
                    print(f"   Tools: {server['tools_count']}, Resources: {server['resources_count']}, Prompts: {server['prompts_count']}")
        
        elif choice == "3":
            # List server capabilities
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
                continue
                
            print("\nSelect a server:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['name']}")
                
            selection = input("Enter server number: ")
            try:
                idx = int(selection) - 1
                if 0 <= idx < len(servers):
                    server_name = servers[idx]["name"]
                    capabilities = await host.list_server_capabilities(server_name)
                    
                    print(f"\nCapabilities for server '{server_name}':")
                    
                    # Print tools
                    tools = capabilities["tools"].get("tools", [])
                    print(f"\nTools ({len(tools)}):")
                    for tool in tools:
                        print(f"- {tool['name']}: {tool.get('description', 'No description')}")
                    
                    # Print resources
                    resources = capabilities["resources"].get("resources", [])
                    print(f"\nResources ({len(resources)}):")
                    for resource in resources:
                        print(f"- {resource.get('pattern')}: {resource.get('description', 'No description')}")
                    
                    # Print prompts
                    prompts = capabilities["prompts"].get("prompts", [])
                    print(f"\nPrompts ({len(prompts)}):")
                    for prompt in prompts:
                        print(f"- {prompt.get('name')}: {prompt.get('description', 'No description')}")
                else:
                    print(f"❌ Invalid selection")
            except ValueError:
                print(f"❌ Invalid input, please enter a number")
        
        elif choice == "4":
            # Call tool
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
                continue
                
            print("\nSelect a server:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['name']}")
                
            server_selection = input("Enter server number: ")
            try:
                server_idx = int(server_selection) - 1
                if 0 <= server_idx < len(servers):
                    server_name = servers[server_idx]["name"]
                    capabilities = await host.list_server_capabilities(server_name)
                    
                    tools = capabilities["tools"].get("tools", [])
                    if not tools:
                        print(f"❌ No tools available on server '{server_name}'")
                        continue
                        
                    print("\nSelect a tool:")
                    for i, tool in enumerate(tools, 1):
                        print(f"{i}. {tool['name']}: {tool.get('description', 'No description')}")
                    
                    tool_selection = input("Enter tool number: ")
                    try:
                        tool_idx = int(tool_selection) - 1
                        if 0 <= tool_idx < len(tools):
                            tool_name = tools[tool_idx]["name"]
                            
                            # Get parameters
                            params = {}
                            if "parameters" in tools[tool_idx]:
                                print("\nEnter parameters:")
                                for param in tools[tool_idx]["parameters"]:
                                    param_name = param.get("name")
                                    param_type = param.get("type", "string")
                                    is_required = param.get("required", False)
                                    default_value = param.get("default")
                                    
                                    prompt = f"{param_name} ({param_type})"
                                    if default_value is not None:
                                        prompt += f" [default: {default_value}]"
                                    if is_required:
                                        prompt += " (required)"
                                    prompt += ": "
                                    
                                    value = input(prompt).strip()
                                    
                                    if value:
                                        # Convert to appropriate type
                                        if param_type == "number":
                                            try:
                                                if "." in value:
                                                    params[param_name] = float(value)
                                                else:
                                                    params[param_name] = int(value)
                                            except ValueError:
                                                print(f"❌ Invalid number format for {param_name}, using as string")
                                                params[param_name] = value
                                        elif param_type == "boolean":
                                            params[param_name] = value.lower() in ("true", "yes", "y", "1")
                                        else:
                                            params[param_name] = value
                                    elif default_value is not None:
                                        params[param_name] = default_value
                                    elif is_required:
                                        print(f"❌ Parameter {param_name} is required")
                                        continue
                            
                            # Call the tool
                            try:
                                print(f"\nCalling tool '{tool_name}' with parameters: {params}")
                                result = await host.call_tool(server_name, tool_name, params)
                                print(f"\n✅ Tool result:")
                                print(json.dumps(result, indent=2))
                            except Exception as e:
                                print(f"❌ Error calling tool: {e}")
                        else:
                            print(f"❌ Invalid tool selection")
                    except ValueError:
                        print(f"❌ Invalid input, please enter a number")
                else:
                    print(f"❌ Invalid server selection")
            except ValueError:
                print(f"❌ Invalid input, please enter a number")
        
        elif choice == "5":
            # Get resource
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
                continue
                
            print("\nSelect a server:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['name']}")
                
            server_selection = input("Enter server number: ")
            try:
                server_idx = int(server_selection) - 1
                if 0 <= server_idx < len(servers):
                    server_name = servers[server_idx]["name"]
                    capabilities = await host.list_server_capabilities(server_name)
                    
                    resources = capabilities["resources"].get("resources", [])
                    if not resources:
                        print(f"❌ No resources available on server '{server_name}'")
                        continue
                        
                    print("\nAvailable resource patterns:")
                    for i, resource in enumerate(resources, 1):
                        print(f"{i}. {resource.get('pattern')}: {resource.get('description', 'No description')}")
                    
                    resource_uri = input("\nEnter resource URI: ").strip()
                    
                    if not resource_uri:
                        print("❌ Resource URI cannot be empty")
                        continue
                        
                    # Get the resource
                    try:
                        print(f"\nGetting resource '{resource_uri}'")
                        result = await host.get_resource(server_name, resource_uri)
                        print(f"\n✅ Resource content:")
                        if isinstance(result.get("content"), (bytes, bytearray)):
                            print(f"Binary content, {len(result.get('content'))} bytes")
                        else:
                            print(result.get("content"))
                    except Exception as e:
                        print(f"❌ Error getting resource: {e}")
                else:
                    print(f"❌ Invalid server selection")
            except ValueError:
                print(f"❌ Invalid input, please enter a number")
        
        elif choice == "6":
            # Call prompt
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
                continue
                
            print("\nSelect a server:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['name']}")
                
            server_selection = input("Enter server number: ")
            try:
                server_idx = int(server_selection) - 1
                if 0 <= server_idx < len(servers):
                    server_name = servers[server_idx]["name"]
                    capabilities = await host.list_server_capabilities(server_name)
                    
                    prompts = capabilities["prompts"].get("prompts", [])
                    if not prompts:
                        print(f"❌ No prompts available on server '{server_name}'")
                        continue
                        
                    print("\nSelect a prompt:")
                    for i, prompt in enumerate(prompts, 1):
                        print(f"{i}. {prompt.get('name')}: {prompt.get('description', 'No description')}")
                    
                    prompt_selection = input("Enter prompt number: ")
                    try:
                        prompt_idx = int(prompt_selection) - 1
                        if 0 <= prompt_idx < len(prompts):
                            prompt_name = prompts[prompt_idx]["name"]
                            
                            # Get parameters
                            params = {}
                            if "parameters" in prompts[prompt_idx]:
                                print("\nEnter parameters:")
                                for param in prompts[prompt_idx]["parameters"]:
                                    param_name = param.get("name")
                                    param_type = param.get("type", "string")
                                    is_required = param.get("required", False)
                                    default_value = param.get("default")
                                    
                                    prompt = f"{param_name} ({param_type})"
                                    if default_value is not None:
                                        prompt += f" [default: {default_value}]"
                                    if is_required:
                                        prompt += " (required)"
                                    prompt += ": "
                                    
                                    value = input(prompt).strip()
                                    
                                    if value:
                                        # Convert to appropriate type
                                        if param_type == "number":
                                            try:
                                                if "." in value:
                                                    params[param_name] = float(value)
                                                else:
                                                    params[param_name] = int(value)
                                            except ValueError:
                                                print(f"❌ Invalid number format for {param_name}, using as string")
                                                params[param_name] = value
                                        elif param_type == "boolean":
                                            params[param_name] = value.lower() in ("true", "yes", "y", "1")
                                        else:
                                            params[param_name] = value
                                    elif default_value is not None:
                                        params[param_name] = default_value
                                    elif is_required:
                                        print(f"❌ Parameter {param_name} is required")
                                        continue
                            
                            # Call the prompt
                            try:
                                print(f"\nCalling prompt '{prompt_name}' with parameters: {params}")
                                result = await host.call_prompt(server_name, prompt_name, params)
                                print(f"\n✅ Prompt result:")
                                print(json.dumps(result, indent=2, ensure_ascii=False))
                            except Exception as e:
                                print(f"❌ Error calling prompt: {e}")
                        else:
                            print(f"❌ Invalid prompt selection")
                    except ValueError:
                        print(f"❌ Invalid input, please enter a number")
                else:
                    print(f"❌ Invalid server selection")
            except ValueError:
                print(f"❌ Invalid input, please enter a number")
        
        elif choice == "7":
            # View conversation history
            history = host.get_conversation_history()
            
            if not history:
                print("❌ No conversation history")
                continue
                
            print("\nConversation history:")
            for i, entry in enumerate(history, 1):
                entry_type = entry.get("type")
                
                if entry_type == "message":
                    role = entry.get("role", "unknown")
                    content = entry.get("content", "")
                    print(f"{i}. [{role.upper()}] {content}")
                
                elif entry_type in ("tool_call", "resource_request", "prompt_request"):
                    server = entry.get("server", "unknown")
                    if entry_type == "tool_call":
                        tool = entry.get("tool", "unknown")
                        params = entry.get("params", {})
                        print(f"{i}. [TOOL REQUEST] Server: {server}, Tool: {tool}, Params: {params}")
                    elif entry_type == "resource_request":
                        uri = entry.get("uri", "unknown")
                        print(f"{i}. [RESOURCE REQUEST] Server: {server}, URI: {uri}")
                    elif entry_type == "prompt_request":
                        prompt = entry.get("prompt", "unknown")
                        params = entry.get("params", {})
                        print(f"{i}. [PROMPT REQUEST] Server: {server}, Prompt: {prompt}, Params: {params}")
                
                elif entry_type in ("tool_result", "resource_result", "prompt_result"):
                    server = entry.get("server", "unknown")
                    if entry_type == "tool_result":
                        tool = entry.get("tool", "unknown")
                        print(f"{i}. [TOOL RESULT] Server: {server}, Tool: {tool}")
                    elif entry_type == "resource_result":
                        uri = entry.get("uri", "unknown")
                        print(f"{i}. [RESOURCE RESULT] Server: {server}, URI: {uri}")
                    elif entry_type == "prompt_result":
                        prompt = entry.get("prompt", "unknown")
                        print(f"{i}. [PROMPT RESULT] Server: {server}, Prompt: {prompt}")
                
                elif entry_type in ("tool_error", "resource_error", "prompt_error"):
                    server = entry.get("server", "unknown")
                    error = entry.get("error", "unknown error")
                    if entry_type == "tool_error":
                        tool = entry.get("tool", "unknown")
                        print(f"{i}. [TOOL ERROR] Server: {server}, Tool: {tool}, Error: {error}")
                    elif entry_type == "resource_error":
                        uri = entry.get("uri", "unknown")
                        print(f"{i}. [RESOURCE ERROR] Server: {server}, URI: {uri}, Error: {error}")
                    elif entry_type == "prompt_error":
                        prompt = entry.get("prompt", "unknown")
                        print(f"{i}. [PROMPT ERROR] Server: {server}, Prompt: {prompt}, Error: {error}")
                
                else:
                    print(f"{i}. [UNKNOWN] {entry}")
        
        elif choice == "8":
            # Clear conversation history
            confirm = input("Are you sure you want to clear the conversation history? (y/n): ").strip().lower()
            if confirm in ("y", "yes"):
                host.clear_conversation_history()
                print("✅ Conversation history cleared")
        
        elif choice == "9":
            # Disconnect from server
            servers = await host.list_connected_servers()
            
            if not servers:
                print("❌ No servers connected")
                continue
                
            print("\nSelect a server to disconnect:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['name']}")
                
            server_selection = input("Enter server number (or 'all' to disconnect from all): ").strip().lower()
            
            if server_selection == "all":
                for server in servers:
                    await host.disconnect_from_server(server['name'])
                print("✅ Disconnected from all servers")
            else:
                try:
                    server_idx = int(server_selection) - 1
                    if 0 <= server_idx < len(servers):
                        server_name = servers[server_idx]["name"]
                        success = await host.disconnect_from_server(server_name)
                        if success:
                            print(f"✅ Disconnected from server '{server_name}'")
                        else:
                            print(f"❌ Failed to disconnect from server '{server_name}'")
                    else:
                        print(f"❌ Invalid server selection")
                except ValueError:
                    print(f"❌ Invalid input, please enter a number or 'all'")
        
        else:
            print(f"❌ Invalid choice: {choice}")

async def run_demo(server_url: str = None, use_stdio: bool = False):
    """Run a demonstration of the MCP host capabilities."""
    host = MCPHost()
    
    print("\n" + "="*50)
    print("🤖 MCP Host Demo Mode")
    print("="*50)
    
    # Connect to server
    if use_stdio:
        print("\n1️⃣ Connecting to server via stdio...")
        server_name = await host.connect_to_server("", None, "stdio")
    else:
        if not server_url:
            server_url = "http://localhost:8000"
        print(f"\n1️⃣ Connecting to server at {server_url}...")
        server_name = await host.connect_to_server(server_url)
    
    print(f"✅ Connected to server: {server_name}")
    
    # List server capabilities
    print("\n2️⃣ Listing server capabilities...")
    capabilities = await host.list_server_capabilities(server_name)
    
    print(f"✅ Server info: {json.dumps(capabilities['info'], indent=2)}")
    print(f"✅ Tools: {len(capabilities['tools'].get('tools', []))}")
    print(f"✅ Resources: {len(capabilities['resources'].get('resources', []))}")
    print(f"✅ Prompts: {len(capabilities['prompts'].get('prompts', []))}")
    
    # List all tools
    print("\n3️⃣ Available tools:")
    for tool in capabilities['tools'].get('tools', []):
        print(f"- {tool['name']}: {tool.get('description', 'No description')}")
    
    # Demo each capability
    if capabilities['tools'].get('tools', []):
        print("\n4️⃣ Demonstrating tool capabilities...")
        
        # Find a simple tool to demo
        simple_tools = [
            tool for tool in capabilities['tools'].get('tools', [])
            if len(tool.get('parameters', [])) <= 1
        ]
        
        if simple_tools:
            # Choose the first simple tool
            demo_tool = simple_tools[0]
            tool_name = demo_tool['name']
            params = {}
            
            # Populate parameters with default values
            for param in demo_tool.get('parameters', []):
                param_name = param.get('name')
                if 'default' in param:
                    params[param_name] = param['default']
                elif param.get('type') == 'string':
                    params[param_name] = "test"
                elif param.get('type') == 'number':
                    params[param_name] = 42
                elif param.get('type') == 'boolean':
                    params[param_name] = True
            
            print(f"Calling tool '{tool_name}' with parameters: {params}")
            try:
                result = await host.call_tool(server_name, tool_name, params)
                print(f"✅ Tool result: {json.dumps(result, indent=2)}")
            except Exception as e:
                print(f"❌ Error calling tool: {e}")
        else:
            print("❌ No simple tools available for demo")
    
    # Demo resource if available
    if capabilities['resources'].get('resources', []):
        print("\n5️⃣ Demonstrating resource capabilities...")
        
        # Try to find a simple resource pattern to demo
        resources = capabilities['resources'].get('resources', [])
        for resource in resources:
            pattern = resource.get('pattern', '')
            # Extract static parts from the pattern (no variables)
            if '{' not in pattern:
                # This is a static URI, use it
                demo_uri = pattern
                print(f"Getting resource: {demo_uri}")
                try:
                    result = await host.get_resource(server_name, demo_uri)
                    print(f"✅ Resource content: {result.get('content')}")
                    break
                except Exception as e:
                    print(f"❌ Error getting resource: {e}")
            else:
                # Skip parameterized URIs for the demo
                continue
        else:
            print("❌ No simple resources available for demo")
    
    # Demo prompt if available
    if capabilities['prompts'].get('prompts', []):
        print("\n6️⃣ Demonstrating prompt capabilities...")
        
        # Find a simple prompt to demo
        simple_prompts = [
            prompt for prompt in capabilities['prompts'].get('prompts', [])
            if len(prompt.get('parameters', [])) <= 1
        ]
        
        if simple_prompts:
            # Choose the first simple prompt
            demo_prompt = simple_prompts[0]
            prompt_name = demo_prompt['name']
            params = {}
            
            # Populate parameters with default values
            for param in demo_prompt.get('parameters', []):
                param_name = param.get('name')
                if 'default' in param:
                    params[param_name] = param['default']
                elif param.get('type') == 'string':
                    params[param_name] = "test"
                elif param.get('type') == 'number':
                    params[param_name] = 42
                elif param.get('type') == 'boolean':
                    params[param_name] = True
            
            print(f"Calling prompt '{prompt_name}' with parameters: {params}")
            try:
                result = await host.call_prompt(server_name, prompt_name, params)
                print(f"✅ Prompt result: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"❌ Error calling prompt: {e}")
        else:
            print("❌ No simple prompts available for demo")
    
    print("\n7️⃣ Demo complete! Use interactive mode for more capabilities.")
    
    # Clean up
    await host.disconnect_from_server(server_name)
    print(f"✅ Disconnected from server: {server_name}")
    print("="*50)
    
async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Host")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode")
    parser.add_argument("--server", help="MCP server URL (default: http://localhost:8000)")
    parser.add_argument("--stdio", action="store_true", help="Use stdio for communication")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    try:
        if args.demo:
            await run_demo(args.server, args.stdio)
        else:
            await interactive_mode()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
    
if __name__ == "__main__":
    asyncio.run(main()) 

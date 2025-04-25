#!/usr/bin/env python
"""
A2A-MCP Bridge for Weather Insights

This module provides a bridge between Agent-to-Agent (A2A) protocol and 
Model Context Protocol (MCP) servers for weather data analysis.
"""

import logging
import asyncio
import inspect
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class A2AMCPBridge:
    """
    Bridge class to connect A2A and MCP servers.
    
    This bridge allows:
    1. A2A server to use MCP tools
    2. MCP server to use A2A capabilities
    """
    
    def __init__(self, a2a_server: Any, mcp_server: Any, name: str = "weather-bridge"):
        """
        Initialize the bridge between A2A and MCP servers.
        
        Args:
            a2a_server: The A2A server instance
            mcp_server: The MCP server instance
            name: Name for this bridge
        """
        self.a2a_server = a2a_server
        self.mcp_server = mcp_server
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Keep track of registered mappings
        self.a2a_to_mcp_mappings = {}
        self.mcp_to_a2a_mappings = {}
        
        # Automatically register available tools and capabilities
        self._register_mcp_tools_as_a2a()
        self._register_a2a_capabilities_as_mcp()
        
        self.logger.info(f"Bridge created between A2A ({a2a_server.name}) and MCP ({mcp_server.name})")
    
    def _register_mcp_tools_as_a2a(self):
        """Register MCP tools as A2A capabilities."""
        if not hasattr(self.mcp_server, 'tools') or not self.mcp_server.tools:
            self.logger.warning("No MCP tools available to register")
            return
        
        for tool_name, tool_func in self.mcp_server.tools.items():
            try:
                # Get the signature to build schema
                sig = inspect.signature(tool_func)
                
                # Build input schema from signature
                properties = {}
                required = []
                
                for param_name, param in sig.parameters.items():
                    # Skip 'ctx' parameter which is handled internally
                    if param_name == "ctx":
                        continue
                        
                    if param.annotation == inspect.Parameter.empty:
                        param_type = "string"  # Default to string
                    elif param.annotation == str:
                        param_type = "string"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"
                    else:
                        param_type = "object"  # Default complex types to object
                    
                    # Build property definition
                    property_def = {"type": param_type}
                    
                    # Add description if available from docstring
                    if tool_func.__doc__:
                        property_def["description"] = f"Parameter from MCP tool: {tool_func.__doc__.strip()}"
                    
                    properties[param_name] = property_def
                    
                    # Add to required if no default value
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
                
                # Create schema
                input_schema = {
                    "type": "object",
                    "properties": properties
                }
                
                if required:
                    input_schema["required"] = required
                
                # Create wrapper function for A2A capability
                async def mcp_tool_wrapper(data: Dict[str, Any], _tool_name=tool_name, _tool_func=tool_func):
                    try:
                        input_data = data.get("input", {})
                        self.logger.debug(f"Calling MCP tool {_tool_name} with data: {input_data}")
                        
                        # Check if tool expects ctx parameter
                        if "ctx" in sig.parameters:
                            # Create a simplified context
                            ctx = {
                                "client_id": "a2a_bridge",
                                "request_id": data.get("task_id", "unknown")
                            }
                            result = await _tool_func(ctx, **input_data)
                        else:
                            # Call without ctx
                            result = await _tool_func(**input_data)
                            
                        return result
                    except Exception as e:
                        self.logger.error(f"Error in MCP tool {_tool_name}: {str(e)}")
                        return {"error": str(e)}
                
                # Set function name and docstring
                mcp_tool_wrapper.__name__ = f"mcp_{tool_name}"
                if tool_func.__doc__:
                    mcp_tool_wrapper.__doc__ = f"A2A wrapper for MCP tool: {tool_func.__doc__}"
                else:
                    mcp_tool_wrapper.__doc__ = f"A2A wrapper for MCP tool: {tool_name}"
                
                # Register as A2A capability
                capability_name = f"mcp_{tool_name}"
                
                # Register with the A2A server
                self.a2a_server.capability(
                    name=capability_name,
                    description=f"MCP tool: {tool_name}" + (f" - {tool_func.__doc__}" if tool_func.__doc__ else ""),
                    input_schema=input_schema
                )(mcp_tool_wrapper)
                
                # Keep track of mapping
                self.a2a_to_mcp_mappings[capability_name] = tool_name
                
                self.logger.info(f"Registered MCP tool '{tool_name}' as A2A capability '{capability_name}'")
            except Exception as e:
                self.logger.error(f"Failed to register MCP tool '{tool_name}' as A2A capability: {str(e)}")
    
    def _register_a2a_capabilities_as_mcp(self):
        """Register A2A capabilities as MCP tools."""
        if not hasattr(self.a2a_server, 'capabilities') or not self.a2a_server.capabilities:
            self.logger.warning("No A2A capabilities available to register")
            return
        
        for cap_name, cap_info in self.a2a_server.capabilities.items():
            # Skip capabilities that are already MCP tool wrappers
            if cap_name.startswith("mcp_"):
                continue
                
            try:
                # Extract the handler function
                handler_func = cap_info.get("handler")
                if not handler_func:
                    self.logger.warning(f"No handler found for A2A capability '{cap_name}'")
                    continue
                
                # Get input schema
                input_schema = cap_info.get("input_schema", {})
                
                # Create wrapper function for MCP tool
                async def a2a_capability_wrapper(ctx=None, _cap_name=cap_name, _handler_func=handler_func, **kwargs):
                    """MCP tool wrapper for A2A capability."""
                    try:
                        # Format input for A2A capability
                        task_id = f"mcp_{ctx['client_id'] if ctx else 'unknown'}_{asyncio.get_event_loop().time()}"
                        
                        input_data = {
                            "task_id": task_id,
                            "input": kwargs
                        }
                        
                        self.logger.debug(f"Calling A2A capability {_cap_name} with data: {input_data}")
                        result = await _handler_func(input_data)
                        return result
                    except Exception as e:
                        self.logger.error(f"Error in A2A capability {_cap_name}: {str(e)}")
                        return {"error": str(e)}
                
                # Set function name and docstring
                tool_name = f"a2a_{cap_name}"
                a2a_capability_wrapper.__name__ = tool_name
                if handler_func.__doc__:
                    a2a_capability_wrapper.__doc__ = f"MCP wrapper for A2A capability: {handler_func.__doc__}"
                else:
                    a2a_capability_wrapper.__doc__ = f"MCP wrapper for A2A capability: {cap_name}"
                
                # Register as MCP tool
                self.mcp_server.tool()(a2a_capability_wrapper)
                
                # Keep track of mapping
                self.mcp_to_a2a_mappings[tool_name] = cap_name
                
                self.logger.info(f"Registered A2A capability '{cap_name}' as MCP tool '{tool_name}'")
            except Exception as e:
                self.logger.error(f"Failed to register A2A capability '{cap_name}' as MCP tool: {str(e)}")
    
    async def call_mcp_tool_from_a2a(self, tool_name: str, **kwargs) -> Any:
        """
        Call an MCP tool from A2A code.
        
        Args:
            tool_name: Name of the MCP tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from the MCP tool
        """
        if tool_name not in self.mcp_server.tools:
            raise ValueError(f"MCP tool '{tool_name}' not found")
            
        try:
            tool_func = self.mcp_server.tools[tool_name]
            result = await tool_func(**kwargs)
            return result
        except Exception as e:
            self.logger.error(f"Error calling MCP tool '{tool_name}': {str(e)}")
            raise
    
    async def call_a2a_capability_from_mcp(self, capability_name: str, **kwargs) -> Any:
        """
        Call an A2A capability from MCP code.
        
        Args:
            capability_name: Name of the A2A capability to call
            **kwargs: Arguments to pass to the capability
            
        Returns:
            Result from the A2A capability
        """
        if capability_name not in self.a2a_server.capabilities:
            raise ValueError(f"A2A capability '{capability_name}' not found")
            
        try:
            handler_func = self.a2a_server.capabilities[capability_name]["handler"]
            task_id = f"direct_mcp_call_{asyncio.get_event_loop().time()}"
            
            input_data = {
                "task_id": task_id,
                "input": kwargs
            }
            
            result = await handler_func(input_data)
            return result
        except Exception as e:
            self.logger.error(f"Error calling A2A capability '{capability_name}': {str(e)}")
            raise


def create_a2a_mcp_bridge(a2a_server: Any, mcp_server: Any, name: str = None) -> A2AMCPBridge:
    """
    Create an A2A-MCP bridge connecting the two servers.
    
    Args:
        a2a_server: The A2A server instance
        mcp_server: The MCP server instance
        name: Optional name for the bridge
        
    Returns:
        An initialized A2AMCPBridge instance
    """
    if name is None:
        name = f"bridge-{a2a_server.name}-{mcp_server.name}"
        
    return A2AMCPBridge(a2a_server, mcp_server, name) 
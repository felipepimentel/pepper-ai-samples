"""Agent System MCP Server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List

from mcp.server.fastmcp import Context, FastMCP


@dataclass
class Agent:
    """Agent data class."""

    id: str
    name: str
    status: str
    capabilities: List[str]


class AgentSystem:
    """Agent system manager."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent) -> None:
        """Register a new agent."""
        self.agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """List all agents."""
        return list(self.agents.values())


# Create an MCP server with lifespan context
mcp = FastMCP("Agent System")


@asynccontextmanager
async def agent_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Initialize agent system."""
    system = AgentSystem()
    # Register some example agents
    system.register_agent(Agent("1", "FileBot", "ready", ["read", "write"]))
    system.register_agent(Agent("2", "SearchBot", "ready", ["search", "analyze"]))
    try:
        yield {"system": system}
    finally:
        # Cleanup if needed
        pass


# Pass lifespan to server
mcp = FastMCP("Agent System", lifespan=agent_lifespan)


@mcp.tool()
async def list_agents(ctx: Context) -> List[Dict[str, Any]]:
    """List all available agents."""
    system = ctx.request_context.lifespan_context["system"]
    agents = system.list_agents()
    await ctx.info(f"Listed {len(agents)} agents")
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "capabilities": agent.capabilities,
        }
        for agent in agents
    ]


@mcp.tool()
async def get_agent_info(agent_id: str, ctx: Context) -> Dict[str, Any]:
    """Get information about a specific agent."""
    system = ctx.request_context.lifespan_context["system"]
    agent = system.get_agent(agent_id)
    if agent:
        await ctx.info(f"Retrieved agent: {agent.name}")
        return {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "capabilities": agent.capabilities,
        }
    else:
        await ctx.error(f"Agent not found: {agent_id}")
        return {"error": "Agent not found"}


@mcp.resource("agent://{agent_id}")
async def get_agent_status(agent_id: str, ctx: Context) -> Dict[str, str]:
    """Get agent status."""
    system = ctx.request_context.lifespan_context["system"]
    agent = system.get_agent(agent_id)
    if agent:
        return {"id": agent.id, "status": agent.status}
    return {"error": "Agent not found"}


if __name__ == "__main__":
    mcp.run()

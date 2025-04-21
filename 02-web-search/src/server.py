"""Web Search MCP Server."""

from typing import Dict, List

import httpx
from pepperpymcp import Context, FastMCP

# Create an MCP server
mcp = FastMCP("Web Search")


@mcp.tool()
async def search_web(query: str, ctx: Context) -> List[Dict[str, str]]:
    """Search the web using a search API."""
    # Note: Replace with your actual search API endpoint and key
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.search.example.com/search",
                params={"q": query},
                headers={"Authorization": "Bearer YOUR_API_KEY"},
            )
            results = response.json()
            await ctx.info(f"Search completed for: {query}")
            return [
                {
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                }
                for result in results["items"]
            ]
        except Exception as e:
            await ctx.error(f"Search error: {e}")
            return [{"error": str(e)}]


@mcp.resource("search://{query}")
async def get_search_preview(query: str) -> Dict[str, str]:
    """Get a preview of search results."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.search.example.com/preview",
                params={"q": query},
                headers={"Authorization": "Bearer YOUR_API_KEY"},
            )
            preview = response.json()
            return {
                "query": query,
                "total_results": str(preview["total"]),
                "top_result": preview["top"]["title"],
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()

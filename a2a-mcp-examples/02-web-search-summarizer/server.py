#!/usr/bin/env python3
"""
Web Search Summarizer - A2A-MCP Integration Example

This example demonstrates how to integrate A2A (Agent-to-Agent) and MCP (Model Context Protocol)
for a web search summarization application. It uses:
- MCP for web search capabilities
- A2A for summarization capabilities
- FastAPI for the web interface

The application allows users to:
1. Perform web searches
2. Get AI-generated summaries of search results
"""

import asyncio
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List

import httpx

# Import the A2A-MCP Bridge
from a2a_mcp_bridge import create_a2a_mcp_bridge
from common.transport import PepperFastMCP
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import A2A and MCP libraries
from pepperpya2a import create_a2a_server
from pydantic import BaseModel

# Try to import the MCP web search module if available
try:
    from pepperpymcp.web_search import create_web_search_tool

    has_web_search_tool = True
    logger.info("MCP web search tool is available")
except ImportError:
    has_web_search_tool = False
    logger.warning("MCP web search tool is not available, using simulated search")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Web Search Summarizer")

# Set up templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize MCP server for web search
mcp_server = PepperFastMCP(
    name="Web Search MCP",
    description="MCP server with web search capabilities",
)

# Initialize A2A server for summarization
a2a_server = create_a2a_server(
    agent_id="summarizer",
    name="Summarizer Agent",
    description="An agent that summarizes search results",
)

# Create the bridge between A2A and MCP
bridge = create_a2a_mcp_bridge(a2a_server, mcp_server)


# Define data models
class SearchQuery(BaseModel):
    query: str


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    results: List[SearchResult]


class SummarizeResponse(BaseModel):
    results: List[SearchResult]
    summary: str


# Web search function using real or simulated search
@mcp_server.tool()
async def web_search(query: str) -> Dict[str, Any]:
    """
    Perform a web search and return results.

    Args:
        query: The search query string

    Returns:
        A dictionary with search results
    """
    logger.info(f"Performing web search for: {query}")

    # If the MCP web search tool is available, use it
    if has_web_search_tool:
        try:
            # This assumes the create_web_search_tool function exists in pepperpymcp
            # and returns a function that performs web searches
            web_search_func = create_web_search_tool()
            results = await web_search_func(query)
            logger.info(
                f"Found {len(results.get('results', []))} results using MCP web search tool"
            )
            return results
        except Exception as e:
            logger.error(f"Error using MCP web search tool: {str(e)}")
            logger.info("Falling back to simulated search")
            # Fall back to simulated search

    # Simulated search as fallback
    try:
        # Use a mock search API for demonstration
        async with httpx.AsyncClient(timeout=10.0) as client:
            # URL encode the query
            encoded_query = urllib.parse.quote(query)

            # Simulate network delay
            await asyncio.sleep(1)

            # Simulated search results
            simulated_results = [
                {
                    "title": f"Understanding {query} - Complete Guide",
                    "url": f"https://example.com/guide/{query.replace(' ', '-')}",
                    "snippet": f"A comprehensive guide to understanding {query} with examples and case studies. Learn about key concepts and best practices.",
                },
                {
                    "title": f"{query} Tutorial for Beginners",
                    "url": f"https://example.com/tutorial/{query.replace(' ', '-')}",
                    "snippet": f"Step by step tutorial on {query} designed for beginners. Includes interactive examples and exercises to help you learn quickly.",
                },
                {
                    "title": f"Advanced {query} Techniques",
                    "url": f"https://example.com/advanced/{query.replace(' ', '-')}",
                    "snippet": f"Explore advanced techniques and strategies for {query}. Recommended for users who already have basic knowledge and want to improve.",
                },
                {
                    "title": f"{query} vs Alternative Approaches",
                    "url": f"https://example.com/comparison/{query.replace(' ', '-')}",
                    "snippet": f"A detailed comparison between {query} and alternative approaches. Analyze pros and cons to determine the best fit for your needs.",
                },
                {
                    "title": f"Latest Research on {query}",
                    "url": f"https://example.com/research/{query.replace(' ', '-')}",
                    "snippet": f"Recent research and developments in the field of {query}. Stay updated with the latest findings and innovations.",
                },
            ]

            logger.info(
                f"Found {len(simulated_results)} results using simulated search"
            )
            return {"results": simulated_results}

    except Exception as e:
        logger.error(f"Error during web search: {str(e)}")
        raise Exception(f"Web search failed: {str(e)}")


# A2A summarization capability
@a2a_server.capability("summarize")
async def summarize(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize search results.

    Args:
        data: Dictionary containing search results to summarize

    Returns:
        Dictionary with summary
    """
    logger.info("Summarizing search results")

    # Extract search results and query
    search_results = data.get("search_results", [])
    query = data.get("query", "")

    if not search_results:
        return {"summary": "No search results to summarize."}

    # Simulate waiting for AI processing
    await asyncio.sleep(1)

    # Extract and process snippets from search results
    snippets = [
        result.get("snippet", "") for result in search_results if result.get("snippet")
    ]
    titles = [
        result.get("title", "") for result in search_results if result.get("title")
    ]

    if not snippets:
        return {
            "summary": "Unable to generate summary: No content found in search results."
        }

    # Combine snippets and perform text analysis
    combined_text = "\n\n".join(snippets)

    # Extract main topics (in a real implementation, this would use NLP techniques)
    # For now, we'll use a simple simulation
    main_topics = extract_main_topics(query, titles, snippets)
    key_points = extract_key_points(snippets)

    # Create a structured summary
    summary = f"""
Based on the search results for "{query}", here is a summary:

OVERVIEW:
The search results provide information about {query} across different levels of expertise, from beginner tutorials to advanced techniques. The content includes comprehensive guides, comparison with alternatives, and recent research developments.

MAIN TOPICS:
{format_bullet_points(main_topics)}

KEY POINTS:
{format_bullet_points(key_points)}

CONCLUSION:
These resources offer a wide range of information on {query}, suitable for different knowledge levels and use cases. The materials cover both theoretical understanding and practical application.
    """

    logger.info("Summarization completed")
    return {"summary": summary.strip()}


def extract_main_topics(
    query: str, titles: List[str], snippets: List[str]
) -> List[str]:
    """Extract main topics from search results using simple heuristics."""
    # In a real implementation, this would use NLP techniques
    # For now, we'll simulate with some simple logic

    # Start with some topics based on the query
    topics = [
        f"Understanding {query} fundamentals",
        f"Learning {query} for beginners",
        f"Advanced {query} techniques",
        f"Comparing {query} with alternatives",
        f"Latest research in {query}",
    ]

    # In a real implementation, you would extract these from the actual content
    return topics


def extract_key_points(snippets: List[str]) -> List[str]:
    """Extract key points from snippets using simple heuristics."""
    # In a real implementation, this would use NLP techniques
    # For now, we'll create some generic points

    points = [
        "Comprehensive guides and tutorials are available for all skill levels",
        "Step-by-step resources help beginners learn the fundamentals",
        "Advanced techniques can be explored once basics are understood",
        "Comparing with alternatives helps choose the right approach",
        "Recent research provides insights into latest developments",
    ]

    # In a real implementation, you would extract these from the actual content
    return points


def format_bullet_points(points: List[str]) -> str:
    """Format a list of points as bullet points."""
    return "\n".join(f"• {point}" for point in points)


# FastAPI event handlers
@app.on_event("startup")
async def startup_event():
    """Start MCP and A2A servers on application startup."""
    logger.info("Starting Web Search Summarizer")

    # Start MCP server
    await mcp_server.add_web_client()

    # Start A2A server
    await a2a_server.start_server()

    logger.info("Servers started successfully")
    logger.info(f"Bridge created: {bridge.name}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown MCP and A2A servers on application shutdown."""
    logger.info("Shutting down Web Search Summarizer")

    # Close A2A server
    await a2a_server.close()

    logger.info("Servers shut down successfully")


# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    """
    Perform a web search and return results.

    Args:
        query: The search query

    Returns:
        Search results
    """
    try:
        # Call the MCP web search tool
        search_results = await web_search(query.query)
        return {"results": search_results["results"]}
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.post("/api/search-and-summarize", response_model=SummarizeResponse)
async def search_and_summarize(query: SearchQuery):
    """
    Perform a web search and generate a summary of the results.

    Args:
        query: The search query

    Returns:
        Search results with summary
    """
    try:
        # Call the MCP web search tool
        search_results = await web_search(query.query)

        # Call the A2A summarize capability
        summary_result = await summarize(
            {"search_results": search_results["results"], "query": query.query}
        )

        return {
            "results": search_results["results"],
            "summary": summary_result["summary"],
        }
    except Exception as e:
        logger.error(f"Search and summarize error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search and summarize failed")


# Run the application
if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    # Determine ports (use environment variables if available, otherwise use defaults)
    mcp_port = int(os.environ.get("MCP_PORT", 8000))
    a2a_port = int(os.environ.get("A2A_PORT", 8080))
    
    logger.info(f"Starting MCP server on port {mcp_port}")
    logger.info(f"Starting A2A server on port {a2a_port}")
    
    # Create FastAPI app for A2A server to run on its own port
    a2a_app = a2a_server.get_app()
    
    # Configure servers
    mcp_config = uvicorn.Config(app=app, host="0.0.0.0", port=mcp_port)
    a2a_config = uvicorn.Config(app=a2a_app, host="0.0.0.0", port=a2a_port)
    
    # Create server instances
    mcp_server_instance = uvicorn.Server(mcp_config)
    a2a_server_instance = uvicorn.Server(a2a_config)
    
    # Modify log level to avoid duplicate logs
    mcp_server_instance.config.log_level = "error"
    a2a_server_instance.config.log_level = "error"
    
    # Run both servers
    async def run_servers():
        """Run both MCP and A2A servers concurrently."""
        await asyncio.gather(
            mcp_server_instance.serve(),
            a2a_server_instance.serve()
        )
    
    # Start the servers
    asyncio.run(run_servers())

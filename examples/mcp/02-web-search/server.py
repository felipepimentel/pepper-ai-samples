#!/usr/bin/env python3
"""
Web Search MCP Server Example
Demonstrates how to create an MCP server for web searches and interactions.
"""

import re
import sys
import argparse
import logging
import asyncio
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP as OfficialFastMCP
from pepperpymcp import PepperFastMCP, ConnectionMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Initialize MCP server
mcp = PepperFastMCP(
    name="Web Search",
    description="MCP server for web searches",
    version="1.0.0"
)

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
TIMEOUT = 30.0  # seconds

# Manually set app to avoid AttributeError
if not hasattr(mcp._mcp, "app"):
    mcp._mcp.app = app

@mcp.tool()
async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Performs a web search and returns the results.

    Use this tool when you need to find information on the web about
    any topic, news or fact. Returns a list of results with
    titles, URLs and relevant snippets.

    Examples:
    - search_web("Python best practices")  →  Results about Python
    - search_web("technology news today", 10)  →  10 results about tech news

    Args:
        query: Search term
        num_results: Number of results to return (default: 5, maximum: 10)

    Returns:
        Dictionary with search results, including URLs and snippets
    """
    # Limit number of results
    if num_results > 10:
        num_results = 10

    try:
        # Use DuckDuckGo's public API
        encoded_query = quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&pretty=1"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Extract results
            results = []

            # Add abstract results
            if data.get("Abstract"):
                results.append(
                    {
                        "title": data.get("Heading", "Abstract"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                        "source": "Abstract",
                    }
                )

            # Add related topics
            for topic in data.get("RelatedTopics", [])[: num_results - len(results)]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append(
                        {
                            "title": topic.get("Text", "").split(" - ")[0]
                            if " - " in topic.get("Text", "")
                            else topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                            "source": "Related Topic",
                        }
                    )

            # If we still don't have enough results, add more from results
            if len(results) < num_results and data.get("Results"):
                for result in data.get("Results", [])[: num_results - len(results)]:
                    results.append(
                        {
                            "title": result.get("Text", ""),
                            "url": result.get("FirstURL", ""),
                            "snippet": result.get("Text", ""),
                            "source": "Results",
                        }
                    )

            return {"query": query, "num_results": len(results), "results": results}
    except Exception as e:
        raise RuntimeError(f"Error searching the web: {str(e)}")


@mcp.tool()
async def fetch_url(url: str, extract_text: bool = True) -> Dict[str, Any]:
    """Gets the content of a URL.

    Use this tool when you need the complete content or extracted text
    from a specific web page. Can get either the complete HTML or just
    the extracted text without markup.

    Examples:
    - fetch_url("https://example.com")  →  Gets the text from example.com
    - fetch_url("https://example.com", False)  →  Gets the complete HTML

    Args:
        url: URL of the page to fetch
        extract_text: If True, extracts only text; if False, returns HTML (default: True)

    Returns:
        Dictionary with page content and metadata
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(
                "Invalid URL. Must include protocol (https://) and domain."
            )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            # Detect content type
            content_type = response.headers.get("content-type", "")
            is_html = "text/html" in content_type.lower()

            # Get content
            html_content = response.text

            # Extract text if requested and if HTML
            text_content = None
            if extract_text and is_html:
                text_content = _extract_text_from_html(html_content)

            # Extract title if HTML
            title = None
            if is_html:
                title_match = re.search(
                    r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
                )
                if title_match:
                    title = unescape(title_match.group(1).strip())

            return {
                "url": url,
                "content_type": content_type,
                "title": title,
                "content": text_content if extract_text and is_html else html_content,
                "status_code": response.status_code,
                "is_html": is_html,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            }
    except httpx.HTTPStatusError as e:
        return {
            "url": url,
            "error": f"HTTP Error: {e.response.status_code}",
            "status_code": e.response.status_code,
            "content": None,
        }
    except Exception as e:
        raise RuntimeError(f"Error fetching URL: {str(e)}")


@mcp.tool()
async def extract_links(url: str) -> Dict[str, Any]:
    """Extracts all links from a web page.

    Use this tool when you need to get all links (URLs) present
    on a web page, including internal and external links.

    Examples:
    - extract_links("https://example.com")  →  List of links on example.com

    Args:
        url: URL of the page to extract links from

    Returns:
        Dictionary with extracted links, categorized by type
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            html_content = response.text
            base_url_parsed = urlparse(url)
            base_domain = base_url_parsed.netloc

            # Extract links
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html_content)

            # Process and categorize links
            internal_links = []
            external_links = []
            resource_links = []

            for link in links:
                # Convert relative links to absolute
                if link.startswith("/"):
                    link = f"{base_url_parsed.scheme}://{base_domain}{link}"
                elif not link.startswith(("http://", "https://")):
                    link = f"{base_url_parsed.scheme}://{base_domain}/{link}"

                # Categorize the link
                link_parsed = urlparse(link)

                # Check if it's a resource
                file_extensions = [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".xls",
                    ".xlsx",
                    ".csv",
                ]
                is_resource = any(link.lower().endswith(ext) for ext in file_extensions)

                if is_resource:
                    resource_links.append(link)
                elif link_parsed.netloc == base_domain:
                    internal_links.append(link)
                else:
                    external_links.append(link)

            # Remove duplicates
            internal_links = list(set(internal_links))
            external_links = list(set(external_links))
            resource_links = list(set(resource_links))

            return {
                "url": url,
                "total_links": len(internal_links) + len(external_links) + len(resource_links),
                "internal_links": internal_links,
                "external_links": external_links,
                "resource_links": resource_links,
            }
    except Exception as e:
        raise RuntimeError(f"Error extracting links: {str(e)}")


@mcp.resource("url://{path}")
def url_resource(path: str) -> str:
    """Gets URL content as a resource.

    This resource provides direct access to URL content through a URI.
    Only text content is supported. For binary content, use the fetch_url tool.

    Examples:
    - url://example.com  →  Returns content from example.com
    - url://api.example.com/data  →  Returns content from the API endpoint

    Args:
        path: URL path to fetch

    Returns:
        URL content as string

    Raises:
        ValueError: If URL is invalid
        RuntimeError: If error fetching URL
    """
    try:
        # Validate URL
        if not path.startswith(("http://", "https://")):
            path = "https://" + path

        parsed_url = urlparse(path)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")

        # Use httpx in sync mode for resource
        response = httpx.get(
            path,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=True
        )
        response.raise_for_status()

        return response.text
    except Exception as e:
        raise RuntimeError(f"Error fetching URL: {str(e)}")


@mcp.prompt()
async def summarize_webpage(url: str) -> str:
    """Generates a summary of a web page.

    Use this prompt when you need a natural language summary
    of a web page's content and structure.

    Examples:
    - summarize_webpage("https://example.com")  →  Summary of example.com

    Args:
        url: URL of the page to summarize

    Returns:
        Natural language summary of the page
    """
    try:
        # Fetch page content
        page_data = await fetch_url(url)
        
        # Extract links
        links_data = await extract_links(url)
        
        # Build summary
        summary_parts = []
        
        # Add title and URL
        if page_data.get("title"):
            summary_parts.append(f"Title: {page_data['title']}")
        summary_parts.append(f"URL: {url}")
        
        # Add content type and response info
        summary_parts.append(f"Content Type: {page_data.get('content_type', 'Unknown')}")
        summary_parts.append(f"Response Time: {page_data.get('response_time_ms', 0)}ms")
        
        # Add link statistics
        summary_parts.append("\nLink Analysis:")
        summary_parts.append(f"- Internal Links: {len(links_data.get('internal_links', []))}")
        summary_parts.append(f"- External Links: {len(links_data.get('external_links', []))}")
        summary_parts.append(f"- Resource Links: {len(links_data.get('resource_links', []))}")
        
        # Add content preview
        if page_data.get("content"):
            content = page_data["content"]
            preview = content[:500] + "..." if len(content) > 500 else content
            summary_parts.append("\nContent Preview:")
            summary_parts.append(preview)
        
        return "\n".join(summary_parts)
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def _extract_text_from_html(html: str) -> str:
    """Helper function to extract readable text from HTML."""
    # Remove script and style elements
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    
    # Replace line breaks and paragraphs with newlines
    html = re.sub(r"<br\s*/?>|</p>|</div>", "\n", html)
    
    # Remove all other HTML tags
    html = re.sub(r"<[^>]+>", "", html)
    
    # Decode HTML entities
    text = unescape(html)
    
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Split into lines and remove empty ones
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    
    return "\n".join(lines)


async def main():
    """Main entry point for the server."""
    if args.stdio:
        await mcp._run_stdio()
    else:
        mcp.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Search MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use STDIO transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.stdio:
        print("Starting Web Search MCP Server in STDIO mode", file=sys.stderr)
        asyncio.run(main())
    else:
        print("Starting Web Search MCP Server in HTTP mode", file=sys.stderr)
        mcp.run()

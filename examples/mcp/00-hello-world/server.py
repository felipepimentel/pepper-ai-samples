#!/usr/bin/env python3
"""
Hello World MCP Server Example
Demonstrates how to create a simple MCP server using the official SDK with extensions.
"""

import json
import sys
import argparse
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from pepperpymcp import PepperFastMCP, ConnectionMode
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP as OfficialFastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Initialize MCP server
mcp = PepperFastMCP(
    name="Hello World",
    description="A simple MCP server example",
    version="1.0.0"
)

# Manually set app to avoid AttributeError
if not hasattr(mcp._mcp, "app"):
    mcp._mcp.app = app

# Add MCP tools
@mcp.tool()
def greet(name: str = "World") -> str:
    """Returns a personalized greeting with the provided name.

    Use this tool when you need to create a simple and friendly greeting for a user.

    Examples:
    - For a generic greeting: greet()  →  "Hello, World!"
    - For a personalized greeting: greet("Maria")  →  "Hello, Maria!"

    Args:
        name: The name of the person to greet (default: "World")

    Returns:
        A string containing the greeting
    """
    return f"Hello, {name}!"


@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Performs basic arithmetic operations between two numbers.

    Use this tool when the user requests mathematical calculations like addition,
    subtraction, multiplication or division of two values.

    Examples:
    - To add: calculate("add", 5, 3)  →  8
    - To subtract: calculate("subtract", 10, 4)  →  6
    - To multiply: calculate("multiply", 2, 5)  →  10
    - To divide: calculate("divide", 20, 5)  →  4

    Args:
        operation: The type of operation to perform ("add", "subtract", "multiply", "divide")
        a: The first number in the operation
        b: The second number in the operation

    Returns:
        The result of the operation as a float value

    Raises:
        ValueError: If the operation is unknown or if trying to divide by zero
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")


# Add resources
@mcp.resource("quote://{category}")
def get_quote(category: str) -> str:
    """Gets an inspirational quote based on the requested category.

    Use this resource when you need a specific inspirational quote for a category.
    The resource can be accessed via URI in the format quote://{category}.

    Available categories include: motivation, success, life, work, etc.
    (depending on what's defined in the "quotes" template)

    Examples:
    - quote://motivation  →  Returns a motivational quote
    - quote://success  →  Returns a quote about success

    Args:
        category: The desired quote category

    Returns:
        A string containing the quote or a message indicating the category was not found
    """
    quotes = json.loads(mcp.get_template("quotes"))

    if category in quotes:
        return quotes[category]
    return "No quote found for this category."


# Add prompts
@mcp.prompt()
async def welcome_email(name: str, content: Optional[str] = None) -> str:
    """Generates a formal personalized welcome email for a new user.

    Use this prompt when you need to create a formal welcome email for a new
    user, client or team member. The content can be customized or use
    the default welcome text.

    Examples:
    - welcome_email("John")  →  Formal welcome email for John
    - welcome_email("Maria", "Welcome to our loyalty program!")  →  Customized email for Maria

    Args:
        name: Name of the email recipient
        content: Custom email content (optional). If not provided,
                 a default welcome text will be used.

    Returns:
        The formatted welcome email content
    """
    if not content:
        content = "Welcome to our service! We're very happy to have you with us."

    return mcp.get_template("welcome_email").format(name=name, content=content)


@mcp.prompt()
async def quick_note(name: str, message: str, sender: Optional[str] = "Anonymous") -> str:
    """Generates a quick informal note to send to someone.

    Use this prompt when you need to create a short and informal message
    to send to someone, like a reminder, thank you note or quick notice.

    Examples:
    - quick_note("Carlos", "Meeting tomorrow at 10am", "Ana")  →  Note from Ana to Carlos
    - quick_note("Team", "Don't forget today's deadline!")  →  Note from anonymous sender to the team

    Args:
        name: Name of the note recipient
        message: The message content to be sent
        sender: Name of the sender (default: "Anonymous")

    Returns:
        The formatted note ready to send
    """
    return mcp.get_template("quick_note").format(name=name, message=message, sender=sender)


@mcp.prompt()
async def start_conversation(name: str) -> list[Dict[str, Any]]:
    """Starts a friendly and contextual conversation with the user.

    Use this prompt when you need to start an interaction with a user
    in a friendly and personalized way, adapting the greeting to the time of day
    (good morning, good afternoon or good evening).

    Examples:
    - start_conversation("Paul")  →  Starts a conversation adapted to the current time with Paul

    Args:
        name: Name of the user to start the conversation with

    Returns:
        A list of formatted messages to start the conversation
    """
    hour = datetime.now().hour

    if hour < 12:
        time = "good morning"
    elif hour < 18:
        time = "good afternoon"
    else:
        time = "good evening"

    return [
        {"role": "assistant", "content": f"Hi {name}, {time}! How can I help?"},
        {"role": "user", "content": "I'm here to learn about MCP!"},
        {"role": "assistant", "content": "Great! I'll help you understand how it works. Where would you like to start?"},
    ]


# Add custom HTTP endpoint
@mcp.http_endpoint("/greeting/{name}")
async def get_greeting(name: str):
    """Custom HTTP endpoint for greeting"""
    return {"message": f"Hello, {name}!"}


async def main():
    """Main entry point for the server."""
    if args.stdio:
        await mcp._run_stdio()
    else:
        mcp.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hello World MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use STDIO transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.stdio:
        print("Starting Hello World MCP Server in STDIO mode", file=sys.stderr)
        asyncio.run(main())
    else:
        print("Starting Hello World MCP Server in HTTP mode", file=sys.stderr)
        mcp.run()

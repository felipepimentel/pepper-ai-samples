#!/usr/bin/env python3
"""
Database Query MCP Server Example
Demonstrates how to create an MCP server for database operations.
"""

import sys
import argparse
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from fastapi import FastAPI

from pepperpymcp import PepperFastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize MCP server
mcp = PepperFastMCP(
    name="Database Query",
    description="MCP server for database operations",
    version="1.0.0"
)

# Create async SQLite engine
engine = create_async_engine("sqlite+aiosqlite:///database.db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Define parameter models
class QueryParams(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

class SchemaParams(BaseModel):
    table_name: str

async def init_db():
    """Initialize database with sample tables."""
    async with engine.begin() as conn:
        # Create users table if it doesn't exist
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """))
        
        # Create products table if it doesn't exist
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """))

@mcp.tool()
async def list_tables() -> List[str]:
    """List all tables in the database."""
    try:
        async with async_session() as session:
            result = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result]
            return tables
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise

@mcp.tool()
async def get_schema(params: SchemaParams) -> str:
    """Get schema for a specific table."""
    try:
        async with async_session() as session:
            result = await session.execute(text(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{params.table_name}'"
            ))
            schema = result.scalar()
            if not schema:
                return f"Table {params.table_name} not found"
            return schema
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise

@mcp.tool()
async def query(params: QueryParams) -> str:
    """Execute a SQL query and return results."""
    try:
        async with async_session() as session:
            result = await session.execute(text(params.query), params.params or {})
            rows = result.fetchall()
            if not rows:
                return "No results found"
            return "\n".join(str(row) for row in rows)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

@mcp.tool()
async def ask(question: str) -> str:
    """Ask a natural language question about the database."""
    # This is a placeholder for future NLP implementation
    return f"Natural language processing not implemented yet. Your question was: {question}"

async def init_database():
    """Initialize the database."""
    await init_db()

def run_server():
    """Run the server in the appropriate mode."""
    parser = argparse.ArgumentParser(description="Database Query MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use STDIO transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8001, help="HTTP port")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize database first
    asyncio.run(init_database())

    # Run server
    if args.stdio:
        print("Starting Database Query MCP Server in STDIO mode", file=sys.stderr)
        asyncio.run(mcp._run_stdio())
    else:
        print(f"Starting Database Query MCP Server in SSE mode on port {args.port}", file=sys.stderr)
        import uvicorn
        # Mount the SSE app
        app.mount("/mcp", mcp.sse_app())
        uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    run_server()
"""Database Query MCP Server."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from pepperpymcp import Context, FastMCP


# Create database context
@asynccontextmanager
async def get_db() -> AsyncIterator[sqlite3.Connection]:
    """Get database connection."""
    conn = sqlite3.connect("database.db")
    try:
        yield conn
    finally:
        conn.close()


# Create an MCP server
mcp = FastMCP("Database Query")


@mcp.tool()
async def query_database(sql: str, ctx: Context) -> List[Dict[str, Any]]:
    """Execute a SQL query."""
    async with get_db() as conn:
        try:
            cursor = conn.execute(sql)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row, strict=False)))
            await ctx.info(f"Query executed: {sql}")
            return results
        except Exception as e:
            await ctx.error(f"Query error: {e}")
            return [{"error": str(e)}]


@mcp.resource("table://{name}")
async def get_table_info(name: str) -> Dict[str, Any]:
    """Get table schema information."""
    async with get_db() as conn:
        cursor = conn.execute(f"PRAGMA table_info({name})")
        columns = cursor.fetchall()
        return {
            "table": name,
            "columns": [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "pk": bool(col[5]),
                }
                for col in columns
            ],
        }


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python
"""
Database Query MCP Server Example
Demonstra como criar um servidor MCP para interação com bancos de dados.
"""

import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpymcp import PepperFastMCP
from fastapi import FastAPI
from pydantic import BaseModel

mcp = PepperFastMCP(
    "Database Query", description="Servidor MCP para consultas a bancos de dados"
)

# Armazenar conexões aos bancos de dados
db_connections = {}

# Database connection
DB_PATH = "Chinook.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

@mcp.tool()
async def list_tables() -> Dict:
    """List all tables in the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return {"tables": tables}

@mcp.tool()
async def get_schema(table: str) -> Dict:
    """Get schema information for a specific table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [
        {
            "name": row[1],
            "type": row[2],
            "notnull": bool(row[3]),
            "pk": bool(row[5])
        }
        for row in cursor.fetchall()
    ]
    return {"table": table, "columns": columns}

class QueryRequest(BaseModel):
    query: str
    params: Optional[List] = None

@mcp.tool()
async def query(request: QueryRequest) -> Dict:
    """Execute a SQL query."""
    cursor = conn.cursor()
    try:
        if request.params:
            cursor.execute(request.query, request.params)
        else:
            cursor.execute(request.query)
        
        rows = cursor.fetchall()
        if not rows:
            return {"results": [], "columns": [], "row_count": 0}
            
        columns = [description[0] for description in cursor.description]
        results = [dict(row) for row in rows]
        
        return {
            "results": results,
            "columns": columns,
            "row_count": len(results)
        }
    except sqlite3.Error as e:
        return {"error": str(e)}

@mcp.tool()
async def ask(question: str) -> Dict:
    """Answer questions about the data using natural language."""
    # Map common questions to SQL queries
    queries = {
        "albums by queen": """
            SELECT Album.Title, Artist.Name
            FROM Album 
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            WHERE Artist.Name LIKE '%Queen%'
        """,
        "top 10 longest tracks": """
            SELECT Name, Milliseconds/1000.0 as Seconds
            FROM Track
            ORDER BY Milliseconds DESC
            LIMIT 10
        """,
        "available genres": """
            SELECT Name, COUNT(TrackId) as TrackCount
            FROM Genre
            LEFT JOIN Track ON Genre.GenreId = Track.GenreId
            GROUP BY Genre.GenreId, Genre.Name
            ORDER BY TrackCount DESC
        """,
        "top 5 customers": """
            SELECT 
                Customer.FirstName || ' ' || Customer.LastName as Customer,
                COUNT(Invoice.InvoiceId) as Purchases,
                SUM(Invoice.Total) as TotalSpent
            FROM Customer
            JOIN Invoice ON Customer.CustomerId = Invoice.CustomerId
            GROUP BY Customer.CustomerId
            ORDER BY TotalSpent DESC
            LIMIT 5
        """,
        "sales by country": """
            SELECT 
                BillingCountry,
                COUNT(DISTINCT CustomerId) as Customers,
                SUM(Total) as TotalSales
            FROM Invoice
            GROUP BY BillingCountry
            ORDER BY TotalSales DESC
        """
    }
    
    # Try to find a matching query
    question = question.lower()
    for key, sql in queries.items():
        if key in question:
            return await query(QueryRequest(query=sql))
    
    # Default to a simple search across tables
    search_term = "%" + "%".join(question.split()) + "%"
    return await query(QueryRequest(
        query="""
            SELECT 'Artist' as Type, Name as Result
            FROM Artist WHERE Name LIKE ?
            UNION
            SELECT 'Album' as Type, Title as Result
            FROM Album WHERE Title LIKE ?
            UNION
            SELECT 'Track' as Type, Name as Result
            FROM Track WHERE Name LIKE ?
            LIMIT 10
        """,
        params=[search_term, search_term, search_term]
    ))

# HTTP endpoints
app = FastAPI()

@app.get("/tables")
async def http_list_tables():
    """List all tables via HTTP."""
    return await list_tables()

@app.get("/schema/{table}")
async def http_get_schema(table: str):
    """Get table schema via HTTP."""
    return await get_schema(table)

@app.post("/query")
async def http_query(request: QueryRequest):
    """Execute query via HTTP."""
    return await query(request)

# Add web client
mcp.add_web_client()

if __name__ == "__main__":
    # Certifique-se de fechar conexões ao encerrar
    try:
        mcp.run()
    finally:
        for alias, conn_info in list(db_connections.items()):
            try:
                conn_info["connection"].close()
            except:
                pass

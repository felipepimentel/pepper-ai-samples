#!/usr/bin/env python
"""
Database Query MCP Server Example
Demonstra como criar um servidor MCP para interação com bancos de dados.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel

mcp = PepperFastMCP(
    "Database Query", description="Servidor MCP para consultas a bancos de dados"
)

# Configurar conexão ao banco de dados
DB_PATH = "Chinook.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


@mcp.tool()
async def list_tables() -> Dict[str, List[str]]:
    """Lista todas as tabelas no banco de dados.
    
    Use esta ferramenta quando precisar descobrir quais tabelas estão disponíveis
    no banco de dados SQLite conectado.
    
    Returns:
        Dicionário contendo a lista de tabelas no banco de dados
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return {"tables": tables}


@mcp.tool()
async def get_schema(table: str) -> Dict[str, Any]:
    """Obtém informações de esquema para uma tabela específica.
    
    Use esta ferramenta quando precisar examinar a estrutura de uma tabela
    específica, incluindo nomes de colunas, tipos e restrições.
    
    Args:
        table: Nome da tabela para obter o esquema
        
    Returns:
        Dicionário contendo informações do esquema da tabela
    """
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
    params: Optional[List[Any]] = None


@mcp.tool()
async def query(request: QueryRequest) -> Dict[str, Any]:
    """Executa uma consulta SQL.
    
    Use esta ferramenta quando precisar executar consultas SQL personalizadas
    no banco de dados.
    
    Args:
        request: Objeto contendo a consulta SQL e parâmetros opcionais
        
    Returns:
        Dicionário contendo os resultados da consulta
    """
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
async def ask(question: str) -> Dict[str, Any]:
    """Responde perguntas sobre os dados usando linguagem natural.
    
    Use esta ferramenta quando quiser fazer perguntas em linguagem natural
    sobre os dados no banco de dados.
    
    Args:
        question: A pergunta em linguagem natural
        
    Returns:
        Dicionário contendo os resultados da consulta correspondente
    """
    # Mapear perguntas comuns para consultas SQL
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
    
    # Tentar encontrar uma consulta correspondente
    question = question.lower()
    for key, sql in queries.items():
        if key in question:
            return await query(QueryRequest(query=sql))
    
    # Padrão para uma pesquisa simples entre tabelas
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


# Endpoints HTTP
app = FastAPI()


@app.get("/tables")
async def http_list_tables() -> Dict[str, List[str]]:
    """Lista todas as tabelas via HTTP."""
    return await list_tables()


@app.get("/schema/{table}")
async def http_get_schema(table: str) -> Dict[str, Any]:
    """Obtém esquema da tabela via HTTP."""
    return await get_schema(table)


@app.post("/query")
async def http_query(request: QueryRequest) -> Dict[str, Any]:
    """Executa consulta via HTTP."""
    return await query(request)


# Adicionar cliente web
mcp.add_web_client()


if __name__ == "__main__":
    # Executar servidor e garantir limpeza adequada
    try:
        # Support both HTTP and stdio modes
    mcp.run()  # Supports both HTTP and stdio modes
    finally:
        # Garantir que a conexão com o banco de dados seja fechada
        if conn:
            conn.close()

#!/usr/bin/env python
"""
Servidor MCP de exemplo para buscas web.
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict, Any, List

from common.transport import SimpleMCP

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("search_server")

# Criar servidor MCP
mcp = SimpleMCP(
    name="Search Server",
    description="Servidor de buscas web"
)

# Dados simulados de busca
SEARCH_RESULTS = {
    "python": [
        {
            "title": "Python Programming Language",
            "url": "https://www.python.org",
            "snippet": "Official website of the Python programming language"
        },
        {
            "title": "Python Tutorial",
            "url": "https://docs.python.org/tutorial",
            "snippet": "Python tutorial for beginners and advanced programmers"
        }
    ],
    "mcp protocol": [
        {
            "title": "Model Context Protocol",
            "url": "https://mcp.dev",
            "snippet": "A protocol for AI model interaction and context management"
        },
        {
            "title": "MCP Documentation",
            "url": "https://docs.mcp.dev",
            "snippet": "Technical documentation for the Model Context Protocol"
        }
    ]
}

@mcp.tool()
async def web_search(query: str, limit: int = 2) -> Dict[str, Any]:
    """
    Realiza uma busca web.
    
    Args:
        query: Termo de busca
        limit: Número máximo de resultados (default: 2)
        
    Returns:
        Resultados da busca
    """
    # Simplificar a query para matching
    query = query.lower()
    
    # Encontrar resultados que contenham qualquer palavra da query
    results: List[Dict[str, str]] = []
    for key, key_results in SEARCH_RESULTS.items():
        if any(word in query for word in key.split()):
            results.extend(key_results)
    
    # Limitar número de resultados
    results = results[:limit]
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results
    }

@mcp.tool()
async def suggest_queries() -> Dict[str, Any]:
    """
    Lista queries de exemplo disponíveis.
    
    Returns:
        Lista de queries sugeridas
    """
    return {
        "suggestions": list(SEARCH_RESULTS.keys())
    }

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Servidor MCP de busca")
    parser.add_argument("--stdio", action="store_true", help="Usar modo stdio")
    parser.add_argument("--port", type=int, default=8001, help="Porta HTTP")
    parser.add_argument("--debug", action="store_true", help="Ativar modo debug")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.stdio:
        logger.info("Iniciando servidor no modo stdio")
        mcp.run_stdio()
    else:
        logger.info(f"Iniciando servidor HTTP na porta {args.port}")
        mcp.run_http(port=args.port)

if __name__ == "__main__":
    main() 
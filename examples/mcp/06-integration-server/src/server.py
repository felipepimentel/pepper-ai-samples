#!/usr/bin/env python
"""
Servidor MCP que integra os serviços de clima e busca.
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict, Any, List

from common.transport import SimpleMCP, MCPClient

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("integration_server")

# Criar servidor MCP
mcp = SimpleMCP(
    name="Integration Server",
    description="Servidor que integra clima e busca"
)

# Clientes MCP para os outros serviços
weather_client = MCPClient("http://localhost:8000")
search_client = MCPClient("http://localhost:8001")

@mcp.tool()
async def get_weather_and_info(location: str) -> Dict[str, Any]:
    """
    Obtém o clima atual e informações relacionadas para uma localização.
    
    Args:
        location: Nome da cidade
        
    Returns:
        Dados do clima e informações relacionadas
    """
    # Obter clima
    try:
        weather = await weather_client.call_tool(
            "get_current_weather",
            location=location
        )
    except Exception as e:
        logger.error(f"Erro ao obter clima: {e}")
        weather = None
    
    # Buscar informações relacionadas
    try:
        search_results = await search_client.call_tool(
            "web_search",
            query=f"weather {location}",
            limit=2
        )
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        search_results = None
    
    return {
        "location": location,
        "weather": weather,
        "related_info": search_results
    }

@mcp.tool()
async def search_weather_locations() -> Dict[str, Any]:
    """
    Lista localizações disponíveis e busca informações sobre elas.
    
    Returns:
        Lista de localizações com informações
    """
    # Obter lista de localizações
    try:
        locations = await weather_client.call_tool("list_locations")
    except Exception as e:
        logger.error(f"Erro ao listar localizações: {e}")
        return {"error": str(e)}
    
    # Buscar informações para cada localização
    results = []
    for location in locations.get("locations", []):
        try:
            search_results = await search_client.call_tool(
                "web_search",
                query=f"travel {location}",
                limit=1
            )
            results.append({
                "location": location,
                "info": search_results.get("results", [])
            })
        except Exception as e:
            logger.error(f"Erro na busca para {location}: {e}")
    
    return {
        "locations": results
    }

async def initialize_clients():
    """Inicializa os clientes MCP."""
    try:
        await weather_client.initialize()
        await search_client.initialize()
        logger.info("Clientes MCP inicializados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar clientes: {e}")
        raise

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Servidor MCP de integração")
    parser.add_argument("--stdio", action="store_true", help="Usar modo stdio")
    parser.add_argument("--port", type=int, default=8002, help="Porta HTTP")
    parser.add_argument("--debug", action="store_true", help="Ativar modo debug")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Inicializar clientes
    asyncio.run(initialize_clients())
    
    if args.stdio:
        logger.info("Iniciando servidor no modo stdio")
        mcp.run_stdio()
    else:
        logger.info(f"Iniciando servidor HTTP na porta {args.port}")
        mcp.run_http(port=args.port)

if __name__ == "__main__":
    main() 
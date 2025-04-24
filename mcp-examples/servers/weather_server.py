#!/usr/bin/env python
"""
Servidor MCP de exemplo para previsão do tempo.
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict, Any

from common.transport import SimpleMCP

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("weather_server")

# Criar servidor MCP
mcp = SimpleMCP(
    name="Weather Server",
    description="Servidor de previsão do tempo"
)

# Dados simulados
WEATHER_DATA = {
    "São Paulo": {
        "temperature": 25,
        "conditions": "Partly cloudy",
        "humidity": 65
    },
    "Rio de Janeiro": {
        "temperature": 30,
        "conditions": "Sunny",
        "humidity": 70
    },
    "Curitiba": {
        "temperature": 20,
        "conditions": "Rainy",
        "humidity": 80
    }
}

@mcp.tool()
async def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Obtém o clima atual para uma localização.
    
    Args:
        location: Nome da cidade
        
    Returns:
        Dados do clima atual
        
    Raises:
        ValueError: Se a localização não for encontrada
    """
    location = location.title()  # Normalizar nome da cidade
    
    if location not in WEATHER_DATA:
        raise ValueError(f"Localização '{location}' não encontrada")
        
    return {
        "location": location,
        **WEATHER_DATA[location]
    }

@mcp.tool()
async def list_locations() -> Dict[str, Any]:
    """
    Lista todas as localizações disponíveis.
    
    Returns:
        Lista de localizações com dados de clima
    """
    return {
        "locations": list(WEATHER_DATA.keys())
    }

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Servidor MCP de clima")
    parser.add_argument("--stdio", action="store_true", help="Usar modo stdio")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP")
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
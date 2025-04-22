#!/usr/bin/env python
"""
Exemplo de integração A2A+MCP.

Este exemplo demonstra como integrar agentes A2A e MCP,
permitindo que serviços A2A acessem ferramentas MCP e vice-versa.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Adicionar o diretório principal ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a import create_a2a_server
from libs.pepperpymcp import create_mcp_server
from a2a_mcp_bridge import create_a2a_mcp_bridge

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Criar um servidor A2A
a2a = create_a2a_server(
    name="A2A+MCP Integration Agent",
    description="Um agente que demonstra a integração entre os protocolos A2A e MCP",
    version="0.1.0"
)

# Habilitar CORS para uso em navegadores
a2a.enable_cors()

# Criar um servidor MCP
mcp = create_mcp_server(
    name="MCP+A2A Integration Tools",
    description="Um servidor MCP que demonstra a integração com o protocolo A2A"
)

# Definir uma capacidade A2A
@a2a.capability(
    name="summarize",
    description="Cria um resumo de um texto",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Texto a ser resumido"}
        },
        "required": ["text"]
    }
)
async def summarize(data):
    """Capacidade A2A para resumir texto."""
    logger.info(f"Recebida solicitação de resumo via A2A")
    input_data = data.get("input", {})
    text = input_data.get("text", "")
    
    if not text:
        return {"error": "Texto não fornecido"}
    
    # Lógica simples de resumo (apenas para demonstração)
    words = text.split()
    if len(words) <= 5:
        summary = text
    else:
        summary = " ".join(words[:5]) + "..."
    
    return {
        "original_length": len(text),
        "summary_length": len(summary),
        "summary": summary
    }

# Definir uma ferramenta MCP
@mcp.tool()
async def weather(location: str = "São Paulo") -> Dict[str, Any]:
    """Obtém a previsão do tempo para uma localização."""
    logger.info(f"Recebida solicitação de previsão do tempo via MCP para {location}")
    
    # Dados simulados (apenas para demonstração)
    weather_data = {
        "São Paulo": {"temp": 28, "condition": "Parcialmente nublado"},
        "Rio de Janeiro": {"temp": 32, "condition": "Ensolarado"},
        "Brasília": {"temp": 30, "condition": "Ensolarado"},
        "Curitiba": {"temp": 22, "condition": "Chuvoso"}
    }
    
    return weather_data.get(location, {"temp": 25, "condition": "Desconhecido"})

# Definir um recurso MCP
@mcp.resource("info://{topic}")
async def info_resource(topic: str) -> str:
    """Fornece informações sobre um tópico."""
    logger.info(f"Recebida solicitação de recurso info:// para tópico {topic}")
    
    topics = {
        "a2a": "A2A (Agent-to-Agent) é um protocolo aberto desenvolvido pelo Google para comunicação entre agentes.",
        "mcp": "MCP (Model Context Protocol) é um protocolo para permitir que modelos de linguagem interajam com ferramentas e recursos.",
        "integration": "A integração A2A+MCP permite que agentes de diferentes tipos interajam e compartilhem capacidades."
    }
    
    return topics.get(topic, f"Informação sobre '{topic}' não disponível.")

# Criar a ponte entre A2A e MCP
bridge = create_a2a_mcp_bridge(a2a, mcp)

async def main():
    """Função principal que inicia os servidores."""
    # Iniciar os servidores em portas diferentes
    a2a_task = asyncio.create_task(run_a2a_server())
    mcp_task = asyncio.create_task(run_mcp_server())
    
    # Aguardar indefinidamente
    await asyncio.gather(a2a_task, mcp_task)

async def run_a2a_server():
    """Inicia o servidor A2A."""
    import uvicorn
    config = uvicorn.Config(
        app=a2a.app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
    server = uvicorn.Server(config)
    logger.info("Iniciando servidor A2A na porta 8080")
    await server.serve()

async def run_mcp_server():
    """Inicia o servidor MCP."""
    logger.info("Iniciando servidor MCP na porta 8000")
    await mcp._run_async(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    logger.info("Iniciando servidores A2A e MCP integrados")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
    except Exception as e:
        logger.exception("Erro ao iniciar os servidores") 
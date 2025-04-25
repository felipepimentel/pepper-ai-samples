#!/usr/bin/env python
"""
Cliente para interagir com a rede de agentes A2A.

Este cliente envia mensagens para o agente coordenador e outros agentes especializados.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pprint import pprint
from typing import Any, Dict

# Adicionar o diretório principal ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a.src.pepperpya2a import create_a2a_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NetworkClient:
    """Cliente para interagir com a rede de agentes A2A."""

    def __init__(self, coordinator_url="http://localhost:8081"):
        """
        Inicializa o cliente da rede A2A.

        Args:
            coordinator_url: URL do agente coordenador
        """
        self.coordinator_url = coordinator_url
        self.agents = {
            "coordinator": coordinator_url,
            "math": "http://localhost:8082",
            "text": "http://localhost:8083",
        }
        self.connected_agents = {}

    async def connect(self):
        """Conecta a todos os agentes da rede."""
        logger.info("Conectando aos agentes da rede...")

        for name, url in self.agents.items():
            try:
                client = create_a2a_client(url)
                info = await client.get_agent_info()
                self.connected_agents[name] = {"client": client, "info": info}
                logger.info(f"Conectado a {name}: {info['name']} em {url}")
            except Exception as e:
                logger.error(f"Erro ao conectar ao agente {name} em {url}: {str(e)}")

    async def disconnect(self):
        """Desconecta de todos os agentes."""
        for name, agent in self.connected_agents.items():
            try:
                await agent["client"].close()
                logger.info(f"Desconectado de {name}")
            except Exception as e:
                logger.error(f"Erro ao desconectar de {name}: {str(e)}")

    async def list_agents(self):
        """Lista todos os agentes conectados e suas capacidades."""
        result = []

        for name, agent in self.connected_agents.items():
            try:
                client = agent["client"]
                capabilities = await client.list_capabilities()

                agent_info = {
                    "name": name,
                    "agent_name": agent["info"]["name"],
                    "description": agent["info"].get("description", ""),
                    "url": self.agents[name],
                    "capabilities": [
                        {"name": cap["name"], "description": cap.get("description", "")}
                        for cap in capabilities.get("capabilities", [])
                    ],
                }
                result.append(agent_info)
            except Exception as e:
                logger.error(f"Erro ao listar capacidades do agente {name}: {str(e)}")

        return result

    async def call_capability(
        self, agent_name: str, capability: str, params: Dict[str, Any]
    ):
        """
        Chama uma capacidade de um agente específico.

        Args:
            agent_name: Nome do agente (coordinator, math, text)
            capability: Nome da capacidade a ser chamada
            params: Parâmetros para a chamada

        Returns:
            Resultado da chamada
        """
        if agent_name not in self.connected_agents:
            raise ValueError(f"Agente {agent_name} não está conectado")

        client = self.connected_agents[agent_name]["client"]
        logger.info(
            f"Chamando {capability} no agente {agent_name} com params: {params}"
        )

        try:
            result = await client.call_capability(capability, params)
            return result
        except Exception as e:
            logger.error(
                f"Erro ao chamar {capability} no agente {agent_name}: {str(e)}"
            )
            raise

    async def process_query(self, query: str):
        """
        Processa uma consulta de texto enviando para o agente coordenador.

        Args:
            query: Consulta em texto natural

        Returns:
            Resposta do coordenador
        """
        if "coordinator" not in self.connected_agents:
            raise ValueError("Agente coordenador não está conectado")

        client = self.connected_agents["coordinator"]["client"]
        logger.info(f"Enviando consulta para o coordenador: {query}")

        try:
            result = await client.call_capability("process_query", {"query": query})
            return result
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {str(e)}")
            raise


async def main():
    """Função principal do cliente da rede A2A."""
    parser = argparse.ArgumentParser(description="Cliente para rede de agentes A2A")

    # Comandos principais
    parser.add_argument(
        "command", choices=["list", "query", "call"], help="Comando a ser executado"
    )

    # Argumentos para 'call'
    parser.add_argument("--agent", help="Nome do agente para chamar diretamente")
    parser.add_argument("--capability", help="Capacidade a ser chamada")
    parser.add_argument("--params", help="Parâmetros em formato JSON")

    # Argumento para 'query'
    parser.add_argument("--text", help="Consulta em texto natural para o coordenador")

    # Argumentos para conexão
    parser.add_argument(
        "--coordinator",
        default="http://localhost:8081",
        help="URL do agente coordenador",
    )

    args = parser.parse_args()

    # Inicializar o cliente
    client = NetworkClient(coordinator_url=args.coordinator)

    try:
        # Conectar aos agentes
        await client.connect()

        # Executar comando
        if args.command == "list":
            agents = await client.list_agents()
            print("\n=== REDE DE AGENTES A2A ===\n")

            for agent in agents:
                print(f"• {agent['name']} - {agent['agent_name']}")
                print(f"  URL: {agent['url']}")
                print(f"  Descrição: {agent['description']}")
                print("  Capacidades:")

                for cap in agent["capabilities"]:
                    print(f"    - {cap['name']}: {cap['description']}")

                print()

        elif args.command == "query":
            if not args.text:
                print("Erro: Argumento --text é obrigatório para o comando 'query'")
                return

            result = await client.process_query(args.text)
            print("\n=== RESPOSTA DO COORDENADOR ===\n")
            pprint(result)

        elif args.command == "call":
            if not args.agent or not args.capability:
                print(
                    "Erro: Argumentos --agent e --capability são obrigatórios para o comando 'call'"
                )
                return

            params = {}
            if args.params:
                try:
                    params = json.loads(args.params)
                except json.JSONDecodeError:
                    print("Erro: O parâmetro --params deve ser um JSON válido")
                    return

            result = await client.call_capability(args.agent, args.capability, params)
            print(
                f"\n=== RESULTADO DA CHAMADA {args.capability} NO AGENTE {args.agent} ===\n"
            )
            pprint(result)

    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        print(f"Erro: {str(e)}")

    finally:
        # Desconectar dos agentes
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

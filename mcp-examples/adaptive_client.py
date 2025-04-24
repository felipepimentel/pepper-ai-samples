#!/usr/bin/env python
"""
Cliente MCP Adaptativo.
Se adapta automaticamente aos servidores MCP disponíveis.
"""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, List

from mcp_discovery import MCPDiscovery
from common.transport import MCPClient, HTTPTransport, StdioTransport

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("adaptive_client")

class AdaptiveMCPClient:
    """Cliente MCP que se adapta automaticamente aos servidores disponíveis."""
    
    def __init__(self):
        self.discovery = MCPDiscovery()
        self.clients: Dict[str, MCPClient] = {}
        self.current_server: Optional[str] = None
    
    async def initialize(self, server_name: Optional[str] = None) -> None:
        """
        Inicializa o cliente descobrindo e conectando aos servidores disponíveis.
        
        Args:
            server_name: Nome do servidor específico para usar (opcional)
        """
        # Descobrir servidores
        await self.discovery.discover_servers()
        available_servers = self.discovery.list_servers()
        
        if not available_servers:
            raise ValueError("Nenhum servidor MCP encontrado")
        
        logger.info(f"Servidores disponíveis: {available_servers}")
        
        # Se um servidor específico foi solicitado
        if server_name:
            if server_name not in available_servers:
                raise ValueError(f"Servidor '{server_name}' não encontrado")
            await self._connect_to_server(server_name)
            self.current_server = server_name
            return
        
        # Conectar a todos os servidores disponíveis
        for name in available_servers:
            try:
                await self._connect_to_server(name)
                if not self.current_server:
                    self.current_server = name
            except Exception as e:
                logger.warning(f"Erro ao conectar ao servidor '{name}': {e}")
    
    async def _connect_to_server(self, server_name: str) -> None:
        """
        Conecta a um servidor específico.
        
        Args:
            server_name: Nome do servidor para conectar
        """
        config = self.discovery.get_server_config(server_name)
        
        # Criar transporte apropriado
        if config.get("type") == "stdio":
            transport = StdioTransport(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env", {})
            )
        else:  # sse ou http
            url = config.get("url", f"http://localhost:{config.get('port', 8000)}")
            transport = HTTPTransport(
                url,
                headers=config.get("headers", {})
            )
        
        # Criar e inicializar cliente
        client = MCPClient(transport)
        await client.initialize()
        
        # Armazenar cliente
        self.clients[server_name] = client
        logger.info(f"Conectado ao servidor '{server_name}'")
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista ferramentas disponíveis em um servidor.
        
        Args:
            server_name: Nome do servidor (opcional, usa o atual se não especificado)
            
        Returns:
            Lista de ferramentas disponíveis
        """
        client = await self._get_client(server_name)
        tools = await client.list_tools()
        return tools["tools"]
    
    async def call_tool(self, tool_name: str, **params) -> Dict[str, Any]:
        """
        Chama uma ferramenta em um servidor.
        
        Args:
            tool_name: Nome da ferramenta para chamar
            **params: Parâmetros para a ferramenta
            
        Returns:
            Resultado da ferramenta
        """
        client = await self._get_client()
        return await client.call_tool(tool_name, **params)
    
    async def _get_client(self, server_name: Optional[str] = None) -> MCPClient:
        """
        Obtém um cliente MCP para um servidor.
        
        Args:
            server_name: Nome do servidor (opcional, usa o atual se não especificado)
            
        Returns:
            Cliente MCP
            
        Raises:
            ValueError: Se o servidor não for encontrado
        """
        name = server_name or self.current_server
        if not name:
            raise ValueError("Nenhum servidor selecionado")
            
        if name not in self.clients:
            raise ValueError(f"Servidor '{name}' não encontrado")
            
        return self.clients[name]
    
    def get_current_server(self) -> Optional[str]:
        """
        Retorna o nome do servidor atual.
        
        Returns:
            Nome do servidor ou None se nenhum estiver selecionado
        """
        return self.current_server
    
    def set_current_server(self, server_name: str) -> None:
        """
        Define o servidor atual.
        
        Args:
            server_name: Nome do servidor para usar
            
        Raises:
            ValueError: Se o servidor não estiver disponível
        """
        if server_name not in self.clients:
            raise ValueError(f"Servidor '{server_name}' não disponível")
        self.current_server = server_name

async def main():
    """Função principal para teste."""
    client = AdaptiveMCPClient()
    
    try:
        # Inicializar e descobrir servidores
        await client.initialize()
        
        # Mostrar servidor atual
        current = client.get_current_server()
        print(f"\nServidor atual: {current}")
        
        # Listar ferramentas disponíveis
        tools = await client.list_tools()
        print("\nFerramentas disponíveis:")
        print(json.dumps(tools, indent=2))
        
        # Se tiver mais de um servidor, testar mudança
        servers = client.discovery.list_servers()
        if len(servers) > 1:
            other_server = [s for s in servers if s != current][0]
            print(f"\nMudando para servidor: {other_server}")
            client.set_current_server(other_server)
            
            tools = await client.list_tools()
            print("\nFerramentas no novo servidor:")
            print(json.dumps(tools, indent=2))
            
    except Exception as e:
        logger.error(f"Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
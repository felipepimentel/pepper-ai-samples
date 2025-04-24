#!/usr/bin/env python
"""
MCP Server Discovery Module.
Permite descoberta automática e gerenciamento de servidores MCP disponíveis.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("mcp_discovery")

class MCPDiscovery:
    """Gerenciador de descoberta de servidores MCP."""
    
    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.config_paths = [
            Path.home() / ".config" / "mcp" / "servers.json",
            Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            Path.cwd() / ".mcp" / "servers.json",
            Path.cwd() / ".vscode" / "mcp.json"
        ]
        
    async def discover_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Descobre servidores MCP disponíveis em várias fontes.
        
        Returns:
            Dict com servidores encontrados
        """
        # Limpar servidores anteriores
        self.servers.clear()
        
        # Buscar em arquivos de configuração
        for config_path in self.config_paths:
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text())
                    if "servers" in config:
                        logger.info(f"Encontrados servidores em {config_path}")
                        self.servers.update(config["servers"])
                    elif "mcpServers" in config:  # Formato Claude Desktop
                        logger.info(f"Encontrados servidores Claude Desktop em {config_path}")
                        self.servers.update(config["mcpServers"])
                except Exception as e:
                    logger.warning(f"Erro ao ler {config_path}: {e}")
        
        # Buscar em variáveis de ambiente
        if "MCP_SERVERS" in os.environ:
            try:
                env_servers = json.loads(os.environ["MCP_SERVERS"])
                logger.info("Encontrados servidores em MCP_SERVERS")
                self.servers.update(env_servers)
            except Exception as e:
                logger.warning(f"Erro ao ler MCP_SERVERS: {e}")
        
        return self.servers
    
    def get_server_config(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém configuração de um servidor específico ou o primeiro disponível.
        
        Args:
            server_name: Nome do servidor desejado (opcional)
            
        Returns:
            Configuração do servidor
            
        Raises:
            ValueError: Se nenhum servidor for encontrado
        """
        if not self.servers:
            raise ValueError("Nenhum servidor MCP encontrado")
        
        if server_name:
            if server_name not in self.servers:
                raise ValueError(f"Servidor '{server_name}' não encontrado")
            return self.servers[server_name]
        
        # Retornar primeiro servidor disponível
        server_name = next(iter(self.servers))
        return self.servers[server_name]
    
    def list_servers(self) -> List[str]:
        """
        Lista nomes dos servidores disponíveis.
        
        Returns:
            Lista de nomes de servidores
        """
        return list(self.servers.keys())

async def main():
    """Função principal para teste."""
    discovery = MCPDiscovery()
    servers = await discovery.discover_servers()
    
    print("\nServidores MCP encontrados:")
    for name, config in servers.items():
        print(f"\n{name}:")
        print(json.dumps(config, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 
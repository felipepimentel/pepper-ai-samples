#!/usr/bin/env python
"""
MCP Runner - Executor de servidores MCP.

Este módulo fornece uma interface para carregar e executar servidores MCP
a partir de uma configuração JSON.
"""

import argparse
import asyncio
import importlib
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable, Tuple, Union

# Configurar o logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_runner")

# Adicionar o diretório raiz ao sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

class MCPRunner:
    """
    Classe principal para execução de servidores MCP.
    
    Esta classe carrega a configuração dos servidores e inicia
    cada servidor como especificado no arquivo de configuração.
    """
    
    def __init__(self, config_file: str):
        """
        Inicializa o MCPRunner com um arquivo de configuração.
        
        Args:
            config_file: Caminho para o arquivo de configuração JSON
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.servers = {}  # Armazenar as instâncias dos servidores
        
        logger.info(f"MCPRunner inicializado com configuração: {config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração a partir do arquivo JSON.
        
        Returns:
            Dicionário com a configuração carregada
        
        Raises:
            FileNotFoundError: Se o arquivo de configuração não existir
            json.JSONDecodeError: Se o arquivo não for um JSON válido
        """
        logger.info(f"Carregando configuração de: {self.config_file}")
        
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_file}")
        
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info(f"Configuração carregada com {len(config.get('servers', []))} servidores")
        return config
    
    async def _load_server_module(self, server_config: Dict[str, Any]) -> Tuple[str, Callable]:
        """
        Carrega o módulo do servidor e obtém a função de criação.
        
        Args:
            server_config: Configuração do servidor
        
        Returns:
            Tupla com o ID do servidor e a função de criação
        
        Raises:
            ImportError: Se o módulo não puder ser importado
            AttributeError: Se a função de criação não for encontrada
        """
        server_id = server_config.get("id")
        if not server_id:
            raise ValueError("Configuração do servidor deve incluir um 'id'")
        
        module_path = server_config.get("module")
        if not module_path:
            raise ValueError(f"Servidor {server_id} deve especificar um 'module'")
        
        logger.info(f"Carregando módulo para o servidor {server_id}: {module_path}")
        
        # Verificar se o módulo especifica um caminho absoluto ou um módulo python
        if os.path.exists(module_path) or module_path.endswith(".py"):
            # Carregar de um arquivo
            module_name = Path(module_path).stem
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Não foi possível carregar o módulo: {module_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # Importar de um módulo Python
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise ImportError(f"Não foi possível importar o módulo {module_path}: {e}")
        
        # Obter a função de criação
        create_func_name = server_config.get("create_function", "create_server")
        if not hasattr(module, create_func_name):
            raise AttributeError(f"Função '{create_func_name}' não encontrada no módulo {module_path}")
        
        create_func = getattr(module, create_func_name)
        logger.info(f"Função '{create_func_name}' encontrada para o servidor {server_id}")
        
        return server_id, create_func
    
    async def load_servers(self) -> Dict[str, Any]:
        """
        Carrega todos os servidores especificados na configuração.
        
        Returns:
            Dicionário com as instâncias dos servidores
        """
        servers_config = self.config.get("servers", [])
        logger.info(f"Carregando {len(servers_config)} servidores")
        
        for server_config in servers_config:
            try:
                server_id, create_func = await self._load_server_module(server_config)
                
                # Extrair parâmetros para o servidor
                params = server_config.get("params", {})
                params["id"] = server_id
                params["name"] = server_config.get("name", server_id)
                params["host"] = server_config.get("host", "127.0.0.1")
                params["port"] = server_config.get("port", 8000)
                params["options"] = server_config.get("options", {})
                
                # Criar o servidor
                logger.info(f"Criando servidor {server_id} com parâmetros: {params}")
                server_instance = await create_func(**params)
                
                # Armazenar a instância
                self.servers[server_id] = server_instance
                logger.info(f"Servidor {server_id} carregado com sucesso")
            
            except Exception as e:
                logger.error(f"Erro ao carregar servidor {server_config.get('id', 'unknown')}: {e}")
                if self.config.get("fail_fast", False):
                    raise
        
        return self.servers
    
    async def run_servers(self):
        """
        Executa todos os servidores carregados.
        """
        if not self.servers:
            logger.warning("Nenhum servidor carregado para execução")
            return
        
        logger.info(f"Iniciando {len(self.servers)} servidores")
        
        # Criar tarefas para cada servidor
        tasks = []
        for server_id, server in self.servers.items():
            logger.info(f"Criando tarefa para o servidor {server_id}")
            task = asyncio.create_task(
                server.run(),
                name=f"server_{server_id}"
            )
            tasks.append(task)
        
        # Aguardar todas as tarefas
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Erro durante a execução dos servidores: {e}")
            # Cancelar todas as tarefas restantes
            for task in tasks:
                if not task.done():
                    task.cancel()
    
    async def run(self):
        """
        Carrega e executa todos os servidores.
        """
        await self.load_servers()
        await self.run_servers()


async def main():
    """Função principal para execução do MCPRunner."""
    parser = argparse.ArgumentParser(description="MCP Runner - Executor de servidores MCP")
    parser.add_argument("config", help="Arquivo de configuração JSON")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Nível de log")
    
    args = parser.parse_args()
    
    # Configurar nível de log
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Criar e executar o runner
    runner = MCPRunner(args.config)
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main()) 
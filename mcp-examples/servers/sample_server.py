"""
Servidor de Amostra para MCP Runner.

Este módulo fornece uma implementação de servidor MCP de amostra para
demonstrar como os servidores podem ser carregados dinamicamente pelo MCPRunner.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

# Importar as bibliotecas MCP
import sys
from pathlib import Path

# Adicionar o diretório raiz ao sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.pepperpymcp.src.pepperpymcp.mcp import create_mcp_server

logger = logging.getLogger("sample_server")

class SampleServer:
    """Implementação de servidor MCP de amostra para o MCPRunner."""
    
    def __init__(self, id: str, name: str, host: str = "127.0.0.1", port: int = 8000, 
                 options: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Inicializa o servidor de amostra.
        
        Args:
            id: Identificador do servidor
            name: Nome amigável do servidor
            host: Endereço de host para ouvir
            port: Porta para ouvir
            options: Opções adicionais de configuração
            **kwargs: Argumentos adicionais
        """
        options = options or {}
        self.id = id
        self.name = name
        self.host = host
        self.port = port
        self.options = options
        
        # Criar o servidor MCP
        self.mcp = create_mcp_server(name)
        
        # Dados de exemplo
        self.items = {}
        
        # Carregar dados de amostra se configurado
        if options.get("load_data", True):
            item_count = options.get("count", 5)
            self._load_sample_data(item_count)
        
        # Registrar as ferramentas e recursos
        self._register_tools()
        self._register_resources()
    
    def _load_sample_data(self, count: int = 5):
        """
        Carrega dados de amostra para o servidor.
        
        Args:
            count: Número de itens a serem criados
        """
        for i in range(1, count + 1):
            item_id = f"item_{i}"
            self.items[item_id] = {
                "id": item_id,
                "name": f"Item de Amostra {i}",
                "description": f"Este é um item de amostra número {i}",
                "created_at": "2023-08-01T00:00:00Z",
                "tags": ["amostra", f"tag_{i}"]
            }
        
        logger.info(f"Carregados {len(self.items)} itens de amostra")
    
    def _register_tools(self):
        """Registra ferramentas para o servidor MCP."""
        
        @self.mcp.tool()
        async def get_item(id: str) -> Dict[str, Any]:
            """
            Obtém um item pelo ID.
            
            Args:
                id: Identificador do item
                
            Returns:
                Dados do item ou mensagem de erro
            """
            logger.info(f"Ferramenta get_item chamada com id: {id}")
            
            if id in self.items:
                return {
                    "status": "success",
                    "item": self.items[id]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Item com ID '{id}' não encontrado"
                }
        
        @self.mcp.tool()
        async def search_items(query: str = "", limit: int = 10) -> Dict[str, Any]:
            """
            Pesquisa itens que correspondem à consulta.
            
            Args:
                query: Termo de pesquisa
                limit: Número máximo de resultados
                
            Returns:
                Lista de itens correspondentes
            """
            logger.info(f"Ferramenta search_items chamada com query: {query}, limit: {limit}")
            
            results = []
            query = query.lower()
            
            for item_id, item in self.items.items():
                if (not query or 
                    query in item_id.lower() or
                    query in item["name"].lower() or
                    query in item["description"].lower()):
                    results.append(item)
                
                if len(results) >= limit:
                    break
            
            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results
            }
    
    def _register_resources(self):
        """Registra recursos para o servidor MCP."""
        
        @self.mcp.resource("item://{id}")
        async def get_item_resource(id: str) -> bytes:
            """
            Obtém um item como recurso.
            
            Args:
                id: Identificador do item
                
            Returns:
                Dados do item como bytes JSON
            """
            logger.info(f"Recurso item://{id} solicitado")
            
            if id in self.items:
                return json.dumps(self.items[id]).encode("utf-8")
            else:
                raise KeyError(f"Item com ID '{id}' não encontrado")
    
    async def run(self):
        """Executa o servidor MCP."""
        logger.info(f"Iniciando servidor {self.name} em {self.host}:{self.port}")
        await self.mcp.run(host=self.host, port=self.port)


# Função de fábrica para criar um servidor
async def create_server(**kwargs) -> SampleServer:
    """
    Cria um servidor de amostra.
    
    Args:
        **kwargs: Argumentos de configuração
        
    Returns:
        Instância do servidor de amostra
    """
    return SampleServer(**kwargs) 
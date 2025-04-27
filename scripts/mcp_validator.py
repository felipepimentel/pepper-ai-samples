#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server Validator para Monorepo

Este script percorre um monorepo para identificar e validar múltiplos servidores MCP.
Cada diretório é tratado como um potencial servidor MCP para testes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, cast

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-monorepo-validator")

# Constantes
DEFAULT_TIMEOUT = 30
DEFAULT_PORT = 8000
PROTOCOL_VERSION = "2025-03-26"
MAX_RETRY_ATTEMPTS = 2
SERVER_START_WAIT_TIME = 10

class McpMonorepoValidator:
    """Classe principal para validação de servidores MCP em monorepo.
    
    Esta classe descobre, inicia e valida servidores MCP em um monorepo,
    gerando relatórios detalhados de conformidade com o protocolo.
    """
    
    def __init__(
        self, 
        monorepo_path: str, 
        timeout: int = DEFAULT_TIMEOUT,
        pattern: Optional[str] = None,
        exclude: Optional[List[str]] = None
    ) -> None:
        """
        Inicializa o validador.
        
        Args:
            monorepo_path: Caminho para o monorepo contendo servidores MCP
            timeout: Tempo limite em segundos para testes
            pattern: Padrão glob para identificar diretórios de servidor MCP
            exclude: Lista de diretórios para excluir da validação
        """
        self.monorepo_path = Path(monorepo_path).resolve()
        self.timeout = timeout
        self.pattern = pattern
        self.exclude = exclude or []
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.server_processes: Dict[str, ServerProcess] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.server_info: Dict[str, Any] = {}
        
        # Descobrir servidores
        self._discover_servers()
    
    def _discover_servers(self) -> None:
        """
        Descobre servidores MCP no monorepo baseado em convenções.
        
        Identifica potenciais servidores MCP com base em padrões de arquivos
        e estrutura de diretórios, suportando servidores Python e Node.js.
        """
        logger.info(f"Descobrindo servidores MCP em: {self.monorepo_path}")
        
        # Lista para armazenar os servidores descobertos
        discovered_servers: Dict[str, Dict[str, Any]] = {}
        
        # Se um padrão específico foi fornecido, use-o para encontrar diretórios
        if self.pattern:
            server_dirs = list(self.monorepo_path.glob(self.pattern))
        else:
            # Caso contrário, considere todos os diretórios de primeiro nível como potenciais servidores
            server_dirs = [d for d in self.monorepo_path.iterdir() if d.is_dir()]
            # Se o monorepo_path for diretório e tiver server.py, considere ele próprio
            if os.path.isfile(os.path.join(self.monorepo_path, "server.py")):
                server_dirs.append(self.monorepo_path)
        
        # Filtrar diretórios excluídos
        server_dirs = [d for d in server_dirs if d.name not in self.exclude and ".git" not in d.parts]
        logger.info(f"Diretórios potenciais: {[d.name for d in server_dirs]}")
        
        # Para cada diretório, tente identificar um servidor MCP
        for server_dir in server_dirs:
            server_id = server_dir.name
            
            # Verificar se há um arquivo package.json (servidor Node.js)
            if self._is_nodejs_server(server_dir, server_id, discovered_servers):
                continue
            
            # Verificar arquivos Python
            self._check_python_server(server_dir, server_id, discovered_servers)
        
        # Atualizar servidores
        self.servers = discovered_servers
        logger.info(f"Descobertos {len(self.servers)} servidores MCP potenciais.")
        
        # Listar servidores descobertos
        for server_id, config in self.servers.items():
            logger.info(f"  - {server_id} ({config['type']}): {config['command']} {' '.join(config['args'])}")
    
    def _is_nodejs_server(self, server_dir: Path, server_id: str, 
                          discovered_servers: Dict[str, Dict[str, Any]]) -> bool:
        """Verifica se o diretório contém um servidor Node.js e o registra."""
        package_json = server_dir / "package.json"
        if not package_json.exists():
            return False
            
        try:
            with open(package_json, 'r') as f:
                package_data = json.load(f)
            
            main_file = package_data.get("main", "index.js")
            if not main_file.endswith(".js"):
                main_file += ".js"
            
            # Verificar se o arquivo principal existe
            main_path = server_dir / main_file
            dist_path = server_dir / "dist" / main_file
            build_path = server_dir / "build" / main_file
            
            if main_path.exists():
                command = "node"
                args = [str(main_path)]
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "nodejs",
                    "directory": str(server_dir)
                }
            elif dist_path.exists():
                command = "node"
                args = [str(dist_path)]
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "nodejs",
                    "directory": str(server_dir)
                }
            elif build_path.exists():
                command = "node"
                args = [str(build_path)]
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "nodejs",
                    "directory": str(server_dir)
                }
            else:
                # Tente usar npm/yarn/pnpm start
                if os.path.exists(server_dir / "yarn.lock"):
                    command = "yarn"
                    args = ["--cwd", str(server_dir), "start"]
                elif os.path.exists(server_dir / "pnpm-lock.yaml"):
                    command = "pnpm"
                    args = ["--dir", str(server_dir), "start"]
                else:
                    command = "npm"
                    args = ["--prefix", str(server_dir), "start"]
                
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "nodejs-pkg",
                    "directory": str(server_dir)
                }
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Erro ao analisar package.json em {server_dir}: {e}")
            return False
    
    def _check_python_server(self, server_dir: Path, server_id: str, 
                            discovered_servers: Dict[str, Dict[str, Any]]) -> None:
        """Verifica se o diretório contém um servidor Python e o registra."""
        python_files = list(server_dir.glob("*.py"))
        logger.debug(f"Arquivos Python em {server_dir}: {[f.name for f in python_files]}")
        
        if python_files:
            # Procurar por arquivos com padrão comum para servidores MCP
            mcp_candidates = [f for f in python_files if any(
                pattern in f.name.lower() for pattern in 
                ["mcp", "server", "main", "app", "index"]
            )]
            
            if mcp_candidates:
                server_file = mcp_candidates[0]  # Usa o primeiro candidato encontrado
                logger.debug(f"Candidato encontrado: {server_file}")
                command = "python"
                args = [str(server_file)]
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "python",
                    "directory": str(server_dir)
                }
            elif python_files:
                # Se não encontrou candidatos específicos, use o primeiro arquivo Python
                server_file = python_files[0]
                logger.debug(f"Usando primeiro arquivo Python: {server_file}")
                command = "python"
                args = [str(server_file)]
                discovered_servers[server_id] = {
                    "command": command,
                    "args": args,
                    "type": "python",
                    "directory": str(server_dir)
                }
    
    async def validate_all(self) -> None:
        """
        Valida todos os servidores descobertos.
        
        Executa a validação em paralelo para todos os servidores MCP descobertos,
        exibindo os resultados diretamente no console.
        """
        logger.info("Iniciando validação de todos os servidores...")
        
        if not self.servers:
            logger.error("Nenhum servidor MCP foi descoberto para validação.")
            return
        
        tasks = []
        for server_id, server_config in self.servers.items():
            tasks.append(self.validate_server(server_id, server_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for i, server_id in enumerate(self.servers.keys()):
            if isinstance(results[i], Exception):
                self.results[server_id] = {
                    "status": "error",
                    "error": str(results[i]),
                    "tests": {}
                }
            else:
                self.results[server_id] = cast(Dict[str, Any], results[i])
        
        # Exibir os resultados no console
        self._print_results()
        logger.info("Validação concluída.")
    
    async def _cleanup_all(self) -> None:
        """
        Limpa todos os recursos e processos.
        
        Garante que todos os processos de servidor sejam encerrados corretamente
        antes da finalização do validador.
        """
        logger.info("Limpando todos os processos e recursos...")
        
        # Encerra todos os processos de servidor
        for server_id, server_process in list(self.server_processes.items()):
            await server_process.stop()
            self.server_processes.pop(server_id, None)
    
    async def validate_server(self, server_id: str, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa validação em um servidor MCP específico.
        
        Inicia o servidor, executa uma série de testes para validar conformidade
        com o protocolo MCP e retorna um relatório detalhado dos resultados.
        
        Args:
            server_id: Identificador do servidor
            server_config: Configuração do servidor
            
        Returns:
            Dicionário com resultados dos testes
        """
        logger.info(f"Validando servidor: {server_id}")
        
        # Extrai configuração do servidor
        command = server_config.get("command")
        args = server_config.get("args", [])
        directory = server_config.get("directory")
        server_type = server_config.get("type", "unknown")
        
        if not command:
            return {"status": "error", "error": "Comando não especificado", "tests": {}}
        
        # Resultados
        results = {
            "status": "pending",
            "tests": {},
            "start_time": datetime.now().isoformat(),
            "server_type": server_type,
            "directory": directory
        }
        
        try:
            # Criar e iniciar o processo do servidor
            server_process = ServerProcess(
                server_id=server_id,
                command=command,
                args=args,
                directory=directory,
                timeout=self.timeout
            )
            
            success, error_message = await server_process.start()
            if not success:
                results["status"] = "error"
                results["error"] = error_message or "Falha ao iniciar o servidor"
                return results
                
            # Armazenar o processo para limpeza posterior
            self.server_processes[server_id] = server_process
            
            # Executar todos os testes
            await self._run_all_tests(server_id, server_process, results)
            
            # Calcular resultado final
            self._calculate_final_result(results)
                
        except Exception as e:
            logger.error(f"Erro ao validar servidor {server_id}: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        finally:
            # Encerrar o servidor
            if server_id in self.server_processes:
                await self.server_processes[server_id].stop()
                self.server_processes.pop(server_id, None)
            results["end_time"] = datetime.now().isoformat()
        
        return results
    
    async def _run_all_tests(self, server_id: str, server_process: 'ServerProcess', 
                           results: Dict[str, Any]) -> None:
        """Executa todos os testes para um servidor."""
        # Testes de MCP
        results["tests"]["initialization"] = await self._test_initialization(server_id, server_process)
        
        if results["tests"]["initialization"]["status"] == "pass":
            # Se a inicialização passou, executar mais testes
            capabilities = results["tests"]["initialization"].get("server_info", {}).get("capabilities", {})
            
            # Testes específicos baseados nas capacidades
            if "tools" in capabilities:
                results["tests"]["tools"] = await self._test_capability(server_id, "tools", "tools/list", 2)
            
            if "resources" in capabilities:
                results["tests"]["resources"] = await self._test_capability(server_id, "resources", "resources/list", 4)
            
            if "prompts" in capabilities:
                results["tests"]["prompts"] = await self._test_capability(server_id, "prompts", "prompts/list", 7)
    
    def _calculate_final_result(self, results: Dict[str, Any]) -> None:
        """Calcula o resultado final com base nos testes realizados."""
        failed_tests = [t for t in results["tests"].values() 
                       if t.get("status") == "fail"]
        
        if failed_tests:
            results["status"] = "fail"
        else:
            results["status"] = "pass"
    
    async def _test_initialization(self, server_id: str, server_process: 'ServerProcess') -> Dict[str, Any]:
        """
        Testa a inicialização do servidor MCP.
        
        Envia uma requisição de inicialização para o servidor e valida a resposta.
        
        Args:
            server_id: Identificador do servidor
            server_process: Processo do servidor
            
        Returns:
            Resultado do teste de inicialização
        """
        logger.info(f"Testando inicialização do servidor {server_id}")
        
        # Preparar parâmetros de inicialização
        init_params = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "MCPValidator",
                "version": "1.0.0"
            }
        }
        
        # Enviar requisição e validar resposta
        success, response, error_reason = await server_process.send_request(
            "initialize", init_params, 1, "inicialização"
        )
        
        # Se falhou, retornar erro
        if not success:
            return {
                "status": "fail",
                "reason": error_reason,
                "response": response
            }
        
        # Verificar versão do protocolo
        protocol_version = response.get("result", {}).get("protocolVersion")
        if not protocol_version:
            return {
                "status": "fail",
                "reason": "Versão do protocolo não especificada na resposta",
                "response": response
            }
        
        # Enviar notificação de inicialização
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        if server_process.process and server_process.process.stdin:
            server_process.process.stdin.write(json.dumps(init_notification) + "\n")
            server_process.process.stdin.flush()
        
        # Guardar informações para testes futuros
        self.server_info = {
            "protocol_version": protocol_version,
            "capabilities": response.get("result", {}).get("capabilities", {}),
            "server_info": response.get("result", {}).get("serverInfo", {})
        }
        
        return {
            "status": "pass",
            "protocol_version": protocol_version,
            "server_info": self.server_info
        }
    
    async def _test_capability(self, server_id: str, capability_type: str, 
                          list_method: str, id_base: int) -> Dict[str, Any]:
        """
        Método genérico para testar uma capacidade do servidor MCP.
        
        Args:
            server_id: Identificador do servidor
            capability_type: Tipo de capacidade a testar (tools, resources, prompts)
            list_method: Método JSONRPC para listar as capacidades
            id_base: ID base para as requisições JSONRPC
            
        Returns:
            Resultado do teste
        """
        logger.info(f"Testando {capability_type} do servidor {server_id}")
        
        server_process = self.server_processes.get(server_id)
        if not server_process:
            return {"status": "error", "reason": "Servidor não está em execução"}
        
        # Listar capacidades
        success, response, error_reason = await server_process.send_request(
            list_method, request_id=id_base, description=f"lista de {capability_type}"
        )
        
        if not success:
            return {
                "status": "fail",
                "reason": error_reason,
                "response": response if response else None
            }
        
        # Extract capabilities based on type
        if capability_type == "tools":
            items = response.get("result", {}).get("tools", [])
            item_field = "tools_count"
        elif capability_type == "resources":
            items = response.get("result", {}).get("resources", [])
            item_field = "resources_count"
        elif capability_type == "prompts":
            items = response.get("result", {}).get("prompts", [])
            item_field = "prompts_count"
        else:
            return {"status": "error", "reason": f"Tipo de capacidade desconhecido: {capability_type}"}
        
        # Se não há items, verifica alternativas ou retorna aviso
        if not items:
            if capability_type == "resources":
                return await self._test_resource_templates(server_id, server_process, response)
            
            return {
                "status": "warn",
                "reason": f"Servidor não expõe {capability_type}",
                "response": response
            }
        
        # Testar o primeiro item baseado no tipo
        if capability_type == "tools":
            first_item = items[0]
            item_name = first_item.get("name")
            args = self._generate_tool_args(first_item)
            return await self._call_tool(server_process, item_name, args, items)
        elif capability_type == "resources":
            return await self._test_resource_read(server_id, server_process, items)
        elif capability_type == "prompts":
            first_item = items[0]
            item_name = first_item.get("name")
            args = self._generate_prompt_args(first_item)
            return await self._call_prompt(server_process, item_name, args, items)
        
        return {"status": "error", "reason": "Implementação de teste não disponível"}
    
    async def _call_tool(self, server_process: 'ServerProcess', tool_name: str, 
                        tool_args: Dict[str, Any], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tenta chamar uma ferramenta e retorna o resultado do teste."""
        params = {
            "name": tool_name,
            "arguments": tool_args
        }
        
        success, response, error_reason = await server_process.send_request(
            "tools/call", params, 3, f"chamada da ferramenta {tool_name}"
        )
        
        if not success:
            return {
                "status": "fail",
                "reason": error_reason,
                "response": response if response else None
            }
        
        return {
            "status": "pass",
            "tools_count": len(tools),
            "tested_tool": tool_name,
            "test_arguments": tool_args,
            "call_result": "result" in response
        }
    
    def _generate_tool_args(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Gera argumentos para uma ferramenta baseado no esquema de entrada."""
        tool_args = {}
        input_schema = tool.get("inputSchema", {})
        
        # Tenta gerar argumentos com base no esquema
        if input_schema and input_schema.get("type") == "object":
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                if prop_name in required:
                    # Gerar um valor padrão com base no tipo
                    prop_type = prop_schema.get("type")
                    if prop_type == "string":
                        tool_args[prop_name] = "test_value"
                    elif prop_type == "number" or prop_type == "integer":
                        tool_args[prop_name] = 1
                    elif prop_type == "boolean":
                        tool_args[prop_name] = True
                    elif prop_type == "array":
                        tool_args[prop_name] = []
                    elif prop_type == "object":
                        tool_args[prop_name] = {}
        
        return tool_args
    
    async def _test_resource_templates(self, server_id: str, server_process: 'ServerProcess', 
                                     resources_response: Dict[str, Any]) -> Dict[str, Any]:
        """Testa templates de recursos quando não há recursos disponíveis."""
        success, templates_response, error_reason = await server_process.send_request(
            "resources/templates/list", request_id=5, description="lista de templates"
        )
        
        if not success:
            return {
                "status": "warn",
                "reason": "Sem recursos e " + error_reason,
                "resources_response": resources_response,
                "templates_response": templates_response if templates_response else None
            }
        
        templates = templates_response.get("result", {}).get("resourceTemplates", [])
        
        return {
            "status": "pass" if templates else "warn",
            "resources_count": 0,
            "templates_count": len(templates)
        }
    
    async def _test_resource_read(self, server_id: str, server_process: 'ServerProcess', 
                               resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Testa a leitura de um recurso."""
        first_resource = resources[0]
        resource_uri = first_resource.get("uri")
        
        params = {
            "uri": resource_uri
        }
        
        success, read_response, error_reason = await server_process.send_request(
            "resources/read", params, 6, f"leitura do recurso {resource_uri}"
        )
        
        if not success:
            return {
                "status": "fail",
                "reason": error_reason,
                "resources_count": len(resources),
                "response": read_response if read_response else None
            }
        
        return {
            "status": "pass",
            "resources_count": len(resources),
            "tested_resource": resource_uri,
            "read_result": "result" in read_response
        }
    
    async def _call_prompt(self, server_process: 'ServerProcess', prompt_name: str, 
                         prompt_args: Dict[str, Any], prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tenta chamar um prompt e retorna o resultado do teste."""
        params = {
            "name": prompt_name,
            "arguments": prompt_args
        }
        
        success, get_response, error_reason = await server_process.send_request(
            "prompts/get", params, 8, f"obtenção do prompt {prompt_name}"
        )
        
        if not success:
            return {
                "status": "fail",
                "reason": error_reason,
                "prompts_count": len(prompts),
                "response": get_response if get_response else None
            }
        
        return {
            "status": "pass",
            "prompts_count": len(prompts),
            "tested_prompt": prompt_name,
            "test_arguments": prompt_args,
            "get_result": "result" in get_response
        }
    
    def _generate_prompt_args(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Gera argumentos para um prompt."""
        prompt_args = {}
        for arg in prompt.get("arguments", []):
            if arg.get("required", False):
                prompt_args[arg.get("name")] = "test_value"
        return prompt_args
    
    def _print_results(self) -> None:
        """
        Exibe os resultados da validação diretamente no console.
        """
        # Calcular estatísticas
        stats = self._calculate_statistics()
        
        # Exibir cabeçalho
        print("\n" + "=" * 80)
        print(f"Relatório de Validação MCP - {datetime.now().isoformat()}")
        print("=" * 80 + "\n")
        
        print(f"Monorepo: {self.monorepo_path}\n")
        print(f"Total de servidores: {stats['total']}")
        print(f"Aprovados: {stats['passed']}")
        print(f"Falhas: {stats['failed']}")
        print(f"Erros: {stats['errors']}\n")
        
        # Detalhes por servidor
        print("Detalhes por servidor:")
        print("-" * 80)
        
        for server_id, result in self.results.items():
            status = result.get("status", "desconhecido")
            status_symbol = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️" 
            server_type = result.get("server_type", "desconhecido")
            directory = result.get("directory", "desconhecido")
            
            print(f"{status_symbol} {server_id} ({server_type}): {status.upper()}")
            print(f"   Diretório: {directory}")
            
            # Detalhes do servidor
            server_info = None
            for test_name, test_result in result.get("tests", {}).items():
                if test_name == "initialization" and test_result.get("status") == "pass":
                    server_info = test_result.get("server_info", {})
                    
            if server_info:
                server_name = server_info.get("server_info", {}).get("name", "Desconhecido")
                protocol_version = server_info.get("protocol_version", "Desconhecido")
                capabilities = server_info.get("capabilities", {})
                
                print(f"   Nome: {server_name}")
                print(f"   Versão do Protocolo: {protocol_version}")
                if capabilities:
                    print(f"   Capacidades: {', '.join(capabilities.keys())}")
            
            # Detalhes dos testes
            tests = result.get("tests", {})
            if tests:
                print("   Testes:")
                for test_name, test_result in tests.items():
                    test_status = test_result.get("status", "desconhecido")
                    test_symbol = "✅" if test_status == "pass" else "❌" if test_status == "fail" else "⚠️"
                    
                    print(f"    {test_symbol} {test_name}: {test_status.upper()}")
                    
                    # Mostrar razão se falhou
                    if test_status != "pass" and "reason" in test_result:
                        print(f"        Razão: {test_result['reason']}")
                    
                    # Detalhes específicos por tipo de teste
                    if test_name == "tools" and "tools_count" in test_result:
                        print(f"        Ferramentas: {test_result['tools_count']}")
                        if "tested_tool" in test_result:
                            print(f"        Testada: {test_result['tested_tool']}")
                    
                    if test_name == "resources" and "resources_count" in test_result:
                        print(f"        Recursos: {test_result['resources_count']}")
                        if "tested_resource" in test_result:
                            print(f"        Testado: {test_result['tested_resource']}")
                        if "templates_count" in test_result:
                            print(f"        Templates: {test_result['templates_count']}")
                    
                    if test_name == "prompts" and "prompts_count" in test_result:
                        print(f"        Prompts: {test_result['prompts_count']}")
                        if "tested_prompt" in test_result:
                            print(f"        Testado: {test_result['tested_prompt']}")
            
            print("")
    
    def _calculate_statistics(self) -> Dict[str, int]:
        """Calcula estatísticas dos resultados."""
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get("status") == "pass")
        failed = sum(1 for r in self.results.values() if r.get("status") == "fail")
        errors = sum(1 for r in self.results.values() if r.get("status") == "error")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors
        }

class ServerProcess:
    """
    Gerencia o ciclo de vida de um processo de servidor MCP.
    
    Encapsula a inicialização, comunicação e encerramento de um processo
    de servidor, gerenciando entradas e saídas de forma assíncrona.
    """
    
    def __init__(self, server_id: str, command: str, args: List[str], 
                directory: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Inicializa um gerenciador de processo de servidor.
        
        Args:
            server_id: Identificador do servidor
            command: Comando para iniciar o servidor
            args: Argumentos do comando
            directory: Diretório de trabalho
            timeout: Timeout para operações
        """
        self.server_id = server_id
        self.command = command
        self.args = args
        self.directory = directory
        self.timeout = timeout
        self.process: Optional[subprocess.Popen] = None
        self.log_path: Optional[str] = None
        self.log_file: Optional[Any] = None
    
    async def start(self, port: int = DEFAULT_PORT) -> Tuple[bool, Optional[str]]:
        """
        Inicia o processo do servidor.
        
        Args:
            port: Porta para o servidor
            
        Returns:
            Tupla com sucesso (bool) e mensagem de erro (se houver)
        """
        logger.info(f"Iniciando servidor {self.server_id}: {self.command} {' '.join(self.args)}")
        
        # Preparar ambiente
        temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
        self.log_path = temp_log.name
        temp_log.close()
        self.log_file = open(self.log_path, "w")
        
        # Executar preflight check
        preflight_error = self._preflight_check(port)
        if preflight_error:
            logger.error(f"Preflight falhou para {self.server_id}: {preflight_error}")
            return False, preflight_error
        
        # Ajustar comando para uv run se necessário
        adjusted_command, adjusted_args = self._adjust_command_for_server()
        
        try:
            # Forçar modo STDIO para o servidor
            if "--stdio" not in adjusted_args:
                adjusted_args.append("--stdio")
            
            # Iniciar processo
            process_env = os.environ.copy()
            
            logger.debug(f"Iniciando processo com comando: {adjusted_command} {' '.join(adjusted_args)}")
            
            self.process = subprocess.Popen(
                [adjusted_command] + adjusted_args,
                env=process_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log_file,
                text=True,
                bufsize=1,
                cwd=self.directory
            )
            
            # Aguardar inicialização
            start_result = await self._wait_for_start()
            if start_result != "success":
                return False, f"Falha ao iniciar: {start_result}"
                
            logger.info(f"Servidor {self.server_id} iniciado com PID {self.process.pid}")
            return True, None
            
        except Exception as e:
            if self.log_file:
                self.log_file.close()
            return False, str(e)
    
    async def stop(self) -> None:
        """
        Encerra o processo do servidor.
        """
        if not self.process:
            return
            
        logger.info(f"Encerrando servidor {self.server_id} (PID {self.process.pid})")
        
        # Tentar encerramento normal fechando stdin
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        
        # Aguardar encerramento
        try:
            await asyncio.wait_for(
                asyncio.create_subprocess_shell(f"kill -0 {self.process.pid} 2>/dev/null"),
                timeout=3
            )
            # Enviar SIGTERM
            logger.info(f"Enviando SIGTERM para servidor {self.server_id}")
            try:
                self.process.terminate()
                await asyncio.sleep(2)
                
                if self.process.poll() is None:
                    # Se ainda não encerrou, enviar SIGKILL
                    logger.info(f"Enviando SIGKILL para servidor {self.server_id}")
                    self.process.kill()
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Erro ao encerrar servidor {self.server_id}: {e}")
        except (asyncio.TimeoutError, ProcessLookupError):
            # O processo já encerrou
            logger.info(f"Processo {self.server_id} já estava encerrado")
        
        # Fechar arquivo de log
        if self.log_file:
            self.log_file.close()
            
        self.process = None
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None,
                         request_id: int = 1, description: str = "requisição") -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Envia uma requisição JSONRPC para o servidor.
        
        Args:
            method: Método JSONRPC
            params: Parâmetros (opcional)
            request_id: ID da requisição
            description: Descrição para logs
            
        Returns:
            Tupla com sucesso, resposta e mensagem de erro
        """
        if not self.process:
            return False, None, "Servidor não está em execução"
            
        # Criar requisição
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
            
        # Enviar requisição
        logger.info(f"Enviando {description} ({method})")
        json_request = json.dumps(request) + "\n"
        logger.debug(f"Request enviado: {json_request.strip()}")
        
        if self.process.stdin:
            self.process.stdin.write(json_request)
            self.process.stdin.flush()
        
        # Aguardar resposta
        try:
            response = await asyncio.wait_for(
                self._read_response(),
                timeout=self.timeout
            )
            
            # Verificar se houve resposta
            if not response:
                return False, None, f"Sem resposta para {description}"
                
            # Validar formato da resposta
            if not self._validate_jsonrpc_response(response, request_id):
                return False, response, f"Resposta de {description} inválida"
                
            # Verificar erro na resposta
            if "error" in response:
                error = response.get("error", {})
                return False, response, f"Erro na {description}: {error.get('message', 'Desconhecido')}"
                
            return True, response, None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout aguardando resposta de {description}")
            return False, None, f"Timeout aguardando {description}"
    
    def _preflight_check(self, port: int) -> Optional[str]:
        """Realiza verificações de pré-voo antes de iniciar o servidor."""
        if not self.directory:
            return "Diretório não especificado"
            
        # Verificar versão do Python
        if sys.version_info < (3, 10):
            return "Python 3.10+ required"
            
        # Verificar dependências
        try:
            result = subprocess.run(["uv", "pip", "check"], 
                                  cwd=self.directory, 
                                  capture_output=True, 
                                  text=True)
            if result.returncode != 0:
                return f"Dependency check failed:\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            logger.warning("UV package manager not found, skipping dependency check")
            
        # Verificar ponto de entrada (server.py no root ou src/)
        server_py_in_root = os.path.exists(os.path.join(self.directory, "server.py"))
        server_py_in_src = os.path.exists(os.path.join(self.directory, "src", "server.py"))
        
        has_server_py = (server_py_in_root or 
                       server_py_in_src or 
                       any(f.name == "server.py" for f in Path(self.directory).rglob("server.py")))
                       
        if not has_server_py:
            return "Entrypoint server.py not found in root or src/"
            
        # Verificar porta
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("localhost", port))
        except OSError:
            return f"Port {port} is in use"
        finally:
            s.close()
            
        return None
    
    def _adjust_command_for_server(self) -> Tuple[str, List[str]]:
        """Ajusta o comando para usar uv run para arquivos server.py"""
        if not self.directory:
            return self.command, self.args
            
        server_py_path = os.path.join(self.directory, "server.py")
        if os.path.exists(server_py_path):
            return "uv", ["run", server_py_path]
        
        server_py_path = os.path.join(self.directory, "src", "server.py")
        if os.path.exists(server_py_path):
            return "uv", ["run", server_py_path]
            
        return self.command, self.args
    
    async def _wait_for_start(self) -> str:
        """Aguarda o servidor iniciar e verifica erros no log."""
        if not self.process or not self.log_path:
            return "error"
            
        # Aguardar até 10 segundos, verificar log para erros
        for _ in range(SERVER_START_WAIT_TIME):
            await asyncio.sleep(1)
            if self.process.poll() is not None:
                break
                
            # Verificar log para erros
            with open(self.log_path, "r") as lf:
                lines = lf.readlines()[-20:]
                for line in lines:
                    if any(err in line for err in ["Traceback", "Error", "Exception"]):
                        logger.error(f"Detected error in log for {self.server_id}: {line.strip()}")
                        self.process.terminate()
                        return "error"
        
        if self.process.poll() is not None:
            logger.error(f"Servidor {self.server_id} encerrou prematuramente com código: {self.process.returncode}")
            with open(self.log_path, "r") as lf:
                log_excerpt = ''.join(lf.readlines()[-20:])
                logger.error(f"Log excerpt for {self.server_id}:\n{log_excerpt}")
            return "terminated"
            
        return "success"
    
    async def _read_response(self) -> Optional[Dict[str, Any]]:
        """Lê uma resposta do servidor."""
        if not self.process or not self.process.stdout:
            return None
        
        try:
            # Ler uma linha da saída padrão
            line = await asyncio.to_thread(self.process.stdout.readline)
            
            if not line:
                return None
                
            logger.debug(f"Resposta recebida: {line.strip()}")
                
            try:
                return json.loads(line.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar resposta JSON: {e}")
                logger.error(f"Resposta recebida: {line.strip()}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao ler resposta do servidor: {e}")
            return None
    
    def _validate_jsonrpc_response(self, response: Any, expected_id: int) -> bool:
        """Valida o formato básico de uma resposta JSONRPC."""
        return (isinstance(response, dict) and
                response.get("jsonrpc") == "2.0" and
                response.get("id") == expected_id and
                ("result" in response or "error" in response))

def main() -> None:
    """
    Função principal do validador.
    
    Configura argumentos de linha de comando e executa a validação
    nos servidores MCP encontrados no monorepo.
    """
    parser = argparse.ArgumentParser(
        description="Validador de servidores MCP para Monorepo - Testa múltiplos servidores para conformidade com o protocolo"
    )
    parser.add_argument(
        "monorepo", 
        help="Caminho para o diretório monorepo contendo servidores MCP"
    )
    parser.add_argument(
        "-t", "--timeout", 
        help="Timeout em segundos para operações de teste", 
        type=int, 
        default=DEFAULT_TIMEOUT
    )
    parser.add_argument(
        "-p", "--pattern", 
        help="Padrão glob para filtrar diretórios de servidor (ex: 'mcp-*')", 
        default=None
    )
    parser.add_argument(
        "-e", "--exclude", 
        help="Lista de diretórios para excluir, separados por vírgula", 
        default=None
    )
    parser.add_argument(
        "-v", "--verbose", 
        help="Modo verboso", 
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Processar lista de exclusão
    exclude_list = []
    if args.exclude:
        exclude_list = [item.strip() for item in args.exclude.split(",")]
    
    try:
        # Criar validador
        validator = McpMonorepoValidator(
            monorepo_path=args.monorepo,
            timeout=args.timeout,
            pattern=args.pattern,
            exclude=exclude_list
        )
        
        # Configurar tratamento de sinais para saída limpa
        setup_signal_handlers(validator)
        
        # Executar o validador
        asyncio.run(validator.validate_all())
    except KeyboardInterrupt:
        logger.info("Validação interrompida pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro durante validação: {e}")
        if args.verbose:
            logger.exception("Detalhes do erro:")
        sys.exit(1)

def setup_signal_handlers(validator: McpMonorepoValidator) -> None:
    """Configura handlers de sinais para saída limpa."""
    def signal_handler(sig, frame):
        logger.info("Encerrando validação por solicitação do usuário...")
        # Criar uma nova task para o cleanup, mesmo fora de um contexto async
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(validator._cleanup_all())
            else:
                loop.run_until_complete(validator._cleanup_all())
        except RuntimeError:
            # Se não temos um loop em execução, apenas saímos
            pass
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()
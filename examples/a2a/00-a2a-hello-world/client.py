#!/usr/bin/env python
"""
Cliente A2A básico para testar o servidor hello-world.

Este cliente demonstra como enviar tarefas para um servidor A2A
e processar as respostas, incluindo fluxos de múltiplos turnos.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, Optional
import uuid

import aiohttp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class A2AClient:
    """Cliente simples para interagir com servidores A2A."""
    
    def __init__(self, base_url: str):
        """
        Inicializa o cliente A2A.
        
        Args:
            base_url: URL base do servidor A2A, incluindo protocolo e porta
        """
        self.base_url = base_url.rstrip("/")
        self.session = None
    
    async def __aenter__(self):
        """Gerenciador de contexto assíncrono."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fechar a sessão HTTP ao sair."""
        if self.session:
            await self.session.close()
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Obtém o Agent Card do servidor A2A.
        
        Returns:
            Informações do agente e suas capacidades
        """
        url = f"{self.base_url}/.well-known/agent.json"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def send_task(self, 
                       skill: str, 
                       input_data: Dict[str, Any],
                       task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Envia uma tarefa para o servidor A2A.
        
        Args:
            skill: Nome da capacidade a ser invocada
            input_data: Dados de entrada para a capacidade
            task_id: ID opcional de tarefa (para atualizações)
            
        Returns:
            Resposta do servidor
        """
        url = f"{self.base_url}/tasks/send"
        payload = {
            "skill": skill,
            "input": input_data
        }
        
        if task_id:
            payload["task_id"] = task_id
        
        async with self.session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtém o status de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Status atual da tarefa
        """
        url = f"{self.base_url}/tasks/get?task_id={task_id}"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def wait_for_task_completion(self, 
                                     task_id: str, 
                                     polling_interval: float = 0.5,
                                     timeout: float = 30.0) -> Dict[str, Any]:
        """
        Aguarda a conclusão de uma tarefa, com suporte para fluxos de múltiplos turnos.
        
        Args:
            task_id: ID da tarefa
            polling_interval: Intervalo entre verificações em segundos
            timeout: Tempo limite total em segundos
            
        Returns:
            Status final da tarefa
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Verificar se atingimos o timeout
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                raise TimeoutError(f"Tempo limite atingido ao aguardar tarefa {task_id}")
            
            # Obter status da tarefa
            task_status = await self.get_task_status(task_id)
            status = task_status.get("status")
            
            # Verificar estados finais
            if status == "completed":
                return task_status
            elif status == "error":
                logger.error(f"Erro na tarefa: {task_status.get('error')}")
                return task_status
            elif status == "canceled":
                logger.warning(f"Tarefa cancelada: {task_id}")
                return task_status
            elif status == "input-required":
                # Retornar controle para permitir que o chamador forneça input
                return task_status
            
            # Aguardar antes da próxima verificação
            await asyncio.sleep(polling_interval)


async def interactive_test():
    """Teste interativo do servidor A2A."""
    server_url = "http://localhost:8080"
    
    async with A2AClient(server_url) as client:
        # Obter informações do agente
        try:
            agent_info = await client.get_agent_card()
            print("\n===== Informações do Agente =====")
            print(f"Nome: {agent_info.get('name')}")
            print(f"Descrição: {agent_info.get('description')}")
            print(f"Versão: {agent_info.get('version')}")
            print("\nCapacidades disponíveis:")
            for capability in agent_info.get('capabilities', []):
                print(f"- {capability.get('name')}: {capability.get('description')}")
        except Exception as e:
            logger.error(f"Erro ao obter agent card: {e}")
            print("\nErro: O servidor A2A não parece estar em execução. Inicie o servidor primeiro.")
            return
        
        # Menu interativo
        while True:
            print("\n===== Menu A2A =====")
            print("1. Testar capacidade 'greet'")
            print("2. Testar capacidade 'chat' (conversa simples)")
            print("3. Testar capacidade 'chat' (múltiplos turnos)")
            print("4. Testar capacidade 'calculate'")
            print("5. Sair")
            
            choice = input("\nEscolha uma opção (1-5): ")
            
            if choice == "1":
                # Testar greet
                name = input("Digite seu nome: ")
                print("\nEnviando tarefa 'greet'...")
                
                response = await client.send_task("greet", {"name": name})
                task_id = response.get("task_id")
                
                print(f"Tarefa criada com ID: {task_id}")
                
                result = await client.wait_for_task_completion(task_id)
                if result.get("status") == "completed":
                    print(f"\nResposta: {result.get('result', {}).get('message')}")
                else:
                    print(f"\nTarefa não completada. Status: {result.get('status')}")
                    print(f"Detalhes: {json.dumps(result, indent=2)}")
            
            elif choice == "2":
                # Testar chat simples
                message = input("Digite sua mensagem: ")
                print("\nEnviando tarefa 'chat'...")
                
                response = await client.send_task("chat", {"message": message})
                task_id = response.get("task_id")
                
                print(f"Tarefa criada com ID: {task_id}")
                
                result = await client.wait_for_task_completion(task_id)
                if result.get("status") == "completed":
                    print(f"\nResposta: {result.get('result', {}).get('response')}")
                else:
                    print(f"\nTarefa não completada. Status: {result.get('status')}")
                    print(f"Detalhes: {json.dumps(result, indent=2)}")
            
            elif choice == "3":
                # Testar chat com múltiplos turnos
                print("\nTestando conversa com múltiplos turnos (pergunte sobre cor favorita)")
                message = input("Digite sua mensagem (ex: 'Qual é a sua cor favorita?'): ")
                print("\nEnviando tarefa 'chat'...")
                
                response = await client.send_task("chat", {"message": message})
                task_id = response.get("task_id")
                
                print(f"Tarefa criada com ID: {task_id}")
                
                # Aguardar primeira resposta
                result = await client.wait_for_task_completion(task_id)
                
                # Verificar se entrada adicional é necessária
                if result.get("status") == "input-required":
                    print(f"\nEntrada adicional necessária: {result.get('required_input', {}).get('description')}")
                    color = input("Digite sua cor favorita: ")
                    
                    # Fornecer entrada adicional
                    print("\nEnviando resposta...")
                    response = await client.send_task("chat", {"color": color}, task_id)
                    
                    # Aguardar resposta final
                    result = await client.wait_for_task_completion(task_id)
                
                if result.get("status") == "completed":
                    print(f"\nResposta final: {result.get('result', {}).get('response')}")
                else:
                    print(f"\nTarefa não completada. Status: {result.get('status')}")
                    print(f"Detalhes: {json.dumps(result, indent=2)}")
            
            elif choice == "4":
                # Testar calculate
                print("\nTestando capacidade 'calculate'")
                operation = input("Operação (add, subtract, multiply, divide): ")
                
                try:
                    a = float(input("Primeiro número: "))
                    b = float(input("Segundo número: "))
                except ValueError:
                    print("Erro: Por favor, insira números válidos")
                    continue
                
                print("\nEnviando tarefa 'calculate'...")
                
                response = await client.send_task("calculate", {
                    "operation": operation,
                    "a": a,
                    "b": b
                })
                task_id = response.get("task_id")
                
                print(f"Tarefa criada com ID: {task_id}")
                
                result = await client.wait_for_task_completion(task_id)
                if result.get("status") == "completed":
                    r = result.get('result', {})
                    if "error" in r:
                        print(f"\nErro: {r.get('error')}")
                    else:
                        print(f"\nResultado: {r.get('result')}")
                        print(f"Operação: {a} {operation} {b} = {r.get('result')}")
                else:
                    print(f"\nTarefa não completada. Status: {result.get('status')}")
                    print(f"Detalhes: {json.dumps(result, indent=2)}")
            
            elif choice == "5":
                print("Saindo...")
                break
            
            else:
                print("Opção inválida. Por favor, escolha uma opção de 1 a 5.")


if __name__ == "__main__":
    print("Cliente A2A Hello World")
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário")
    except Exception as e:
        logger.exception("Erro não tratado")
        print(f"\nErro: {e}") 
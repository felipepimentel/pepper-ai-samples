#!/usr/bin/env python
"""
Exemplo básico de servidor A2A (Agent-to-Agent).

Este exemplo demonstra a implementação de um agente compatível
com o protocolo A2A, oferecendo capacidades básicas.
"""

import asyncio
import logging
import sys
import os

# Adicionar o diretório principal ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a import create_a2a_server

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Criar um servidor A2A
a2a = create_a2a_server(
    name="Hello World A2A Agent",
    description="Um agente A2A básico que demonstra as capacidades fundamentais do protocolo",
    version="0.1.0"
)

# Habilitar CORS para uso em navegadores
a2a.enable_cors()

# Definir uma capacidade simples de saudação
@a2a.capability(
    name="greet",
    description="Cumprimenta uma pessoa pelo nome",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Nome da pessoa"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Mensagem de saudação"}
        }
    }
)
async def greet(data):
    """Manipulador para a capacidade 'greet'."""
    logger.info(f"Recebida solicitação de saudação: {data}")
    input_data = data.get("input", {})
    name = input_data.get("name", "Mundo")
    return {"message": f"Olá, {name}! Bem-vindo ao mundo A2A."}

# Definir uma capacidade que demonstra interação em múltiplos turnos
@a2a.capability(
    name="chat",
    description="Conversa com o agente, demonstrando interação em múltiplos turnos",
    input_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Mensagem do usuário"},
            "color": {"type": "string", "description": "Cor favorita do usuário"}
        }
    }
)
async def chat(data):
    """Manipulador para a capacidade 'chat'."""
    logger.info(f"Recebida solicitação de chat: {data}")
    task_id = data.get("task_id")
    input_data = data.get("input", {})
    
    # Verificar se temos uma mensagem
    if "message" in input_data:
        message = input_data["message"]
        
        # Perguntar sobre a cor favorita se mencionada na mensagem
        if "cor favorita" in message.lower() or "cor preferida" in message.lower():
            logger.info(f"Solicitando cor favorita para task_id {task_id}")
            a2a.require_input(
                task_id=task_id,
                description="Por favor, compartilhe sua cor favorita",
                schema={
                    "type": "object",
                    "properties": {
                        "color": {"type": "string", "description": "Sua cor favorita"}
                    }
                }
            )
            return None  # Será atualizado quando o input for fornecido
        
        # Resposta normal para outras mensagens
        return {"response": f"Você disse: '{message}'. Como posso ajudar você hoje?"}
    
    # Processar a cor favorita se fornecida
    elif "color" in input_data:
        color = input_data["color"]
        logger.info(f"Cor favorita recebida: {color}")
        return {"response": f"{color} é uma cor linda! Pessoalmente, eu gosto de azul."}
    
    # Resposta padrão
    else:
        return {"response": "Olá! Como posso ajudar você hoje?"}

# Definir uma capacidade para calcular
@a2a.capability(
    name="calculate",
    description="Realiza cálculos matemáticos simples",
    input_schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "description": "Operação (add, subtract, multiply, divide)"},
            "a": {"type": "number", "description": "Primeiro número"},
            "b": {"type": "number", "description": "Segundo número"}
        },
        "required": ["operation", "a", "b"]
    }
)
async def calculate(data):
    """Manipulador para a capacidade 'calculate'."""
    logger.info(f"Recebida solicitação de cálculo: {data}")
    input_data = data.get("input", {})
    
    operation = input_data.get("operation")
    a = input_data.get("a")
    b = input_data.get("b")
    
    if None in (operation, a, b):
        return {"error": "Parâmetros de operação incompletos"}
    
    result = None
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "Divisão por zero não é permitida"}
        result = a / b
    else:
        return {"error": f"Operação desconhecida: {operation}"}
    
    return {
        "result": result,
        "operation": operation,
        "a": a,
        "b": b
    }

if __name__ == "__main__":
    logger.info("Iniciando servidor A2A Hello World")
    a2a.run(port=8080) 
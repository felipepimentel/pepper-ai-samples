#!/usr/bin/env python
"""
Hello World MCP Server Example
Demonstra como criar um servidor MCP simples usando as utilidades comuns.
"""

import json
from datetime import datetime
from typing import List, Optional

from pepperpymcp import AssistantMessage, Message, SimpleMCP, UserMessage

# Cria o servidor MCP
mcp = SimpleMCP("Hello World", "Um exemplo simples de servidor MCP")


# Adiciona ferramentas MCP
@mcp.tool()
def greet(name: str = "World") -> str:
    """Retorna uma saudação amigável"""
    return f"Hello, {name}!"


@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Realiza operações aritméticas básicas

    Args:
        operation: Um dos valores "add", "subtract", "multiply", "divide"
        a: Primeiro número
        b: Segundo número
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Não é possível dividir por zero")
        return a / b
    else:
        raise ValueError(f"Operação desconhecida: {operation}")


# Adiciona recursos
@mcp.resource("quote://{category}")
def get_quote(category: str) -> str:
    """Obtém uma citação inspiradora por categoria"""
    quotes = json.loads(mcp.get_template("quotes"))

    if category in quotes:
        return quotes[category]
    return "Nenhuma citação encontrada para essa categoria."


# Adiciona prompts
@mcp.prompt()
async def welcome_email(name: str, content: Optional[str] = None) -> str:
    """Gera um email de boas-vindas formal"""
    if not content:
        content = "Bem-vindo(a) ao nosso serviço! Estamos muito felizes em tê-lo(a) conosco."

    return mcp.get_template("welcome_email").format(name=name, content=content)


@mcp.prompt()
async def quick_note(name: str, message: str, sender: Optional[str] = "Anônimo") -> str:
    """Gera uma nota rápida e informal"""
    return mcp.get_template("quick_note").format(name=name, message=message, sender=sender)


@mcp.prompt()
async def start_conversation(name: str) -> List[Message]:
    """Inicia uma conversa amigável com o usuário"""
    hour = datetime.now().hour

    if hour < 12:
        time = "bom dia"
    elif hour < 18:
        time = "boa tarde"
    else:
        time = "boa noite"

    return [
        AssistantMessage(f"Olá {name}, {time}! Como posso ajudar?"),
        UserMessage("Estou aqui para aprender sobre MCP!"),
        AssistantMessage("Ótimo! Vou te ajudar a entender como funciona. Por onde quer começar?"),
    ]


# Adiciona endpoint HTTP personalizado
@mcp.http_endpoint("/greeting/{name}")
async def get_greeting(name: str):
    """Endpoint HTTP personalizado para saudação"""
    return {"message": f"Olá, {name}!"}


if __name__ == "__main__":
    mcp.run()

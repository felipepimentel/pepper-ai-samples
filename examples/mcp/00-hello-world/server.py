#!/usr/bin/env python
"""
Hello World MCP Server Example
Demonstra como criar um servidor MCP simples usando o SDK oficial com extensões.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from pepperpymcp import PepperFastMCP

mcp = PepperFastMCP("Hello World", description="Um exemplo simples de servidor MCP")


# Adiciona ferramentas MCP
@mcp.tool()
def greet(name: str = "World") -> str:
    """Retorna uma saudação personalizada com o nome fornecido.

    Use esta ferramenta quando precisar criar uma saudação simples e amigável para um usuário.

    Exemplos de uso:
    - Para uma saudação genérica: greet()  →  "Hello, World!"
    - Para uma saudação personalizada: greet("Maria")  →  "Hello, Maria!"

    Args:
        name: O nome da pessoa a ser saudada (padrão: "World")

    Returns:
        Uma string contendo a saudação
    """
    return f"Hello, {name}!"


@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Realiza operações aritméticas básicas entre dois números.

    Use esta ferramenta quando o usuário solicitar cálculos matemáticos como adição,
    subtração, multiplicação ou divisão de dois valores.

    Exemplos de uso:
    - Para somar: calculate("add", 5, 3)  →  8
    - Para subtrair: calculate("subtract", 10, 4)  →  6
    - Para multiplicar: calculate("multiply", 2, 5)  →  10
    - Para dividir: calculate("divide", 20, 5)  →  4

    Args:
        operation: O tipo de operação a ser realizada ("add", "subtract", "multiply", "divide")
        a: O primeiro número na operação
        b: O segundo número na operação

    Returns:
        O resultado da operação como um valor de ponto flutuante

    Raises:
        ValueError: Se a operação for desconhecida ou se tentar dividir por zero
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
    """Obtém uma citação inspiradora com base na categoria solicitada.

    Use este recurso quando precisar de uma citação inspiradora específica para uma categoria.
    O recurso pode ser acessado via URI no formato quote://{category}.

    Categorias disponíveis incluem: motivação, sucesso, vida, trabalho, etc.
    (dependendo do que estiver definido no template "quotes")

    Exemplos de uso:
    - quote://motivação  →  Retorna uma citação motivacional
    - quote://sucesso  →  Retorna uma citação sobre sucesso

    Args:
        category: A categoria da citação desejada

    Returns:
        Uma string contendo a citação ou uma mensagem indicando que a categoria não foi encontrada
    """
    quotes = json.loads(mcp.get_template("quotes"))

    if category in quotes:
        return quotes[category]
    return "Nenhuma citação encontrada para essa categoria."


# Adiciona prompts
@mcp.prompt()
async def welcome_email(name: str, content: Optional[str] = None) -> str:
    """Gera um email de boas-vindas formal personalizado para um novo usuário.

    Use este prompt quando precisar criar um email formal de boas-vindas para um novo
    usuário, cliente ou membro da equipe. O conteúdo pode ser personalizado ou usar
    o texto padrão de boas-vindas.

    Exemplos de uso:
    - welcome_email("João")  →  Email formal de boas-vindas para João
    - welcome_email("Maria", "Bem-vinda ao nosso programa de fidelidade!")  →  Email personalizado para Maria

    Args:
        name: Nome do destinatário do email
        content: Conteúdo personalizado do email (opcional). Se não fornecido,
                 será usado um texto padrão de boas-vindas.

    Returns:
        O conteúdo formatado do email de boas-vindas
    """
    if not content:
        content = "Bem-vindo(a) ao nosso serviço! Estamos muito felizes em tê-lo(a) conosco."

    return mcp.get_template("welcome_email").format(name=name, content=content)


@mcp.prompt()
async def quick_note(name: str, message: str, sender: Optional[str] = "Anônimo") -> str:
    """Gera uma nota rápida e informal para enviar a alguém.

    Use este prompt quando precisar criar uma mensagem curta e informal
    para enviar a alguém, como um lembrete, agradecimento ou aviso rápido.

    Exemplos de uso:
    - quick_note("Carlos", "Reunião amanhã às 10h", "Ana")  →  Nota de Ana para Carlos
    - quick_note("Equipe", "Não esqueçam do prazo de hoje!")  →  Nota de remetente anônimo para a equipe

    Args:
        name: Nome do destinatário da nota
        message: O conteúdo da mensagem a ser enviada
        sender: Nome do remetente (padrão: "Anônimo")

    Returns:
        A nota formatada pronta para envio
    """
    return mcp.get_template("quick_note").format(name=name, message=message, sender=sender)


@mcp.prompt()
async def start_conversation(name: str) -> list[Dict[str, Any]]:
    """Inicia uma conversa amigável e contextual com o usuário.

    Use este prompt quando precisar iniciar uma interação com um usuário
    de forma amigável e personalizada, adaptando a saudação ao momento do dia
    (bom dia, boa tarde ou boa noite).

    Exemplos de uso:
    - start_conversation("Paulo")  →  Inicia uma conversa adaptada ao horário atual com Paulo

    Args:
        name: Nome do usuário com quem iniciar a conversa

    Returns:
        Uma lista de mensagens formatadas para iniciar a conversa
    """
    hour = datetime.now().hour

    if hour < 12:
        time = "bom dia"
    elif hour < 18:
        time = "boa tarde"
    else:
        time = "boa noite"

    return [
        mcp.create_assistant_message(f"Olá {name}, {time}! Como posso ajudar?"),
        mcp.create_user_message("Estou aqui para aprender sobre MCP!"),
        mcp.create_assistant_message("Ótimo! Vou te ajudar a entender como funciona. Por onde quer começar?"),
    ]


# Adiciona endpoint HTTP personalizado
@mcp.http_endpoint("/greeting/{name}")
async def get_greeting(name: str):
    """Endpoint HTTP personalizado para saudação"""
    return {"message": f"Olá, {name}!"}


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Hello World MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use stdin/stdout for MCP transport")
    parser.add_argument("--http", action="store_true", help="Use HTTP for MCP transport (default)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Detectar modo automaticamente se não estiver especificado
    if args.stdio:
        print("Starting Hello World MCP Server in STDIO mode", file=sys.stderr)
        mcp.run(transport_mode="stdio", debug=args.debug)
    else:
        print("Starting Hello World MCP Server in HTTP mode", file=sys.stderr)
        mcp.run(transport_mode="http", debug=args.debug)

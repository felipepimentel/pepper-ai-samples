#!/usr/bin/env python
"""
Exemplo de uso do cliente MCP adaptativo.
"""

import asyncio
import json
from adaptive_client import AdaptiveMCPClient

async def main():
    # Criar cliente adaptativo
    client = AdaptiveMCPClient()
    
    try:
        # Inicializar - vai descobrir e conectar aos servidores disponíveis
        print("\nIniciando descoberta de servidores...")
        await client.initialize()
        
        # Mostrar servidor atual
        current = client.get_current_server()
        print(f"\nServidor atual: {current}")
        
        # Listar ferramentas no servidor atual
        print("\nFerramentas disponíveis no servidor atual:")
        tools = await client.list_tools()
        print(json.dumps(tools, indent=2))
        
        # Exemplo: chamar ferramenta de clima
        if "get_current_weather" in [t["name"] for t in tools]:
            print("\nObtendo clima para São Paulo...")
            weather = await client.call_tool("get_current_weather", location="São Paulo")
            print(json.dumps(weather, indent=2))
        
        # Listar todos os servidores disponíveis
        servers = client.discovery.list_servers()
        print(f"\nTodos os servidores disponíveis: {servers}")
        
        # Mudar para outro servidor se houver
        if len(servers) > 1:
            other_server = [s for s in servers if s != current][0]
            print(f"\nMudando para servidor: {other_server}")
            client.set_current_server(other_server)
            
            # Listar ferramentas no novo servidor
            print("\nFerramentas disponíveis no novo servidor:")
            tools = await client.list_tools()
            print(json.dumps(tools, indent=2))
            
            # Exemplo: chamar ferramenta de busca se disponível
            if "web_search" in [t["name"] for t in tools]:
                print("\nRealizando busca...")
                results = await client.call_tool("web_search", query="Python MCP protocol")
                print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
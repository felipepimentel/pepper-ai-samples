# Integração A2A+MCP

Este exemplo demonstra como integrar os protocolos A2A (Agent-to-Agent) e MCP (Model Context Protocol), permitindo que agentes de diferentes tipos interajam e compartilhem capacidades.

## Conceito

Este exemplo implementa:

1. **Ponte entre Protocolos**: Uma camada intermediária que permite:
   - Agentes A2A acessarem ferramentas MCP
   - Servidores MCP acessarem capacidades A2A

2. **Servidores Simultâneos**:
   - Servidor A2A na porta 8080
   - Servidor MCP na porta 8000

3. **Capacidades Compartilhadas**:
   - Ferramentas MCP expostas como capacidades A2A
   - Capacidades A2A expostas como ferramentas MCP

## Arquitetura

```
┌───────────────┐       ┌─────────────────┐
│               │       │                 │
│  Cliente A2A  │◄─────►│  Servidor A2A   │
│               │       │    (8080)       │
└───────────────┘       └────────┬────────┘
                                 │
                         ┌───────▼───────┐
                         │               │
                         │  A2A-MCP      │
                         │  Bridge       │
                         │               │
                         └───────┬───────┘
                                 │
┌───────────────┐       ┌────────▼────────┐
│               │       │                 │
│  Cliente MCP  │◄─────►│  Servidor MCP   │
│               │       │    (8000)       │
└───────────────┘       └─────────────────┘
```

## Funcionalidades

### Capacidades A2A Nativas
- `summarize`: Cria um resumo de um texto

### Ferramentas MCP Nativas
- `weather`: Obtém a previsão do tempo para uma localização
- Recurso `info://{topic}`: Fornece informações sobre tópicos

### Capacidades A2A derivadas do MCP
- `mcp_weather`: Acessa a ferramenta MCP de previsão do tempo

### Ferramentas MCP derivadas do A2A
- `a2a_summarize`: Acessa a capacidade A2A de resumo

## Requisitos

- Python 3.10+
- Dependências listadas em `requirements.txt`
- Bibliotecas `pepperpya2a` e `pepperpymcp` (diretório libs)

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar as bibliotecas (modo desenvolvimento)
pip install -e ../../libs/pepperpya2a
pip install -e ../../libs/pepperpymcp
```

## Execução

```bash
# Iniciar os servidores
python server.py
```

Isto iniciará:
- Servidor A2A na porta 8080
- Servidor MCP na porta 8000

## Teste

### Teste via A2A
Você pode usar o cliente A2A do exemplo hello-world para testar:

```bash
cd ../00-a2a-hello-world
python client.py
```

Altere a URL para `http://localhost:8080` e teste a capacidade `summarize` e também a capacidade MCP exposta `mcp_weather`.

### Teste via MCP
Você pode usar qualquer cliente MCP para testar a ferramenta `weather` diretamente ou a ferramenta A2A exposta `a2a_summarize`.

### URLs Importantes

- A2A Agent Card: http://localhost:8080/.well-known/agent.json
- MCP Server Info: http://localhost:8000/info

## Próximos Passos

Após este exemplo, você pode:

1. Implementar sistemas multi-agente mais complexos combinando A2A e MCP
2. Criar agentes especializados que delegam tarefas entre diferentes protocolos
3. Explorar a integração com outros sistemas e APIs externas 
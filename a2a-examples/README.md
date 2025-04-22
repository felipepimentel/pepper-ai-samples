# A2A Examples

This directory contains examples of Agent-to-Agent (A2A) protocol implementations.

## What is A2A?

A2A (Agent-to-Agent) is a protocol designed to enable AI agents to communicate directly with each other, facilitating multi-agent collaboration and complex task coordination. The protocol allows agents to:

- Exchange structured messages
- Coordinate on tasks
- Share knowledge and resources
- Negotiate and collaborate

## Examples

- **[00-a2a-hello-world](00-a2a-hello-world/)**: Basic A2A agent that demonstrates core protocol functionality
- **[01-a2a-mcp-integration](01-a2a-mcp-integration/)**: Integration between A2A and MCP protocols
- **15-a2a-web**: Web-based agent-to-agent interaction example demonstrating how agents can communicate through browser interfaces

## Getting Started

Each example directory contains:
- Source code for the implementation
- Documentation on how to run the example
- Configuration files
- Client implementations where applicable

## Requirements

- Python 3.10+
- Web browser (for web-based examples)
- See individual example READMEs for specific requirements

## Progressive Learning Path

The examples in this directory follow a progressive learning path:

1. **Basic A2A (00-a2a-hello-world)**:
   - Core A2A protocol concepts
   - Task handling and management
   - Agent discovery
   - Multi-turn interactions

2. **Protocol Integration (01-a2a-mcp-integration)**:
   - Bridging A2A and MCP protocols
   - Exposing MCP tools as A2A capabilities
   - Exposing A2A capabilities as MCP tools
   - Running hybrid agent systems

3. **Web-based A2A (15-a2a-web)**:
   - Web interface for A2A agents
   - Browser-based interactions
   - Extended functionality

## O que é A2A?

A2A (Agent-to-Agent Protocol) é um protocolo aberto desenvolvido pelo Google que permite que agentes de IA autônomos se comuniquem e colaborem entre si, independentemente das estruturas subjacentes ou fornecedores.

Características principais do protocolo A2A:
- **Comunicação interoperável**: Conecta agentes construídos em diferentes frameworks
- **Descoberta de capacidades**: Permite que agentes descubram recursos de outros agentes
- **Negociação de experiência do usuário**: Agentes podem negociar como interagirão com os usuários
- **Gerenciamento de tarefas e estados**: Coordenação de estados e progresso de tarefas
- **Suporte multimodal**: Comunicação usando texto, formulários, áudio/vídeo
- **Colaboração segura**: Implementação de mecanismos de segurança para comunicação entre agentes

## Exemplos Disponíveis

- **[15-a2a-web](15-a2a-web/)**: Agente de busca na web com suporte A2A e integração com MCP

## Como Executar os Exemplos

Cada exemplo possui seu próprio README com instruções específicas, mas o padrão geral é:

```bash
# Navegar para o diretório do exemplo
cd 15-a2a-web

# Criar ambiente virtual
uv venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
uv pip install -r requirements.txt

# Executar o servidor do agente
python server.py

# Em outro terminal, executar o cliente
python client.py
```

## A2A vs MCP: Comparação de Protocolos

| Característica | A2A | MCP |
|----------------|-----|-----|
| Foco principal | Comunicação entre agentes | Comunicação agente-ferramentas |
| Descoberta | Cartão do agente (Agent Card) | Listagem de ferramentas |
| Comunicação | Bidirecional entre agentes | Unidirecional agente→ferramenta |
| Estado | Gerenciamento de estado de tarefas | Sem estado entre chamadas |
| Formatos | Multimodal (texto, áudio, vídeo, formulários) | Principalmente estruturado |
| Caso de uso | Sistemas multi-agente colaborativos | Agentes usando ferramentas externas |

## Integração A2A/MCP

Os exemplos nesta pasta também demonstram como integrar os protocolos A2A e MCP, permitindo que:
- Agentes A2A possam acessar ferramentas MCP
- Agentes MCP possam se comunicar com agentes A2A
- Sistemas híbridos possam aproveitar o melhor dos dois protocolos

## Recursos

- [Documentação oficial A2A](https://google.github.io/A2A/)
- [Repositório A2A no GitHub](https://github.com/google/A2A)
- [Blog post A2A](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) 
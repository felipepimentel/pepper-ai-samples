# A2A Basics Example

Este exemplo demonstra os conceitos básicos do protocolo A2A (Agent-to-Agent) através de um agente meteorológico simples.

## Visão Geral

O exemplo implementa um agente A2A básico que fornece informações meteorológicas para diferentes cidades. Ele demonstra:

- Criação e exposição de um Agent Card para descoberta
- Gerenciamento de tarefas (tasks)
- Processamento de mensagens simples
- Comunicação cliente-servidor através do protocolo A2A

## Componentes Principais

- **Agent Card**: Metadados que descrevem o agente e suas capacidades
- **Endpoints A2A**: Implementação dos endpoints básicos do protocolo
- **Processador de Mensagens**: Lógica para responder a consultas sobre o clima
- **Cliente A2A**: Cliente interativo para conversar com o agente

## Pré-requisitos

- Python 3.10 ou superior
- Gerenciador de pacotes uv

## Instalação

```bash
# Navegue até este diretório
cd a2a-examples/03-a2a-basics

# Crie um ambiente virtual com uv
uv venv

# Ative o ambiente virtual
# No Linux/macOS:
source .venv/bin/activate
# No Windows:
# .venv\Scripts\activate

# Instale as dependências
uv pip install -e .
```

## Executando o Exemplo

1. Inicie o servidor A2A:

```bash
# No diretório do exemplo
python src/server.py
```

2. Em outro terminal, execute o cliente:

```bash
# Ative o ambiente virtual
source .venv/bin/activate

# Execute o cliente para interagir com o agente
python src/client.py
```

3. Converse com o agente fazendo perguntas sobre o clima em diferentes cidades.

Exemplos de perguntas:
- "Como está o tempo em São Paulo?"
- "Como está o tempo em Rio de Janeiro?"
- "Como está o tempo em Brasília?"
- "Como está o tempo em Curitiba?"

## Conceitos Demonstrados

### 1. Agent Card

O Agent Card é um documento JSON exposto em `/.well-known/agent.json` que descreve o agente e suas capacidades:

```json
{
  "name": "Assistente Meteorológico",
  "description": "Fornece informações sobre clima e previsões do tempo",
  "url": "http://localhost:8000",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "previsao_tempo",
      "name": "Previsão do Tempo",
      "description": "Fornece previsão meteorológica para diferentes cidades"
    },
    ...
  ]
}
```

### 2. Gerenciamento de Tarefas

O protocolo A2A gerencia a comunicação através de tarefas (tasks) que passam por diferentes estados:

- `submitted`: Tarefa recém-criada
- `working`: Agente está processando a tarefa
- `input_required`: Agente precisa de mais informações
- `completed`: Tarefa concluída com sucesso
- `failed`: Erro no processamento da tarefa

### 3. Mensagens e Respostas

As mensagens no protocolo A2A são compostas por partes e podem incluir texto, dados estruturados ou arquivos:

```json
{
  "role": "user",
  "parts": [
    {
      "type": "text",
      "text": "Como está o tempo em São Paulo?"
    }
  ]
}
```

## Próximos Passos

Após entender este exemplo básico, explore exemplos mais avançados:

- Integração com APIs reais de clima
- Interações em múltiplos turnos
- Geração de artefatos estruturados
- Comunicação entre múltiplos agentes 
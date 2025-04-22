# A2A Hello World

Este exemplo demonstra a implementação básica de um agente compatível com o protocolo A2A (Agent-to-Agent).

## O que é A2A?

A2A (Agent-to-Agent) é um protocolo aberto desenvolvido pelo Google que permite que agentes de IA autônomos se comuniquem e colaborem entre si, independentemente das estruturas subjacentes ou fornecedores.

## Funcionalidades Demonstradas

Este exemplo implementa:

1. **Descoberta de Agente**: Endpoint `.well-known/agent.json` para anunciar capacidades
2. **Capacidades Básicas**:
   - `greet`: Cumprimentar usuário pelo nome
   - `chat`: Conversa com suporte a múltiplos turnos
   - `calculate`: Realizar operações matemáticas simples
3. **Gestão de Estado**: Demonstração de gerenciamento de estado de tarefas
4. **Interação Multi-turno**: Exemplo de como solicitar informações adicionais do cliente

## Requisitos

- Python 3.10+
- Dependências listadas em `requirements.txt`

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar a biblioteca pepperpya2a (modo desenvolvimento)
pip install -e ../../libs/pepperpya2a
```

## Execução

### Servidor A2A

```bash
# Iniciar o servidor
python server.py
```

O servidor A2A estará acessível em `http://localhost:8080`.

### Cliente de Teste

```bash
# Em outro terminal
python client.py
```

O cliente interativo permite testar as diferentes capacidades do agente:
1. Testar capacidade 'greet'
2. Testar capacidade 'chat' (conversa simples)
3. Testar capacidade 'chat' (múltiplos turnos)
4. Testar capacidade 'calculate'

## Endpoints A2A

- `/.well-known/agent.json`: Descoberta do agente (Agent Card)
- `/tasks/send`: Enviar uma nova tarefa ou atualizar uma existente
- `/tasks/get`: Obter status da tarefa
- `/tasks/cancel`: Cancelar uma tarefa

## Estados de Tarefa

- `in-progress`: Tarefa sendo processada
- `completed`: Tarefa concluída com sucesso
- `error`: Erro durante o processamento
- `input-required`: Necessita de entrada adicional do cliente
- `canceled`: Tarefa cancelada

## Próximos Passos

Após entender este exemplo básico, você pode explorar exemplos mais avançados:

1. Implementação de agentes mais complexos com múltiplas capacidades
2. Integração com o protocolo MCP para uso de ferramentas externas
3. Desenvolvimento de sistemas multi-agentes usando A2A 
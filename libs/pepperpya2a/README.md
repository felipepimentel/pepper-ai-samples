# PepperPyA2A

Uma implementação simples do protocolo A2A (Agent-to-Agent) com uma API baseada em decoradores semelhante ao FastAPI.

## Instalação

```bash
pip install -e ./libs/pepperpya2a
```

## Uso Básico

```python
from pepperpya2a import create_a2a_server

# Criar um servidor A2A
a2a = create_a2a_server(
    name="Meu Agente A2A",
    description="Um agente A2A simples que pode cumprimentar pessoas",
    version="1.0.0"
)

# Definir uma capacidade usando o decorador
@a2a.capability(
    name="greet",
    description="Cumprimenta uma pessoa pelo nome",
    input_schema={"name": {"type": "string", "description": "Nome da pessoa"}}
)
async def greet(data):
    name = data.get("input", {}).get("name", "Mundo")
    return {"message": f"Olá, {name}!"}

# Interação em múltiplos turnos
@a2a.capability(
    name="chat",
    description="Conversa com o agente"
)
async def chat(data):
    task_id = data.get("task_id")
    input_data = data.get("input", {})
    
    if "message" in input_data:
        message = input_data["message"]
        
        if "cor favorita" in message.lower():
            # Solicitar input adicional
            a2a.require_input(
                task_id=task_id,
                description="Por favor, compartilhe sua cor favorita",
                schema={"color": {"type": "string", "description": "Sua cor favorita"}}
            )
            return None  # Será atualizado quando o input for fornecido
        
        return {"response": f"Você disse: {message}. Como posso ajudar?"}
    elif "color" in input_data:
        # Processando o input subsequente
        color = input_data["color"]
        return {"response": f"{color} é uma cor linda! Eu gosto de azul."}
    else:
        return {"response": "Como posso ajudar hoje?"}

# Executar o servidor
if __name__ == "__main__":
    # Opcional: habilitar CORS para uso no navegador
    a2a.enable_cors()
    
    # Iniciar o servidor
    a2a.run()
```

## Endpoints do Protocolo A2A

- `/.well-known/agent.json` - Descoberta do Agente (Agent Card)
- `/tasks/send` - Enviar uma nova tarefa ou atualizar uma existente
- `/tasks/get` - Obter status da tarefa
- `/tasks/cancel` - Cancelar uma tarefa

## Características

- API baseada em decoradores para definir capacidades do agente
- Suporte para interações em múltiplos turnos com estados `input-required`
- Gerenciamento automático do ciclo de vida da tarefa
- Integração direta com FastAPI para desenvolvimento e extensibilidade

## Integração com MCP

Esta biblioteca pode ser combinada com `pepperpymcp` para criar agentes que suportam ambos os protocolos A2A e MCP, permitindo:

- Agentes A2A acessarem ferramentas MCP
- Comunicação entre diferentes tipos de agentes
- Sistemas híbridos que aproveitam o melhor dos dois protocolos 
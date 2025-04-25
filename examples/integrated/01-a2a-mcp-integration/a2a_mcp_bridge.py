"""
Módulo de ponte entre protocolos A2A e MCP.

Este módulo permite que agentes A2A acessem ferramentas MCP e
que agentes MCP se comuniquem com agentes A2A.
"""

import asyncio
import inspect
import logging

from libs.pepperpya2a import PepperA2A
from libs.pepperpymcp import PepperFastMCP

logger = logging.getLogger(__name__)


class A2AMCPBridge:
    """
    Ponte entre os protocolos A2A e MCP.

    Esta classe permite que um agente A2A use ferramentas MCP e
    que um servidor MCP acesse capacidades de agentes A2A.
    """

    def __init__(self, a2a_server: PepperA2A, mcp_server: PepperFastMCP):
        """
        Inicializa a ponte entre A2A e MCP.

        Args:
            a2a_server: Instância do servidor A2A
            mcp_server: Instância do servidor MCP
        """
        self.a2a = a2a_server
        self.mcp = mcp_server

        # Registrar ferramentas MCP como capacidades A2A
        self._register_mcp_tools_as_a2a_capabilities()

        # Registrar capacidades A2A como ferramentas MCP
        self._register_a2a_capabilities_as_mcp_tools()

    def _register_mcp_tools_as_a2a_capabilities(self):
        """Registrar ferramentas MCP como capacidades A2A."""
        # Obter todas as ferramentas MCP
        mcp_tools = getattr(self.mcp, "_mcp", self.mcp).get_tools()

        for tool_name, tool_info in mcp_tools.items():
            logger.info(f"Registrando ferramenta MCP '{tool_name}' como capacidade A2A")

            # Criar um wrapper para a ferramenta MCP
            async def mcp_tool_wrapper(data, _tool_name=tool_name):
                """Wrapper para chamar uma ferramenta MCP a partir do A2A."""
                logger.info(f"Chamando ferramenta MCP '{_tool_name}' via A2A")

                try:
                    # Obter a ferramenta do MCP
                    tool = getattr(self.mcp, "_mcp", self.mcp).tools[_tool_name]

                    # Extrair input da tarefa A2A
                    input_data = data.get("input", {})

                    # Verificar assinatura da ferramenta
                    sig = inspect.signature(tool)

                    # Se a ferramenta espera um parâmetro 'ctx'
                    if "ctx" in sig.parameters:
                        # Criar um contexto fake
                        ctx = {
                            "client_id": "a2a_bridge",
                            "task_id": data.get("task_id"),
                        }
                        result = await tool(ctx, **input_data)
                    else:
                        # Chamar diretamente com os parâmetros
                        result = await tool(**input_data)

                    return {"mcp_result": result}
                except Exception as e:
                    logger.exception(f"Erro ao chamar ferramenta MCP '{_tool_name}'")
                    return {"error": str(e)}

            # Registrar a capacidade A2A
            self.a2a._capabilities.append(
                {
                    "name": f"mcp_{tool_name}",
                    "description": f"MCP Tool: {tool_info.get('description', tool_name)}",
                    "input_schema": tool_info.get("parameters", {}),
                }
            )

            # Registrar o handler
            self.a2a._task_handlers[f"mcp_{tool_name}"] = mcp_tool_wrapper

    def _register_a2a_capabilities_as_mcp_tools(self):
        """Registrar capacidades A2A como ferramentas MCP."""
        # Obter todas as capacidades A2A
        a2a_capabilities = self.a2a._capabilities

        for capability in a2a_capabilities:
            capability_name = capability.get("name")

            # Pular capacidades que já são wrappers de ferramentas MCP
            if capability_name.startswith("mcp_"):
                continue

            logger.info(
                f"Registrando capacidade A2A '{capability_name}' como ferramenta MCP"
            )

            # Criar um wrapper para a capacidade A2A
            async def a2a_capability_wrapper(ctx=None, **kwargs):
                """Wrapper para chamar uma capacidade A2A a partir do MCP."""
                nonlocal capability_name

                logger.info(f"Chamando capacidade A2A '{capability_name}' via MCP")

                try:
                    # Criar uma tarefa A2A
                    task_id = f"mcp_{ctx['client_id'] if ctx else 'unknown'}_{asyncio.get_event_loop().time()}"

                    # Enviar a tarefa ao A2A
                    handler = self.a2a._task_handlers.get(capability_name)
                    if not handler:
                        return {
                            "error": f"Capacidade A2A '{capability_name}' não encontrada"
                        }

                    # Preparar dados da tarefa
                    task_data = {
                        "task_id": task_id,
                        "skill": capability_name,
                        "input": kwargs,
                    }

                    # Registrar a tarefa
                    current_time = asyncio.get_event_loop().time()
                    self.a2a._tasks[task_id] = {
                        "task_id": task_id,
                        "status": "in-progress",
                        "skill": capability_name,
                        "input": kwargs,
                        "result": None,
                        "error": None,
                        "required_input": None,
                        "created_at": current_time,
                        "updated_at": current_time,
                    }

                    # Executar o handler diretamente
                    result = await handler(task_data)

                    # Atualizar o status da tarefa
                    if result is None:
                        # Se o handler retornou None, verificar se foi solicitado input adicional
                        if self.a2a._tasks[task_id]["status"] == "input-required":
                            required_input = self.a2a._tasks[task_id]["required_input"]
                            return {
                                "status": "input-required",
                                "message": required_input.get(
                                    "description", "Input adicional necessário"
                                ),
                                "schema": required_input.get("schema", {}),
                            }
                    else:
                        # Atualizar com o resultado
                        self.a2a._tasks[task_id]["status"] = "completed"
                        self.a2a._tasks[task_id]["result"] = result

                    return result
                except Exception as e:
                    logger.exception(
                        f"Erro ao chamar capacidade A2A '{capability_name}'"
                    )
                    return {"error": str(e)}

            # Registrar a ferramenta MCP
            self.mcp._mcp.tool(
                name=f"a2a_{capability_name}",
                description=capability.get("description", ""),
            )(a2a_capability_wrapper)


# Função de fábrica para criar uma ponte A2A-MCP
def create_a2a_mcp_bridge(
    a2a_server: PepperA2A, mcp_server: PepperFastMCP
) -> A2AMCPBridge:
    """
    Cria uma ponte entre servidores A2A e MCP.

    Args:
        a2a_server: Instância do servidor A2A
        mcp_server: Instância do servidor MCP

    Returns:
        Instância da ponte A2A-MCP
    """
    return A2AMCPBridge(a2a_server, mcp_server)

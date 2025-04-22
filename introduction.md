# Documentação do Protocolo MCP (Model Context Protocol)

## 1. Introdução ao Model Context Protocol

O Model Context Protocol (MCP) é um protocolo aberto que padroniza a comunicação entre aplicações de IA e fontes externas de dados e ferramentas. O MCP permite que modelos de linguagem (LLMs) como Claude possam interagir com arquivos locais, bancos de dados, APIs e ferramentas personalizadas de forma segura e estruturada.

### 1.1 Conceitos Básicos

O protocolo MCP utiliza três componentes principais:

- **Recursos (Resources)**: Dados como arquivos, conteúdo de APIs ou informações de bancos de dados
- **Ferramentas (Tools)**: Funções que podem ser chamadas pelo LLM para executar tarefas específicas
- **Prompts**: Templates reutilizáveis para geração de conteúdo personalizado

### 1.2 Arquitetura

A arquitetura MCP é baseada em um modelo cliente-servidor:

- **Host**: Aplicação como Claude Desktop ou IDE que inicia conexões
- **Cliente**: Conector dentro do host que se comunica com os servidores
- **Servidor**: Serviço que fornece recursos, ferramentas e prompts

## 2. Exemplos de Servidores MCP

### 2.1 Hello World MCP Server

O servidor Hello World demonstra os conceitos fundamentais do MCP através de uma implementação simples:

```python
from pepperpymcp import PepperFastMCP

mcp = PepperFastMCP("Hello World", description="Servidor MCP de exemplo")

@mcp.tool()
def greet(name: str = "World") -> str:
    """Retorna uma saudação personalizada."""
    return f"Hello, {name}!"

# Inicia o servidor
if __name__ == "__main__":
    mcp.run()
```

#### 2.1.1 Ferramentas Implementadas

- **greet**: Retorna saudação personalizada com o nome fornecido
- **calculate**: Realiza operações matemáticas básicas
- Endpoints HTTP personalizados via FastAPI

#### 2.1.2 Recursos Disponíveis

- **quote://{category}**: Acessa citações inspiradoras por categoria

#### 2.1.3 Prompts Disponíveis

- **welcome_email**: Gera emails formais de boas-vindas
- **quick_note**: Cria notas informais rápidas
- **start_conversation**: Inicia diálogos contextuais com base na hora do dia

## 3. Servidores MCP Existentes e Como Usá-los

### 3.1 Servidores Oficiais

| Nome | Repositório | Descrição | Comando de Instalação |
|------|-------------|-----------|------------------------|
| Docker | github.com/ckreiling/mcp-server-docker | Gerencia contêineres, imagens e redes Docker | `npm install -g @mcp/server-docker` |
| Kubernetes | github.com/Flux159/mcp-server-kubernetes | Gerencia recursos Kubernetes | `npm install -g mcp-k8s` |
| Qdrant | github.com/qdrant/mcp-server-qdrant | Implementa memória vetorial com Qdrant | `pip install mcp-qdrant` |
| Obsidian | github.com/calclavia/mcp-obsidian | Acessa notas do Obsidian | `npm install -g mcp-obsidian` |
| Supabase | supabase.com/docs/guides/getting-started/mcp | Interage com bancos de dados Supabase | `npm install @supabase/mcp-server` |

### 3.2 Servidores Comunitários

| Nome | Repositório | Descrição | Comando de Instalação |
|------|-------------|-----------|------------------------|
| Linear | github.com/jerhadf/linear-mcp-server | Gerenciamento de projetos | `npm install -g linear-mcp-server` |
| Spotify | github.com/varunneal/spotify-mcp | Controle do Spotify | `npm install -g spotify-mcp` |
| Axiom | github.com/axiomhq/mcp-server-axiom | Análise de logs e métricas | `npm install @axiom/mcp-server` |
| E2B | github.com/e2b-dev/mcp-server | Execução de código em sandboxes | `npm install @e2b/mcp-server` |
| Snowflake | github.com/datawiz168/mcp-snowflake-service | Consultas em bancos Snowflake | `pip install mcp-snowflake` |

## 4. Como Configurar Servidores MCP

### 4.1 Configuração para Claude Desktop

Para configurar servidores MCP no Claude Desktop, crie ou edite o arquivo de configuração:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 4.2 Configuração para IDEs e Ambientes de Desenvolvimento

Para ambientes de desenvolvimento, como o VS Code com extensões compatíveis, utilize um arquivo `mcp.json` na raiz do projeto ou na pasta `.vscode/`.

## 5. Troubleshooting

### 5.1 Problemas Comuns

- **Erro de Conexão**: Verifique se o servidor está rodando e se o caminho está correto
- **Tempo de Resposta**: A primeira resposta pode levar até 30 segundos
- **Erros de Arquivo**: Certifique-se de que os caminhos dos arquivos estão corretos

### 5.2 Melhores Práticas

- Use docstrings detalhadas para cada ferramenta e recurso
- Implemente tratamento de erros adequado
- Organize seus servidores de forma modular

## 6. Recursos Adicionais

- [Documentação Oficial do MCP](https://mcp.dev/docs)
- [GitHub da Especificação MCP](https://github.com/model-context-protocol/spec)
- [MCP Inspector](https://github.com/mcp-tools/inspector) - Ferramenta CLI para testar servidores MCP
- [MCP Get](https://github.com/mcp-tools/get) - Gerenciador de servidores MCP
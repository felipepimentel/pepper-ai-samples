# MCP Examples

This directory contains examples of Model Context Protocol (MCP) implementations.

MCP is a protocol designed to enable AI models to interact with external tools and resources.

## Examples

- **00-hello-world**: Basic MCP server with tools, resources, and prompts
- **01-file-explorer**: File system exploration
- **02-web-search**: Web search integration
- **03-database-query**: Database querying
- **04-agent-system**: Agent-based system
- **05-api-design**: API design assistant
- **06-performance-profiling**: Performance profiling tools
- **07-architecture-analysis**: Architecture analysis tools
- **08-microservices**: Microservices design and management
- **09-iac-analyzer**: Infrastructure as Code analyzer
- **10-event-driven**: Event-driven architecture examples
- **11-tech-debt**: Technical debt analysis
- **12-doc-writer**: Documentation generation
- **13-education**: Educational tools and examples
- **14-github-projects**: GitHub project analysis

## O que é MCP?

MCP (Model Context Protocol) é um protocolo que padroniza a forma como modelos de linguagem e outros sistemas de IA interagem com ferramentas e fontes de dados externas. Ele permite que agentes acessem recursos como:

- APIs web
- Sistemas de arquivos
- Bancos de dados
- Ferramentas de código
- E outros recursos externos

## Como Executar os Exemplos

Cada exemplo possui seu próprio README com instruções específicas, mas o padrão geral é:

```bash
# Navegar para o diretório do exemplo
cd 00-hello-world

# Criar ambiente virtual
uv venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
uv pip install -r requirements.txt

# Executar o exemplo
python server.py
```

## Biblioteca Comum

Todos os exemplos utilizam a biblioteca comum `pepperpymcp` localizada em [../libs/pepperpymcp](../libs/pepperpymcp/), que fornece:

- Implementação base do protocolo MCP
- Utilitários compartilhados
- Tipos comuns e abstrações reutilizáveis 
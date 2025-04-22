# Exemplos MCP (Model Context Protocol)

Esta pasta contém exemplos de implementação usando o protocolo MCP para conectar agentes a ferramentas, APIs e recursos.

## O que é MCP?

MCP (Model Context Protocol) é um protocolo que padroniza a forma como modelos de linguagem e outros sistemas de IA interagem com ferramentas e fontes de dados externas. Ele permite que agentes acessem recursos como:

- APIs web
- Sistemas de arquivos
- Bancos de dados
- Ferramentas de código
- E outros recursos externos

## Exemplos Disponíveis

- **[00-hello-world](00-hello-world/)**: Servidor MCP básico com ferramentas simples
- **[01-file-explorer](01-file-explorer/)**: Exploração do sistema de arquivos local
- **[02-web-search](02-web-search/)**: Integração com mecanismos de busca na web
- **[03-database-query](03-database-query/)**: Consultas a bancos de dados
- **[04-agent-system](04-agent-system/)**: Sistema baseado em agentes autônomos
- **[05-api-design](05-api-design/)**: Criação e documentação de APIs
- **[06-performance-profiling](06-performance-profiling/)**: Ferramentas de análise de desempenho
- **[07-architecture-analysis](07-architecture-analysis/)**: Análise de arquitetura de software
- **[07-code-review](07-code-review/)**: Revisão automatizada de código
- **[08-microservices](08-microservices/)**: Implementação de microserviços
- **[09-iac-analyzer](09-iac-analyzer/)**: Análise de infraestrutura como código
- **[10-event-driven](10-event-driven/)**: Arquitetura orientada a eventos
- **[11-tech-debt](11-tech-debt/)**: Análise e gestão de dívida técnica
- **[12-doc-writer](12-doc-writer/)**: Geração automatizada de documentação
- **[13-education](13-education/)**: Ferramentas educacionais e de aprendizado
- **[14-github-projects](14-github-projects/)**: Integração com projetos do GitHub

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
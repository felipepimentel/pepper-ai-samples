#!/usr/bin/env python
"""
Web Search MCP Server Example
Demonstra como criar um servidor MCP para pesquisas e interações com a web.
"""

import re
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx
from pepperpymcp import PepperFastMCP

mcp = PepperFastMCP("Web Search", description="Servidor MCP para pesquisas na web")

# Configurações
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
TIMEOUT = 30.0  # segundos


@mcp.tool()
async def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Realiza uma pesquisa na web e retorna os resultados.

    Use esta ferramenta quando precisar encontrar informações na web sobre
    qualquer tópico, notícia ou fato. Retorna uma lista de resultados com
    títulos, URLs e snippets relevantes.

    Exemplos de uso:
    - search_web("melhores práticas de Python")  →  Resultados sobre Python
    - search_web("notícias tecnologia hoje", 10)  →  10 resultados sobre notícias de tecnologia

    Args:
        query: Termo de pesquisa
        num_results: Número de resultados a retornar (padrão: 5, máximo: 10)

    Returns:
        Dicionário com resultados da pesquisa, incluindo URLs e snippets
    """
    # Limitar número de resultados
    if num_results > 10:
        num_results = 10

    try:
        # Usamos a API pública do DuckDuckGo
        encoded_query = quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&pretty=1"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Extrair resultados
            results = []

            # Adicionar resultados abstratos (Abstract)
            if data.get("Abstract"):
                results.append(
                    {
                        "title": data.get("Heading", "Abstract"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                        "source": "Abstract",
                    }
                )

            # Adicionar resultados relacionados (RelatedTopics)
            for topic in data.get("RelatedTopics", [])[: num_results - len(results)]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append(
                        {
                            "title": topic.get("Text", "").split(" - ")[0]
                            if " - " in topic.get("Text", "")
                            else topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                            "source": "Related Topic",
                        }
                    )

            # Se ainda não tivermos resultados suficientes, adicione mais dos resultados
            if len(results) < num_results and data.get("Results"):
                for result in data.get("Results", [])[: num_results - len(results)]:
                    results.append(
                        {
                            "title": result.get("Text", ""),
                            "url": result.get("FirstURL", ""),
                            "snippet": result.get("Text", ""),
                            "source": "Results",
                        }
                    )

            return {"query": query, "num_results": len(results), "results": results}
    except Exception as e:
        raise RuntimeError(f"Erro ao pesquisar na web: {str(e)}")


@mcp.tool()
async def fetch_url(url: str, extract_text: bool = True) -> Dict[str, Any]:
    """Obtém o conteúdo de uma URL.

    Use esta ferramenta quando precisar do conteúdo completo ou do texto extraído
    de uma página web específica. Pode obter tanto o HTML completo quanto apenas
    o texto extraído sem marcações.

    Exemplos de uso:
    - fetch_url("https://example.com")  →  Obtém o texto da página example.com
    - fetch_url("https://exemplo.com.br", False)  →  Obtém o HTML completo

    Args:
        url: URL da página a ser obtida
        extract_text: Se True, extrai apenas o texto; se False, retorna o HTML (padrão: True)

    Returns:
        Dicionário com o conteúdo da página e metadados
    """
    try:
        # Validar URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(
                "URL inválida. Deve incluir protocolo (https://) e domínio."
            )

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            # Detectar tipo de conteúdo
            content_type = response.headers.get("content-type", "")
            is_html = "text/html" in content_type.lower()

            # Obter conteúdo
            html_content = response.text

            # Extrair texto se solicitado e se for HTML
            text_content = None
            if extract_text and is_html:
                text_content = _extract_text_from_html(html_content)

            # Extrair título se for HTML
            title = None
            if is_html:
                title_match = re.search(
                    r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
                )
                if title_match:
                    title = unescape(title_match.group(1).strip())

            return {
                "url": url,
                "content_type": content_type,
                "title": title,
                "content": text_content if extract_text and is_html else html_content,
                "status_code": response.status_code,
                "is_html": is_html,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            }
    except httpx.HTTPStatusError as e:
        return {
            "url": url,
            "error": f"Erro HTTP: {e.response.status_code}",
            "status_code": e.response.status_code,
            "content": None,
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao obter URL: {str(e)}")


@mcp.tool()
async def extract_links(url: str) -> Dict[str, Any]:
    """Extrai todos os links de uma página web.

    Use esta ferramenta quando precisar obter todos os links (URLs) presentes
    em uma página web, incluindo links internos e externos.

    Exemplos de uso:
    - extract_links("https://example.com")  →  Lista de links na página example.com

    Args:
        url: URL da página da qual extrair os links

    Returns:
        Dicionário com os links extraídos, categorizados por tipo
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            html_content = response.text
            base_url_parsed = urlparse(url)
            base_domain = base_url_parsed.netloc

            # Extrair links
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html_content)

            # Processar e categorizar links
            internal_links = []
            external_links = []
            resource_links = []

            for link in links:
                # Converter links relativos em absolutos
                if link.startswith("/"):
                    link = f"{base_url_parsed.scheme}://{base_domain}{link}"
                elif not link.startswith(("http://", "https://")):
                    link = f"{base_url_parsed.scheme}://{base_domain}/{link}"

                # Categorizar o link
                link_parsed = urlparse(link)

                # Verificar se é um recurso
                file_extensions = [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".xls",
                    ".xlsx",
                    ".csv",
                ]
                is_resource = any(link.lower().endswith(ext) for ext in file_extensions)

                if is_resource:
                    resource_links.append(link)
                elif link_parsed.netloc == base_domain:
                    internal_links.append(link)
                else:
                    external_links.append(link)

            # Remover duplicatas
            internal_links = list(set(internal_links))
            external_links = list(set(external_links))
            resource_links = list(set(resource_links))

            return {
                "url": url,
                "total_links": len(internal_links) + len(external_links) + len(resource_links),
                "internal_links": internal_links,
                "external_links": external_links,
                "resource_links": resource_links,
            }
    except Exception as e:
        raise RuntimeError(f"Erro ao extrair links: {str(e)}")


@mcp.resource("url://{path}")
def url_resource(path: str) -> str:
    """Acessar o conteúdo de uma URL como um recurso MCP.

    Este recurso permite acessar conteúdo da web diretamente como recursos MCP.
    O URI deve estar no formato url://{path}, onde {path} é a URL codificada.

    Exemplos de uso:
    - url://example.com  →  Acessa o conteúdo de https://example.com
    - url://api.example.com/data  →  Acessa uma API

    Args:
        path: URL a ser acessada (sem https://)

    Returns:
        O conteúdo da URL como string
    """
    import asyncio
    
    async def get_url_content():
        url = f"https://{path}"
        response = await fetch_url(url)
        return response.get("content", f"Erro ao acessar {url}")
    
    # Executar a função assíncrona
    loop = asyncio.get_event_loop()
    content = loop.run_until_complete(get_url_content())
    
    return content


@mcp.prompt()
async def summarize_webpage(url: str) -> str:
    """Gera um resumo do conteúdo de uma página web.

    Use este prompt quando precisar criar um resumo estruturado de uma página web,
    incluindo título, conteúdo principal e links mais importantes.

    Exemplos de uso:
    - summarize_webpage("https://example.com")  →  Resumo da página example.com

    Args:
        url: URL da página a ser resumida

    Returns:
        Resumo formatado da página web
    """
    try:
        # Obter conteúdo da página
        page_data = await fetch_url(url, extract_text=True)
        
        if "error" in page_data:
            return f"Erro ao acessar a página: {page_data['error']}"
        
        # Obter links da página
        links_data = await extract_links(url)
        
        # Extrair principais informações
        title = page_data.get("title", "Sem título")
        content = page_data.get("content", "")
        
        # Truncar conteúdo se for muito longo
        if len(content) > 1500:
            content = content[:1500] + "..."
        
        # Selecionar links importantes
        important_links = []
        
        # Priorizar links internos
        internal_links = links_data.get("internal_links", [])
        if internal_links:
            important_links.extend(internal_links[:3])
        
        # Adicionar alguns links externos
        external_links = links_data.get("external_links", [])
        if external_links:
            important_links.extend(external_links[:2])
        
        # Construir o resumo
        return mcp.get_template("webpage_summary").format(
            url=url,
            title=title,
            content=content,
            links=important_links,
            link_count=links_data.get("total_links", 0)
        )
    except Exception as e:
        return f"Erro ao resumir página: {str(e)}"


def _extract_text_from_html(html: str) -> str:
    """Extrai texto de conteúdo HTML, removendo tags.
    
    Esta função auxiliar remove tags HTML e formata o texto para melhor legibilidade.
    
    Args:
        html: O conteúdo HTML para processar
        
    Returns:
        Texto extraído do HTML
    """
    # Padrão para identificar scripts, estilos, comentários, etc.
    patterns_to_remove = [
        r"<style[^>]*>.*?</style>",
        r"<script[^>]*>.*?</script>",
        r"<!--.*?-->",
        r"<head>.*?</head>",
    ]
    
    # Remover padrões indesejados
    for pattern in patterns_to_remove:
        html = re.sub(pattern, " ", html, flags=re.DOTALL)
    
    # Substituir quebras de linha e tags de parágrafo
    html = re.sub(r"<br[^>]*>|<p[^>]*>", "\n", html)
    
    # Remover todas as tags HTML restantes
    html = re.sub(r"<[^>]*>", " ", html)
    
    # Substituir múltiplos espaços por um único espaço
    html = re.sub(r"\s+", " ", html)
    
    # Decodificar entidades HTML
    text = unescape(html)
    
    # Limpar quebras de linha duplicadas
    text = re.sub(r"\n\s*\n", "\n\n", text)
    
    return text.strip()


# Adicionar cliente web
mcp.add_web_client()


if __name__ == "__main__":
    try:
        # Support both HTTP and stdio modes
    mcp.run()  # Supports both HTTP and stdio modes
    finally:
        # Não são necessárias ações específicas de limpeza para este exemplo
        pass

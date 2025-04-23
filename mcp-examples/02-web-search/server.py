#!/usr/bin/env python
"""
Web Search MCP Server Example
Demonstra como criar um servidor MCP para pesquisas e interações com a web.
"""

import re
from html import unescape
from typing import Any, Dict
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
                "total_links": len(internal_links)
                + len(external_links)
                + len(resource_links),
                "internal_links": internal_links,
                "external_links": external_links,
                "resource_links": resource_links,
            }
    except Exception as e:
        raise RuntimeError(f"Erro ao extrair links: {str(e)}")


@mcp.resource("url://{path}")
def url_resource(path: str) -> str:
    """Acessa uma URL como recurso.

    Use este recurso para acessar o conteúdo de uma URL via URI no formato url://{path}.

    Exemplos de uso:
    - url://example.com  →  Obtém o conteúdo de example.com
    - url://docs.python.org/3/library/asyncio.html  →  Documentação do asyncio

    Args:
        path: URL a ser acessada

    Returns:
        O conteúdo textual da URL
    """
    try:
        # Verificar se a URL tem o protocolo
        if not path.startswith(("http://", "https://")):
            path = f"https://{path}"

        response = httpx.get(
            path,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()

        # Verificar se é HTML
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type.lower():
            return _extract_text_from_html(response.text)
        else:
            return f"[Conteúdo não-HTML detectado: {content_type}]\n\n{response.text[:2000]}"
    except Exception as e:
        return f"Erro ao acessar URL: {str(e)}"


@mcp.prompt()
async def summarize_webpage(url: str) -> str:
    """Gera um resumo formatado de uma página web.

    Use este prompt quando precisar de um resumo bem formatado de uma página web,
    incluindo título, principais links e uma visão geral do conteúdo.

    Exemplos de uso:
    - summarize_webpage("https://example.com")  →  Resumo da página example.com

    Args:
        url: URL da página web a ser resumida

    Returns:
        Um resumo formatado em markdown da página web
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            )
            response.raise_for_status()

            # Extrair informações
            html_content = response.text

            # Extrair título
            title_match = re.search(
                r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
            )
            title = "Sem título"
            if title_match:
                title = unescape(title_match.group(1).strip())

            # Extrair texto
            text_content = _extract_text_from_html(html_content)

            # Extrair alguns links importantes
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html_content)
            links = [
                link for link in links if link.startswith(("http://", "https://", "/"))
            ]
            links = list(set(links))[:5]  # Remover duplicatas e limitar a 5

            # Criar resumo
            summary = f"""
# Resumo da página: {title}

URL: {url}

## Conteúdo principal:
{text_content[:500]}...

## Links principais:
"""

            for link in links:
                if link.startswith("/"):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    full_link = f"{base_url}{link}"
                    summary += f"- [{link}]({full_link})\n"
                else:
                    summary += f"- [{link}]({link})\n"

            return summary
    except Exception as e:
        return f"Erro ao resumir página: {str(e)}"


# Função auxiliar para extrair texto de HTML
def _extract_text_from_html(html: str) -> str:
    """Extrai texto legível de conteúdo HTML, removendo tags."""
    # Remover scripts e estilos
    html = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html)
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html)

    # Remover tags HTML
    html = re.sub(r"<[^>]*>", " ", html)

    # Substituir múltiplos espaços em branco por um único espaço
    html = re.sub(r"[ \t\r\f\v]+", " ", html)

    # Substituir múltiplas quebras de linha por uma única quebra
    html = re.sub(r"\n+", "\n", html)

    # Decodificar entidades HTML
    html = unescape(html)

    # Remover espaços em branco no início e fim
    html = html.strip()

    return html


if __name__ == "__main__":
    mcp.run()

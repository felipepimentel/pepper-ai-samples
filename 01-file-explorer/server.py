#!/usr/bin/env python
"""
File Explorer MCP Server Example
Demonstra como criar um servidor MCP para exploração de sistema de arquivos.
"""

import datetime
import os
import stat
from typing import Any, Dict, List

from pepperpymcp import PepperFastMCP

mcp = PepperFastMCP(
    "File Explorer", description="Servidor MCP para exploração de sistema de arquivos"
)


@mcp.tool()
def list_directory(path: str = ".") -> List[Dict[str, Any]]:
    """Lista arquivos e diretórios em um caminho especificado.

    Use esta ferramenta quando precisar explorar o conteúdo de um diretório,
    listar arquivos ou navegar pelo sistema de arquivos.

    Exemplos de uso:
    - list_directory()  →  Lista arquivos no diretório atual
    - list_directory("/home/user")  →  Lista arquivos no diretório /home/user
    - list_directory("../")  →  Lista arquivos no diretório pai

    Args:
        path: Caminho do diretório para listar (padrão: diretório atual)

    Returns:
        Lista de dicionários contendo informações sobre cada arquivo/diretório

    Raises:
        FileNotFoundError: Se o diretório não existir
        PermissionError: Se não tiver permissão para acessar o diretório
    """
    try:
        result = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            stats = os.stat(item_path)

            # Determinar o tipo
            item_type = "unknown"
            if os.path.isdir(item_path):
                item_type = "directory"
            elif os.path.isfile(item_path):
                item_type = "file"
            elif os.path.islink(item_path):
                item_type = "symlink"

            # Formatação de data e permissões
            modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
            permissions = stat.filemode(stats.st_mode)

            result.append(
                {
                    "name": item,
                    "path": os.path.abspath(item_path),
                    "type": item_type,
                    "size": stats.st_size,
                    "modified": modified_time,
                    "permissions": permissions,
                }
            )

        return result
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Erro ao listar diretório: {str(e)}")


@mcp.tool()
def read_file(path: str, max_size: int = 100000) -> Dict[str, Any]:
    """Lê o conteúdo de um arquivo.

    Use esta ferramenta quando precisar ler o conteúdo de um arquivo de texto.
    Limitado a arquivos de texto com tamanho máximo configurável.

    Exemplos de uso:
    - read_file("arquivo.txt")  →  Lê o conteúdo do arquivo.txt
    - read_file("/caminho/para/config.json", 5000)  →  Lê config.json limitado a 5000 bytes

    Args:
        path: Caminho do arquivo a ser lido
        max_size: Tamanho máximo a ser lido em bytes (padrão: 100000)

    Returns:
        Dicionário contendo informações do arquivo e seu conteúdo

    Raises:
        FileNotFoundError: Se o arquivo não existir
        PermissionError: Se não tiver permissão para ler o arquivo
        ValueError: Se o arquivo exceder o tamanho máximo
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.isfile(path):
            raise FileNotFoundError(f"O arquivo '{path}' não existe")

        # Verificar o tamanho do arquivo
        file_size = os.path.getsize(path)
        if file_size > max_size:
            raise ValueError(
                f"Arquivo muito grande: {file_size} bytes (máximo: {max_size} bytes)"
            )

        # Tentar determinar o tipo de arquivo
        file_type = "text"
        file_extension = os.path.splitext(path)[1].lower()
        binary_extensions = [
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".zip",
            ".exe",
            ".bin",
            ".jpg",
            ".png",
            ".gif",
        ]

        if file_extension in binary_extensions:
            file_type = "binary"
            content = "[Arquivo binário - conteúdo não exibido]"
        else:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except UnicodeDecodeError:
                file_type = "binary"
                content = "[Codificação desconhecida - conteúdo não exibido]"

        # Obter estatísticas do arquivo
        stats = os.stat(path)
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()

        return {
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "size": file_size,
            "type": file_type,
            "modified": modified_time,
            "content": content,
        }
    except (FileNotFoundError, PermissionError, ValueError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Erro ao ler arquivo: {str(e)}")


@mcp.tool()
def write_file(path: str, content: str, mode: str = "w") -> Dict[str, Any]:
    """Escreve conteúdo em um arquivo.

    Use esta ferramenta quando precisar criar ou modificar um arquivo de texto.

    Exemplos de uso:
    - write_file("novo.txt", "Conteúdo do arquivo")  →  Cria/sobrescreve novo.txt
    - write_file("log.txt", "Nova linha", "a")  →  Adiciona conteúdo ao final de log.txt

    Args:
        path: Caminho do arquivo a ser escrito
        content: Conteúdo a ser escrito no arquivo
        mode: Modo de escrita ('w' para sobrescrever, 'a' para adicionar)

    Returns:
        Dicionário com informações sobre a operação

    Raises:
        PermissionError: Se não tiver permissão para escrever no arquivo
        ValueError: Se o modo for inválido
    """
    if mode not in ["w", "a"]:
        raise ValueError("Modo deve ser 'w' (sobrescrever) ou 'a' (adicionar)")

    try:
        with open(path, mode, encoding="utf-8") as file:
            file.write(content)

        file_size = os.path.getsize(path)

        return {
            "success": True,
            "path": os.path.abspath(path),
            "size": file_size,
            "mode": mode,
            "message": f"Arquivo {'sobrescrito' if mode == 'w' else 'atualizado'} com sucesso",
        }
    except PermissionError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Erro ao escrever arquivo: {str(e)}")


@mcp.tool()
def get_file_info(path: str) -> Dict[str, Any]:
    """Obtém informações detalhadas sobre um arquivo ou diretório.

    Use esta ferramenta quando precisar obter metadados detalhados sobre
    um arquivo ou diretório sem ler seu conteúdo.

    Exemplos de uso:
    - get_file_info("arquivo.txt")  →  Retorna metadados de arquivo.txt
    - get_file_info("/home/user")  →  Retorna metadados do diretório /home/user

    Args:
        path: Caminho do arquivo ou diretório

    Returns:
        Dicionário contendo informações detalhadas sobre o arquivo/diretório

    Raises:
        FileNotFoundError: Se o arquivo/diretório não existir
        PermissionError: Se não tiver permissão para acessar o arquivo/diretório
    """
    try:
        # Verificar se o caminho existe
        if not os.path.exists(path):
            raise FileNotFoundError(f"O caminho '{path}' não existe")

        # Obter estatísticas
        stats = os.stat(path)

        # Determinar o tipo
        item_type = "unknown"
        if os.path.isdir(path):
            item_type = "directory"
        elif os.path.isfile(path):
            item_type = "file"
        elif os.path.islink(path):
            item_type = "symlink"

        # Formatação de datas
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
        access_time = datetime.datetime.fromtimestamp(stats.st_atime).isoformat()
        create_time = datetime.datetime.fromtimestamp(stats.st_ctime).isoformat()

        # Permissões
        permissions = stat.filemode(stats.st_mode)

        result = {
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "type": item_type,
            "size": stats.st_size,
            "permissions": permissions,
            "modified_time": modified_time,
            "access_time": access_time,
            "create_time": create_time,
            "uid": stats.st_uid,
            "gid": stats.st_gid,
            "exists": True,
        }

        # Adicionar detalhes específicos para diretórios
        if item_type == "directory":
            try:
                result["item_count"] = len(os.listdir(path))
            except PermissionError:
                result["item_count"] = "Permissão negada"

        # Adicionar informações de extensão para arquivos
        if item_type == "file":
            result["extension"] = os.path.splitext(path)[1].lower()

        return result
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Erro ao obter informações: {str(e)}")


@mcp.resource("file://{path}")
def file_resource(path: str) -> str:
    """Acessa um arquivo como recurso.

    Use este recurso para acessar o conteúdo de um arquivo via URI no formato file://{path}.

    Exemplos de uso:
    - file://arquivo.txt  →  Acessa o conteúdo de arquivo.txt
    - file:///home/user/documento.md  →  Acessa um arquivo com caminho absoluto

    Args:
        path: Caminho para o arquivo a ser acessado

    Returns:
        O conteúdo do arquivo como string

    Raises:
        FileNotFoundError: Se o arquivo não existir
        PermissionError: Se não tiver permissão para ler o arquivo
    """
    try:
        if not os.path.isfile(path):
            return f"Erro: O arquivo '{path}' não existe ou não é um arquivo regular."

        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        return "[Arquivo binário ou codificação não suportada]"
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"


@mcp.prompt()
async def file_summary(path: str) -> str:
    """Gera um resumo do conteúdo de um arquivo.

    Use este prompt quando precisar de um resumo formatado do conteúdo
    de um arquivo, incluindo estatísticas como contagem de linhas.

    Exemplos de uso:
    - file_summary("arquivo.py")  →  Resumo do conteúdo de arquivo.py

    Args:
        path: Caminho para o arquivo a ser resumido

    Returns:
        Um resumo formatado do arquivo
    """
    try:
        if not os.path.isfile(path):
            return f"O arquivo '{path}' não existe ou não é um arquivo regular."

        size = os.path.getsize(path)
        stats = os.stat(path)
        modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Tentar ler o arquivo
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                lines = content.split("\n")
                line_count = len(lines)

                # Limitar o conteúdo para o resumo
                preview = "\n".join(lines[:10])
                if line_count > 10:
                    preview += f"\n... (mais {line_count - 10} linhas)"

                return f"""
# Resumo do Arquivo: {os.path.basename(path)}

Caminho: {os.path.abspath(path)}
Tamanho: {size} bytes
Modificado: {modified}
Linhas: {line_count}

## Prévia do conteúdo:
```
{preview}
```
"""
        except UnicodeDecodeError:
            return f"""
# Resumo do Arquivo: {os.path.basename(path)}

Caminho: {os.path.abspath(path)}
Tamanho: {size} bytes
Modificado: {modified}
Tipo: Arquivo binário (não é possível mostrar prévia)
"""
    except Exception as e:
        return f"Erro ao gerar resumo do arquivo: {str(e)}"


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python
"""
File Explorer MCP Server Example
Demonstra como criar um servidor MCP para exploração de sistema de arquivos.
"""

import datetime
import os
import stat
from typing import Any, Dict, List, Optional

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
            "modified": modified_time,
            "accessed": access_time,
            "created": create_time,
            "permissions": permissions,
            "user_id": stats.st_uid,
            "group_id": stats.st_gid,
        }

        # Se for um diretório, adicionar contagem de itens
        if item_type == "directory":
            try:
                result["item_count"] = len(os.listdir(path))
            except PermissionError:
                result["item_count"] = None

        return result
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Erro ao obter informações: {str(e)}")


@mcp.tool()
def delete_item(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Exclui um arquivo ou diretório.

    Use esta ferramenta quando precisar remover um arquivo ou diretório
    do sistema de arquivos.

    Exemplos de uso:
    - delete_item("arquivo.txt")  →  Remove o arquivo.txt
    - delete_item("/caminho/diretorio", True)  →  Remove o diretório e seu conteúdo

    Args:
        path: Caminho do arquivo ou diretório a ser excluído
        recursive: Se True, remove diretórios não vazios (padrão: False)

    Returns:
        Dicionário com informações sobre a operação

    Raises:
        FileNotFoundError: Se o arquivo/diretório não existir
        PermissionError: Se não tiver permissão para excluir
        IsADirectoryError: Se tentar excluir um diretório não vazio sem recursive=True
    """
    try:
        # Verificar se o caminho existe
        if not os.path.exists(path):
            raise FileNotFoundError(f"O caminho '{path}' não existe")

        # Se for um diretório
        if os.path.isdir(path):
            if recursive:
                import shutil
                shutil.rmtree(path)
            else:
                os.rmdir(path)  # Isso falha se o diretório não estiver vazio
        else:
            # É um arquivo ou link simbólico
            os.remove(path)

        return {
            "success": True,
            "path": path,
            "message": f"{'Diretório' if os.path.isdir(path) else 'Arquivo'} excluído com sucesso",
        }
    except (FileNotFoundError, PermissionError) as e:
        raise e
    except OSError as e:
        if os.path.isdir(path):
            raise IsADirectoryError(
                f"Diretório '{path}' não está vazio. Use recursive=True para excluir."
            )
        raise RuntimeError(f"Erro ao excluir: {str(e)}")


@mcp.resource("file://{path}")
def file_resource(path: str) -> str:
    """Acessar o conteúdo de um arquivo como um recurso MCP.

    Este recurso permite acessar arquivos do sistema diretamente como recursos MCP.
    O URI deve estar no formato file://{path}, onde {path} é o caminho do arquivo.

    Exemplos de uso:
    - file:///etc/hosts  →  Acessa o arquivo /etc/hosts
    - file://./config.json  →  Acessa o arquivo config.json no diretório atual

    Args:
        path: Caminho do arquivo a ser acessado

    Returns:
        O conteúdo do arquivo como string

    Raises:
        FileNotFoundError: Se o arquivo não existir
        PermissionError: Se não tiver permissão para ler o arquivo
    """
    try:
        path = path.replace("file://", "")
        
        if not os.path.isfile(path):
            raise FileNotFoundError(f"O arquivo '{path}' não existe")
        
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        return "[Arquivo binário - conteúdo não exibido]"


@mcp.prompt()
async def file_summary(path: str) -> str:
    """Gera um resumo das informações de um arquivo ou diretório.

    Use este prompt quando precisar de uma descrição em linguagem natural
    das informações de um arquivo ou diretório.

    Exemplos de uso:
    - file_summary("arquivo.txt")  →  Resumo do arquivo.txt
    - file_summary("/caminho/para/diretório")  →  Resumo do diretório

    Args:
        path: Caminho do arquivo ou diretório

    Returns:
        Resumo em texto das informações do arquivo ou diretório
    """
    try:
        info = get_file_info(path)
        
        # Determinar o tipo
        item_type = info["type"]
        
        if item_type == "directory":
            items = list_directory(path)
            num_files = sum(1 for item in items if item["type"] == "file")
            num_dirs = sum(1 for item in items if item["type"] == "directory")
            
            return mcp.get_template("directory_summary").format(
                path=info["path"],
                item_count=info["item_count"],
                num_files=num_files,
                num_dirs=num_dirs,
                modified=info["modified"]
            )
        elif item_type == "file":
            file_info = read_file(path)
            
            # Se o arquivo for muito grande, não incluir o conteúdo
            content_preview = None
            if file_info["type"] == "text" and file_info["size"] < 1024:
                content_preview = file_info["content"]
            
            return mcp.get_template("file_summary").format(
                name=info["name"],
                path=info["path"],
                size=info["size"],
                modified=info["modified"],
                type=file_info["type"],
                preview=content_preview if content_preview else "[Conteúdo muito grande para exibição]"
            )
        else:
            return f"Item de tipo desconhecido: {item_type}"
    except Exception as e:
        return f"Erro ao gerar resumo: {str(e)}"


# Adicionar cliente web
mcp.add_web_client()


if __name__ == "__main__":
    # Executar servidor (sem necessidade de código de limpeza específico)
    mcp.run()

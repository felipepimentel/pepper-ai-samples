#!/usr/bin/env python
"""
Servidor de Busca para MCP (Model Context Protocol).

Este módulo implementa um servidor de busca que permite pesquisar
documentos e recuperar seu conteúdo usando o protocolo MCP.
"""

import asyncio
import json
import logging
import os
import re
import string
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple, Union

from fastapi import FastAPI
import uvicorn

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("search_server")

# Adicionar o diretório raiz ao path para importações
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar SimpleMCP
from common.transport import SimpleMCP

class SearchServer:
    """
    Servidor de busca que permite pesquisar documentos através do protocolo MCP.
    
    Oferece ferramentas para:
    - Buscar documentos por palavras-chave
    - Recuperar documentos por ID
    - Listar todos os documentos disponíveis
    
    Também expõe recursos para acessar os documentos e resultados de busca.
    """
    
    def __init__(self, 
                 id: str = "search", 
                 name: str = "Document Search", 
                 host: str = "127.0.0.1", 
                 port: int = 8000,
                 options: Dict[str, Any] = None):
        """
        Inicializa o servidor de busca.
        
        Args:
            id: Identificador único do servidor
            name: Nome amigável do servidor
            host: Host para escutar conexões
            port: Porta para escutar conexões
            options: Opções adicionais de configuração
                - documents: Lista de documentos pré-definidos
                - document_path: Caminho para carregar documentos
                - stopwords_lang: Idioma para stopwords (default: "portuguese")
        """
        self.id = id
        self.name = name
        self.host = host
        self.port = port
        self.options = options or {}
        
        # Inicializar o servidor MCP
        self.mcp = SimpleMCP(
            name=name,
            description="Servidor de busca de documentos",
            version="1.0.0"
        )
        
        # Carregar documentos e criar índice
        self.documents = self._load_documents()
        self.index = self._create_index()
        
        # Registrar ferramentas e recursos
        self._register_tools()
        self._register_resources()
        
        logger.info(f"Servidor de busca '{name}' inicializado com {len(self.documents)} documentos")

    def _load_documents(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega documentos da configuração ou usa documentos de exemplo.
        
        Returns:
            Dicionário de documentos com ID como chave
        """
        # Verificar se documentos foram passados nas opções
        if "documents" in self.options:
            logger.info(f"Carregando {len(self.options['documents'])} documentos das opções")
            return {doc.get("id", str(i)): doc 
                    for i, doc in enumerate(self.options["documents"])}
        
        # Verificar se existe caminho para carregar documentos
        if "document_path" in self.options:
            path = Path(self.options["document_path"])
            if path.exists() and path.is_dir():
                logger.info(f"Carregando documentos do diretório: {path}")
                documents = {}
                for file_path in path.glob("*.json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            doc = json.load(f)
                            doc_id = doc.get("id", file_path.stem)
                            documents[doc_id] = doc
                    except Exception as e:
                        logger.error(f"Erro ao carregar documento {file_path}: {e}")
                
                if documents:
                    return documents
        
        # Usar documentos de exemplo
        logger.info("Carregando documentos de exemplo")
        return {
            "doc1": {
                "id": "doc1",
                "title": "Introdução à Programação Python",
                "content": """
                Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.
                Foi criada por Guido van Rossum e lançada pela primeira vez em 1991.
                Python é conhecida por sua sintaxe simples e legibilidade, o que facilita o aprendizado.
                A linguagem suporta múltiplos paradigmas de programação, incluindo programação orientada a objetos,
                programação imperativa, programação funcional e programação procedural.
                """,
                "tags": ["python", "programação", "introdução"]
            },
            "doc2": {
                "id": "doc2",
                "title": "Frameworks Web em Python",
                "content": """
                Existem diversos frameworks web para Python, como Django, Flask, FastAPI e Pyramid.
                Django é um framework web de alto nível que encoraja o desenvolvimento rápido e design limpo.
                Flask é um microframework que é ideal para aplicações pequenas e APIs.
                FastAPI é um framework moderno e de alto desempenho para construir APIs.
                Pyramid é um framework flexível que pode ser usado tanto para aplicações pequenas quanto para grandes.
                """,
                "tags": ["python", "web", "frameworks", "django", "flask"]
            },
            "doc3": {
                "id": "doc3",
                "title": "Processamento de Linguagem Natural com Python",
                "content": """
                O Processamento de Linguagem Natural (NLP) é uma área da inteligência artificial
                que se concentra na interação entre computadores e linguagem humana.
                Python oferece excelentes bibliotecas para NLP, como NLTK, spaCy e Gensim.
                NLTK (Natural Language Toolkit) é uma plataforma para construir programas em Python
                que trabalham com dados de linguagem humana.
                spaCy é uma biblioteca para NLP avançado em Python, projetada para uso em produção.
                Gensim é uma biblioteca robusta de modelagem de tópicos e similaridade de documentos.
                """,
                "tags": ["python", "nlp", "processamento de linguagem", "nltk", "spacy"]
            },
            "doc4": {
                "id": "doc4",
                "title": "Machine Learning com Python",
                "content": """
                Python é uma das linguagens mais populares para Machine Learning devido às suas poderosas bibliotecas.
                Scikit-learn é uma biblioteca que oferece ferramentas simples e eficientes para análise preditiva.
                TensorFlow e PyTorch são bibliotecas populares para deep learning.
                Pandas é utilizada para manipulação e análise de dados.
                NumPy é fundamental para computação numérica em Python.
                Matplotlib e Seaborn são bibliotecas para visualização de dados.
                """,
                "tags": ["python", "machine learning", "scikit-learn", "tensorflow", "pytorch"]
            },
            "doc5": {
                "id": "doc5",
                "title": "APIs RESTful com Python",
                "content": """
                APIs RESTful são interfaces que permitem a comunicação entre sistemas usando princípios REST.
                Python possui diversas ferramentas para criar APIs RESTful, como Flask, Django REST Framework e FastAPI.
                Flask pode ser usado com extensões como Flask-RESTful para criar APIs rapidamente.
                Django REST Framework é uma poderosa ferramenta para construir APIs Web.
                FastAPI é um framework moderno que combina alto desempenho com facilidade de uso.
                """,
                "tags": ["python", "api", "rest", "fastapi", "django"]
            }
        }

    def _create_index(self) -> Dict[str, Set[str]]:
        """
        Cria um índice invertido para busca eficiente.
        
        Returns:
            Dicionário onde a chave é o termo e o valor é um conjunto de IDs de documentos
        """
        index = {}
        stopwords = self._get_stopwords(self.options.get("stopwords_lang", "portuguese"))
        
        for doc_id, doc in self.documents.items():
            # Processar título
            terms = self._tokenize(doc.get("title", ""), stopwords)
            for term in terms:
                if term not in index:
                    index[term] = set()
                index[term].add(doc_id)
                
            # Processar conteúdo
            terms = self._tokenize(doc.get("content", ""), stopwords)
            for term in terms:
                if term not in index:
                    index[term] = set()
                index[term].add(doc_id)
                
            # Adicionar tags ao índice
            for tag in doc.get("tags", []):
                term = tag.lower()
                if term not in index:
                    index[term] = set()
                index[term].add(doc_id)
        
        logger.info(f"Índice criado com {len(index)} termos")
        return index

    def _tokenize(self, text: str, stopwords: Set[str]) -> List[str]:
        """
        Tokeniza um texto em termos para o índice.
        
        Args:
            text: Texto a ser tokenizado
            stopwords: Conjunto de stopwords para filtrar
            
        Returns:
            Lista de termos normalizados
        """
        # Converter para minúsculas
        text = text.lower()
        
        # Remover pontuação
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        
        # Tokenizar
        tokens = text.split()
        
        # Remover stopwords e termos muito curtos
        tokens = [token for token in tokens if token not in stopwords and len(token) > 2]
        
        return tokens

    def _get_stopwords(self, language: str) -> Set[str]:
        """
        Retorna um conjunto de stopwords para o idioma especificado.
        
        Args:
            language: Idioma para as stopwords
        
        Returns:
            Conjunto de stopwords
        """
        if language == "portuguese":
            return {
                "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo",
                "as", "até", "com", "como", "da", "das", "de", "dela", "delas", "dele",
                "deles", "depois", "do", "dos", "e", "ela", "elas", "ele", "eles", "em",
                "entre", "era", "eram", "eramos", "essa", "essas", "esse", "esses", "esta",
                "estas", "este", "estes", "eu", "foi", "fomos", "for", "foram", "fosse",
                "fossem", "ha", "isso", "isto", "ja", "lhe", "lhes", "mais", "mas", "me",
                "mesmo", "meu", "meus", "minha", "minhas", "muito", "na", "nas", "nem",
                "no", "nos", "nossa", "nossas", "nosso", "nossos", "num", "numa", "o",
                "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "quando",
                "que", "quem", "se", "seja", "sejam", "sem", "seu", "seus", "so", "somos",
                "sou", "sua", "suas", "também", "te", "tem", "temos", "tenho", "teu", "teus",
                "tu", "tua", "tuas", "um", "uma", "umas", "uns", "você", "vocês", "vos"
            }
        elif language == "english":
            return {
                "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
                "which", "this", "that", "these", "those", "then", "just", "so", "than",
                "such", "when", "who", "how", "where", "why", "is", "are", "was", "were",
                "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
                "doing", "would", "should", "could", "ought", "i'm", "you're", "he's",
                "she's", "it's", "we're", "they're", "i've", "you've", "we've", "they've",
                "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll",
                "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't",
                "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't",
                "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't",
                "mustn't", "let's", "that's", "who's", "what's", "here's", "there's",
                "when's", "where's", "why's", "how's", "a", "an", "the", "and", "but",
                "if", "or", "because", "as", "until", "while", "of", "at", "by", "for",
                "with", "about", "against", "between", "into", "through", "during",
                "before", "after", "above", "below", "to", "from", "up", "down", "in",
                "out", "on", "off", "over", "under", "again", "further", "then", "once",
                "here", "there", "when", "where", "why", "how", "all", "any", "both",
                "each", "few", "more", "most", "other", "some", "such", "no", "nor",
                "not", "only", "own", "same", "so", "than", "too", "very"
            }
        else:
            logger.warning(f"Idioma {language} não suportado para stopwords. Usando conjunto vazio.")
            return set()

    def _register_tools(self) -> None:
        """
        Registra as ferramentas do servidor MCP.
        """
        @self.mcp.tool()
        async def search_documents(query: str, limit: int = 10) -> Dict[str, Any]:
            """
            Busca documentos que correspondem à consulta.
            
            Args:
                query: Termos de busca
                limit: Número máximo de resultados
                
            Returns:
                Dicionário com resultados da busca
            """
            logger.info(f"Buscando documentos com a consulta: '{query}', limit: {limit}")
            
            # Tokenizar a consulta
            stopwords = self._get_stopwords(self.options.get("stopwords_lang", "portuguese"))
            query_terms = self._tokenize(query, stopwords)
            
            if not query_terms:
                return {
                    "query": query,
                    "count": 0,
                    "results": []
                }
            
            # Encontrar documentos que correspondem aos termos
            doc_scores = {}
            for term in query_terms:
                if term in self.index:
                    for doc_id in self.index[term]:
                        if doc_id not in doc_scores:
                            doc_scores[doc_id] = 0
                        doc_scores[doc_id] += 1
            
            # Ordenar por pontuação
            sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            # Criar resultados
            results = []
            for doc_id, score in sorted_docs:
                doc = self.documents.get(doc_id, {})
                results.append({
                    "id": doc_id,
                    "title": doc.get("title", ""),
                    "summary": self._generate_summary(doc.get("content", ""), 150),
                    "tags": doc.get("tags", []),
                    "score": score
                })
            
            return {
                "query": query,
                "count": len(results),
                "results": results
            }
        
        @self.mcp.tool()
        async def get_document(doc_id: str) -> Dict[str, Any]:
            """
            Recupera um documento pelo seu ID.
            
            Args:
                doc_id: ID do documento
                
            Returns:
                Documento completo ou mensagem de erro
            """
            logger.info(f"Recuperando documento com ID: {doc_id}")
            
            if doc_id in self.documents:
                return {
                    "success": True,
                    "document": self.documents[doc_id]
                }
            else:
                return {
                    "success": False,
                    "error": f"Documento com ID '{doc_id}' não encontrado"
                }
        
        @self.mcp.tool()
        async def list_documents(tag: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
            """
            Lista todos os documentos, opcionalmente filtrados por tag.
            
            Args:
                tag: Tag para filtrar (opcional)
                limit: Número máximo de resultados
                
            Returns:
                Lista de documentos
            """
            logger.info(f"Listando documentos{' com tag: ' + tag if tag else ''}")
            
            results = []
            
            for doc_id, doc in self.documents.items():
                if tag and tag.lower() not in [t.lower() for t in doc.get("tags", [])]:
                    continue
                
                results.append({
                    "id": doc_id,
                    "title": doc.get("title", ""),
                    "summary": self._generate_summary(doc.get("content", ""), 150),
                    "tags": doc.get("tags", [])
                })
                
                if len(results) >= limit:
                    break
            
            return {
                "count": len(results),
                "tag": tag,
                "documents": results
            }

    def _register_resources(self) -> None:
        """
        Registra os recursos do servidor MCP.
        """
        @self.mcp.resource("document://{doc_id}")
        async def document_resource(doc_id: str) -> bytes:
            """
            Recurso para acessar um documento pelo ID.
            
            Args:
                doc_id: ID do documento
                
            Returns:
                Conteúdo do documento como bytes JSON
            """
            if doc_id in self.documents:
                return json.dumps(self.documents[doc_id]).encode("utf-8")
            else:
                return json.dumps({
                    "error": f"Documento com ID '{doc_id}' não encontrado"
                }).encode("utf-8")
        
        @self.mcp.resource("search://{query}")
        async def search_resource(query: str) -> bytes:
            """
            Recurso para acessar resultados de busca.
            
            Args:
                query: Termos de busca
                
            Returns:
                Resultados da busca como bytes JSON
            """
            # Reutilizar a ferramenta de busca
            results = await self.mcp.tools["search_documents"](query=query)
            return json.dumps(results).encode("utf-8")

    def _generate_summary(self, text: str, max_length: int = 150) -> str:
        """
        Gera um resumo do texto, limitando o comprimento.
        
        Args:
            text: Texto a ser resumido
            max_length: Comprimento máximo do resumo
        
        Returns:
            Resumo do texto
        """
        text = text.strip()
        if len(text) <= max_length:
            return text
        
        # Truncar e adicionar elipses
        summary = text[:max_length].strip()
        if summary[-1] in ",.;:!?":
            summary = summary[:-1]
        
        return summary + "..."

    async def run(self) -> None:
        """
        Executa o servidor MCP.
        """
        logger.info(f"Iniciando servidor de busca em {self.host}:{self.port}")
        await self.mcp.run(host=self.host, port=self.port)


async def create_server(id: str, name: str, host: str = "127.0.0.1", 
                        port: int = 8000, options: Dict[str, Any] = None) -> SearchServer:
    """
    Função fábrica para criar um novo servidor de busca.
    
    Args:
        id: Identificador único do servidor
        name: Nome amigável do servidor
        host: Host para escutar conexões
        port: Porta para escutar conexões
        options: Opções adicionais de configuração
    
    Returns:
        Instância do servidor de busca
    """
    server = SearchServer(id=id, name=name, host=host, port=port, options=options)
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor de Busca MCP")
    parser.add_argument("--port", type=int, default=8000, help="Porta para escutar conexões")
    parser.add_argument("--host", default="127.0.0.1", help="Host para escutar conexões")
    
    args = parser.parse_args()
    
    server = SearchServer(host=args.host, port=args.port)
    asyncio.run(server.run()) 
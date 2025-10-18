from dotenv import load_dotenv
import os
from typing import List

from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain.tools import Tool

# ==============
# Config & setup
# ==============
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None

EMB = OpenAIEmbeddings()

def _client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def get_qdrant_collection(name: str) -> Qdrant:
    """
    Devuelve un vectorstore Qdrant enlazado a una colección existente.
    Usamos el cliente oficial para evitar problemas de firma (embedding/path/url).
    """
    client = _client()
    return Qdrant(
        client=client,
        collection_name=name,
        embeddings=EMB,
    )

# ===================
# Retrievers por KB
# ===================
def products_retriever(k: int = 5):
    vs = get_qdrant_collection("catalog_kb")
    return vs.as_retriever(search_kwargs={"k": k})

def other_retriever(k: int = 5):
    vs = get_qdrant_collection("other_kb")
    return vs.as_retriever(search_kwargs={"k": k})

# ==========================
# Funciones RAG por dominio
# ==========================
def _combine_docs_text(docs: List) -> str:
    if not docs:
        return "No se encontraron resultados relevantes."
    return "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)

def get_products_rag(query: str) -> str:
    """
    Recupera información relevante del vectorstore 'catalog_kb' (productos)
    para la consulta dada y devuelve un texto combinado.
    """
    retriever = products_retriever(k=5)
    results = retriever.get_relevant_documents(query)
    return _combine_docs_text(results)

def get_other_rag(query: str) -> str:
    """
    Recupera información relevante del vectorstore 'other_kb' (otros temas)
    para la consulta dada y devuelve un texto combinado.
    """
    retriever = other_retriever(k=5)
    results = retriever.get_relevant_documents(query)
    return _combine_docs_text(results)

# ======================
# Exponer como Tools
# ======================
products_tool = Tool(
    name="products_retrieval_tool",
    func=get_products_rag,
    description=(
        "Usa esta herramienta para responder preguntas sobre productos del catálogo. "
        "La entrada es una consulta en texto; la salida es un resumen concatenado "
        "de los documentos relevantes en 'catalog_kb'."
    ),
)

other_tool = Tool(
    name="other_retrieval_tool",
    func=get_other_rag,
    description=(
        "Usa esta herramienta para responder preguntas de la base 'other_kb'. "
        "La entrada es una consulta en texto; la salida es un resumen concatenado "
        "de los documentos relevantes en 'other_kb'."
    ),
)

# (Opcional) lista de tools para inyectar en tu agente
RETRIEVAL_TOOLS = [products_tool, other_tool]

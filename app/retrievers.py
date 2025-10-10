import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant

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

def products_retriever():
    vs = get_qdrant_collection("catalog_kb")
    return vs.as_retriever(search_kwargs={"k": 6})

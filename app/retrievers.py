
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None

EMB = OpenAIEmbeddings()

def get_qdrant_collection(name: str):
    return Qdrant.from_existing_collection(
        collection_name=name, url=QDRANT_URL, api_key=QDRANT_API_KEY, embeddings=EMB
    )

def products_retriever():
    q = get_qdrant_collection("catalog_kb")
    return q.as_retriever(search_kwargs={"k": 6})


import os, csv
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
EMB = OpenAIEmbeddings()

def run(path="data/catalog_samples.csv", collection="catalog_kb"):
    docs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            content = f"{row['title']} — {row['brand']} — USD {row['price']}"
            meta = {"sku": row["sku"], "brand": row["brand"], "price": row["price"], "category": row["category"]}
            docs.append(Document(page_content=content, metadata=meta))

    Qdrant.from_documents(
        docs, EMB, location=QDRANT_URL, prefer_grpc=False,
        collection_name=collection, api_key=QDRANT_API_KEY
    )
    print(f"Ingestados {len(docs)} documentos en {collection}.")

if __name__ == "__main__":
    run()

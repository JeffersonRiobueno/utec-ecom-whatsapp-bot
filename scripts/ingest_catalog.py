import os, csv, sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.documents import Document

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
print(f"[INFO] Usando Qdrant en: {QDRANT_URL}")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
EMB = OpenAIEmbeddings()

def normalize_headers(row: dict) -> dict:
    # Limpieza y normalización de cabeceras
    return { (k or "").strip().lower().replace("\ufeff", ""): (v or "").strip() for k, v in row.items() }

def run(path="data/catalog_samples.csv", collection="catalog_kb"):
    docs = []

    if not os.path.exists(path):
        print(f"[ERROR] No se encontró el archivo: {path}", file=sys.stderr)
        sys.exit(1)

    # Abrimos con newline="" y utf-8-sig para soportar BOM y CRLF
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        # Normalizamos líneas de salto
        content = f.read().replace("\r\n", "\n").strip()
        lines = content.split("\n")

        # Si no hay encabezados detectables
        if not lines or len(lines) < 2:
            print("[ERROR] El archivo CSV no contiene datos.")
            sys.exit(1)

        # Volvemos a procesar como CSV
        reader = csv.DictReader(lines)
        print("[INFO] Cabeceras detectadas:", reader.fieldnames)

        for raw in reader:
            if not raw:
                continue
            row = normalize_headers(raw)
            title  = row.get("title")    or row.get("nombre") or ""
            brand  = row.get("brand")    or row.get("marca")  or ""
            price  = row.get("price")    or row.get("precio") or ""
            cat    = row.get("category") or row.get("categoria") or ""
            sku    = row.get("sku") or ""

            if not title:
                print(f"[WARN] Fila omitida por falta de 'title': {row}")
                continue

            text = f"{title} — {brand} — USD {price} — {cat}".strip(" —")
            meta = {"sku": sku, "brand": brand, "price": price, "category": cat}
            docs.append(Document(page_content=text, metadata=meta))

    if not docs:
        print("[WARN] No se generaron documentos. Revisa cabeceras y contenido del CSV.")
        sys.exit(1)

    # Insertar documentos en Qdrant usando la nueva API
    Qdrant.from_documents(
        documents=docs,
        embedding=EMB,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=collection,
    )


    print(f"✅ Ingestados {len(docs)} productos en Qdrant ({collection}).")

if __name__ == "__main__":
    run()

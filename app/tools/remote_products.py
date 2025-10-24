"""Tool para llamar al agente remoto de productos.

Esta tool encapsula la llamada HTTP al contenedor agent_product para búsquedas de productos.
Se integra como una tool de LangChain para que los agentes puedan usarla.
"""

import httpx,os
from langchain.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()
AGENT_PRODUCTS_URL = os.getenv("AGENT_PRODUCTS_URL", "http://agent_product:8000")

class RemoteProductsTool(BaseTool):
    name: str = "remote_products_search"
    description: str = "Busca productos usando un agente remoto. Úsalo cuando el usuario pregunte por productos disponibles, como '¿Tienen zapatos Nike?'."

    async def _arun(self, query: str) -> str:
        """Versión async de la tool."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{AGENT_PRODUCTS_URL}/products_agent_search",
                    json={"text": query},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("result", "No se encontraron productos.")
            except Exception as e:
                return f"Error conectando con agente productos: {e}"

    def _run(self, query: str) -> str:
        """Versión síncrona (fallback)."""
        import asyncio
        return asyncio.run(self._arun(query))


# Instancia global para usar en el webhook
remote_products_tool = RemoteProductsTool()
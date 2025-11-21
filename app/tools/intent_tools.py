"""Tools para cada intención del bot de ecommerce.

Cada tool maneja una intención específica: productos, pedidos, pagos, etc.
"""

from langchain.tools import BaseTool
import httpx, os
from dotenv import load_dotenv

load_dotenv()
AGENT_PRODUCTS_URL = os.getenv("AGENT_PRODUCTS_URL", "http://agent_product:8000")
AGENT_SALUDOS_URL = os.getenv("AGENT_SALUDOS_URL", "http://agent_saludos:8000")
AGENT_PAGOS_URL = os.getenv("AGENT_PAGOS_URL", "http://agent_payment:8000")

class ProductsTool(BaseTool):
    name: str = "products_search"
    description: str = "Busca y consulta productos disponibles. Úsalo para preguntas sobre catálogo, precios o disponibilidad de productos."

    async def _arun(self, query: str) -> str:
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
                print(f"[ERROR] Failed to connect to products agent: {e}")
                return f"Error conectando con agente productos: {e}"

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class OrdersTool(BaseTool):
    name: str = "orders_management"
    description: str = "Maneja pedidos y órdenes. Úsalo para crear, consultar o gestionar pedidos."

    async def _arun(self, query: str) -> str:
        # Placeholder: implementar lógica real para pedidos
        return "Agente Pedidos: próximamente. Procesando consulta sobre pedidos."

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class PaymentsTool(BaseTool):
    name: str = "payments_handling"
    description: str = "Maneja pagos y métodos de pago. Úsalo para consultas sobre formas de pago."

    async def _arun(self, query: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{AGENT_PAGOS_URL}/payment_agent",
                    json={"text": query},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("result", "No se encontraron productos.")
            except Exception as e:
                print(f"[ERROR] Failed to connect to products agent: {e}")
                return f"Error conectando con agente productos: {e}"

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class OtherTool(BaseTool):
    name: str = "general_queries"
    description: str = "Maneja consultas generales como tallas, envíos, tienda física, etc."

    async def _arun(self, query: str) -> str:
        # Placeholder
        return "Agente para atender otras consultas: próximamente."

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class GreetingTool(BaseTool):
    name: str = "greetings"
    description: str = "Maneja saludos y conversaciones iniciales."

    async def _arun(self, query: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{AGENT_SALUDOS_URL}/greeting_agent",
                    json={"text": query},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("result", "No se encontraron saludos.")
            except Exception as e:
                print(f"[ERROR] Failed to connect to Greetings agent: {e}")
                return f"Error conectando con agente saludos: {e}"

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class TrackingTool(BaseTool):
    name: str = "order_tracking"
    description: str = "Maneja seguimiento de pedidos."

    async def _arun(self, query: str) -> str:
        return "Si quieres revisar un pedido, por favor proporciona el número de pedido o el correo asociado."

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


class HumanTool(BaseTool):
    name: str = "human_transfer"
    description: str = "Transfiere a un humano cuando el usuario lo solicita o hay problemas."

    async def _arun(self, query: str) -> str:
        return "Te transferiré a un agente humano. Por favor espera un momento."

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))


# Instancias de tools
products_tool = ProductsTool()
orders_tool = OrdersTool()
payments_tool = PaymentsTool()
other_tool = OtherTool()
greeting_tool = GreetingTool()
tracking_tool = TrackingTool()
human_tool = HumanTool()

# Mapeo de intenciones a tools
intent_tools = {
    "consulta_producto": products_tool,
    "productos": products_tool,
    "pedido": orders_tool,
    "pagos": payments_tool,
    "otro": other_tool,
    "talla": other_tool,
    "entregas": other_tool,
    "saludo": greeting_tool,
    "seguimiento": tracking_tool,
    "humano": human_tool,
}
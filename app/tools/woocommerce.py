import os
from typing import Any, Dict, Optional
from dataclasses import dataclass

try:
    from woocommerce import API as WCAPI
except Exception:
    WCAPI = None  # runtime import guard

# LangChain Tool (import at runtime for optional dependency)
from langchain.tools import Tool
from langchain.tools import tool


@dataclass
class WooClient:
    url: str
    consumer_key: str
    consumer_secret: str
    timeout: int = 30

    def __post_init__(self):
        if WCAPI is None:
            raise RuntimeError("Package 'woocommerce' no está instalado. Instálalo con: pip install woocommerce")
        self.client = WCAPI(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            version="wc/v3",
            timeout=self.timeout,
        )

    @classmethod
    def from_env(cls) -> "WooClient":
        url = os.getenv("WC_URL")
        key = os.getenv("WC_KEY")
        secret = os.getenv("WC_SECRET")
        if not url or not key or not secret:
            raise RuntimeError("WC_URL, WC_KEY y WC_SECRET deben estar configurados en el entorno.")
        return cls(url=url, consumer_key=key, consumer_secret=secret)
    @tool
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una orden en WooCommerce. order_data debe seguir la API de WC.
        Retorna el JSON de la orden creada o lanza RuntimeError con mensaje.
        """
        try:
            resp = self.client.post("orders", order_data).json()
            return resp
        except Exception as e:
            raise RuntimeError(f"Error creando orden en WooCommerce: {e}")
    @tool
    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Recupera una orden por ID."""
        try:
            resp = self.client.get(f"orders/{order_id}").json()
            return resp
        except Exception as e:
            raise RuntimeError(f"Error obteniendo orden {order_id}: {e}")



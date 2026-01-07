"""
Configuración de Langfuse para observabilidad usando LangChain / LangGraph.
Esta versión es explícita, simple y funcional.
"""

import os
import traceback
from typing import Optional

# ===============================
# Environment variables
# ===============================

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://langfuse:3000")

# Langfuse SDK espera /api
if LANGFUSE_HOST and not LANGFUSE_HOST.rstrip("/").endswith("/api"):
    LANGFUSE_HOST = LANGFUSE_HOST.rstrip("/") + "/api"


# ===============================
# Langfuse SDK imports
# ===============================

try:
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
except Exception:
    print("[ERROR] Langfuse SDK not installed or incompatible")
    traceback.print_exc()
    Langfuse = None
    LangfuseCallbackHandler = None


# ===============================
# Langfuse client (manual tracing)
# ===============================

_langfuse_client: Optional[Langfuse] = None


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Returns a Langfuse client for manual tracing.
    """
    global _langfuse_client

    if _langfuse_client:
        return _langfuse_client

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("[WARNING] Langfuse keys not configured. Observability disabled.")
        return None

    if not Langfuse:
        print("[WARNING] Langfuse SDK unavailable.")
        return None

    try:
        _langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        print("[INFO] Langfuse client initialized")
        return _langfuse_client
    except Exception:
        print("[ERROR] Failed to initialize Langfuse client")
        traceback.print_exc()
        return None


# ===============================
# LangChain / LangGraph callback
# ===============================

def get_langfuse_callback_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: str = "orchestrator",
):
    """
    Returns a Langfuse callback handler to be passed explicitly
    to LangChain / LangGraph execution.
    """
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return None

    if not LangfuseCallbackHandler:
        print("[WARNING] Langfuse callback handler not available")
        return None

    try:
        return LangfuseCallbackHandler(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
            session_id=session_id,
            user_id=user_id,
            trace_name=trace_name,
        )
    except Exception:
        print("[ERROR] Failed to create Langfuse callback handler")
        traceback.print_exc()
        return None

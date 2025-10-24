import json
import os
from typing import Any, Dict, Optional, Tuple
from fastapi import FastAPI, Query
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# Proveedores de LangChain
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

from app.router import make_router
from app.memory import get_message_history
from langchain.agents import initialize_agent, AgentType
from app.tools.intent_tools import products_tool, orders_tool, payments_tool, other_tool, greeting_tool, tracking_tool, human_tool

# =========================
# Config & utilidades
# =========================
load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai | ollama | gemini
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")          # por proveedor
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# (Opcional) URLs/keys por proveedor
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # requerido si usas gemini

# =========================
# Fábrica de LLMs
# =========================
def make_llm(
    provider: str,
    model: str,
    temperature: float
):
    provider = (provider or DEFAULT_PROVIDER).lower()

    if provider == "openai":
        # Requiere: OPENAI_API_KEY
        return ChatOpenAI(model=model, temperature=temperature)

    if provider == "ollama":
        # Requiere: Ollama corriendo localmente o remoto
        # Modelos típicos: "llama3.1", "qwen2.5", "phi3", etc.
        return ChatOllama(model=model, base_url=OLLAMA_BASE_URL, temperature=temperature)

    if provider == "gemini":
        # Requiere: GOOGLE_API_KEY
        if not GOOGLE_API_KEY:
            raise RuntimeError("Falta GOOGLE_API_KEY para usar Gemini.")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=GOOGLE_API_KEY)

    raise ValueError(f"Proveedor LLM no soportado: {provider}. Usa: openai | ollama | gemini")

def build_runtime(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None
):
    """Crea (llm, router_chain, router_summary, router_with_mem, agent) con el proveedor indicado."""
    use_provider = (provider or DEFAULT_PROVIDER).lower()
    use_model = model or DEFAULT_MODEL
    use_temperature = float(temperature if temperature is not None else DEFAULT_TEMPERATURE)

    llm = make_llm(use_provider, use_model, use_temperature)

    router_chain, router_summary, router_with_mem = make_router(llm)

    # Crear agente con tools
    tools = [products_tool, orders_tool, payments_tool, other_tool, greeting_tool, tracking_tool, human_tool]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )

    return {
        "provider": use_provider,
        "model": use_model,
        "temperature": use_temperature,
        "llm": llm,
        "router_chain": router_chain,
        "router_summary": router_summary,
        "router_with_mem": router_with_mem,
        "agent": agent,
    }

# =========================
# FastAPI app
# =========================
app = FastAPI(title="Ecom WhatsApp Bot")

# Runtime por defecto (env)
_runtime = build_runtime()

def products_agent_dump():
    return _runtime["products_agent_obj"].dump()

class WAIn(BaseModel):
    session_id: str
    text: str

@app.get("/health")
def health():
    return {"ok": True, "provider": _runtime["provider"], "model": _runtime["model"]}

@app.post("/webhook")
async def webhook(
    msg: WAIn,
    provider: Optional[str] = Query(None, description="Override provider: openai|ollama|gemini"),
    model: Optional[str] = Query(None, description="Override model name for the selected provider"),
    temperature: Optional[float] = Query(None, description="Override temperature")
):
    """
    Permite override puntual del proveedor/modelo/temperature vía query params.
    Si no se pasa nada, usa el runtime por defecto (env).
    """
    # Si llega override, levantamos un runtime temporal para esta llamada
    runtime = _runtime if not (provider or model or (temperature is not None)) else build_runtime(provider, model, temperature)

    hist = get_message_history(msg.session_id)

    # Intent: recuperar top-3 del historial (últimos 3 mensajes del buffer)
    top_history = []
    try:
        # Si la historia expone `.messages` (ChatMessageHistory), usamos esa lista
        if hasattr(hist, "messages") and isinstance(hist.messages, list):
            # tomamos los últimos 3
            last_msgs = hist.messages[-3:]
            top_history = [{"type": m.type, "content": m.content} for m in last_msgs]
        else:
            # Algunas implementaciones ofrecen get_messages() o get_recent_messages()
            if hasattr(hist, "get_messages"):
                msgs = hist.get_messages() or []
                last_msgs = msgs[-3:]
                # Mensajes pueden venir como dicts o objetos
                formatted = []
                for m in last_msgs:
                    if isinstance(m, dict):
                        formatted.append({"type": m.get("type"), "content": m.get("content")})
                    else:
                        # intentar atributos
                        t = getattr(m, "type", None)
                        c = getattr(m, "content", None)
                        formatted.append({"type": t, "content": c})
                top_history = formatted
    except Exception:
        top_history = []

    # Usar el agente con tools para manejar la intención y ejecutar la acción
    output = await runtime["agent"].arun(msg.text)

    hist.add_user_message(msg.text)
    hist.add_ai_message(output)

    runtime["router_summary"].save_context({"input": msg.text}, {"output": output})
    
    # DEBUGs útiles
    print("[DEBUG] Provider:", runtime["provider"])
    print("[DEBUG] Model:", runtime["model"])
    print("[DEBUG] History:", [{"type": m.type, "content": m.content} for m in hist.messages])

    return {
        "provider": runtime["provider"],
        "model": runtime["model"],
        "reply": output,
        "top_history": top_history,
    }

@app.get("/debug/memory")
def debug_memory(session_id: str = Query(..., description="ID de sesión")) -> Dict[str, Any]:
    hist = get_message_history(session_id)
    history_msgs = [{"type": m.type, "content": m.content} for m in hist.messages]

    router_vars = _runtime["router_summary"].load_memory_variables({})
    summary_context = router_vars.get("summary_context", [])

    prod_mem = products_agent_dump()
    return {
        "session_id": session_id,
        "provider": _runtime["provider"],
        "model": _runtime["model"],
        "history": history_msgs,
        "router_summary_context": summary_context,
        "products_agent_memory": prod_mem,
    }

@app.get("/debug/search")
def debug_search(q: str):
    docs = _runtime["products_agent_obj"].retriever.get_relevant_documents(q)
    return [{"content": d.page_content, "meta": d.metadata} for d in docs]

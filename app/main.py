from typing import Any, Dict, Optional, Tuple
from fastapi import FastAPI, Query
from pydantic import BaseModel


from app.router import make_router
from app.memory import get_message_history
from app.graph import run_graph
from app.llm_utils import make_llm, DEFAULT_PROVIDER, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from app.media_utils import preprocess_message
from app.metrics.prometheus_metrics import get_metrics
from fastapi import Query
import httpx

async def send_webhook_test(session_id: str, message: str, msg_type: str, user: Optional[str] = None) -> Optional[str]:
    url = "https://NNNNNNNNNNNN.com/webhook/chatwood-bot"
    data = {
        "user": user or "unknown",
        "mensaje": message,
        "type": msg_type,
        "conversation_id": session_id
    }
    try:
        # Timeout un poco mayor para permitir lectura de respuesta
        async with httpx.AsyncClient(timeout=3.0) as client:
           resp = await client.post(url, json=data)
           if resp.status_code == 200:
               try:
                   data_resp = resp.json()
                   print(f"[DEBUG] Webhook response: {data_resp}")
                   # Intenta capturar conversation_id o id de la respuesta
                   # Priorizamos conversation_id si viene en la respuesta
                   val = data_resp.get("conversation_id") or data_resp.get("id")
                   return str(val) if val else None
               except Exception as e:
                   print(f"[WARN] Error parsing webhook json: {e}")
    except Exception as e:
        print(f"[WARN] Failed to send webhook data to {url}: {e}")
    return None

# =========================
# Fábrica de LLMs
# =========================
# Movido a app/llm_utils.py

def build_runtime(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None
):
    """Crea (llm, router_chain, router_summary, router_with_mem) con el proveedor indicado."""
    use_provider = (provider or DEFAULT_PROVIDER).lower()
    use_model = model or DEFAULT_MODEL
    use_temperature = float(temperature if temperature is not None else DEFAULT_TEMPERATURE)

    llm = make_llm(use_provider, use_model, use_temperature)

    router_chain, router_summary, router_with_mem = make_router(llm)

    return {
        "provider": use_provider,
        "model": use_model,
        "temperature": use_temperature,
        "llm": llm,
        "router_chain": router_chain,
        "router_summary": router_summary,
        "router_with_mem": router_with_mem,
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
    mimetype: str = "text"  # Default to text for backward compatibility
    filename: str = ""

@app.get("/health")
def health():
    return {"ok": True, "provider": _runtime["provider"], "model": _runtime["model"]}

@app.get("/metrics")
def metrics():
    """Endpoint de métricas de Prometheus."""
    return get_metrics()

@app.post("/webhook")
async def webhook(
    msg: WAIn,
    provider: Optional[str] = Query(None, description="Override provider: openai|ollama|gemini"),
    model: Optional[str] = Query(None, description="Override model name for the selected provider"),
    temperature: Optional[float] = Query(None, description="Override temperature"),
    disable_guardrail: Optional[bool] = Query(False, description="Disable orchestrator guardrail for this request")
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

    # Preprocesar mensaje multimedia si es necesario
    processed_text = preprocess_message(msg.text, msg.mimetype, msg.filename, runtime["provider"])
    print(f"[DEBUG] Processed text: {processed_text[:100]}...")

    # Notificar Incoming (Usuario -> Agente)
    # Iniciamos la tarea pero guardamos la referencia para esperar su resultado después
    import asyncio
    initial_webhook_task = None
    try:
         # Usamos msg.session_id inicialmente. Si el webhook devuelve un ID numérico (conversation_id), actualizaremos chatwood_id después.
         initial_webhook_task = asyncio.create_task(send_webhook_test(msg.session_id, processed_text, "incoming", user=msg.session_id))
    except Exception as e:
         print(f"[WARN] Error dispatching incoming webhook: {e}")

    # Usar el grafo de LangGraph para manejar la intención y ejecutar la acción
    try:
            output, intent = await run_graph(
                msg.session_id,
                processed_text,
                runtime["provider"],
                runtime["model"],
                runtime["temperature"],
                runtime.get("router_summary"),
                disable_guardrail=disable_guardrail,
            )
    except Exception as e:
        print(f"[ERROR] Exception in webhook run_graph: {e}")
        import traceback
        traceback.print_exc()
        output = "Parece que hubo un problema al intentar conectar con el agente. Esto puede deberse a un error de red. Te recomiendo intentar de nuevo más tarde. Si el problema persiste, por favor contáctanos por otro medio. ¡Estamos aquí para ayudarte!"
        intent = "error"

    runtime["router_summary"].save_context({"input": msg.text}, {"output": output})

    # Recuperar conversation_id actualizado del webhook inicial (si existe)
    chatwood_id = msg.session_id
    if initial_webhook_task:
        try:
            # Esperamos a que termine el webhook inicial (ya debería haber terminado o estar cerca)
            result_id = await initial_webhook_task
            if result_id:
                chatwood_id = str(result_id)
                print(f"[DEBUG] Updated conversation_id from webhook: {chatwood_id}")
        except Exception as e:
            print(f"[WARN] Error awaiting initial webhook: {e}")

    # Notificar Outgoing (Agente -> Usuario) usando el ID actualizado
    try:
         asyncio.create_task(send_webhook_test(chatwood_id, output, "outgoing"))
    except Exception as e:
         print(f"[WARN] Error dispatching outgoing webhook: {e}")
    
    # DEBUGs útiles
    print("[DEBUG] Provider:", runtime["provider"])
    print("[DEBUG] Model:", runtime["model"])
    print("[DEBUG] History:", [{"type": m.type, "content": m.content} for m in hist.messages])

    return {
        "provider": runtime["provider"],
        "model": runtime["model"],
        "reply": output,
        "top_history": top_history,
        "conversation_id": chatwood_id,
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

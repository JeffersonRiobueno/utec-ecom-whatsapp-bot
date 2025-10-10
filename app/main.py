
import os
from typing import Any, Dict
from fastapi import FastAPI, Query
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI



from app.router import make_router
from app.agents.products import make_products_agent
from app.memory import get_message_history

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

app = FastAPI(title="Ecom WhatsApp Bot")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

router_chain, router_summary, router_with_mem = make_router(llm)
products_agent_obj = make_products_agent(llm, hybrid=True)

def products_agent_dump():
    return products_agent_obj.dump()

class WAIn(BaseModel):
    session_id: str
    text: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/webhook")
async def webhook(msg: WAIn):
    hist = get_message_history(msg.session_id)
    hist.add_user_message(msg.text)

    intent = router_chain.invoke({"input": msg.text}).strip().lower()

    if intent == "productos":
        output = products_agent_obj({"input": msg.text})
    elif intent == "pedidos":
        output = "Agente Pedidos: próximamente."
    elif intent == "pagos":
        output = "Agente Pagos: próximamente."
    elif intent == "ofertas":
        output = "Agente Ofertas: próximamente."
    else:
        output = "Puedo ayudarte con productos, pedidos, pagos u ofertas. ¿Cuál prefieres?"

    hist.add_ai_message(output)
    router_summary.save_context({"input": msg.text}, {"output": output})
    
    print("[DEBUG] Router summary:", router_summary.load_memory_variables({}).get("summary_context", []))
    print("[DEBUG] Products mem:", products_agent_dump())
    print("[DEBUG] History:", [{"type": m.type, "content": m.content} for m in hist.messages])

    return {"intent": intent, "reply": output}


@app.get("/debug/memory")
def debug_memory(session_id: str = Query(..., description="ID de sesión")) -> Dict[str, Any]:
    # 1) Historial crudo (mensajes)
    hist = get_message_history(session_id)
    history_msgs = [{"type": m.type, "content": m.content} for m in hist.messages]

    # 2) Resumen global del router
    router_vars = router_summary.load_memory_variables({})
    summary_context = router_vars.get("summary_context", [])

    # 3) Memoria del agente de productos
    # (ver paso 2B para exponer la memoria del agente)
    prod_mem = products_agent_dump()  # <- función que vamos a agregar abajo
    return {
        "session_id": session_id,
        "history": history_msgs,
        "router_summary_context": summary_context,
        "products_agent_memory": prod_mem,
    }

@app.get("/debug/search")
def debug_search(q: str):
    docs = products_agent_obj.retriever.get_relevant_documents(q)
    return [{"content": d.page_content, "meta": d.metadata} for d in docs]
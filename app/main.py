
import os
from fastapi import FastAPI
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
products_agent = make_products_agent(llm, hybrid=True)

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
        output = products_agent({"input": msg.text})
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

    return {"intent": intent, "reply": output}

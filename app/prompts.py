
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_BASE = """Eres un asistente de ecommerce por WhatsApp.
- Sé claro y breve.
- Si falta información, pregunta.
- No inventes datos de pedidos ni stock: usa herramientas o indica que necesitas consultar.
- Responde en el idioma del usuario (español por defecto).
"""

def agent_prompt(name: str):
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_BASE + f"\nEres el agente: {name}."),
        MessagesPlaceholder("summary_context"),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_BASE + """
Clasifica la intención del usuario exactamente en: productos | pedidos | pagos | ofertas | otro.
Responde solo una palabra de la lista.
"""),
    MessagesPlaceholder("summary_context"),
    ("human", "{input}")
])

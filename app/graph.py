"""Grafo de LangGraph para el bot de ecommerce con patrón Orquestador - Worker - Sintetizador y state persistente."""

from typing import TypedDict, Annotated, Sequence, Any
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from app.tools.intent_tools import products_tool, orders_tool, payments_tool, other_tool, greeting_tool, tracking_tool, human_tool
from app.router import make_router
from app.memory import get_message_history
from app.llm_utils import make_llm

# Función para obtener LLM para sintetizador
def get_synthesizer_llm(provider=None, model=None, temperature=None):
    return make_llm(provider, model, temperature)

# Estado del grafo
class BotState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "add_messages"]
    intent: str
    session_id: str
    raw_output: str  # Output crudo del Worker
    final_output: str  # Output sintetizado
    llm: Any  # LLM dinámico

# Prompt para el Sintetizador (modificable en app/prompts.py o aquí)
SYNTHESIZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Eres un sintetizador de respuestas para un bot de ecommerce por WhatsApp.
- Toma la respuesta cruda del worker y la refina para que sea clara, breve y amigable.
- Mantén el idioma del usuario (español por defecto).
- Si la respuesta es sobre productos, incluye detalles relevantes.
- Si es un error, explica de forma útil.
- No inventes información.
"""),
    ("human", "{raw_output}")
])

# Instancia del router (asumiendo que se crea una vez)
_router_chain = None

def get_router(provider=None, model=None, temperature=None):
    global _router_chain
    if _router_chain is None:
        llm = get_synthesizer_llm(provider, model, temperature)  # Reusar LLM
        _router_chain, _, _ = make_router(llm)
    return _router_chain

# Nodo: Clasificar intención
def classify_intent(state: BotState) -> BotState:
    user_message = state["messages"][-1].content if state["messages"] else ""
    llm = state["llm"]
    router, _, _ = make_router(llm)  # Crear router con llm dinámico
    intent = router.invoke({"input": user_message}).strip().lower()
    print(f"[DEBUG] Classified intent: {intent}")
    return {"intent": intent}

# Nodos: Manejar cada intención
def handle_products(state: BotState) -> BotState:
    user_message = state["messages"][-1].content
    output = products_tool._run(user_message)  # Síncrono por simplicidad
    print(f"[DEBUG] Raw output from products_tool: {output}")
    return {"raw_output": output}

def handle_orders(state: BotState) -> BotState:
    output = orders_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

def handle_payments(state: BotState) -> BotState:
    output = payments_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

def handle_other(state: BotState) -> BotState:
    output = other_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

def handle_greeting(state: BotState) -> BotState:
    output = greeting_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

def handle_tracking(state: BotState) -> BotState:
    output = tracking_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

def handle_human(state: BotState) -> BotState:
    output = human_tool._run(state["messages"][-1].content)
    return {"raw_output": output}

# Nodo: Sintetizar respuesta
def synthesize(state: BotState) -> BotState:
    llm = state["llm"]
    chain = SYNTHESIZER_PROMPT | llm
    response = chain.invoke({"raw_output": state["raw_output"]})
    print(f"[DEBUG] Synthesized output: {response.content}")
    return {"final_output": response.content}

# Función de ruteo condicional
def route_intent(state: BotState) -> str:
    intent = state.get("intent", "")
    mapping = {
        "consulta_producto": "handle_products",
        "productos": "handle_products",
        "pedido": "handle_orders",
        "pagos": "handle_payments",
        "otro": "handle_other",
        "talla": "handle_other",
        "entregas": "handle_other",
        "saludo": "handle_greeting",
        "seguimiento": "handle_tracking",
        "humano": "handle_human",
    }
    return mapping.get(intent, "handle_other")

# Construir el grafo
graph = StateGraph(BotState)

# Agregar nodos
graph.add_node("classify_intent", classify_intent)
graph.add_node("handle_products", handle_products)
graph.add_node("handle_orders", handle_orders)
graph.add_node("handle_payments", handle_payments)
graph.add_node("handle_other", handle_other)
graph.add_node("handle_greeting", handle_greeting)
graph.add_node("handle_tracking", handle_tracking)
graph.add_node("handle_human", handle_human)
graph.add_node("synthesize", synthesize)

# Edges
graph.set_entry_point("classify_intent")
graph.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "handle_products": "handle_products",
        "handle_orders": "handle_orders",
        "handle_payments": "handle_payments",
        "handle_other": "handle_other",
        "handle_greeting": "handle_greeting",
        "handle_tracking": "handle_tracking",
        "handle_human": "handle_human",
    }
)

# Todos los nodos de manejo van a synthesize
for node in ["handle_products", "handle_orders", "handle_payments", "handle_other", "handle_greeting", "handle_tracking", "handle_human"]:
    graph.add_edge(node, "synthesize")

# Sintetizador va a END
graph.add_edge("synthesize", END)

# Compilar el grafo
compiled_graph = graph.compile()

# Función para invocar el grafo
async def run_graph(session_id: str, user_text: str, provider=None, model=None, temperature=None) -> str:
    try:
        # Obtener historial
    ##    hist = get_message_history(session_id)
    ##    hist.add_user_message(user_text)

        # Estado inicial
        initial_state = {
            "messages": [HumanMessage(content=user_text)],
            "intent": "",
            "session_id": session_id,
            "raw_output": "",
            "final_output": "",
            "llm": get_synthesizer_llm(provider, model, temperature),
        }

        print(f"[DEBUG] Initial state: {initial_state}")

        # Ejecutar grafo
        result = await compiled_graph.ainvoke(initial_state)
        print(f"[DEBUG] Graph result: {result}")

        # Guardar respuesta en historial
        output = result.get("final_output", "Respuesta no disponible.")
    ##    hist.add_ai_message(output)

        return output
    except Exception as e:
        print(f"[ERROR] Exception in run_graph: {e}")
        import traceback
        traceback.print_exc()
        return "Parece que hubo un problema al intentar conectar con el agente. Esto puede deberse a un error de red. Te recomiendo intentar de nuevo más tarde. Si el problema persiste, por favor contáctanos por otro medio. ¡Estamos aquí para ayudarte!"
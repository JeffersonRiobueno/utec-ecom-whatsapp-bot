"""Grafo de LangGraph para el bot de ecommerce con patrón Orquestador - Worker - Sintetizador y state persistente."""

from typing import TypedDict, Annotated, Sequence, Any, Tuple
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from app.tools.intent_tools import products_tool, orders_tool, knowledge_tool, greeting_tool, human_tool, tracking_tool
from app.router import make_router
from app.memory import get_message_history
from app.llm_utils import make_llm
from app.metrics.prometheus_metrics import (
    increment_agent_request_count, observe_agent_latency,
    increment_intent_count, increment_guardrail_count
)
from app.chatwoot_client import add_chatwoot_label
import os
import traceback
import time

# Función para obtener LLM para sintetizador
def get_synthesizer_llm(provider=None, model=None, temperature=None):
    return make_llm(provider, model, temperature)

# Estado del grafo
class BotState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "add_messages"]
    intent: str
    session_id: str
    context_summary: str
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

# Prompt para Guardrail
GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Eres un guardrail de seguridad para un bot de ecommerce.
Tu tarea es revisar la respuesta final antes de enviarla al usuario.
Verifica que:
- No contenga lenguaje ofensivo, discriminatorio o inapropiado.
- No revele información sensible (datos personales, etc.), si hay datos personales emascarar con ****.
- No prometa productos no disponibles o invente información.
- La respuesta debe ser informativa y relevante para la consulta del usuario.

Si la respuesta pasa todas las verificaciones y es apropiada, responde con: "APROBADO: [respuesta original]"
Si falla alguna verificación o es demasiado vaga/irrelevante, responde con: "RECHAZADO: [explicación breve del problema] [respuesta corregida o alternativa]"
"""),
    ("human", "{final_output}")
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
    start_time = time.time()
    user_message = state["messages"][-1].content if state["messages"] else ""
    context = state.get("context_summary", "")
    combined_input = (f"{context}\n\n{user_message}") if context else user_message
    llm = state["llm"]
    router, _, _ = make_router(llm)  # Crear router con llm dinámico
    intent = router.invoke({"input": combined_input}).strip().lower()

    # Métricas
    increment_intent_count(intent)

    duration = time.time() - start_time
    print(f"[DEBUG] Classified intent: {intent} (took {duration:.3f}s)")
    return {"intent": intent}

# Nodos: Manejar cada intención
def handle_products(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    try:
        output = products_tool._run(user_message, session_id=session_id, context_summary=context)  # Síncrono por simplicidad
        increment_agent_request_count("products", "success")
    except Exception as e:
        print(f"[ERROR] Products agent error: {e}")
        output = "Lo siento, hubo un problema al consultar productos. Por favor intenta de nuevo."
        increment_agent_request_count("products", "error")

    duration = time.time() - start_time
    observe_agent_latency("products", duration)
    print(f"[DEBUG] Raw output from products_tool: {output} (took {duration:.3f}s)")
    return {"raw_output": output}

def handle_orders(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    try:
        output = orders_tool._run(user_message, session_id=session_id, context_summary=context)
        increment_agent_request_count("orders", "success")
    except Exception as e:
        print(f"[ERROR] Orders agent error: {e}")
        output = "Lo siento, hubo un problema al consultar pedidos. Por favor intenta de nuevo."
        increment_agent_request_count("orders", "error")

    duration = time.time() - start_time
    observe_agent_latency("orders", duration)
    return {"raw_output": output}

def handle_knowledge(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    try:
        output = knowledge_tool._run(user_message, session_id=session_id, context_summary=context)
        increment_agent_request_count("knowledge", "success")
    except Exception as e:
        print(f"[ERROR] Knowledge agent error: {e}")
        output = "Lo siento, hubo un problema al consultar información. Por favor intenta de nuevo."
        increment_agent_request_count("knowledge", "error")

    duration = time.time() - start_time
    observe_agent_latency("knowledge", duration)
    return {"raw_output": output}

def handle_greeting(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    try:
        output = greeting_tool._run(user_message, session_id=session_id, context_summary=context)
        increment_agent_request_count("greeting", "success")
    except Exception as e:
        print(f"[ERROR] Greeting agent error: {e}")
        output = "¡Hola! ¿En qué puedo ayudarte hoy?"
        increment_agent_request_count("greeting", "error")

    duration = time.time() - start_time
    observe_agent_latency("greeting", duration)
    return {"raw_output": output}

def handle_tracking(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    try:
        output = tracking_tool._run(user_message, session_id=session_id, context_summary=context)
        increment_agent_request_count("tracking", "success")
    except Exception as e:
        print(f"[ERROR] Tracking agent error: {e}")
        output = "Lo siento, hubo un problema al consultar el seguimiento. Por favor intenta de nuevo."
        increment_agent_request_count("tracking", "error")

    duration = time.time() - start_time
    observe_agent_latency("tracking", duration)
    return {"raw_output": output}

async def handle_human(state: BotState) -> BotState:
    start_time = time.time()
    user_message = state["messages"][-1].content
    session_id = state.get("session_id")
    context = state.get("context_summary", "")

    # Ejecutar etiquetado en Chatwoot (side effect)
    try:
        if session_id:
             await add_chatwoot_label(session_id, "human")
    except Exception as e:
        print(f"[WARN] Could not label conversation as human: {e}")

    try:
        output = human_tool._run(user_message, session_id=session_id, context_summary=context)
        increment_agent_request_count("human", "success")
    except Exception as e:
        print(f"[ERROR] Human agent error: {e}")
        output = "Lo siento, necesito transferirte con un agente humano. Por favor espera un momento."
        increment_agent_request_count("human", "error")

    duration = time.time() - start_time
    observe_agent_latency("human", duration)
    return {"raw_output": output}

# Nodo: Sintetizar respuesta
def synthesize(state: BotState) -> BotState:
    # Bypass summarization as per user request
    # llm = state["llm"]
    # chain = SYNTHESIZER_PROMPT | llm
    # response = chain.invoke({"raw_output": state["raw_output"]})
    # print(f"[DEBUG] Synthesized output: {response.content}")
    # return {"final_output": response.content}
    
    print(f"[DEBUG] Bypassing synthesizer, returning raw output")
    return {"final_output": state["raw_output"]}

# Nodo: Guardrail de seguridad
def guardrail(state: BotState) -> BotState:
    # Allow bypassing the guardrail per-request via state flag or global env var
    disabled_env = os.getenv("ORCHESTRATOR_GUARDRAIL_ENABLED", "true").lower() in ["0", "false", "no"]
    if state.get("disable_guardrail") or disabled_env:
        increment_guardrail_count("skipped")
        print("[DEBUG] Guardrail disabled for this request; bypassing checks.")
        return {"final_output": state["final_output"]}

    llm = state["llm"]
    chain = GUARDRAIL_PROMPT | llm
    response = chain.invoke({"final_output": state["final_output"]})
    guarded_output = response.content.strip()

    if guarded_output.startswith("APROBADO:"):
        # Extraer la respuesta original
        final_output = guarded_output.replace("APROBADO:", "").strip()
        increment_guardrail_count("approved")
        print(f"[DEBUG] Guardrail passed: {final_output[:100]}...")
    elif guarded_output.startswith("RECHAZADO:"):
        # Usar la respuesta corregida o alternativa
        final_output = guarded_output.replace("RECHAZADO:", "").strip()
        increment_guardrail_count("rejected")
        print(f"[DEBUG] Guardrail rejected and corrected: {final_output[:100]}...")
    else:
        # Fallback: asumir aprobado si no sigue el formato
        final_output = state["final_output"]
        increment_guardrail_count("fallback")
        print(f"[DEBUG] Guardrail format unexpected, using original: {final_output[:100]}...")

    return {"final_output": final_output}

# Función de ruteo condicional
def route_intent(state: BotState) -> str:
    intent = state.get("intent", "")
    mapping = {
        "consulta_producto": "handle_products",
        "productos": "handle_products",
        "pedido": "handle_orders",
        "otro": "handle_knowledge",
        "saludo": "handle_greeting",
        "seguimiento": "handle_tracking",
        "humano": "handle_human",
        "human": "handle_human",
    }
    return mapping.get(intent, "handle_knowledge")

# Construir el grafo
graph = StateGraph(BotState)

# Agregar nodos
graph.add_node("classify_intent", classify_intent)
graph.add_node("handle_products", handle_products)
graph.add_node("handle_orders", handle_orders)
graph.add_node("handle_knowledge", handle_knowledge)
graph.add_node("handle_greeting", handle_greeting)
graph.add_node("handle_human", handle_human)
graph.add_node("handle_tracking", handle_tracking)
graph.add_node("synthesize", synthesize)
graph.add_node("guardrail", guardrail)

# Edges
graph.set_entry_point("classify_intent")
graph.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "handle_products": "handle_products",
        "handle_orders": "handle_orders",
        "handle_knowledge": "handle_knowledge",
        "handle_greeting": "handle_greeting",
        "handle_tracking": "handle_tracking",
        "handle_human": "handle_human",
    }
)

# Todos los nodos de manejo van a synthesize
for node in ["handle_products", "handle_orders", "handle_knowledge", "handle_greeting", "handle_tracking", "handle_human"]:
    graph.add_edge(node, "synthesize")

# Sintetizador va a guardrail
graph.add_edge("synthesize", "guardrail")

# Guardrail va a END
graph.add_edge("guardrail", END)

# Compilar el grafo
compiled_graph = graph.compile()

# Función para invocar el grafo
async def run_graph(session_id: str, user_text: str, provider=None, model=None, temperature=None, router_summary=None, disable_guardrail: bool = False) -> Tuple[str, str]:
    try:
        # INTEGRACIÓN MINIMALISTA LANGFUSE (PoC)
        langfuse_handler = None
        try:
            try:
                from langfuse.callback import CallbackHandler
            except ImportError:
                from langfuse.langchain import CallbackHandler
            
            # Confiamos 100% en las variables de entorno (LANGFUSE_HOST, PUBLIC_KEY, SECRET_KEY)
            print(f"[INFO] Inicializando Langfuse para sesión: {session_id}")
            try:
                # SDK < 3.0.0 acepta session_id en constructor
                langfuse_handler = CallbackHandler(session_id=session_id)
            except Exception as e:
                print(f"[WARN] Error init CallbackHandler con session_id: {e}. Probando sin args.")
                langfuse_handler = CallbackHandler()

            if hasattr(langfuse_handler, "auth_check"):
                langfuse_handler.auth_check()
        except Exception as e:
            print(f"[WARN] Langfuse no disponible: {e}")

        # Obtener historial y añadir mensaje del usuario
        hist = get_message_history(session_id)
        try:
            hist.add_user_message(user_text)
        except Exception:
            # Si la implementación de historial falla, continuar
            pass

        # Construir context_summary a partir de la memoria del router si está disponible
        context_summary = ""
        if router_summary is not None:
            try:
                router_vars = router_summary.load_memory_variables({})
                ctx = router_vars.get("summary_context", "")
                if isinstance(ctx, list):
                    # Extraer texto si vienen como mensajes
                    parts = []
                    for m in ctx:
                        if hasattr(m, "content"):
                            parts.append(m.content)
                        else:
                            parts.append(str(m))
                    context_summary = " ".join(parts)
                else:
                    context_summary = str(ctx)
            except Exception:
                context_summary = ""

        # Estado inicial
        initial_state = {
            "messages": [HumanMessage(content=user_text)],
            "intent": "",
            "session_id": session_id,
            "context_summary": context_summary,
            "raw_output": "",
            "final_output": "",
            "llm": get_synthesizer_llm(provider, model, temperature),
            # Per-request flag to disable guardrail
            "disable_guardrail": bool(disable_guardrail),
        }

        print(f"[DEBUG] Initial state: {initial_state}")

        # Ejecutar grafo
        callbacks = [langfuse_handler] if langfuse_handler else []
        result = await compiled_graph.ainvoke(initial_state, config={"callbacks": callbacks})

        # FLUSH: Vital para asegurar envío de datos antes de terminar
        if langfuse_handler:
            try:
               langfuse_handler.flush()
            except Exception as e:
               print(f"[WARN] Fallo al hacer flush de Langfuse: {e}")

        print(f"[DEBUG] Graph result: {result}")

        # Guardar respuesta en historial
        output = result.get("final_output", "Respuesta no disponible.")
        intent = result.get("intent", "otro")
        try:
            hist.add_ai_message(output)
        except Exception:
            pass

        return output, intent
    except Exception as e:
        print(f"[ERROR] Exception in run_graph: {e}")
        import traceback
        traceback.print_exc()
        return "Parece que hubo un problema al intentar conectar con el agente. Esto puede deberse a un error de red. Te recomiendo intentar de nuevo más tarde. Si el problema persiste, por favor contáctanos por otro medio. ¡Estamos aquí para ayudarte!", "error"
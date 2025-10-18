# agent.py
from __future__ import annotations
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import Tool

# IMPORTA LAS TOOLS QUE CREAMOS ANTES
# Si las definiste en vector/vector.py usa esta línea:
#from vector.vector import products_tool, other_tool
from app.vector.vector import products_tool, other_tool

# Si las dejaste en vector/__init__.py, cambia por:
# from vector import products_tool, other_tool

load_dotenv()

# =========================
# Modelo de respuesta final
# =========================
class FormatResponse(BaseModel):
    descripcion: str
    tools_usadas: List[str]

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Parser
parser = PydanticOutputParser(pydantic_object=FormatResponse)

# =========================
# Prompt del agente
# =========================
sysprompt = """
Eres un asistente experto en buscar productos de la tienda de zapatos. Ayudas a usuarios a responder preguntas sobre productos y encontrar información relevante.
Usas herramientas para buscar información relevante y responder consultas de usuarios.

Proporcionas respuestas EXACTAMENTE en este formato y no provees otro texto:
{format_instructions}

Cuando tengas la respuesta completa y formateada, deberás guardar la información en un archivo de texto.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(sysprompt),
    ("placeholder", "{chat_history}"),
    HumanMessagePromptTemplate.from_template("Investiga el siguiente tema: {query}."),
    ("placeholder", "{agent_scratchpad}"),
]).partial(format_instructions=parser.get_format_instructions())

# =========================
# Fábrica de agentes
# =========================
def _create_agent_with_tools(tools: List[Tool]) -> AgentExecutor:
    """
    Crea un AgentExecutor con el prompt y las tools proporcionadas.
    """
    agent = create_openai_tools_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )
    executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True
    )
    return executor



def _run_agent(executor: AgentExecutor, query_text: str) -> str:
    """
    Ejecuta el agente con la query dada y devuelve SOLO la 'descripcion' (str).
    Si el parseo falla o el campo no existe, retorna el texto crudo del output.
    """
    raw = executor.invoke({"query": query_text, "chat_history": []})
    raw_text = raw.get("output", "")

    print("[DEBUG] Query text:", query_text)
    print("[DEBUG] Raw output:", raw_text)
    # 1) Intentar parsear con Pydantic
    try:
        parsed = parser.parse(raw_text)
        # parsed es un BaseModel: acceso directo
        return getattr(parsed, "descripcion", raw_text) or raw_text
    except Exception as e:
        pass  # seguimos intentando otras rutas

    # 2) Si el LLM devolvió JSON, intentar parsear a dict y extraer 'descripcion'
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "descripcion" in data:
            return data.get("descripcion") or raw_text
    except Exception:
        pass

    # 3) Fallback total: devolver el texto crudo
    return raw_text

# =========================
# Funciones públicas
# =========================
def agent_products(text: str) -> Dict[str, Any]:
    """
    Invoca un agente que usa la tool de productos (catalog_kb).
    """
    executor = _create_agent_with_tools([products_tool])
    return _run_agent(executor, text)

def agent_other(text: str) -> Dict[str, Any]:
    """
    Invoca un agente que usa la tool de 'otros' (other_kb).
    """
    executor = _create_agent_with_tools([other_tool])
    return _run_agent(executor, text)

# =========================
# Ejemplos rápidos
# =========================
#if __name__ == "__main__":
#    # Ejemplo Products
#    res1 = agent_products("Tienes zapatos Puma?")
#    print("RAW PRODUCTS:", json.dumps(res1["raw"], ensure_ascii=False, indent=2))
#    print("PARSED PRODUCTS:", res1["parsed"])#

    # Ejemplo Other
#    res2 = agent_other("restaurantes criollos con show en vivo en Miraflores")
#    print("RAW OTHER:", json.dumps(res2["raw"], ensure_ascii=False, indent=2))
#    print("PARSED OTHER:", res2["parsed"])

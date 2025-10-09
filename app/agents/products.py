
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from app.prompts import agent_prompt
from app.memory import make_agent_window_memory, make_hybrid_memory
from app.retrievers import products_retriever

def make_products_agent(llm: ChatOpenAI, hybrid: bool = True):
    memory = make_hybrid_memory(llm) if hybrid else make_agent_window_memory(k=5)
    retriever = products_retriever()
    prompt = agent_prompt("Productos")

    chain = (
        {
            "summary_context": RunnableLambda(lambda x: memory.load_memory_variables({}).get("summary_context", [])),
            "chat_history":   RunnableLambda(lambda x: memory.load_memory_variables({}).get("chat_history", [])),
            "input":          RunnablePassthrough(),
            "docs":           RunnableLambda(lambda x: retriever.get_relevant_documents(x["input"]))
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    def call(inputs: Dict[str, Any]) -> str:
        user = inputs.get("input", "")
        memory.save_context({"input": user}, {"output": ""})
        out = chain.invoke(inputs)
        memory.save_context({"input": user}, {"output": out})
        return out

    return call

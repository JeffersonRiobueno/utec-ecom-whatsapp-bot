from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from app.prompts import agent_prompt
from app.memory import make_agent_window_memory, make_hybrid_memory
from app.retrievers import products_retriever

class ProductsAgent:
    def __init__(self, llm: ChatOpenAI, hybrid: bool = True):
        self.memory = make_hybrid_memory(llm) if hybrid else make_agent_window_memory(k=5)
        self.retriever = products_retriever()
        self.prompt = agent_prompt("Productos")

        self.chain = (
            {
                "summary_context": RunnableLambda(lambda x: self.memory.load_memory_variables({}).get("summary_context", [])),
                "chat_history":   RunnableLambda(lambda x: self.memory.load_memory_variables({}).get("chat_history", [])),
                "input":          RunnablePassthrough(),
                "docs":           RunnableLambda(lambda x: self.retriever.get_relevant_documents(x["input"]))
            }
            | self.prompt
            | llm
            | StrOutputParser()
        )


    
    def __call__(self, inputs):
        user = inputs.get("input", "")
        # NO guardes esta línea previa con output vacío:
        # self.memory.save_context({"input": user}, {"output": ""})

        out = self.chain.invoke(inputs)

        # Guarda el turno completo (input + output)
        self.memory.save_context({"input": user}, {"output": out})
        return out

    def dump(self) -> Dict[str, Any]:
        """Devuelve todas las variables de memoria disponibles."""
        return self.memory.load_memory_variables({})

def make_products_agent(llm: ChatOpenAI, hybrid: bool = True) -> ProductsAgent:
    return ProductsAgent(llm, hybrid=hybrid)


from typing import Tuple, Callable, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.prompts import ROUTER_PROMPT
from app.memory import make_global_summary_memory

def make_router(llm: ChatOpenAI) -> Tuple[Any, Any, Callable[[Dict[str, Any]], Dict[str, Any]]]:
    summary = make_global_summary_memory(llm)

    chain = (
        {
            "summary_context": RunnableLambda(lambda x: summary.load_memory_variables({}).get("summary_context", [])),
            "input": RunnablePassthrough(),
        }
        | ROUTER_PROMPT
        | llm
        | StrOutputParser()
    )

    def with_memory(inputs: Dict[str, Any]):
        summary.save_context({"input": inputs.get("input","")}, {"output": inputs.get("output","")})
        return inputs

    return chain, summary, with_memory

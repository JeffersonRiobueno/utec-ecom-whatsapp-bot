import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationSummaryMemory,
)
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"

def get_message_history(session_id: str):
    """
    Retorna una historia de chat.
    Si USE_REDIS=false, usa memoria en RAM (no persistente).
    """
    if USE_REDIS:
        try:
            return RedisChatMessageHistory(session_id=session_id, url=REDIS_URL)
        except Exception as e:
            print(f"[WARN] Redis no disponible ({e}). Usando memoria local temporal.")
            return ChatMessageHistory()
    else:
        print("[INFO] Redis deshabilitado, usando ChatMessageHistory en memoria.")
        return ChatMessageHistory()

def make_global_summary_memory(llm: ChatOpenAI):
    return ConversationSummaryMemory(llm=llm, memory_key="summary_context", return_messages=True)

def make_agent_window_memory(k: int = 5):
    return ConversationBufferWindowMemory(k=k, memory_key="chat_history", return_messages=True)

def make_hybrid_memory(llm: ChatOpenAI, max_tokens: int = 800):
    return ConversationSummaryBufferMemory(
        llm=llm, max_token_limit=max_tokens, memory_key="summary_context", return_messages=True
    )

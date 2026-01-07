import os
from typing import Optional
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def make_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None
):
    provider = (provider or DEFAULT_PROVIDER).lower()
    model = model or DEFAULT_MODEL
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE

    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    else:
        # Only OpenAI supported in this build to avoid extra optional providers.
        raise ValueError(f"Unsupported provider: {provider}. Supported: openai")
    
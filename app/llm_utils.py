import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
    elif provider == "ollama":
        return ChatOllama(model=model, base_url=OLLAMA_BASE_URL, temperature=temperature)
    elif provider == "gemini":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY required for Gemini")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=GOOGLE_API_KEY)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
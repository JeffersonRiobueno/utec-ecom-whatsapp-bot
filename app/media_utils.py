"""Utilidades para procesar mensajes multimedia (audio e imagen)."""

import os
import base64
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_gemini_llm():
    """Obtener instancia de Gemini para multimedia."""
    return ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

def transcribe_audio(base64_audio: str) -> str:
    """Transcribe audio base64 a texto usando Gemini."""
    logger.info("Transcribiendo audio...")
    try:
        audio_data = base64.b64decode(base64_audio)
        logger.info(f"Base64 decodificado exitosamente, tamaño: {len(audio_data)} bytes")
    except Exception as e:
        logger.error(f"Base64 inválido para audio: {e}")
        return f"Error: Base64 de audio inválido. {e}"

    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("models/gemini-2.5-flash")

        response = model.generate_content([
            "Transcribe este audio a texto.",
            {"mime_type": "audio/ogg; codecs=opus", "data": audio_data}
        ])
        transcribed = response.text
        logger.info(f"Transcripción obtenida: '{transcribed}'")

        if not transcribed or transcribed.strip() == "":
            logger.error("Transcripción vacía o inválida.")
            return "Error: No se pudo transcribir el audio. Intente nuevamente."

        return transcribed
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        return f"Error en transcripción: {e}"

def extract_text_from_image(base64_image: str, mimetype: str) -> str:
    """Extrae texto de imagen base64 usando Gemini OCR."""
    logger.info(f"Extrayendo texto de imagen, tamaño base64: {len(base64_image)}")
    try:
        image_data = base64.b64decode(base64_image)
        logger.info(f"Base64 decodificado exitosamente, tamaño: {len(image_data)} bytes")
    except Exception as e:
        logger.error(f"Base64 inválido para imagen: {e}")
        return f"Error: Base64 de imagen inválido. {e}"

    try:
        llm = get_gemini_llm()
        data_url = f"data:{mimetype};base64,{base64_image}"
        message = HumanMessage(content=[
            {"type": "text", "text": "Extrae el texto de esta imagen usando OCR."},
            {"type": "image_url", "image_url": {"url": data_url}}
        ])
        response = llm.invoke([message])
        extracted = response.content
        logger.info(f"Texto extraído de imagen: '{extracted}'")

        if not extracted or extracted.strip() == "":
            logger.error("Texto extraído vacío o inválido.")
            return "Error: No se pudo extraer texto de la imagen. Intente con una imagen más clara."

        return extracted
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return f"Error en OCR: {e}"

def preprocess_message(text: str, mimetype: str, filename: str) -> str:
    """Preprocesa el mensaje basado en mimetype, convirtiendo a texto si es necesario."""
    if mimetype == "text" or mimetype.startswith("text/"):
        return text
    elif mimetype.startswith("audio/ogg; codecs=opus") or mimetype.startswith("audio/"):
        return transcribe_audio(text)  # text es base64
    elif mimetype.startswith("image/"):
        return extract_text_from_image(text, mimetype)  # text es base64
    else:
        logger.warning(f"Tipo de mensaje no soportado: {mimetype}")
        return f"Tipo de mensaje no soportado: {mimetype}. Por favor use texto, audio o imagen."
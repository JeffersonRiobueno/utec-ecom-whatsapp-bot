"""Utilidades para procesar mensajes multimedia (audio e imagen)."""

import os
import base64
import logging
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import openai

load_dotenv()
logger = logging.getLogger(__name__)


def transcribe_audio(base64_audio: str, provider: str = "openai") -> str:
    """Transcribe audio base64 a texto usando el provider especificado."""
    logger.info(f"Transcribiendo audio con {provider}...")
    try:
        audio_data = base64.b64decode(base64_audio)
        logger.info(f"Base64 decodificado exitosamente, tamaño: {len(audio_data)} bytes")
    except Exception as e:
        logger.error(f"Base64 inválido para audio: {e}")
        return f"Error: Base64 de audio inválido. {e}"

    if provider.lower() == "openai":
        return _transcribe_audio_openai(audio_data)
    else:
        logger.warning(f"Provider {provider} no soporta transcripción de audio. Use 'openai'.")
        return "Error: provider not supported for audio transcription. Use 'openai'."

# Gemini-specific transcription removed to avoid Google dependency. Use OpenAI transcription.

def _transcribe_audio_openai(audio_data: bytes) -> str:
    try:
        import tempfile
        import os

        # Guardar temporalmente el audio
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(temp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        # Limpiar archivo temporal
        os.unlink(temp_file_path)

        logger.info(f"Transcripción OpenAI obtenida: '{transcript}'")

        if not transcript or transcript.strip() == "":
            logger.error("Transcripción vacía o inválida.")
            return "Error: No se pudo transcribir el audio. Intente nuevamente."

        return transcript
    except Exception as e:
        logger.error(f"Error en transcripción OpenAI: {e}")
        return f"Error en transcripción: {e}"

def extract_text_from_image(base64_image: str, mimetype: str, provider: str = "openai") -> str:
    """Extrae texto de imagen base64 usando el provider especificado."""
    logger.info(f"Extrayendo texto de imagen con {provider}, tamaño base64: {len(base64_image)}")
    try:
        image_data = base64.b64decode(base64_image)
        logger.info(f"Base64 decodificado exitosamente, tamaño: {len(image_data)} bytes")
    except Exception as e:
        logger.error(f"Base64 inválido para imagen: {e}")
        return f"Error: Base64 de imagen inválido. {e}"

    if provider.lower() == "openai":
        return _extract_text_from_image_openai(base64_image, mimetype)
    else:
        logger.warning(f"Provider {provider} no soporta OCR. Use 'openai'.")
        return "Error: provider not supported for image OCR. Use 'openai'."

# Gemini-specific OCR removed to avoid Google dependency. Use OpenAI-based OCR instead.

def _extract_text_from_image_openai(base64_image: str, mimetype: str) -> str:
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        data_url = f"data:{mimetype};base64,{base64_image}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # o gpt-4o para mejor visión
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extrae el texto de esta imagen usando OCR."},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            max_tokens=500
        )
        extracted = response.choices[0].message.content
        logger.info(f"Texto extraído OpenAI: '{extracted}'")

        if not extracted or extracted.strip() == "":
            logger.error("Texto extraído vacío o inválido.")
            return "Error: No se pudo extraer texto de la imagen. Intente con una imagen más clara."

        return extracted
    except Exception as e:
        logger.error(f"Error en OCR OpenAI: {e}")
        return f"Error en OCR: {e}"

def preprocess_message(text: str, mimetype: str, filename: str, provider: str = "gemini") -> str:
    """Preprocesa el mensaje basado en mimetype, convirtiendo a texto si es necesario."""
    if mimetype == "text" or mimetype.startswith("text/"):
        return text
    elif mimetype.startswith("audio/ogg; codecs=opus") or mimetype.startswith("audio/"):
        return transcribe_audio(text, provider)  # text es base64
    elif mimetype.startswith("image/"):
        return extract_text_from_image(text, mimetype, provider)  # text es base64
    else:
        logger.warning(f"Tipo de mensaje no soportado: {mimetype}")
        return f"Tipo de mensaje no soportado: {mimetype}. Por favor use texto, audio o imagen."
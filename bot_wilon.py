import os
import requests
from openai import OpenAI

# Configuración de Evolution API
INSTANCE_NAME = "wilon_bot"
API_URL = "https://evolution-api-wilon.onrender.com"
API_KEY = "123456"

# Inicializar cliente de OpenAI (utiliza la variable de entorno OPENAI_API_KEY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def responder_whatsapp(numero, texto_mensaje):
    """Envía respuesta de texto directa sin retardo (delay)."""
    url = f"{API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }

    # Aseguramos enviar solo el número limpio (ej. 573108788739)
    numero_limpio = numero.split("@")[0]

    # Payload simplificado e inmediato:
    payload = {
        "number": numero_limpio,
        "text": texto_mensaje,
        "textMessage": {"text": texto_mensaje}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Estado de envío: {response.status_code}")
        print(f"Respuesta API: {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")
        return None


def obtener_recomendacion_anime(prompt_usuario):
    """Consulta a la API de OpenAI para obtener una recomendación de anime personalizada."""
    if not prompt_usuario.strip():
        prompt_usuario = "Recomiéndame un anime popular muy bueno de cualquier género."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto recomendador de anime entusiasta y conciso. "
                        "Da recomendaciones breves, entretenidas, formateadas con emojis y negritas para WhatsApp. "
                        "Incluye: Título, Género, Número de episodios y un resumen sin spoilers de máximo 2 oraciones."
                    )
                },
                {"role": "user", "content": prompt_usuario}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error con OpenAI: {e}")
        return "❌ Ocurrió un error al generar la recomendación. Intenta de nuevo."
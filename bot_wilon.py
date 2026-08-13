import requests

INSTANCE_NAME = "wilon_bot"
API_URL = "https://evolution-api-latest-bkbs.onrender.com"
API_KEY = "123456"


def responder_whatsapp(numero, texto_mensaje):
    """Envía respuesta de texto directa sin retardo (delay)."""
    url = f"{API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}

    # Aseguramos enviar solo el número limpio (ej. 573108788739)
    numero_limpio = numero.split("@")[0]

    # Payload simplificado e inmediato:
    payload = {
        "number": numero_limpio,
        "text": texto_mensaje,
        "textMessage": {"text": texto_mensaje},
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📩 Estado de envío: {response.status_code}")
        print(f"📄 Respuesta API: {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")
        return None
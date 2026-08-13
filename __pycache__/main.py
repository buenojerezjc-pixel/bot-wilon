import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cargar variables de entorno
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")


@app.route("/webhook", methods=["POST"])
def webhook():
    request_json = request.get_json(silent=True) or {}

    # --- PEGA EL PARSEO SEGURO AQUÍ ---
    data = request_json.get("data", {})

    # Si 'data' viene como una lista, tomamos el primer elemento
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    # Extraer el mensaje y el remitente
    key = data.get("key", {}) if isinstance(data, dict) else {}
    remote_jid = key.get("remoteJid")
    from_me = key.get("fromMe", False)

    if not from_me and remote_jid:
        message_content = (
            data.get("message", {}) if isinstance(data, dict) else {}
        )
        text = (
            message_content.get("conversation")
            or message_content.get("extendedTextMessage", {}).get("text")
            or ""
        )

        # Lógica para responder al #hola
        if text.strip().lower().startswith("#hola"):
            # Endpoint correcto para Evolution API v2
            url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
            headers = {
                "apikey": EVOLUTION_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "number": remote_jid,
                "options": {
                    "delay": 1200,
                    "presence": "composing",
                    "linkPreview": False,
                },
                "textMessage": {"text": "¡Hola! 👋 Tu bot ya está respondiendo perfectamente desde Render."},
            }
            # Enviar mensaje a WhatsApp
            requests.post(url, json=payload, headers=headers)

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
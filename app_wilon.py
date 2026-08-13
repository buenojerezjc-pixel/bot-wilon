import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")


@app.route("/webhook", methods=["POST"])
def webhook():
    request_json = request.get_json(silent=True) or {}

    # Parseo seguro de la data
    data = request_json.get("data", {})
    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    if not isinstance(data, dict):
        return jsonify({"status": "ignored"}), 200

    key = data.get("key", {})
    remote_jid = key.get("remoteJid")
    from_me = key.get("fromMe", False)

    if not from_me and remote_jid:
        message_content = data.get("message", {})
        text = (
            message_content.get("conversation")
            or message_content.get("extendedTextMessage", {}).get("text")
            or ""
        )

        if text.strip().lower().startswith("#hola"):
            # URL y headers alineados con Evolution API v2
            url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
            headers = {
                "apikey": EVOLUTION_API_KEY,
                "Content-Type": "application/json",
            }

            # En Evolution API v2 el número debe ser limpio y el campo es 'text'
            clean_number = remote_jid.split("@")[0]

            payload = {
                "number": clean_number,
                "text": "¡Hola! 👋 Tu bot ya está respondiendo perfectamente desde Render.",
                "delay": 1200,
                "linkPreview": False,
            }

            res = requests.post(url, json=payload, headers=headers)
            print(
                f"Respuesta de Evolution API: {res.status_code} - {res.text}"
            )

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
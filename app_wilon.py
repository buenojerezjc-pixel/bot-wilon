import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE")

# Variable global para controlar el estado del bot
bot_activo = True


@app.route("/webhook", methods=["POST"])
def webhook():
    global bot_activo

    request_json = request.get_json(silent=True) or {}
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

        comando = text.strip().lower()
        respuesta_texto = None

        # --- COMANDOS PARA ENCENDER Y APAGAR ---
        if comando == "#desactivar wilon":
            bot_activo = False
            respuesta_texto = "🤫 *Wilon Bot ha sido desactivado.* No responderé a más comandos hasta que me vuelvas a activar."

        elif comando == "#activar wilon":
            bot_activo = True
            respuesta_texto = "🔊 *Wilon Bot ha sido activado.* ¡Estoy listo de nuevo!"

        # --- COMANDOS SOLO SI EL BOT ESTÁ ACTIVO ---
        elif bot_activo:
            if comando.startswith("#hola"):
                respuesta_texto = "¡Hola! 👋 Soy *Wilon Bot*. Escribe *#ayuda* para ver mis opciones."
            elif comando.startswith("#ayuda") or comando.startswith("#menu"):
                respuesta_texto = (
                    "🤖 *WILON BOT*\n\n"
                    "• *#hola* - Saludo inicial.\n"
                    "• *#desactivar wilon* - Apaga el bot temporalmente.\n"
                    "• *#activar wilon* - Enciende el bot nuevamente."
                )

        # Envío del mensaje si aplica
        if respuesta_texto:
            url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
            headers = {
                "apikey": EVOLUTION_API_KEY,
                "Content-Type": "application/json",
            }
            clean_number = remote_jid.split("@")[0]

            payload = {
                "number": clean_number,
                "text": respuesta_texto,
                "delay": 1000,
                "linkPreview": False,
            }
            requests.post(url, json=payload, headers=headers)

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
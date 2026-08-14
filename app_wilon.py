from flask import Flask, request, jsonify
# Añadimos 'obtener_recomendacion_anime' a la importación
from bot_wilon import responder_whatsapp, obtener_recomendacion_anime

import os
from flask import Flask, request, jsonify
# Importamos la función de envío y la de OpenAI desde bot_wilon
from bot_wilon import responder_whatsapp, obtener_recomendacion_anime

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    
    # Extraemos los datos del payload de Evolution API
    key = data.get("data", {}).get("key", {})
    remote_jid = key.get("remoteJid")
    from_me = key.get("fromMe", False)

    # Procesamos solo si el mensaje no lo envió el propio bot
    if not from_me and remote_jid:
        message_content = (
            data.get("data", {}).get("message", {})
            if isinstance(data.get("data"), dict) else {}
        )
        
        # Extraemos el texto del mensaje
        text = (
            message_content.get("conversation")
            or message_content.get("extendedTextMessage", {}).get("text")
            or ""
        )
        
        texto_limpio = text.strip().lower()

        # 1. Comando de prueba #hola
        if texto_limpio.startswith("#hola"):
            responder_whatsapp(remote_jid, "¡Hola! 👋 Tu bot sigue respondiendo perfectamente desde Render.")

        # 2. NUEVO: Comando #anime
        elif texto_limpio.startswith("#anime"):
            # Extraemos la petición del usuario quitando la palabra '#anime'
            peticion = text.strip()[6:].strip()
            
            # Consultamos a OpenAI
            respuesta_anime = obtener_recomendacion_anime(peticion)
            
            # Enviamos la respuesta a WhatsApp
            responder_whatsapp(remote_jid, respuesta_anime)

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
    # --- RUTA RAÍZ PARA CRON-JOB / DESPERTADOR ---
@app.route('/', methods=['GET'])
def index():
    return "¡Wilon está despierto y listo! 🤖", 200
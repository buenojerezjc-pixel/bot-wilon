import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------------------------------
# CONFIGURACIÓN EXACTA DESDE TUS VARIABLES DE RENDER
# ----------------------------------------------------
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "https://evolution-api-wilon.onrender.com").rstrip('/')
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE", "wilon")
API_KEY = os.getenv("EVOLUTION_API_KEY", "42267431-8921-4d83-a9d5-31a89c211234")


def enviar_mensaje_whatsapp(destino, texto, quoted_data=None):
    """
    Envía la respuesta a WhatsApp usando la URL y API Key
    exactas de Render.
    """
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    payload = {
        "number": destino,
        "textMessage": {
            "text": texto
        },
        "options": {
            "presence": "composing",
            "linkPreview": False,
            "remoteJid": destino
        }
    }
    
    if quoted_data:
        payload["quoted"] = quoted_data

    try:
        print(f"🔗 Apuntando a: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📤 Respuesta enviada a [{destino}] (HTTP {response.status_code}):", response.text)
        return response.status_code
    except Exception as e:
        print("❌ Error de conexión al enviar mensaje:", e)
        return None


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    print("📩 EVENTO RECIBIDO EN WEBHOOK:", data)
    
    try:
        if 'data' in data:
            data_inner = data['data']
            key_obj = data_inner.get('key', {})
            message_obj = data_inner.get('message', {})
            
            remote_jid = key_obj.get('remoteJid', '')
            remote_alt = key_obj.get('remoteJidAlt', '')
            from_me = key_obj.get('fromMe', False)
            
            # REGLA: Ignorar si viene de nosotros mismos (salvo en grupos)
            if from_me and '@g.us' not in remote_jid:
                return jsonify({"status": "ignored_from_me"}), 200

            # DETERMINAR DESTINO
            destino = remote_jid
            if remote_alt and '@s.whatsapp.net' in remote_alt:
                destino = remote_alt

            quoted_data = {
                "key": key_obj,
                "message": message_obj
            }

            # Extraer texto del mensaje
            texto_mensaje = ""
            if 'conversation' in message_obj:
                texto_mensaje = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj:
                texto_mensaje = message_obj['extendedTextMessage'].get('text', '')

            texto_limpio = texto_mensaje.strip().lower()
            print(f"💬 Mensaje procesado de [{destino}]: '{texto_limpio}'")
            
            # COMANDOS AUTOMÁTICOS
            if texto_limpio in ['#activar wilon', '#hola']:
                respuesta = "🤖 *Wilon Bot Activado:*\n¡Hola! Estoy activo en este chat. ¿En qué te puedo colaborar?"
                enviar_mensaje_whatsapp(destino, respuesta, quoted_data)

            elif texto_limpio == '#desactivar wilon':
                respuesta = "😴 *Wilon Bot Desactivado:*\nHe pasado al modo suspensión. Para reactivarme escribe `#activar wilon`."
                enviar_mensaje_whatsapp(destino, respuesta, quoted_data)

            elif texto_limpio == '#anime':
                respuesta = "🍿 *Sección Anime:*\nPróximamente catálogo de recomendaciones y novedades."
                enviar_mensaje_whatsapp(destino, respuesta, quoted_data)
                
            elif texto_limpio in ['#menu', '#ayuda']:
                respuesta = (
                    "📜 *Comandos Disponibles:*\n\n"
                    "• `#activar wilon` / `#hola` - Activa el bot\n"
                    "• `#desactivar wilon` - Desactiva el bot\n"
                    "• `#anime` - Sección Anime\n"
                    "• `#menu` / `#ayuda` - Lista de comandos"
                )
                enviar_mensaje_whatsapp(destino, respuesta, quoted_data)

    except Exception as e:
        print("⚠️ Error procesando estructura:", e)

    return jsonify({"status": "success"}), 200

@app.route('/', methods=['GET'])
def index():
    return "Bot Wilon en línea y sincronizado con Render 🚀", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
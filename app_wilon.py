import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------------------------------
# CONFIGURACIÓN DE EVOLUTION API
# ----------------------------------------------------
EVOLUTION_API_URL = "https://evolution-wilon-api.onrender.com"
INSTANCE_NAME = "wilon"

# API Key Maestra
API_KEY = "MiClaveSuperSecreta123"


def enviar_mensaje_whatsapp(destino, texto, quoted_data=None):
    """
    Envía la respuesta a WhatsApp forzando el identificador original
    en las opciones profundas para evitar que la API lo sobreescriba.
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
            # FORZAMOS A QUE LA API RESPETE EL @lid O @g.us AQUÍ
            "remoteJid": destino
        }
    }
    
    if quoted_data:
        payload["quoted"] = quoted_data

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📤 Respuesta enviada a [{destino}] (HTTP {response.status_code}):", response.text)
    except Exception as e:
        print("❌ Error de red al enviar mensaje por HTTP:", e)


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
            
            # REGLA DEL DUEÑO DEL QR (fromMe)
            if from_me and '@g.us' not in remote_jid:
                return jsonify({"status": "ignored_from_me_private"}), 200

            # DETERMINAR DESTINO (Aceptando el LID tal cual viene)
            if '@g.us' in remote_jid:
                destino = remote_jid
            elif remote_alt and '@s.whatsapp.net' in remote_alt:
                destino = remote_alt
            else:
                destino = remote_jid

            quoted_data = {
                "key": key_obj,
                "message": message_obj
            }

            texto_mensaje = ""
            if 'conversation' in message_obj:
                texto_mensaje = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj:
                texto_mensaje = message_obj['extendedTextMessage'].get('text', '')

            texto_limpio = texto_mensaje.strip().lower()
            print(f"💬 Mensaje procesado de [{destino}]: '{texto_limpio}'")
            
            # LÓGICA DE COMANDOS
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
        print("⚠️ Error al procesar la estructura del mensaje:", e)

    return jsonify({"status": "success"}), 200

@app.route('/', methods=['GET'])
def index():
    return "Bot funcionando", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
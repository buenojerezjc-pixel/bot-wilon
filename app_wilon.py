import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------------------------------
# CONFIGURACIÓN DE EVOLUTION API
# ----------------------------------------------------
EVOLUTION_API_URL = "https://evolution-wilon-api.onrender.com"
INSTANCE_NAME = "wilon"

# API Key Maestra de Evolution API
API_KEY = "MiClaveSuperSecreta123"


def enviar_mensaje_whatsapp(numero, texto):
    """Envía la respuesta a WhatsApp a través de Evolution API v2"""
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    # Payload exacto exigido por Evolution v2
    payload = {
        "number": numero,
        "textMessage": {
            "text": texto
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📤 Respuesta enviada a WhatsApp ({response.status_code}):", response.text)
    except Exception as e:
        print("❌ Error al enviar mensaje por HTTP:", e)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Ruta del webhook que procesa los mensajes de WhatsApp"""
    data = request.get_json()
    
    print("📩 EVENTO RECIBIDO EN WEBHOOK:", data)
    
    try:
        if data and 'data' in data and 'message' in data['data']:
            message_obj = data['data']['message']
            key_obj = data['data']['key']
            
            # Evitar bucles omitiendo mensajes propios
            from_me = key_obj.get('fromMe', False)
            if from_me:
                return jsonify({"status": "ignored_from_me"}), 200
            
            remote_jid = key_obj.get('remoteJid', '')
            
            # Captura del contenido del mensaje
            texto_mensaje = ""
            if 'conversation' in message_obj:
                texto_mensaje = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj and 'text' in message_obj['extendedTextMessage']:
                texto_mensaje = message_obj['extendedTextMessage']['text']
                
            texto_limpio = texto_mensaje.strip().lower()
            print(f"💬 Mensaje de [{remote_jid}]: '{texto_limpio}'")
            
            # ----------------------------------------------------
            # LÓGICA DE COMANDOS
            # ----------------------------------------------------
            if texto_limpio == '#hola':
                respuesta = "¡Hola! 👋 Soy el bot de Wilon. ¿En qué te puedo ayudar hoy?"
                enviar_mensaje_whatsapp(remote_jid, respuesta)

            elif texto_limpio == '#anime':
                respuesta = "🍿 ¡Sección Anime! Próximamente recomendaciones y listas actualizadas."
                enviar_mensaje_whatsapp(remote_jid, respuesta)

            elif texto_limpio in ['#menu', '#ayuda']:
                respuesta = "📜 *Comandos Disponibles:*\n\n• `#hola` - Saludo inicial\n• `#anime` - Ver sección de anime\n• `#menu` - Ver esta lista de ayuda"
                enviar_mensaje_whatsapp(remote_jid, respuesta)

    except Exception as e:
        print("⚠️ Error al procesar la estructura del mensaje:", e)

    return jsonify({"status": "success"}), 200


@app.route('/', methods=['GET'])
def index():
    return "Bot de Wilon funcionando correctamente", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
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


def enviar_mensaje_whatsapp(destino, texto):
    """
    Envía la respuesta a WhatsApp al destino correcto.
    Maneja Grupos (@g.us), Números normales y Chats Privados LID (@lid).
    """
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    # Para la Evolution API, si el destino contiene @lid o @g.us, 
    # enviamos la dirección completa para que no le auto-concatene @s.whatsapp.net
    payload = {
        "number": destino,
        "textMessage": {
            "text": texto
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📤 Respuesta enviada a [{destino}] (HTTP {response.status_code}):", response.text)
    except Exception as e:
        print("❌ Error de red al enviar mensaje por HTTP:", e)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Ruta del webhook que procesa los eventos entrantes de WhatsApp"""
    data = request.get_json()
    
    print("📩 EVENTO RECIBIDO EN WEBHOOK:", data)
    
    try:
        if data and 'data' in data and 'message' in data['data']:
            message_obj = data['data']['message']
            key_obj = data['data']['key']
            
            remote_jid = key_obj.get('remoteJid', '')
            remote_alt = key_obj.get('remoteJidAlt', '')
            from_me = key_obj.get('fromMe', False)
            
            # ----------------------------------------------------
            # REGLA DEL DUEÑO DEL QR (fromMe)
            # ----------------------------------------------------
            # Ignora auto-respuestas en chat privado propio, pero permite usarlo en grupos
            if from_me and '@g.us' not in remote_jid:
                return jsonify({"status": "ignored_from_me_private"}), 200

            # ----------------------------------------------------
            # DETERMINAR DESTINO EXACTO
            # ----------------------------------------------------
            if '@g.us' in remote_jid:
                # 1. GRUPO: Respondemos al grupo directamente (Sin necesidad de @bot)
                destino = remote_jid
            elif remote_alt and '@s.whatsapp.net' in remote_alt:
                # 2. CHAT PRIVADO: Si tenemos el número real en remoteJidAlt
                destino = remote_alt
            else:
                # 3. CHAT PRIVADO CON PRIVACIDAD LID: Enviamos la ID LID completa (@lid)
                destino = remote_jid

            # ----------------------------------------------------
            # MANEJO FLEXIBLE DE MENSAJES
            # ----------------------------------------------------
            texto_mensaje = ""
            if 'conversation' in message_obj:
                texto_mensaje = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj:
                texto_mensaje = message_obj['extendedTextMessage'].get('text', '')
            elif 'buttonsResponseMessage' in message_obj:
                texto_mensaje = message_obj['buttonsResponseMessage'].get('selectedButtonId', '')
            elif 'listResponseMessage' in message_obj:
                texto_mensaje = message_obj['listResponseMessage'].get('singleSelectReply', {}).get('selectedRowId', '')

            texto_limpio = texto_mensaje.strip().lower()
            print(f"💬 Mensaje procesado de [{destino}]: '{texto_limpio}'")
            
            # ----------------------------------------------------
            # LÓGICA DE COMANDOS
            # ----------------------------------------------------
            if texto_limpio in ['#activar wilon', '#hola']:
                respuesta = "🤖 *Wilon Bot Activado:*\n¡Hola! Estoy activo en este chat. ¿En qué te puedo colaborar?"
                enviar_mensaje_whatsapp(destino, respuesta)

            elif texto_limpio == '#desactivar wilon':
                respuesta = "😴 *Wilon Bot Desactivado:*\nHe pasado al modo suspensión. Para reactivarme escribe `#activar wilon`."
                enviar_mensaje_whatsapp(destino, respuesta)

            elif texto_limpio == '#anime':
                respuesta = "🍿 *Sección Anime:*\nPróximamente catálogo de recomendaciones y novedades."
                enviar_mensaje_whatsapp(destino, respuesta)

            elif texto_limpio in ['#menu', '#ayuda']:
                respuesta = (
                    "📜 *Comandos Disponibles:*\n\n"
                    "• `#activar wilon` / `#hola` - Activa el bot\n"
                    "• `#desactivar wilon` - Desactiva el bot\n"
                    "• `#anime` - Sección Anime\n"
                    "• `#menu` / `#ayuda` - Lista de comandos"
                )
                enviar_mensaje_whatsapp(destino, respuesta)

    except Exception as e:
        print("⚠️ Error al procesar la estructura del mensaje:", e)

    return jsonify({"status": "success"}), 200


@app.route('/', methods=['GET'])
def index():
    return "Bot de Wilon funcionando correctamente", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
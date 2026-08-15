import os
import re
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
    Envía la respuesta a WhatsApp.
    - Si es grupo: usa el ID del grupo (@g.us).
    - Si es privado: usa el número telefónico real (ej: 573108788739).
    """
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    if '@g.us' in destino:
        numero_destino = destino
    else:
        # Extraer estrictamente los dígitos numéricos si es un chat privado
        numero_destino = re.sub(r'\D', '', destino.split('@')[0])

    payload = {
        "number": numero_destino,
        "textMessage": {
            "text": texto
        },
        "options": {
            "presence": "composing",
            "linkPreview": False
        }
    }
    
    if '@g.us' in destino:
        payload["options"]["remoteJid"] = destino

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📤 Respuesta enviada a [{numero_destino}] (HTTP {response.status_code}):", response.text)
    except Exception as e:
        print("❌ Error de red al enviar mensaje por HTTP:", e)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Ruta del webhook que procesa los eventos entrantes de WhatsApp"""
    data = request.get_json() or {}
    
    print("📩 EVENTO RECIBIDO EN WEBHOOK:", data)
    
    try:
        # Extraer sender de la raíz del JSON o de la sub-clave 'data'
        sender_root = data.get('sender', '')
        
        if 'data' in data:
            data_inner = data['data']
            key_obj = data_inner.get('key', {})
            message_obj = data_inner.get('message', {})
            
            remote_jid = key_obj.get('remoteJid', '')
            remote_alt = key_obj.get('remoteJidAlt', '')
            sender_inner = data_inner.get('sender', '')
            from_me = key_obj.get('fromMe', False)
            
            # Buscar el sender real en cualquier parte del JSON
            sender_real = sender_root or sender_inner or remote_alt
            
            # ----------------------------------------------------
            # REGLA DEL DUEÑO DEL QR (fromMe)
            # ----------------------------------------------------
            # En PRIVADOS: Ignorar si el mensaje fue enviado por el dueño del QR
            if from_me and '@g.us' not in remote_jid:
                return jsonify({"status": "ignored_from_me_private"}), 200

            # ----------------------------------------------------
            # DETERMINAR DESTINO REAL DE RESPUESTA
            # ----------------------------------------------------
            if '@g.us' in remote_jid:
                # 1. GRUPOS: Responde directo al grupo (sin requerir @bot)
                destino = remote_jid
            else:
                # 2. PRIVADOS / PRIVACIDAD LID:
                #    Priorizar el número telefónico numérico real extraído de sender_real
                if sender_real and '@s.whatsapp.net' in sender_real:
                    destino = sender_real
                elif '@s.whatsapp.net' in remote_jid:
                    destino = remote_jid
                else:
                    # Si no viene @s.whatsapp.net pero sender_real tiene contenido, usarlo
                    destino = sender_real if sender_real else remote_jid

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
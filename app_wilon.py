import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración de tu API de Evolution
# (Asegúrate de que la URL de la API y la API key coincidan con tus datos)
EVOLUTION_API_URL = "https://evolution-wilon-api.onrender.com"
INSTANCE_NAME = "wilon"
API_KEY = "xaipslkt8clk75y0wlnpj"  # Coloca aquí tu Global API Key si la usas en la petición


payload = {
    "number": numero,
    "textMessage": {
        "text": texto
    }
}


@app.route('/webhook', methods=['POST'])
def webhook():
    """Ruta que recibe las notificaciones de WhatsApp desde Evolution API"""
    data = request.get_json()
    
    # Imprimir en la consola de Render para depuración
    print("📩 EVENTO RECIBIDO EN WEBHOOK:", data)
    
    try:
        # Validar si el evento contiene un mensaje
        if data and 'data' in data and 'message' in data['data']:
            message_obj = data['data']['message']
            key_obj = data['data']['key']
            
            # Verificar que el mensaje NO haya sido enviado por el propio bot (fromMe)
            from_me = key_obj.get('fromMe', False)
            if from_me:
                return jsonify({"status": "ignored_from_me"}), 200
            
            # Extraer el número del remitente y el texto enviado
            remote_jid = key_obj.get('remoteJid', '')
            
            # Formatos de texto posibles en WhatsApp
            texto_mensaje = ""
            if 'conversation' in message_obj:
                texto_mensaje = message_obj['conversation']
            elif 'extendedTextMessage' in message_obj and 'text' in message_obj['extendedTextMessage']:
                texto_mensaje = message_obj['extendedTextMessage']['text']
                
            texto_limpio = texto_mensaje.strip().lower()
            print(f"💬 Mensaje de [{remote_jid}]: '{texto_limpio}'")
            
            # ----------------------------------------------------
            # 🤖 LÓGICA DE COMANDOS DEL BOT
            # ----------------------------------------------------
            if texto_limpio == '#hola':
                respuesta = "¡Hola! 👋 Soy el bot de Wilon. ¿En qué te puedo ayudar hoy?"
                enviar_mensaje_whatsapp(remote_jid, respuesta)

            elif texto_limpio == '#anime':
                respuesta = "🍿 ¡Sección Anime! Próximamente recomendaciones y listas actualizadas."
                enviar_mensaje_whatsapp(remote_jid, respuesta)

            elif texto_limpio == '#menu' or texto_limpio == '#ayuda':
                respuesta = "📜 *Comandos Disponibles:*\n\n• `#hola` - Saludo inicial\n• `#anime` - Ver sección de anime\n• `#menu` - Ver esta lista de ayuda"
                enviar_mensaje_whatsapp(remote_jid, respuesta)

    except Exception as e:
        print("⚠️ Error al procesar la estructura del mensaje:", e)

    return jsonify({"status": "success"}), 200


@app.route('/', methods=['GET'])
def index():
    """Ruta de prueba de estado"""
    return "Bot de Wilon funcionando correctamente", 200


if __name__ == '__main__':
    # Para ejecución local
    app.run(host='0.0.0.0', port=5000)
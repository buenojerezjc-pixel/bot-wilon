from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración de tu Evolution API local
# Nota: Si subes esto a Render, necesitas usar tu URL pública (ej. Ngrok) 
# para que Render se conecte a tu PC.
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
API_KEY = "42267431-8921-4d83-a9d5-31a89c211234"
INSTANCE_NAME = "bot-wilon"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    try:
        # Extrae la información del mensaje entrante
        message_data = data.get('data', {})
        key = message_data.get('key', {})
        
        # Ignorar los mensajes enviados por el propio bot
        if key.get('fromMe'):
            return jsonify({'status': 'ignored'}), 200

        # Obtener el número de la persona que escribe
        numero = key.get('remoteJid')
        
        # Obtener el texto del mensaje
        mensaje_obj = message_data.get('message', {})
        texto_mensaje = (
            mensaje_obj.get('conversation') or 
            mensaje_obj.get('extendedTextMessage', {}).get('text') or 
            ""
        ).strip()

        # =========================================================
        # 🎯 FILTRO DEL PREFIJO '#'
        # =========================================================
        if texto_mensaje.startswith("#"):
            # Quita el '#' y pasa todo a minúsculas para leer la orden
            comando = texto_mensaje[1:].lower()  
            
            if comando == "hola":
                respuesta = "¡Hola! ¿En qué te puedo ayudar?"
            elif comando == "menu":
                respuesta = "Aquí tienes las opciones principales:\n1. Servicios\n2. Contacto"
            else:
                respuesta = f"El comando #{comando} no existe. Intenta con #hola o #menu."
                
            # Envía la respuesta a WhatsApp (SIN el prefijo '#')
            enviar_mensaje_whatsapp(numero, respuesta)
        # =========================================================

    except Exception as e:
        print("Error al procesar el mensaje:", e)

    return jsonify({'status': 'success'}), 200


def enviar_mensaje_whatsapp(numero, texto):
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero,
        "text": texto
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Respuesta de Evolution API:", response.status_code)
    except Exception as e:
        print("Error al enviar mensaje:", e)


if __name__ == '__main__':
    app.run(port=5000)
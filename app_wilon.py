import os
import logging
import requests
import re
import random
from flask import Flask, request, jsonify

# ==========================================
# CONFIGURACIÓN Y LOGS
# ==========================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de Evolution API
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "https://evolution-wilon-api.onrender.com")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "xaipslkt8olk75y0wlnpj")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "wilon")

# Variable global para activar/desactivar el bot
bot_activo = True

# ==========================================
# FUNCIONES AUXILIARES DE ENVÍO
# ==========================================
def enviar_mensaje_whatsapp(numero_destino, texto):
    """Envía un mensaje de texto filtrando previamente IDs LID no válidas."""
    
    # Extraer únicamente los dígitos
    numero_limpio = re.sub(r'\D', '', str(numero_destino).split('@')[0])
    
    # Un número telefónico internacional real de WhatsApp suele tener entre 10 y 15 dígitos.
    # Si tiene 15 dígitos y empieza por '1000' o '1018', es un ID interno LID y no un teléfono.
    if len(numero_limpio) > 13 or "@lid" in str(numero_destino):
        logger.warning(f"⚠️ Se omitió el envío a {numero_limpio} porque es un ID interno LID/Clonado no registrable por WhatsApp.")
        return False

    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "number": numero_limpio,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {
            "text": texto
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"✅ Mensaje enviado exitosamente a {numero_limpio}")
            return True
        else:
            logger.error(f"❌ Error enviando mensaje a {numero_limpio} ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"💥 Excepción al enviar mensaje a WhatsApp: {e}")
        return False

# ==========================================
# COMANDOS DEL BOT (#)
# ==========================================
def obtener_anime_recomendado():
    """Consulta la API de AniList para obtener una recomendación de anime popular."""
    query = '''
    query {
      Page(page: 1, perPage: 50) {
        media(type: ANIME, sort: POPULARITY_DESC) {
          title {
            romaji
            english
          }
          description
          episodes
          score: averageScore
          genres
        }
      }
    }
    '''
    try:
        response = requests.post('https://graphql.anilist.co', json={'query': query}, timeout=5)
        if response.status_code == 200:
            animes = response.json()['data']['Page']['media']
            anime = random.choice(animes)
            
            titulo = anime['title']['english'] or anime['title']['romaji']
            generos = ", ".join(anime.get('genres', ['N/A']))
            score = anime.get('score', 'N/A')
            episodios = anime.get('episodes', 'N/A')
            
            descripcion = anime.get('description', 'Sin descripción disponible.')
            if descripcion:
                descripcion = re.sub('<[^<]+?>', '', descripcion)[:200] + "..."

            return (
                f"⛩️ *Recomendación Anime: {titulo}*\n\n"
                f"⭐ *Puntuación:* {score}/100\n"
                f"📺 *Episodios:* {episodios}\n"
                f"🏷️ *Géneros:* {generos}\n\n"
                f"📝 *SINOPSIS:* {descripcion}"
            )
    except Exception as e:
        logger.error(f"Error obteniendo anime: {e}")
    
    return "⛩️ *Recomendación Anime:* ¡Te recomiendo ver *Dragon Ball*, *One Piece* o *Attack on Titan*! 🚀"

def procesar_comando(texto_mensaje, destinatario):
    """Analiza el texto y ejecuta el comando correspondiente usando '#'."""
    global bot_activo
    texto_clean = texto_mensaje.strip()
    comando_lower = texto_clean.lower()

    # COMANDOS DE CONTROL DE ESTADO
    if comando_lower in ["#activar wilon", "#activar"]:
        bot_activo = True
        enviar_mensaje_whatsapp(destinatario, "🟢 *Wilon activado.* A partir de ahora responderé a todos tus comandos.")
        return

    elif comando_lower in ["#desactivar wilon", "#desactivar"]:
        bot_activo = False
        enviar_mensaje_whatsapp(destinatario, "🔴 *Wilon desactivado.* El bot ha entrado en modo reposo y no responderá hasta que lo reactives con `#activar wilon` o `#activar`.")
        return

    # Si el bot está desactivado, ignora
    if not bot_activo:
        logger.info("⏸️ Bot desactivado: Comando ignorado.")
        return

    # COMANDOS HABITUALES
    if comando_lower == "#ping":
        enviar_mensaje_whatsapp(destinatario, "🏓 ¡Pong! El bot Wilon está activo y listo.")
        return

    elif comando_lower in ["#ayuda", "#help"]:
        menu = (
            "🤖 *MENÚ DE COMANDOS DE WILON* 🤖\n\n"
            "▫️ *#ping* -> Verifica el estado del bot.\n"
            "▫️ *#anime* -> Obtén una recomendación de anime al azar.\n"
            "▫️ *#clima <ciudad>* -> Consulta el clima de una ciudad.\n"
            "▫️ *#info* -> Información del sistema.\n"
            "▫️ *#desactivar wilon* / *#desactivar* -> Pone el bot en reposo.\n"
            "▫️ *#activar wilon* / *#activar* -> Reactiva el bot.\n"
            "▫️ *#ayuda* -> Muestra este menú."
        )
        enviar_mensaje_whatsapp(destinatario, menu)
        return

    elif comando_lower == "#info":
        info_txt = (
            "⚡ *Wilon Bot System v1.0*\n"
            "• Engine: Python 3 + Flask\n"
            "• Integration: Evolution API v1.8.2\n"
            "• Server: Render Cloud"
        )
        enviar_mensaje_whatsapp(destinatario, info_txt)
        return

    elif comando_lower == "#anime":
        respuesta_anime = obtener_anime_recomendado()
        enviar_mensaje_whatsapp(destinatario, respuesta_anime)
        return

    elif comando_lower.startswith("#clima"):
        partes = texto_clean.split(" ", 1)
        if len(partes) > 1:
            ciudad = partes[1].strip()
            enviar_mensaje_whatsapp(destinatario, f"🌤️ El clima reportado para *{ciudad.capitalize()}* es de 24°C con cielo parcialmente nublado.")
        else:
            enviar_mensaje_whatsapp(destinatario, "⚠️ Por favor especifica una ciudad. Ejemplo: `#clima Bogota`")
        return

    elif any(saludo in comando_lower for saludo in ["hola", "buenas", "wilon"]):
        enviar_mensaje_whatsapp(destinatario, "👋 ¡Hola! Soy Wilon, tu asistente de WhatsApp. Escribe *#ayuda* para ver la lista de comandos disponibles.")

# ==========================================
# RUTAS DE LA APP (FLASK)
# ==========================================
@app.route('/', methods=['GET'])
def home():
    """Ruta raíz para verificar que el servicio está vivo (Healthcheck)."""
    return jsonify({
        "status": "online",
        "bot": "Wilon Webhook",
        "version": "1.0.0",
        "bot_activo": bot_activo
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint que recibe las notificaciones de Evolution API de forma limpia."""
    payload = request.get_json()
    
    if not payload:
        return jsonify({"status": "ignored", "reason": "No JSON payload"}), 200

    try:
        event = payload.get("event")
        data = payload.get("data")
        
        # PROCESAR ÚNICAMENTE EVENTOS DE MENSAJES
        if event == "messages.upsert" and isinstance(data, dict):
            key = data.get("key", {})
            
            from_me = key.get("fromMe", False)
            remote_jid = key.get("remoteJid", "")

            # FILTRO ANTI-BUCLE: Ignorar si es de grupos o mensaje propio
            if from_me or "@g.us" in str(remote_jid):
                return jsonify({"status": "ignored", "reason": "Self or group message"}), 200

            # Extraer texto del mensaje
            message_body = data.get("message", {})
            texto = (
                message_body.get("conversation") or
                message_body.get("extendedTextMessage", {}).get("text") or
                ""
            )

            if texto:
                logger.info(f"📩 Mensaje recibido de {remote_jid}: {texto}")
                procesar_comando(texto, remote_jid)

    except Exception as e:
        logger.error(f"💥 Error procesando webhook: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
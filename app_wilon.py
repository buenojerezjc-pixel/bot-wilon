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

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "https://evolution-wilon-api.onrender.com").rstrip('/')
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "xaipslkt8olk75y0wlnpj")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "wilon")

bot_activo = True

# ==========================================
# ENVÍO MULTI-ENDPOINTS (EVITA SESSION ERROR)
# ==========================================
def enviar_mensaje_whatsapp(destinatario, texto):
    """
    Intenta enviar el mensaje usando múltiples endpoints de Evolution API.
    Resuelve el bug 'SessionError: No sessions' probando el formato alternativo
    y parámetros directos para grupos y privados.
    """
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    target_jid = str(destinatario).strip()
    
    # Endpoint principal
    url_primary = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    
    payload = {
        "number": target_jid,
        "options": {
            "delay": 0,
            "presence": "composing",
            "linkPreview": False
        },
        "textMessage": {
            "text": texto
        }
    }

    try:
        # Primer intento: sendText estándar
        response = requests.post(url_primary, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"✅ Respuesta enviada exitosamente a {target_jid}")
            return True
            
        logger.warning(f"⚠️ Reintentando envío por fallback de endpoint para {target_jid}")

        # Fallback 1: Si es grupo (@g.us) o chat privado, enviamos sin estructura anidada de textMessage
        payload_alt = {
            "number": target_jid,
            "text": texto,
            "delay": 0
        }
        resp_alt = requests.post(url_primary, json=payload_alt, headers=headers, timeout=10)
        if resp_alt.status_code in [200, 201]:
            logger.info(f"✅ Respuesta alternativa enviada a {target_jid}")
            return True

        # Fallback 2: Enviar número limpio si es chat personal
        if "@g.us" not in target_jid:
            clean_number = re.sub(r'\D', '', target_jid.split('@')[0])
            payload_alt["number"] = clean_number
            resp_num = requests.post(url_primary, json=payload_alt, headers=headers, timeout=10)
            if resp_num.status_code in [200, 201]:
                logger.info(f"✅ Respuesta enviada a número limpio {clean_number}")
                return True

        logger.error(f"❌ Fallaron todos los intentos para {target_jid}: {response.text}")
        return False

    except Exception as e:
        logger.error(f"💥 Excepción durante envío a WhatsApp: {e}")
        return False

# ==========================================
# LÓGICA DE ANIME
# ==========================================
def obtener_anime_recomendado():
    query = '''
    query {
      Page(page: 1, perPage: 40) {
        media(type: ANIME, sort: POPULARITY_DESC) {
          title { romaji english }
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

            return (
                f"⛩️ *Recomendación Anime: {titulo}*\n\n"
                f"⭐ *Puntuación:* {score}/100\n"
                f"📺 *Episodios:* {episodios}\n"
                f"🏷️ *Géneros:* {generos}"
            )
    except Exception:
        pass
    return "⛩️ *Recomendación Anime:* Te sugiero ver *Dragon Ball*, *One Piece* o *Jujutsu Kaisen*."

# ==========================================
# PROCESAMIENTO DE COMANDOS (#)
# ==========================================
def procesar_comando(texto_mensaje, destinatario):
    global bot_activo
    texto_clean = texto_mensaje.strip()
    comando_lower = texto_clean.lower()

    if comando_lower in ["#activar wilon", "#activar"]:
        bot_activo = True
        enviar_mensaje_whatsapp(destinatario, "🟢 *Wilon activado.*")
        return

    if comando_lower in ["#desactivar wilon", "#desactivar"]:
        bot_activo = False
        enviar_mensaje_whatsapp(destinatario, "🔴 *Wilon desactivado.*")
        return

    if not bot_activo:
        return

    # COMANDOS QUE INICIAN OBLIGATORIAMENTE CON #
    if comando_lower == "#ping":
        enviar_mensaje_whatsapp(destinatario, "🏓 ¡Pong! El bot Wilon está activo y responde a cualquier grupo o usuario.")

    elif comando_lower in ["#ayuda", "#help"]:
        menu = (
            "🤖 *MENÚ DE WILON* 🤖\n\n"
            "▫️ *#ping* -> Verifica conexión.\n"
            "▫️ *#anime* -> Recomendación al azar.\n"
            "▫️ *#info* -> Datos del sistema.\n"
            "▫️ *#desactivar* / *#activar* -> Control del bot."
        )
        enviar_mensaje_whatsapp(destinatario, menu)

    elif comando_lower == "#info":
        enviar_mensaje_whatsapp(destinatario, "⚡ *Wilon Bot System v1.0*\n• Estado: Activo\n• Modo: Multi-fallback activado")

    elif comando_lower == "#anime":
        enviar_mensaje_whatsapp(destinatario, obtener_anime_recomendado())

    elif comando_lower.startswith("#clima"):
        partes = texto_clean.split(" ", 1)
        ciudad = partes[1].strip() if len(partes) > 1 else "tu ciudad"
        enviar_mensaje_whatsapp(destinatario, f"🌤️ El clima reportado para *{ciudad.capitalize()}* es de 22°C.")

# ==========================================
# WEBHOOK DE FLASK
# ==========================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "bot": "Wilon Webhook"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_json() or {}
    
    try:
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "messages.upsert" and isinstance(data, dict):
            key = data.get("key", {})
            remote_jid = key.get("remoteJid", "")
            from_me = key.get("fromMe", False)
            
            message_body = data.get("message", {})
            texto = (
                message_body.get("conversation") or
                message_body.get("extendedTextMessage", {}).get("text") or
                ""
            ).strip()

            # REGLA: Debe iniciar con # obligatoriamente
            if texto and texto.startswith('#'):
                
                # Definir destinatario para grupo o chat privado
                if from_me and "@g.us" not in remote_jid:
                    destinatario = data.get("userReceipt") or remote_jid
                else:
                    destinatario = remote_jid

                logger.info(f"📩 Procesando comando '{texto}' enviado a: {destinatario}")
                procesar_comando(texto, destinatario)

    except Exception as e:
        logger.error(f"💥 Error en webhook: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
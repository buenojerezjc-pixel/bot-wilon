import os
import logging
import requests
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
economia_usuarios = {}

MI_LID_NUMERICO = "101847280934918"
MI_NUMERO_REAL = "573124592327@s.whatsapp.net"

# ==========================================
# MAPA Y TRADUCTOR ULTRA FORZADO DE LID
# ==========================================
MAPA_LIDS = {
    "101847280934918": "573124592327@s.whatsapp.net",
}

def resolver_id(id_recibido):
    if not id_recibido:
        return ""
    
    id_str = str(id_recibido).strip().lower()
    base_id = id_str.split("@")[0]
    
    # 1. Búsqueda en mapa directo
    if base_id in MAPA_LIDS:
        return MAPA_LIDS[base_id]
        
    # 2. Coincidencia con tu LID numérico
    if MI_LID_NUMERICO in id_str:
        return MI_NUMERO_REAL

    # 3. Forzar traducción de cualquier @lid de la cuenta principal
    if "@lid" in id_str:
        return MI_NUMERO_REAL
        
    # 4. Formatear como JID válido de WhatsApp
    if not id_str.endswith("@s.whatsapp.net") and not id_str.endswith("@g.us"):
        return f"{base_id}@s.whatsapp.net"

    return id_str

# ==========================================
# ENVÍO DE MENSAJES UNIFICADO
# ==========================================
def enviar_mensaje_whatsapp(destinatario, texto):
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    destinatario_str = str(destinatario).strip()
    
    # TRADUCCIÓN OBLIGATORIA DEL DESTINATARIO
    if destinatario_str.endswith("@g.us"):
        destinatario_final = destinatario_str
    else:
        destinatario_final = resolver_id(destinatario_str)
    
    # Extraer únicamente los dígitos para la API
    numero_limpio = destinatario_final.split("@")[0]

    payload = {
        "number": numero_limpio,
        "text": texto
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"✅ Mensaje enviado exitosamente a: {numero_limpio}")
        else:
            logger.error(f"❌ Error {response.status_code} al enviar a {numero_limpio}: {response.text}")
    except Exception as e:
        logger.error(f"💥 Excepción al enviar: {e}")

# ==========================================
# COMANDOS Y JUEGOS DE ROL
# ==========================================
def jugar_ruleta():
    resultado = random.randint(1, 6)
    if resultado == 1:
        return "💥 *¡BANG!* La recámara tenía la bala. Has caído en combate... 🪦"
    return f"🔫 **Clic*... La recámara estaba vacía. Te has salvado esta vez ({resultado}/6)."

def dar_abrazo(persona):
    emoji = random.choice(["🫂✨", "🤗💖", "🥰🐾", "🥺💙"])
    if persona:
        return f"{emoji} ¡Wilon le da un super abrazo a *{persona}*!"
    return f"{emoji} ¡Un gran abrazo para todos!"

def trabajar_rpg(usuario):
    usuario_real = resolver_id(usuario)
    ganancia = random.randint(50, 350)
    trabajos = ["programando un bot", "vendiendo empanadas", "reparando servidores", "minando criptos"]
    trabajo = random.choice(trabajos)
    
    saldo_actual = economia_usuarios.get(usuario_real, 0) + ganancia
    economia_usuarios[usuario_real] = saldo_actual
    
    return f"💼 Trabajas {trabajo} y ganas *${ganancia} WilonCoins*.\n💰 *Saldo total:* ${saldo_actual} WilonCoins."

def consultar_saldo(usuario):
    usuario_real = resolver_id(usuario)
    saldo = economia_usuarios.get(usuario_real, 0)
    return f"💳 *BANCO WILON*\n💰 Tu saldo actual es: *${saldo} WilonCoins*."

def robar_rpg(usuario, objetivo):
    usuario_real = resolver_id(usuario)
    if not objetivo:
        return "⚠️ *Uso:* `#robar <nombre_o_persona>`"
    
    saldo_ladron = economia_usuarios.get(usuario_real, 0)
    exito = random.choice([True, False, False])
    
    if exito:
        botin = random.randint(30, 150)
        economia_usuarios[usuario_real] = saldo_ladron + botin
        return f"🥷 *¡Robo Exitoso!* Le has quitado *${botin} WilonCoins* a *{objetivo}*.\n💰 *Saldo:* ${economia_usuarios[usuario_real]} WilonCoins."
    else:
        multa = random.randint(20, 80)
        nuevo_saldo = max(0, saldo_ladron - multa)
        economia_usuarios[usuario_real] = nuevo_saldo
        return f"🚨 *¡TE ATRAPARON!* Intentaste robarle a *{objetivo}*.\n💸 *Multa:* ${multa} WilonCoins.\n💰 *Saldo actual:* ${nuevo_saldo} WilonCoins."

def regalar_rpg(usuario, texto_argumentos):
    usuario_real = resolver_id(usuario)
    partes = texto_argumentos.split(" ", 1)
    
    if len(partes) < 2 or not partes[0].isdigit():
        return "⚠️ *Uso:* `#regalar <monto> <persona>`"
    
    monto = int(partes[0])
    objetivo = partes[1].strip()
    
    saldo_actual = economia_usuarios.get(usuario_real, 0)
    
    if monto <= 0:
        return "⚠️ El monto debe ser mayor a 0."
    if saldo_actual < monto:
        return f"❌ *Fondos insuficientes.* Tienes ${saldo_actual} WilonCoins."
    
    economia_usuarios[usuario_real] = saldo_actual - monto
    return f"🎁 Has regalado *${monto} WilonCoins* a *{objetivo}*.\n💰 *Tu nuevo saldo:* ${economia_usuarios[usuario_real]} WilonCoins."

def obtener_anime_recomendado():
    try:
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

def procesar_comando(texto_mensaje, destinatario, emisor):
    global bot_activo
    texto_clean = texto_mensaje.strip()
    comando_lower = texto_clean.lower()

    if comando_lower in ["#activar wilon", "#activar"]:
        bot_activo = True
        enviar_mensaje_whatsapp(destinatario, "🟢 *Wilon activado.*")
        return

    if comando_lower in ["#desactivar wilon", "#desactivar"]:
        bot_activo = False
        enviar_mensaje_whatsapp(destinatario, "🔴 *Desactivado.*")
        return

    if not bot_activo:
        return

    if comando_lower == "#ping":
        enviar_mensaje_whatsapp(destinatario, "🏓 ¡Pong! Bot activo y traductor a 57312 funcionando.")
    elif comando_lower in ["#ayuda", "#help"]:
        menu = (
            "🤖 *MENÚ DE WILON* 🤖\n\n"
            "▫️ *#ping* -> Estado.\n"
            "▫️ *#anime* -> Anime aleatorio.\n\n"
            "🎭 *ROL Y ECONOMÍA:*\n"
            "▫️ *#trabajar* -> Ganar WilonCoins.\n"
            "▫️ *#bal* / *#saldo* -> Ver tus monedas.\n"
            "▫️ *#robar <nombre>* -> Intentar robar.\n"
            "▫️ *#regalar <monto> <nombre>* -> Dar monedas.\n"
            "▫️ *#ruleta* -> Ruleta rusa.\n"
            "▫️ *#abrazo <nombre>* -> Abrazo.\n\n"
            "▫️ *#desactivar* / *#activar*"
        )
        enviar_mensaje_whatsapp(destinatario, menu)
    elif comando_lower == "#info":
        enviar_mensaje_whatsapp(destinatario, "⚡ *Wilon Bot System v2.3*\n• Sistema activo con resolución automática LID -> 312.")
    elif comando_lower == "#anime":
        enviar_mensaje_whatsapp(destinatario, obtener_anime_recomendado())
    elif comando_lower == "#ruleta":
        enviar_mensaje_whatsapp(destinatario, jugar_ruleta())
    elif comando_lower.startswith("#abrazo"):
        partes = texto_clean.split(" ", 1)
        objetivo = partes[1].strip() if len(partes) > 1 else ""
        enviar_mensaje_whatsapp(destinatario, dar_abrazo(objetivo))
    elif comando_lower == "#trabajar":
        enviar_mensaje_whatsapp(destinatario, trabajar_rpg(emisor))
    elif comando_lower in ["#bal", "#saldo"]:
        enviar_mensaje_whatsapp(destinatario, consultar_saldo(emisor))
    elif comando_lower.startswith("#robar"):
        partes = texto_clean.split(" ", 1)
        objetivo = partes[1].strip() if len(partes) > 1 else ""
        enviar_mensaje_whatsapp(destinatario, robar_rpg(emisor, objetivo))
    elif comando_lower.startswith("#regalar"):
        partes = texto_clean.split(" ", 1)
        argumentos = partes[1].strip() if len(partes) > 1 else ""
        enviar_mensaje_whatsapp(destinatario, regalar_rpg(emisor, argumentos))

# ==========================================
# WEBHOOK FLASK
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

            if not remote_jid or remote_jid == "status@broadcast":
                return jsonify({"status": "ignored"}), 200

            if remote_jid.endswith("@g.us"):
                destinatario_final = remote_jid
            else:
                destinatario_final = resolver_id(remote_jid)

            emisor_raw = (
                data.get("senderPn") or 
                key.get("participantPn") or 
                key.get("participant") or 
                data.get("participant") or 
                data.get("sender") or 
                (key.get("fromMe") and MI_NUMERO_REAL) or
                remote_jid
            )
            emisor_real = resolver_id(emisor_raw)

            message_body = data.get("message", {})
            
            texto = (
                message_body.get("conversation") or
                message_body.get("extendedTextMessage", {}).get("text") or
                message_body.get("imageMessage", {}).get("caption") or
                message_body.get("videoMessage", {}).get("caption") or
                ""
            ).strip()

            if texto.startswith('#'):
                logger.info(f"📩 Comando '{texto}' | Destino: {destinatario_final} | Emisor traducido: {emisor_real}")
                procesar_comando(texto, destinatario_final, emisor_real)

    except Exception as e:
        logger.error(f"💥 Error en webhook: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
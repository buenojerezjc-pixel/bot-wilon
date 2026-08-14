import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Configuración de OpenAI API Key desde las variables de entorno de Render
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Variable global para controlar si el bot está activo o desactivado
bot_activo = True

# Historial simple para almacenar los últimos mensajes de la conversación
historial_mensajes = []

def guardar_en_historial(remitente, texto):
    """Guarda los últimos 10 mensajes para que la IA tenga contexto de los gustos."""
    historial_mensajes.append(f"{remitente}: {texto}")
    if len(historial_mensajes) > 10:
        historial_mensajes.pop(0)

@app.route("/webhook", methods=["POST"])
def webhook():
    global bot_activo
    
    data = request.get_json()
    
    # Extraer mensaje del formato de Evolution API
    try:
        data_message = data.get("data", {})
        key = data_message.get("key", {})
        
        # Ignorar mensajes enviados por el propio bot para evitar bucles
        if key.get("fromMe", False):
            return jsonify({"status": "ignored", "reason": "Self message"}), 200

        message_content = data_message.get("message", {})
        
        # Obtener el texto del mensaje
        texto_mensaje = (
            message_content.get("conversation") or 
            message_content.get("extendedTextMessage", {}).get("text", "")
        ).strip()

        if not texto_mensaje:
            return jsonify({"status": "ignored", "reason": "No text content"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    texto_lower = texto_mensaje.lower()

    # ----------------------------------------------------
    # 1. COMANDOS DE CONTROL (#desactivar / #activar)
    # ----------------------------------------------------
    if texto_lower == "#desactivar wilon":
        bot_activo = False
        return responder_whatsapp("🔴 Wilon se ha desactivado. No analizaré los mensajes hasta que pongas #activar wilon.")

    if texto_lower == "#activar wilon":
        bot_activo = True
        return responder_whatsapp("🟢 Wilon activo de nuevo. ¡Estoy listo para analizar la conversación y recomendarte animes!")

    # Si el bot está desactivado, ignora cualquier otro mensaje
    if not bot_activo:
        return jsonify({"status": "disabled"}), 200

    # Guardar mensaje en el historial si el bot está activo
    guardar_en_historial("Usuario", texto_mensaje)

    # ----------------------------------------------------
    # 2. COMANDO #anime (INTELEGENTE)
    # ----------------------------------------------------
    if texto_lower.startswith("#anime"):
        # Extraer lo que viene después de #anime
        busqueda = texto_mensaje[6:].strip()

        if busqueda:
            # CASO A: Especificó un anime (ej. #anime Naruto)
            prompt = (
                f"El usuario te pidió información sobre el anime: '{busqueda}'. "
                f"Dame una sinopsis breve, género, por qué vale la pena verlo y si está finalizado o en emisión."
            )
        else:
            # CASO B: Escribió solo #anime (Recomendación inteligente por historial)
            contexto = "\n".join(historial_mensajes)
            prompt = (
                f"Aquí está el historial reciente de la conversación:\n{contexto}\n\n"
                f"Basándote en los temas, tono o emociones reflejados en esos mensajes, "
                f"recomiéndale UN anime ideal que encaje con su estado de ánimo o gustos. "
                f"Explícale de forma cercana y amigable por qué se lo estás recomendando en base a lo que han hablado."
            )

        respuesta_ia = consultar_openai(prompt)
        return responder_whatsapp(respuesta_ia)

    return jsonify({"status": "received", "note": "Mensaje procesado"}), 200


def consultar_openai(prompt_texto):
    """Envía la consulta a la API de OpenAI (GPT-3.5-turbo o GPT-4o-mini)."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres Wilon, un asistente de WhatsApp experto en anime, simpático, conciso y directo."},
                {"role": "user", "content": prompt_texto}
            ],
            max_tokens=350,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ocurrió un error al consultar con la IA: {str(e)}"


def responder_whatsapp(texto_respuesta):
    """Formatea la respuesta JSON que espera Render / Evolution API."""
    return jsonify({
        "status": "success",
        "response": texto_respuesta
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
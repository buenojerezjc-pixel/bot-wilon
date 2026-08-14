import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Inicializar cliente de OpenAI usando la Variable de Entorno
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# -------------------------------------------------------------------
# 🟢 1. RUTA RAÍZ PARA EL CRONJOB (Mantiene el servidor despierto 24/7)
# -------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health_check():
    return "OK - Servidor Wilon Activo", 200

# -------------------------------------------------------------------
# 🤖 2. FUNCIÓN PARA CONSULTAR A OPENAI
# -------------------------------------------------------------------
def consultar_openai(prompt_texto):
    """Envía la consulta a la API de OpenAI (GPT-4o-mini)."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres Wilon, un asistente de WhatsApp experto en anime, simpático, conciso y directo."
                },
                {"role": "user", "content": prompt_texto}
            ],
            max_tokens=350,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ocurrió un error al consultar con la IA: {str(e)}"

# -------------------------------------------------------------------
# 📲 3. FORMATO DE RESPUESTA PARA EVOLUTION API
# -------------------------------------------------------------------
def responder_whatsapp(texto_respuesta):
    """Formatea la respuesta JSON que espera Render / Evolution API."""
    return jsonify({
        "status": "success",
        "response": texto_respuesta
    }), 200

# -------------------------------------------------------------------
# 📩 4. RUTA WEBHOOK (Recibe los mensajes de WhatsApp)
# -------------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Validar que lleguen datos
    if not data:
        return jsonify({"status": "ignored", "reason": "No JSON data"}), 200

    try:
        # Extraer el mensaje y el emisor según la estructura de Evolution API
        data_inner = data.get("data", {})
        message_data = data_inner.get("message", {})
        
        # Obtener el texto del mensaje
        texto_mensaje = (
            message_data.get("conversation") or 
            message_data.get("extendedTextMessage", {}).get("text") or 
            ""
        ).strip()

        # Si el mensaje incluye el comando #anime
        if "#anime" in texto_mensaje.lower():
            # Extraer el parámetro (ejemplo: "#anime Naruto" -> "Naruto")
            partes = texto_mensaje.split("#anime", 1)
            busqueda = partes[1].strip() if len(partes) > 1 else ""

            if busqueda:
                prompt = f"Dame un resumen conciso, opinión y calificación del anime: {busqueda}"
            else:
                prompt = "Dame una recomendación rápida de un anime popular y divertido de ver hoy en día."

            # Consultar a la IA
            respuesta_ia = consultar_openai(prompt)
            return responder_whatsapp(respuesta_ia)

    except Exception as e:
        print(f"Error procesando el webhook: {e}")

    return jsonify({"status": "ignored"}), 200

# -------------------------------------------------------------------
# 🚀 5. INICIALIZACIÓN DEL SERVIDOR
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
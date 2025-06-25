import logging
from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import re

# Logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Iniciando aplicación Flask")

app = Flask(__name__)

# Clave de Kluster desde variables de entorno (recomendado en Railway)
KLUSTER_API_KEY = os.getenv("KLUSTER_API_KEY", "2b4aa715-f361-4650-8efb-15c2dced2f67")
MODEL = "deepseek-ai/DeepSeek-V3-0324"

# Catálogo simplificado
CATALOGO = [
    {"nombre": "Mighty+ PLUS", "precio": "$279.990 (oferta) / $399.990", "descripcion": "Vaporizador portátil con carga rápida USB-C."},
    {"nombre": "ANIX Urano", "precio": "$69.990", "descripcion": "Diseño metálico tipo maleta. Compatible con líquidos."},
    {"nombre": "Volcano Hybrid", "precio": "$599.990", "descripcion": "Vaporizador de escritorio con control vía app."},
    {"nombre": "ANIX Tauro", "precio": "$39.990", "descripcion": "Portátil para hierbas secas, control de temperatura."}
]

FAQ = {
    "envios": "Envíos a todo Chile en máximo 2 días hábiles tras el pago.",
    "garantia": "Garantía legal de 6 meses, incluye cambio o reparación.",
    "pago": "Aceptamos efectivo, transferencia, y tarjetas vía SumUp.",
    "portabilidad": "Todos son portables con batería, excepto Volcano.",
    "tecnico": "Servicio técnico en Santiago de Chile."
}

def generar_prompt_catalogo():
    productos = "\n".join([f"- {p['nombre']}: {p['precio']} – {p['descripcion']}" for p in CATALOGO])
    prompt = f"""
Eres un asistente conciso y claro de VaporCity.cl. Recomienda productos según las necesidades.

Catálogo:
{productos}

FAQs:
- Envíos: {FAQ['envios']}
- Garantía: {FAQ['garantia']}
- Pago: {FAQ['pago']}
- Portabilidad: {FAQ['portabilidad']}
- Técnico: {FAQ['tecnico']}

Si no sabes la respuesta, sugiere contactar al equipo humano. Responde de forma breve y útil.
"""
    return prompt

def sanitize_input(text):
    if not text:
        return ""
    sanitized = re.sub(r'[<>"\'\\]', '', text)
    return sanitized[:500]

@app.route("/")
def home():
    return """
    <h1>API Chatbot VaporCity.cl</h1>
    <p>POST a /chat con JSON {"message":"tu pregunta"}</p>
    <p>Ejemplo con curl:<br>
    curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d '{"message":"¿Qué vaporizador me recomiendas?"}'
    </p>
    """

@app.route("/health")
def health_check():
    return jsonify({"status": "OK", "timestamp": datetime.now().isoformat(), "service": "VaporCity Chatbot API"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    logger.info("Petición /chat recibida")
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"IP cliente: {client_ip}")

    data = request.get_json(force=True, silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "JSON inválido o falta campo 'message'"}), 400

    user_input = sanitize_input(data["message"])
    if len(user_input) < 2:
        return jsonify({"error": "Mensaje demasiado corto"}), 400

    logger.info(f"Mensaje usuario: {user_input}")

    messages = [
        {"role": "system", "content": generar_prompt_catalogo()},
        {"role": "user", "content": user_input}
    ]

    try:
        start_time = datetime.now()
        response = requests.post(
            "https://api.kluster.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KLUSTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "max_tokens": 250,
                "temperature": 0.5
            },
            timeout=15
        )
        response.raise_for_status()
        response_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Respuesta Kluster en {response_time:.2f}s")

        result = response.json()
        if "choices" not in result or not result["choices"]:
            return jsonify({"error": "Respuesta inesperada del modelo"}), 500

        reply = result["choices"][0]["message"]["content"].strip()
        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        logger.error(f"Error API Kluster: {e}")
        return jsonify({"error": "Error al conectar con la API de IA", "details": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno", "details": str(e)}), 500

# CORS simple
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return response

@app.route("/chat", methods=["OPTIONS"])
def handle_options():
    return jsonify({}), 200
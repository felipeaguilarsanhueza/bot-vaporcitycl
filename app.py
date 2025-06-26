import logging
from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime, timedelta
import re
from collections import defaultdict

# Configuración avanzada de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Iniciando aplicación Flask")

app = Flask(__name__)

# Clave de Kluster desde variables de entorno
KLUSTER_API_KEY = os.getenv("KLUSTER_API_KEY", "2b4aa715-f361-4650-8efb-15c2dced2f67")
MODEL = "deepseek-ai/DeepSeek-V3-0324"

# Configuración de sesiones
SESSION_TIMEOUT = timedelta(minutes=30)  # Tiempo de expiración de sesiones

# Catálogo simplificado
CATALOGO = [
    {
        "nombre": "Mighty+ PLUS",
        "precio": "$279.990 (oferta) / $399.990",
        "descripcion": "Vaporizador portátil con carga rápida USB-C.",
        "caracteristicas": [
            "Calentamiento híbrido (convección + conducción)",
            "Rango de temperatura: 104 °F – 410 °F (40 °C – 210 °C)",
            "Tiempo de calentamiento: ~60 s",
            "Batería: interna recargable, 8‑12 sesiones por carga (~90 min)",
            "Carga rápida USB‑C: 80 % en ~40 min con Supercharger",
            "Cámara revestida en cerámica, buena retención del sabor",
            "Pantalla LCD y controles digitales, función Superbooster",
            "Dimensiones: 5.5″ × 3.2″ × 1.2″; peso: 0.5 lb (~227 g)",
            "Garantía: 2 años + 1 año adicional con registro" 
        ]
    },
    {
        "nombre": "ANIX Urano",
        "precio": "$69.990",
        "descripcion": "Diseño metálico tipo maleta. Compatible con líquidos.",
        "caracteristicas": [
            "Batería 2200 mAh con carga rápida USB‑C (5 V/1 A)",
            "Pantalla OLED + 3 botones; vibración al alcanzar temperatura",
            "Rango de temperatura: 300 °F – 435 °F (149 °C – 224 °C)",
            "Cámara en acero inoxidable SUS304 + bobina cerámica",
            "Dimensiones: 103 × 50 × 27 mm; portátil y ergonómico",
            "Boca magnética y enfriamiento tipo panal"
        ]
    },
    {
        "nombre": "Volcano Hybrid",
        "precio": "$599.990",
        "descripcion": "Vaporizador de escritorio con control vía app.",
        "caracteristicas": [
            "Calentamiento híbrido (convección + conducción)",
            "Rango de temperatura: 40 °C – 230 °C (104 °F – 446 °F)",
            "Pantalla táctil digital + control Bluetooth vía app Web S&B",
            "Tiempo de calentamiento: ~40 s a 180 °C",
            "Entrega de vapor por bolsa (Easy Valve) o tubo (whip)",
            "Caudal de aire: ~30 L/min; casi sin resistencia al inhalar",
            "Dimensiones: 20 × 20 × 18 cm; peso: 1.8 kg",
            "Incluye set completo: bolsas, tubos, cámara, molinillo"
        ]
    },
    {
        "nombre": "ANIX Tauro",
        "precio": "$39.990",
        "descripcion": "Portátil para hierbas secas, control de temperatura.",
        "caracteristicas": [
            "Batería 1300 mAh con carga por USB‑C (5 V/1 A)",
            "Temperatura ajustable: 200 °F – 428 °F (93 °C – 220 °C)",
            "Pantalla OLED; cámara de cerámica (0.5 ohm)",
            "Dimensiones: 125 × 27 × 24 mm; ligero (~200 g)",
            "Protecciones: cortocircuito, bajo voltaje, sobrecorriente",
            "Incluye fundas, cepillo de limpieza y accesorios"
        ]
    }
]

FAQ = {
    "envios": (
        "Realizamos envíos a todo Chile. Una vez verificado el pago, el pedido se despacha en un plazo máximo de 2 días hábiles. "
        "La entrega posterior depende de los tiempos del courier. No contamos con tienda física, somos una tienda 100% online. "
        "Sin embargo, es posible coordinar entregas presenciales en Santiago en estaciones de metro Tobalaba o Ñuble, previa coordinación."
    ),
    "garantia": (
        "Todos los productos cuentan con garantía legal de 6 meses desde la fecha de compra. "
        "Esta garantía cubre fallas de fabricación y permite cambio, reparación o devolución, según corresponda."
    ),
    "pago": (
        "Aceptamos múltiples métodos de pago: efectivo (solo para entregas presenciales en Santiago), "
        "transferencia bancaria y tarjetas de débito/crédito a través de la plataforma SumUp. "
        "La preparación del pedido se inicia una vez verificado el pago."
    ),
    "portabilidad": (
        "La mayoría de nuestros vaporizadores son portátiles y funcionan con batería interna recargable, ideales para llevar a cualquier parte. "
        "La única excepción es el Volcano Hybrid, un modelo de escritorio que requiere estar conectado a la corriente para funcionar."
    ),
    "tecnico": (
        "Contamos con servicio técnico en Santiago de Chile para mantenimiento o reparaciones. "
        "Si estás en regiones, puedes enviarnos tu equipo por courier, previa coordinación, y te mantendremos informado durante el proceso técnico."
    ),
    "salud": (
        "Vapear hierbas secas es considerablemente más saludable que fumar, ya que no hay combustión, cenizas ni humo tóxico. "
        "El vaporizador calienta la hierba a una temperatura controlada que libera sus compuestos activos en forma de vapor, "
        "sin alcanzar el punto de combustión (que ocurre cerca de los 230 °C).\n\n"
        "Puedes vaporizar una variedad de plantas según el efecto deseado, por ejemplo:\n"
        "- *Menta* (170–180 °C): alivia la congestión y relaja.\n"
        "- *Tomillo* (130–150 °C): propiedades antisépticas, útil para bronquitis o resfríos.\n"
        "- *Lavanda* (130–160 °C): relajante y ansiolítica.\n"
        "- *Manzanilla* (125–150 °C): efecto calmante, ideal para dormir mejor.\n"
        "- *Hierba buena, salvia, melisa, eucalipto* y muchas más.\n\n"
        "Usar un vaporizador te permite ajustar la temperatura para extraer compuestos específicos (terpenos, cannabinoides o aceites esenciales), "
        "lo que mejora la experiencia terapéutica y cuida tus pulmones."
    ),
    "contacto": (
        "Puedes comunicarte con nosotros a través de distintos canales:\n\n"
        "- ✉️ Correo: contacto@vaporcity.cl\n"
        "- 📱 WhatsApp: +56 9 8256 9331\n"
        "- 📸 Instagram: mensaje directo en [@vaporcity.cl](https://www.instagram.com/vaporcity.cl)\n"
        "- 💬 Deja tu opinión o comentario sobre un producto en: https://tally.so/r/nPe2xx\n"
        "- 🛒 Visita nuestra tienda online para compras con tarjeta de crédito o débito en: https://www.vaporcity.cl/productos\n\n"
        "Respondemos los mensajes lo más rápido posible dentro del horario hábil. ¡Gracias por preferirnos!"
    )
}


def generar_prompt_catalogo():
    productos = "\n".join([f"- {p['nombre']}: {p['precio']} – {p['descripcion']}" for p in CATALOGO])
    prompt = f"""
Eres un asistente conciso y claro de VaporCity.cl. Responde con frases breves, sin usar saltos de línea innecesarios. 
Usa <strong> solo si es necesario, pero no agregues salto de línea luego de etiquetas HTML.

Catálogo:
{productos}

FAQs:
- Envíos: {FAQ['envios']}
- Garantía: {FAQ['garantia']}
- Pago: {FAQ['pago']}
- Portabilidad: {FAQ['portabilidad']}
- Técnico: {FAQ['tecnico']}
- Salud: {FAQ['salud']}
- Contacto: {FAQ['contacto']}

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
    <p>Para reiniciar conversación: POST /reset con JSON {"session_id":"tu_sesion"}</p>
    """

@app.route("/health")
def health_check():
    return jsonify({
        "status": "OK", 
        "timestamp": datetime.now().isoformat(), 
        "service": "VaporCity Chatbot API",
        "sessions": len(conversation_history)
    }), 200

# Almacenamiento de sesiones con tiempo de última actividad
conversation_history = defaultdict(list)
session_activity = {}

# Limpiar sesiones expiradas
def clean_expired_sessions():
    now = datetime.now()
    expired = []
    for session_id, last_active in list(session_activity.items()):
        if now - last_active > SESSION_TIMEOUT:
            expired.append(session_id)
    
    for session_id in expired:
        if session_id in conversation_history:
            del conversation_history[session_id]
        if session_id in session_activity:
            del session_activity[session_id]
        logger.info(f"Sesión expirada eliminada: {session_id}")

@app.route("/reset", methods=["POST"])
def reset_chat():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id")
    
    if not session_id:
        return jsonify({"error": "Falta session_id"}), 400
    
    if session_id in conversation_history:
        del conversation_history[session_id]
    if session_id in session_activity:
        del session_activity[session_id]
    
    logger.info(f"Sesión reiniciada: {session_id}")
    return jsonify({"status": "Sesión reiniciada", "session_id": session_id})

@app.route("/chat", methods=["POST"])
def chat():
    clean_expired_sessions()  # Limpiar sesiones antes de procesar
    
    logger.info("Petición /chat recibida")
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"IP cliente: {client_ip}")

    data = request.get_json(force=True, silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "JSON inválido o falta campo 'message'"}), 400

    user_input = sanitize_input(data["message"])
    if len(user_input) < 2:
        return jsonify({"error": "Mensaje demasiado corto"}), 400

    # Sanitizar y obtener session_id
    raw_session_id = data.get("session_id", "default_" + re.sub(r'\W+', '', client_ip))
    session_id = re.sub(r'\W+', '', raw_session_id)[:64] or "default_session"
    
    # Actualizar tiempo de actividad
    session_activity[session_id] = datetime.now()

    # Inicializar sesión si es nueva
    if session_id not in conversation_history:
        conversation_history[session_id].append({
            "role": "system",
            "content": generar_prompt_catalogo()
        })
        logger.info(f"Nueva sesión iniciada: {session_id}")

    # Añadir mensaje de usuario al historial
    conversation_history[session_id].append({
        "role": "user",
        "content": user_input
    })

    logger.info(f"Session: {session_id} - Mensaje: {user_input}")
    logger.debug(f"Historial actual: {conversation_history[session_id]}")

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
                "messages": conversation_history[session_id],
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

        reply = result["choices"][0]["message"]["content"].replace('\n', ' ').strip()
        
        # Añadir respuesta al historial
        conversation_history[session_id].append({
            "role": "assistant",
            "content": reply
        })
        
        # Mantener sistema + últimos 4 intercambios (máximo 9 mensajes)
        if len(conversation_history[session_id]) > 9:
            conversation_history[session_id] = [conversation_history[session_id][0]] + conversation_history[session_id][-8:]

        logger.debug(f"Historial actualizado: {conversation_history[session_id]}")

        return jsonify({
            "reply": reply,
            "session_id": session_id  # Devolver ID para continuar conversación
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error API Kluster: {e}")
        return jsonify({"error": "Error al conectar con la API de IA", "details": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno", "details": str(e)}), 500

# CORS
ALLOWED_ORIGINS = ["https://www.vaporcity.cl", "https://vaporcity.cl", "https://bio.vaporcity.cl"]
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET, DELETE'
    return response

@app.route("/chat", methods=["OPTIONS"])
def handle_options():
    return jsonify({}), 200
import logging
from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import re

# Configuración avanzada de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Iniciando aplicación Flask")

app = Flask(__name__)

# Obtener claves desde variables de entorno
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY no está configurada en las variables de entorno")
    OPENROUTER_API_KEY = "sk-543fa126bfa44272bb83aa4eda39bcd8"  # Clave temporal para desarrollo
    logger.warning("Usando clave de desarrollo temporal")

MODEL = "deepseek-chat"

# Catálogo de productos
CATALOGO = [
    {
        "nombre": "Mighty+ PLUS",
        "precio": "$279.990 (oferta) / $399.990 (normal)",
        "descripcion": "Vaporizador portátil de alto rendimiento con calentamiento híbrido y carga rápida USB-C."
    },
    {
        "nombre": "ANIX Urano",
        "precio": "$69.990",
        "descripcion": "Diseño metálico tipo maleta. Compatible con líquidos y sales de nicotina. Carga USB-C."
    },
    {
        "nombre": "Volcano Hybrid",
        "precio": "$599.990",
        "descripcion": "Vaporizador de escritorio con inhalación por tubo o globo. Control de temperatura vía app."
    },
    {
        "nombre": "ANIX Tauro",
        "precio": "$39.990",
        "descripcion": "Vaporizador portátil para hierbas secas. Control total de temperatura, diseño discreto."
    }
]

# Preguntas frecuentes
FAQ = {
    "envios": "Hacemos envíos a todo Chile con Chilexpress, CorreosChile, etc. Máximo 2 días hábiles tras el pago.",
    "garantia": "Garantía legal de 6 meses. Puedes pedir cambio, reparación o devolución si tiene fallas.",
    "pago": "Aceptamos efectivo, transferencia, tarjetas de crédito o débito vía SumUp.",
    "portabilidad": "Todos nuestros vaporizadores son portables con batería, excepto el Volcano.",
    "tecnico": "Contamos con servicio técnico en Santiago de Chile."
}

def generar_prompt_catalogo():
    """Genera el prompt del sistema con información del catálogo y FAQs"""
    productos = "\n".join([f"- {p['nombre']}: {p['precio']} – {p['descripcion']}" for p in CATALOGO])
    prompt = f"""
Eres un agente de ventas experto de VaporCity.cl. Recomiendas productos de vapeo según las necesidades del cliente.

Tu catálogo:
{productos}

Preguntas frecuentes:
- Envíos: {FAQ['envios']}
- Garantía: {FAQ['garantia']}
- Métodos de pago: {FAQ['pago']}
- Portabilidad: {FAQ['portabilidad']}
- Servicio técnico: {FAQ['tecnico']}

Si no puedes responder, ofrece redirigir al equipo humano. Sé amable, claro y útil.
"""
    return prompt

@app.route("/")
def home():
    """Página de inicio para la API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VaporCity Chatbot API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                text-align: center;
                background-color: #f0f0f0;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 30px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
            }
            .status {
                padding: 10px;
                background: #4CAF50;
                color: white;
                border-radius: 5px;
                margin: 20px 0;
            }
            .endpoints {
                text-align: left;
                margin-top: 30px;
            }
            .endpoint {
                background: #f9f9f9;
                padding: 15px;
                border-left: 4px solid #3498db;
                margin-bottom: 15px;
                border-radius: 0 5px 5px 0;
            }
            code {
                background: #eee;
                padding: 2px 5px;
                border-radius: 3px;
            }
            .footer {
                margin-top: 30px;
                color: #7f8c8d;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>API del Chatbot de VaporCity.cl</h1>
            <div class="status">
                <strong>Estado:</strong> Operativo ✅
            </div>
            <p>Esta API alimenta el asistente virtual de <a href="https://www.vaporcity.cl" target="_blank">VaporCity.cl</a></p>
            
            <div class="endpoints">
                <h2>Endpoints Disponibles:</h2>
                <div class="endpoint">
                    <strong>POST /chat</strong>
                    <p>Endpoint para interactuar con el chatbot.</p>
                    <p><code>Request: {"message": "Tu mensaje aquí"}</code></p>
                    <p><code>Response: {"reply": "Respuesta del chatbot"}</code></p>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2023 VaporCity.cl - Todos los derechos reservados</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "VaporCity Chatbot API"
    }), 200

def sanitize_input(text):
    """Limpia el texto de entrada de posibles ataques"""
    if not text:
        return ""
    sanitized = re.sub(r'[<>"\'\\]', '', text)
    return sanitized[:500]

@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint principal para el chatbot"""
    logger.info("Recibí una petición /chat")
    
    # Registrar la IP del cliente
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"Solicitud desde IP: {client_ip}")
    
    # Obtener y validar los datos JSON
    data = request.get_json(force=True, silent=True)
    
    if not data:
        logger.warning("Solicitud sin datos JSON válidos")
        return jsonify({
            "error": "Formato JSON inválido",
            "suggestion": "Asegúrate de enviar un JSON válido con el campo 'message'"
        }), 400
    
    if "message" not in data:
        logger.warning("Falta 'message' en el JSON recibido")
        return jsonify({
            "error": "Falta campo 'message' en JSON",
            "suggestion": "Agrega un campo 'message' con tu consulta"
        }), 400
    
    user_input = data["message"]
    
    # Sanitizar y validar entrada
    sanitized_input = sanitize_input(user_input)
    if not sanitized_input or len(sanitized_input) < 2:
        logger.warning("Entrada inválida o demasiado corta")
        return jsonify({
            "error": "Mensaje inválido",
            "suggestion": "El mensaje debe tener al menos 2 caracteres válidos"
        }), 400
    
    logger.info(f"Mensaje del usuario: {sanitized_input}")

    # Crear mensajes para la API de OpenRouter
    messages = [
        {"role": "system", "content": generar_prompt_catalogo()},
        {"role": "user", "content": sanitized_input}
    ]

    try:
        # Registrar tiempo de inicio
        start_time = datetime.now()
        
        # Llamar a la API de OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "max_tokens": 500
            },
            timeout=15
        )
        
        # Calcular tiempo de respuesta
        response_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"OpenRouter API respondió en {response_time:.2f} segundos")
        
        # Verificar estado de la respuesta
        response.raise_for_status()
        
        # Procesar la respuesta
        result = response.json()
        
        # Validar estructura de la respuesta
        if "choices" not in result or not result["choices"]:
            logger.error("Respuesta inesperada de OpenRouter API: sin 'choices'")
            return jsonify({
                "error": "Respuesta inesperada del modelo",
                "details": "La respuesta no contiene opciones válidas"
            }), 500
        
        reply = result["choices"][0]["message"]["content"]
        logger.info(f"Respuesta generada: {reply[:100]}...")
        
        return jsonify({"reply": reply})
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la API de OpenRouter: {str(e)}")
        return jsonify({
            "error": "Error al conectar con el servicio de IA",
            "details": str(e)
        }), 500
    except (KeyError, IndexError) as e:
        logger.error(f"Error procesando respuesta: {str(e)}")
        return jsonify({
            "error": "Error procesando la respuesta del modelo",
            "details": str(e)
        }), 500
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor",
            "details": str(e)
        }), 500

# Middleware para CORS
@app.after_request
def add_cors_headers(response):
    """Agrega headers CORS para permitir solicitudes desde cualquier origen"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    return response

# Manejar solicitudes OPTIONS para CORS
@app.route("/chat", methods=["OPTIONS"])
def handle_options():
    """Maneja solicitudes OPTIONS para CORS"""
    return jsonify({}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Iniciando servidor en puerto {port}")
    app.run(host="0.0.0.0", port=port)
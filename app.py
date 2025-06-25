
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Obtener claves desde variables de entorno
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "deepseek-chat"

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

FAQ = {
    "envios": "Hacemos envíos a todo Chile con Chilexpress, CorreosChile, etc. Máximo 2 días hábiles tras el pago.",
    "garantia": "Garantía legal de 6 meses. Puedes pedir cambio, reparación o devolución si tiene fallas.",
    "pago": "Aceptamos efectivo, transferencia, tarjetas de crédito o débito vía SumUp.",
    "portabilidad": "Todos nuestros vaporizadores son portables con batería, excepto el Volcano.",
    "tecnico": "Contamos con servicio técnico en Santiago de Chile."
}

def generar_prompt_catalogo():
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

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    messages = [
        {"role": "system", "content": generar_prompt_catalogo()},
        {"role": "user", "content": user_input}
    ]

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages
        }
    )

    result = response.json()
    reply = result["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

# todo tu código arriba

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

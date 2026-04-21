import json, logging, re, io, base64
import anthropic
from PIL import Image

log = logging.getLogger(__name__)

PROMPT = """Eres experto en marketing para KraftDo, empresa chilena de tecnología NFC.
KraftDo vende: tarjetas NFC, tags NFC, cuadros inteligentes con QR/NFC, menús digitales, perfiles digitales para negocios.

Mira la imagen y genera un meme de 2 líneas relacionado a KraftDo o NFC.

Reglas:
- texto_arriba: la situación o contexto (máx 8 palabras)
- texto_abajo: el remate con KraftDo como solución (máx 8 palabras)
- Tono: humor chileno, relatable para dueños de negocios
- Responde SOLO en JSON sin markdown:
{"texto_arriba": "...", "texto_abajo": "...", "caption": "texto instagram con emojis #KraftDo #NFC"}
"""

def generar_texto_meme(imagen: Image.Image, api_key: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    buf = io.BytesIO()
    imagen.convert("RGB").save(buf, format="JPEG", quality=85)
    b64 = base64.standard_b64encode(buf.getvalue()).decode()

    log.info("Enviando imagen a Claude para generar texto...")
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
            {"type": "text", "text": PROMPT}
        ]}]
    )
    raw = re.sub(r"```json|```", "", response.content[0].text.strip()).strip()
    try:
        data = json.loads(raw)
        log.info(f"Texto → arriba: '{data['texto_arriba']}' | abajo: '{data['texto_abajo']}'")
        return data
    except json.JSONDecodeError:
        log.error(f"JSON inválido: {raw}")
        return {"texto_arriba": "Cuando tu negocio necesita tecnología", "texto_abajo": "KraftDo NFC lo resuelve", "caption": "💡 #KraftDo #NFC #Chile"}

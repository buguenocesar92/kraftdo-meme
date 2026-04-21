"""
meme_generator.py — Automatización completa para KraftDo (Versión Final - Auth Fix)
Genera imagen → Sube a Drive → Postea en Instagram → Actualiza Sheet
"""

import argparse
import io
import logging
import os
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s → %(message)s",
    handlers=[
        logging.FileHandler("meme.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)

# ── Configuración Visual ──────────────────────────────────────────────────────
CANVAS_SIZE  = (1080, 1080)
LOGO_PATH    = Path(__file__).parent / "logo_transparente.png"
LOGO_SIZE    = (170, 170)
LOGO_MARGEN  = 18
OUTPUT_DIR   = Path("output")
COLOR_TEXTO  = (255, 255, 255)
COLOR_SOMBRA = (0, 0, 0)
COLOR_BANDA  = (0, 0, 0, 170)
FUENTES = [
    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", 
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]

def get_font(size: int):
    for f in FUENTES:
        if Path(f).exists(): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def descargar_imagen(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        log.error(f"Error descargando imagen: {e}")
        return None

def fit_imagen(img: Image.Image, size: tuple) -> Image.Image:
    w, h   = img.size
    tw, th = size
    ratio  = max(tw / w, th / h)
    nw, nh = int(w * ratio), int(h * ratio)
    img    = img.resize((nw, nh), Image.LANCZOS)
    left   = (nw - tw) // 2
    top    = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))

def wrap_texto(texto, font, max_width, draw):
    palabras = texto.split()
    lineas, linea = [], ""
    for palabra in palabras:
        prueba = f"{linea} {palabra}".strip()
        bbox   = draw.textbbox((0, 0), prueba, font=font)
        if bbox[2] - bbox[0] <= max_width: linea = prueba
        else:
            if linea: lineas.append(linea)
            linea = palabra
    if linea: lineas.append(linea)
    return lineas

def dibujar_texto(draw, canvas, texto, posicion, font_size=72, padding=28):
    if not texto or not texto.strip(): return
    texto  = texto.upper()
    font   = get_font(font_size)
    max_w  = CANVAS_SIZE[0] - padding * 2
    lineas = wrap_texto(texto, font, max_w, draw)
    line_h = font_size + 12
    total_h = line_h * len(lineas) + padding * 2

    banda_y = 0 if posicion == "arriba" else CANVAS_SIZE[1] - total_h
    banda   = Image.new("RGBA", (CANVAS_SIZE[0], total_h), COLOR_BANDA)
    canvas.paste(banda, (0, banda_y), banda)

    for i, linea in enumerate(lineas):
        bbox = draw.textbbox((0, 0), linea, font=font)
        tw   = bbox[2] - bbox[0]
        x    = (CANVAS_SIZE[0] - tw) // 2
        y    = banda_y + padding + i * line_h
        for ox in range(-3, 4):
            for oy in range(-3, 4):
                if ox != 0 or oy != 0: draw.text((x + ox, y + oy), linea, font=font, fill=COLOR_SOMBRA)
        draw.text((x, y), linea, font=font, fill=COLOR_TEXTO)

def pegar_logo(canvas):
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA").resize(LOGO_SIZE, Image.LANCZOS)
        x = CANVAS_SIZE[0] - LOGO_SIZE[0] - LOGO_MARGEN
        y = CANVAS_SIZE[1] - LOGO_SIZE[1] - LOGO_MARGEN
        canvas.paste(logo, (x, y), logo)

# ── Integraciones ─────────────────────────────────────────────────────────────
def upload_to_drive(ruta_local, creds):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(ruta_local)}
        media = MediaFileUpload(ruta_local, mimetype='image/png')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webContentLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        url = file.get('webContentLink')
        log.info(f"Subido a Drive: {url}")
        return url
    except Exception as e:
        log.error(f"Error subiendo a Drive: {e}")
        return None

def post_to_instagram(image_url, caption):
    ig_user_id = os.getenv("IG_USER_ID")
    access_token = os.getenv("IG_ACCESS_TOKEN")
    if not ig_user_id or not access_token:
        log.warning("Saltando publicación de IG (Faltan credenciales)")
        return False
    try:
        url_media = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        r = requests.post(url_media, data={'image_url': image_url, 'caption': caption, 'access_token': access_token})
        r.raise_for_status()
        url_publish = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
        requests.post(url_publish, data={'creation_id': r.json().get('id'), 'access_token': access_token}).raise_for_status()
        log.info("✅ Publicado en Instagram")
        return True
    except Exception as e:
        log.error(f"Error Instagram: {e}")
        return False

# ── Orquestador ───────────────────────────────────────────────────────────────
def procesar_sheet(credentials_file, spreadsheet_name, worksheet_name, claude_key, run_batch=False, retry_errors=False):
    import gspread
    from google.oauth2.credentials import Credentials as OAuthCreds
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from ai_text import generar_texto_meme

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    token_file = os.path.join(os.path.dirname(credentials_file) or ".", ".kraftdo_token.json")
    creds = None

    if os.path.exists(token_file):
        creds = OAuthCreds.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: 
            creds.refresh(Request())
        else:
            log.info("\n=======================================================")
            log.info("Copia el siguiente enlace y ábrelo en tu navegador web:")
            log.info("=======================================================\n")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            # CAMBIO CLAVE: open_browser=False obliga a mostrar el link y evita que se cuelgue
            creds = flow.run_local_server(port=8080, open_browser=False)
            
        with open(token_file, "w") as token: 
            token.write(creds.to_json())

    gc = gspread.authorize(creds)
    sheet = gc.open(spreadsheet_name).worksheet(worksheet_name)
    rows  = sheet.get_all_records()
    hdrs  = sheet.row_values(1)
    def col(nombre): return hdrs.index(nombre) + 1

    estados_objetivo = ["pendiente"]
    if retry_errors: estados_objetivo.extend(["error_descarga", "error_api_ai", "error_instagram"])
    
    pendientes = [(i+2, r) for i, r in enumerate(rows) if str(r.get("estado","")).strip().lower() in estados_objetivo]

    if not pendientes:
        log.info("No hay trabajo pendiente.")
        return

    if not run_batch: pendientes = pendientes[:1]
    log.info(f"Procesando {len(pendientes)} fila(s)...")

    for idx, row in pendientes:
        texto_arriba = str(row.get("texto_arriba", "")).strip()
        texto_abajo  = str(row.get("texto_abajo", "")).strip()
        caption      = str(row.get("caption", "")).strip()
        imagen_url   = str(row.get("imagen_url", "")).strip()
        estado_final = "listo"
        drive_url    = str(row.get("archivo_salida", ""))

        if not imagen_url:
            estado_final = "error_sin_imagen"
        else:
            img = descargar_imagen(imagen_url)
            if img is None:
                estado_final = "error_descarga"
            else:
                if not (texto_arriba and texto_abajo):
                    try:
                        res_ai = generar_texto_meme(img, claude_key)
                        texto_arriba, texto_abajo, caption = res_ai["texto_arriba"], res_ai["texto_abajo"], res_ai["caption"]
                    except: estado_final = "error_api_ai"
                
                if estado_final == "listo":
                    OUTPUT_DIR.mkdir(exist_ok=True)
                    ruta_local = str(OUTPUT_DIR / f"post_{idx:03d}.png")
                    canvas = fit_imagen(img, CANVAS_SIZE).copy()
                    draw   = ImageDraw.Draw(canvas)
                    dibujar_texto(draw, canvas, texto_arriba, "arriba")
                    dibujar_texto(draw, canvas, texto_abajo, "abajo")
                    pegar_logo(canvas)
                    canvas.convert("RGB").save(ruta_local, "PNG", quality=95)
                    drive_url = upload_to_drive(ruta_local, creds)
                    if not drive_url: estado_final = "error_subida_drive"
                    else:
                        if not post_to_instagram(drive_url, caption) and os.getenv("IG_USER_ID"):
                            estado_final = "error_instagram"

        # Actualizar Sheet
        celdas = [
            {"range": f"{chr(64 + col('estado'))}{idx}", "values": [[estado_final]]},
            {"range": f"{chr(64 + col('archivo_salida'))}{idx}", "values": [[drive_url]]},
            {"range": f"{chr(64 + col('texto_arriba'))}{idx}", "values": [[texto_arriba]]},
            {"range": f"{chr(64 + col('texto_abajo'))}{idx}", "values": [[texto_abajo]]},
            {"range": f"{chr(64 + col('caption'))}{idx}", "values": [[caption]]}
        ]
        sheet.batch_update(celdas)
        log.info(f"Fila {idx} -> {estado_final}")
        if run_batch: time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude-key", default=os.getenv("ANTHROPIC_API_KEY", ""))
    parser.add_argument("--credentials", default="google_credentials.json")
    parser.add_argument("--sheet", default="KraftDo_Content_Calendar")
    parser.add_argument("--worksheet", default="Posts")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--retry", action="store_true", help="Reintenta filas con errores previos")
    args = parser.parse_args()
    procesar_sheet(args.credentials, args.sheet, args.worksheet, args.claude_key, args.batch, args.retry)
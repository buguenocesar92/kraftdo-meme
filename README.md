# KraftDo Meme Generator
> imagen_url en Sheet → Gemini genera texto → Pillow compone PNG 1080x1080

## Setup

```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env
# Editar .env con tu GEMINI_API_KEY
```

### Obtener Gemini API Key (gratis)
1. Ir a https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copiar al .env

## Estructura del Sheet

| imagen_url | caption | estado | texto_arriba | texto_abajo | archivo_salida |
|---|---|---|---|---|---|
| https://... | (vacío) | pendiente | (vacío) | (vacío) | (vacío) |

Solo necesitas poner `imagen_url` y `estado=pendiente`.
Gemini genera el texto automáticamente mirando la imagen.

## Uso

### Test rápido
```bash
python3 meme_generator.py --test --gemini-key TU_KEY
# o con .env configurado:
python3 meme_generator.py --test
```

### Procesar Sheet
```bash
python3 meme_generator.py \
  --credentials google_credentials.json \
  --sheet "KraftDo Content Calendar" \
  --worksheet Posts
```

### Cron (cada hora)
```
0 * * * * cd /home/cesar/Dev/kraftdo_meme && python3 meme_generator.py >> meme.log 2>&1
```

## Posts generados
Quedan en: `kraftdo_meme/output/post_002.png`, etc.

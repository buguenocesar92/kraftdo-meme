# KraftDo Meme Generator

Generador automatico de posts para redes sociales con logo KraftDo.
Lee datos desde Google Sheets y produce imagenes 1080x1080 listas para publicar.

## Como funciona

    Google Sheets (101+ registros)
        | imagen_url + texto + estado
    meme_generator.py
        | descarga imagen + aplica texto + logo
    Post 1080x1080 listo para Instagram y Facebook

## Instalacion

    git clone https://github.com/buguenocesar92/kraftdo-meme.git
    cd kraftdo-meme
    pip install -r requirements.txt --break-system-packages
    cp .env.example .env

Editar .env:

    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_SHEETS_ID=tu_sheets_id_aqui
    INSTAGRAM_ACCESS_TOKEN=tu_token_aqui

## Google Sheets OAuth

    python3 reauth.py
    # Autoriza acceso a tu Google Sheets

## Uso

    python3 meme_generator.py            # generar un post
    python3 meme_generator.py --batch    # todos los pendientes
    python3 meme_generator.py --retry    # re-intentar fallidos

## Estructura del Google Sheet

| columna    | descripcion                              |
|------------|------------------------------------------|
| imagen_url | URL de la imagen base                    |
| texto      | Texto del post (o vacio para generar IA) |
| estado     | pendiente / generado / publicado         |

## Estado actual

- Generacion de imagenes: funcional
- Google Sheets conectado: 101 registros
- Generacion de texto con IA: requiere ANTHROPIC_API_KEY con creditos
- Publicacion automatica Instagram: requiere Meta Developer App

## Stack

- Python 3.12
- Pillow (composicion de imagenes)
- gspread + google-auth (Google Sheets)
- anthropic (generacion de texto con IA)

---

Parte del ecosistema KraftDo SpA — digitalizamos PYMEs chilenas.
https://kraftdo.cl

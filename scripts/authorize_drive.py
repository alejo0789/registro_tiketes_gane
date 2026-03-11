"""
Script de Autorización de Google Drive (ejecutar UNA SOLA VEZ)
=================================================================
Este script abre el navegador para que autorices el acceso a Google Drive
con tu cuenta personal. Genera un archivo 'token.json' que el servidor
usará automáticamente (con refresh automático) para siempre.

Uso:
    python scripts/authorize_drive.py

Pasos:
    1. Ejecuta este script
    2. Se abrirá el navegador con la pantalla de Google
    3. Inicia sesión con tu cuenta y haz clic en "Permitir"
    4. Se creará backend/token.json automáticamente
    5. Copia ese archivo al servidor de producción (misma ruta)
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "backend", "oauth_credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "backend", "token.json")


def authorize():
    creds = None

    # Si ya existe un token guardado, intentar usarlo
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Si no hay credenciales válidas, iniciar flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expirado, refrescando...")
            creds.refresh(Request())
        else:
            print("Iniciando flujo de autorización OAuth2...")
            print("Se abrirá el navegador. Inicia sesión con tu cuenta de Google y autoriza el acceso.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Guardar el token para uso futuro
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        print(f"\n✅ Token guardado exitosamente en: {TOKEN_FILE}")
        print("📋 IMPORTANTE: Copia este archivo al servidor de producción en la misma ruta relativa.")
    else:
        print(f"✅ Token ya existe y es válido en: {TOKEN_FILE}")

    print("\n🚀 ¡Listo! El servidor puede subir imágenes a Google Drive.")


if __name__ == "__main__":
    authorize()

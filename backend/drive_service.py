"""
Google Drive Service - OAuth2 con cuenta personal de Google
Maneja la subida de archivos a Google Drive usando OAuth2.
El token se obtiene ejecutando: python scripts/authorize_drive.py
"""
import os
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Rutas absolutas basadas en la ubicación de este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "oauth_credentials.json")

# Carpeta destino en Google Drive
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1tcBjar6UNyLOstHAJ9bsDUdJP__VgmBT")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_drive_service():
    """Construye y retorna el cliente autenticado de Google Drive usando OAuth2."""
    creds = None

    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(
            f"No se encontró el token de autorización en: {TOKEN_FILE}\n"
            "Ejecuta primero: python scripts/authorize_drive.py"
        )

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refrescar el token si está expirado (automático con el refresh_token)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Guardar el token actualizado
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)
    return service


def upload_file_to_drive(file_bytes: bytes, filename: str, mimetype: str) -> str:
    """
    Sube un archivo a Google Drive y retorna la URL pública de visualización.

    Args:
        file_bytes: Contenido del archivo en bytes.
        filename: Nombre del archivo a guardar en Drive.
        mimetype: Tipo MIME del archivo (ej: 'image/jpeg').

    Returns:
        URL pública del archivo en Google Drive (thumbnail para imágenes).
    """
    service = _get_drive_service()

    # Metadatos del archivo: nombre y carpeta destino
    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID],
    }

    # Crear el stream del archivo en memoria
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mimetype,
        resumable=False,
    )

    # Subir el archivo a la carpeta compartida
    uploaded_file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id",
        )
        .execute()
    )

    file_id = uploaded_file.get("id")

    # Hacer el archivo públicamente accesible (cualquiera con el enlace puede verlo)
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    # URL de thumbnail para mostrar en <img> (funciona directo sin autenticación)
    public_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
    return public_url


def delete_file_from_drive(file_id: str) -> bool:
    """
    Elimina un archivo de Google Drive por su ID.

    Args:
        file_id: ID del archivo en Google Drive.

    Returns:
        True si se eliminó, False si hubo error.
    """
    try:
        service = _get_drive_service()
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"[Drive] Error eliminando archivo {file_id}: {e}")
        return False

import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Cargar variables de entorno por si acaso no están cargadas
load_dotenv()

# Configurar Cloudinary con las credenciales
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image_to_cloudinary(file_bytes: bytes, filename: str, folder: str = "sorteos") -> str:
    """
    Sube una imagen a Cloudinary y retorna la URL segura de visualización.

    Args:
        file_bytes: Contenido de la imagen en bytes.
        filename: Nombre del archivo inicial (se usará para referencia interna).
        folder: Nombre de la carpeta en Cloudinary (nombre del sorteo).

    Returns:
        URL pública de la imagen en Cloudinary.
    """
    try:
        # Generar un nombre único basado en el filename original (sin extensión)
        public_id = os.path.splitext(filename)[0]

        # Subir el archivo directamente desde los bytes en la carpeta especificada
        upload_result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder, # Nombre de la carpeta/sorteo
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        
        # Retornar la URL segura (HTTPS)
        return upload_result.get("secure_url")
        
    except Exception as e:
        print(f"[Cloudinary] Error subiendo imagen: {e}")
        raise e

def delete_image_from_cloudinary(public_id: str):
    """
    Elimina una imagen de Cloudinary por su public_id.
    """
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        print(f"[Cloudinary] Error eliminando imagen {public_id}: {e}")
        return False

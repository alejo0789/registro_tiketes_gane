import os
import sys
import io

# 1. Asegurar codificación UTF-8 en consola para evitar errores con caracteres especiales en Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 2. Asegurar que Python encuentre el paquete 'backend'
sys.path.append(os.getcwd())

# Importamos la URL para verificar la conexión
from backend.db.session import engine, SessionLocal, DATABASE_URL
from backend.db.models import RegistroSorteo, WhatsAppSession, User

def delete_user_data(cedula: str):
    db = SessionLocal()
    
    try:
        print(f"\n--- Iniciando eliminacion total de registros para la cedula: {cedula} ---")
        
        # 1. Borrar registros de sorteo asociados a la cédula
        registros_borrados = db.query(RegistroSorteo).filter(RegistroSorteo.cedula == cedula).delete()
        print(f"[OK] Se eliminaron {registros_borrados} tickets registrados.")
        
        # 2. Borrar sesión de WhatsApp activa para este usuario
        sesiones_borradas = db.query(WhatsAppSession).filter(WhatsAppSession.cedula == cedula).delete()
        print(f"[OK] Se eliminaron {sesiones_borradas} sesiones de WhatsApp.")
        
        # 3. Borrar al usuario de la tabla de clientes
        usuarios_borrados = db.query(User).filter(User.cedula == cedula).delete()
        print(f"[OK] Se elimino al usuario de la tabla de clientes.")

        db.commit()
        print(f"--- Limpieza completada con exito para {cedula} ---")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Durante la eliminacion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Mostrar a qué base de datos nos estamos conectando realmente
    print("=" * 60)
    print(f"CONEXION ACTUAL: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print("=" * 60)

    if len(sys.argv) > 1:
        ENTRADA = sys.argv[1]
    else:
        ENTRADA = "1113783425"

    cedulas = [c.strip() for c in ENTRADA.split(",") if c.strip()]

    if not cedulas:
        print("WARN: No se proporcionaron cedulas para eliminar.")
    else:
        print(f"Procesando eliminacion para {len(cedulas)} usuarios...")
        for cedula in cedulas:
            delete_user_data(cedula)
        print("\nProceso finalizado.")

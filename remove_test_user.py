import os
import sys

# Agregamos la ruta del proyecto actual para que Python detecte el módulo 'backend'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db.session import SessionLocal
from backend.db import models

def delete_user_data(cedula: str):
    db = SessionLocal()
    try:
        print(f"Buscando datos del usuario con cédula: {cedula}")
        
        # 1. Borrar registros de participación en sorteos
        registros = db.query(models.RegistroSorteo).filter(models.RegistroSorteo.cedula == cedula).all()
        if registros:
            print(f"- Se encontraron {len(registros)} tickets registrados. Eliminando...")
            for reg in registros:
                db.delete(reg)
                
        # 2. Borrar sesiones de WhatsApp activas (para resetear el flujo)
        sesiones = db.query(models.WhatsAppSession).filter(models.WhatsAppSession.cedula == cedula).all()
        if sesiones:
            print(f"- Se encontraron {len(sesiones)} sesiones de WhatsApp. Eliminando...")
            for ses in sesiones:
                db.delete(ses)
                
        # 3. Borrar el usuario en sí
        usuario = db.query(models.User).filter(models.User.cedula == cedula).first()
        if usuario:
            print(f"- Usuario {usuario.nombre_completo} encontrado. Eliminando del sistema...")
            db.delete(usuario)
            
        db.commit()
        print("\n¡Limpieza exitosa! Todos los registros de la cédula han sido borrados de la base de datos.")
    
    except Exception as e:
        db.rollback()
        print(f"Ocurrió un error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    CEDULA_DE_PRUEBA = "1113783425"
    delete_user_data(CEDULA_DE_PRUEBA)

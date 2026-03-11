import os
import sys
from sqlalchemy.orm import sessionmaker

# 1. Asegurar que Python encuentre el paquete 'backend'
sys.path.append(os.getcwd())

from backend.db.session import SessionLocal
from backend.db.models import RegistroSorteo, WhatsAppSession, User

def fix_data():
    db = SessionLocal()
    try:
        incorrect_cedula = "hola"
        correct_cedula = "94450968"
        
        print(f"--- Iniciando correccion de datos para Jefferson Correa ---")
        
        # 1. Verificar que ambos usuarios existan
        user_hola = db.query(User).filter(User.cedula == incorrect_cedula).first()
        user_correct = db.query(User).filter(User.cedula == correct_cedula).first()
        
        if not user_correct:
            print(f"ERROR: No se encontro el usuario con la cedula correcta ({correct_cedula}).")
            return

        if user_hola:
            print(f"OK: Se encontro el usuario corrupto: {user_hola.nombre_completo}")
            
            # 2. Mover registros de sorteo directamente con un UPDATE
            # Esto evita conflictos con las relaciones de SQLAlchemy durante el loop
            num_registros = db.query(RegistroSorteo).filter(RegistroSorteo.cedula == incorrect_cedula).update(
                {"cedula": correct_cedula}, synchronize_session='fetch'
            )
            print(f"OK: {num_registros} registros movidos a la cedula correcta.")
            
            # 3. Mover sesiones de WhatsApp
            num_sesiones = db.query(WhatsAppSession).filter(WhatsAppSession.cedula == incorrect_cedula).update(
                {"cedula": correct_cedula}, synchronize_session='fetch'
            )
            print(f"OK: {num_sesiones} sesiones de WhatsApp actualizadas.")

            # 4. Eliminar el usuario "hola"
            db.delete(user_hola)
            print(f"OK: Usuario corrupto ('hola') eliminado.")
            
            db.commit()
            print(f"\n--- Correccion completada con exito ---")
        else:
            print(f"WARN: No se encontro el usuario con cedula 'hola'.")
            
    except Exception as e:
        db.rollback()
        print(f"ERROR: Error durante la correccion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_data()

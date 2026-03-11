import os
import sys
from sqlalchemy.orm import sessionmaker

# 1. Asegurar que Python encuentre el paquete 'backend'
sys.path.append(os.getcwd())

from backend.db.session import SessionLocal
from backend.db.models import RegistroSorteo, User

def inspect_db():
    db = SessionLocal()
    try:
        print("--- Inspeccionando tabla RegistroSorteo para cedulas no numericas ---")
        registros = db.query(RegistroSorteo).all()
        found = False
        for reg in registros:
            if not reg.cedula.isdigit():
                print(f"Registro: ID={reg.id}, Cedula='{reg.cedula}', Ticket={reg.numero_registro}")
                found = True
        
        if not found:
            print("No se encontraron registros con cedulas no numericas en RegistroSorteo.")

        print("\n--- Inspeccionando tabla User para cedulas no numericas ---")
        usuarios = db.query(User).all()
        found = False
        for user in usuarios:
            if not user.cedula.isdigit():
                print(f"Usuario: Cedula='{user.cedula}', Nombre='{user.nombre_completo}'")
                found = True
        
        if not found:
            print("No se encontraron usuarios con cedulas no numericas en User.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()

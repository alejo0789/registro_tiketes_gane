from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

# Add the project root to sys.path to import models
sys.path.append(os.getcwd())

from backend.db.models import RegistroSorteo, Base
from backend.db.database import SQLALCHEMY_DATABASE_URL

def clean_duplicates():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("--- Iniciando limpieza de tickets duplicados ---")
        
        # 1. Obtener todos los registros
        registros = db.query(RegistroSorteo).all()
        
        # 2. Mapa para rastrear versiones limpias
        ticket_map = {} # {ticket_limpio: id_original}
        deleted_count = 0
        updated_count = 0
        
        for reg in registros:
            # Limpiar el número actual
            original_num = reg.numero_registro
            clean_num = original_num.replace("-", "").replace(".", "").replace(" ", "").replace("#", "").strip()
            
            # Si el número cambió al limpiarlo, lo actualizamos en la DB si no genera conflicto
            if original_num != clean_num:
                reg.numero_registro = clean_num
                updated_count += 1
            
            # Verificar si ya existe este número limpio en el mapa
            if clean_num in ticket_map:
                # Es un duplicado, borrar este registro
                print(f"Borrando duplicado: {original_num} (ID: {reg.id})")
                db.delete(reg)
                deleted_count += 1
            else:
                ticket_map[clean_num] = reg.id
        
        db.commit()
        print(f"\nResumen:")
        print(f"- Tickets actualizados a formato limpio: {updated_count}")
        print(f"- Registros duplicados eliminados: {deleted_count}")
        print("--- Limpieza completada con éxito ---")
        
    except Exception as e:
        db.rollback()
        print(f"Error durante la limpieza: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_duplicates()

import sys
import os
import datetime

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.session import SessionLocal, engine
from backend.db import models

def init_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if Baloto exists
    baloto = db.query(models.SorteoConfig).filter(models.SorteoConfig.nombre_sorteo == "Baloto").first()
    if not baloto:
        print("Creating initial Baloto Sorteo...")
        new_sorteo = models.SorteoConfig(
            nombre_sorteo="Baloto",
            fecha_inicio=datetime.date.today(),
            fecha_fin=datetime.date.today() + datetime.timedelta(days=365),
            activo=True
        )
        db.add(new_sorteo)
        db.commit()
    else:
        print("Baloto Sorteo already exists.")
    
    db.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()

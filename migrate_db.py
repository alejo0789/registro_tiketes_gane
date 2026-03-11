import sqlite3
import os

db_path = "acertemos.db"

if os.path.exists(db_path):
    print(f"Migrando base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Intentar agregar la columna comprobante_url
        cursor.execute("ALTER TABLE registros_sorteo ADD COLUMN comprobante_url TEXT")
        conn.commit()
        print("OK: Columna 'comprobante_url' agregada exitosamente a 'registros_sorteo'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("INFO: La columna 'comprobante_url' ya existe.")
        else:
            print(f"ERROR al migrar: {e}")
    finally:
        conn.close()
else:
    print(f"ERROR: No se encontró el archivo de base de datos en {db_path}")

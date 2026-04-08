from fastapi import FastAPI, Depends, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime
import os
import uuid
import re

from backend.cloudinary_service import upload_image_to_cloudinary

from backend.db.session import get_db, engine
from backend.db import models
from backend.api import schemas

# Create tables
models.Base.metadata.create_all(bind=engine)

# Run migration to add new columns if they don't exist yet (safe for SQLite)
from sqlalchemy import text, inspect

def run_migrations():
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # --- gane_clientes_sorteos ---
        t_name = "gane_clientes_sorteos"
        if t_name in inspector.get_table_names():
            existing_cols = [c["name"] for c in inspector.get_columns(t_name)]
            if "telefono" not in existing_cols:
                conn.execute(text(f"ALTER TABLE {t_name} ADD COLUMN telefono VARCHAR(255)"))
                conn.commit()

        # --- gane_registros_sorteo: soporte betplay/chance ---
        t_reg = "gane_registros_sorteo"
        if t_reg in inspector.get_table_names():
            reg_cols = [c["name"] for c in inspector.get_columns(t_reg)]
            new_reg_cols = {
                "tipo_ticket":   "VARCHAR(20)",
                "id_transaccion": "VARCHAR(100)",
                "identificacion": "VARCHAR(100)",
                "valor":          "VARCHAR(50)",
            }
            for col, col_type in new_reg_cols.items():
                if col not in reg_cols:
                    conn.execute(text(f"ALTER TABLE {t_reg} ADD COLUMN {col} {col_type}"))
                    conn.commit()

        # --- gane_sorteos_config ---
        t_sorteo = "gane_sorteos_config"
        if t_sorteo in inspector.get_table_names():
            sorteo_cols = [c["name"] for c in inspector.get_columns(t_sorteo)]
            if "premio" not in sorteo_cols:
                conn.execute(text(f"ALTER TABLE {t_sorteo} ADD COLUMN premio VARCHAR(255)"))
                conn.commit()

        # --- gane_whatsapp_sessions: soporte betplay/chance ---
        t_sess = "gane_whatsapp_sessions"
        if t_sess in inspector.get_table_names():
            sess_cols = [c["name"] for c in inspector.get_columns(t_sess)]
            new_sess_cols = {
                "tipo_ticket_pendiente":   "VARCHAR(20)",
                "identificacion_pendiente": "VARCHAR(100)",
                "valor_pendiente":          "VARCHAR(50)",
            }
            for col, col_type in new_sess_cols.items():
                if col not in sess_cols:
                    conn.execute(text(f"ALTER TABLE {t_sess} ADD COLUMN {col} {col_type}"))
                    conn.commit()

try:
    run_migrations()
except Exception as e:
    print(f"[Migration] Skipped or error: {e}")

def init_admin():
    from backend.db.session import SessionLocal
    import hashlib
    db = SessionLocal()
    try:
        hashed_pw = hashlib.sha256("admin123*".encode()).hexdigest()
        admin = db.query(models.AdminUser).filter(models.AdminUser.username == "admin").first()
        if not admin:
            new_admin = models.AdminUser(username="admin", password_hash=hashed_pw)
            db.add(new_admin)
            db.commit()
            print("[Init Admin] Usuario administrador creado exitosamente.")
    except Exception as e:
        print(f"[Init Admin] Error: {e}")
    finally:
        db.close()

try:
    init_admin()
except Exception as e:
    print(f"[Init Admin] Skipped or error: {e}")

app = FastAPI(title="Acertemos Sorteos API")

# Ensure assets directory exists and mount it
os.makedirs("assets/receipts", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/acertemos_premium_ui", StaticFiles(directory="acertemos_premium_ui"), name="ui")

# Serve index.html at root and /index.html
@app.get("/")
@app.get("/index.html")
def read_index():
    return RedirectResponse(url="dashboard.html")

# Serve dashboard.html
@app.get("/dashboard")
@app.get("/dashboard.html")
def read_dashboard():
    return FileResponse("dashboard.html")

@app.get("/terminos")
@app.get("/terminos.html")
def read_terminos():
    return FileResponse("terminos.html")

@app.get("/login")
@app.get("/login.html")
def read_login():
    return FileResponse("login.html")

@app.post("/api/login", response_model=schemas.Token)
def login_admin(data: schemas.AdminLogin, db: Session = Depends(get_db)):
    import hashlib
    hashed_pw = hashlib.sha256(data.password.encode()).hexdigest()
    admin = db.query(models.AdminUser).filter(
        models.AdminUser.username == data.username,
        models.AdminUser.password_hash == hashed_pw
    ).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    return {"access_token": "valid_admin_token_acertemos", "token_type": "bearer"}

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/check-user/{cedula}", response_model=Optional[schemas.UserBase])
def check_user(cedula: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.cedula == cedula).first()
    if user:
        return user
    return None

@app.post("/upload-receipt")
async def upload_receipt(file: UploadFile = File(...), sorteo_nombre: Optional[str] = Query(None)):
    # Generar nombre único para el archivo
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"comprobante_{uuid.uuid4()}{file_extension}"

    # Leer el contenido del archivo en memoria
    file_bytes = await file.read()

    # Definir la carpeta basado en el sorteo (o 'general' si no viene ninguno)
    folder_name = f"sorteos/{sorteo_nombre.replace(' ', '_')}" if sorteo_nombre else "sorteos/general"

    try:
        # Subir a Cloudinary con el folder dinámico
        public_url = upload_image_to_cloudinary(file_bytes, filename, folder=folder_name)
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen a Cloudinary: {str(e)}")

@app.post("/register", response_model=schemas.RegistroResponse)
def register_to_sorteo(data: schemas.RegistroCreate, db: Session = Depends(get_db)):
    # 1. Validate that comprobante is present
    if not data.comprobante_url or not data.comprobante_url.strip():
        raise HTTPException(status_code=400, detail="La foto del ticket es obligatoria para el registro.")

    # 2. Handle User
    user = db.query(models.User).filter(models.User.cedula == data.cedula).first()
    if not user:
        if not data.nombre_completo:
            raise HTTPException(status_code=400, detail="El nombre completo es obligatorio para nuevos usuarios.")
        if not data.telefono:
            raise HTTPException(status_code=400, detail="El teléfono de contacto es obligatorio para nuevos usuarios.")
        user = models.User(
            cedula=data.cedula,
            nombre_completo=data.nombre_completo,
            telefono=data.telefono
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Check for unique ticket number per sorteo
    existing_reg = db.query(models.RegistroSorteo).filter(
        models.RegistroSorteo.sorteo_id == data.sorteo_id,
        models.RegistroSorteo.numero_registro == data.numero_registro
    ).first()
    
    if existing_reg:
        raise HTTPException(
            status_code=400, 
            detail=f"El ticket '{data.numero_registro}' ya ha sido registrado anteriormente."
        )

    # 4. Create the registration
    new_reg = models.RegistroSorteo(
        cedula=data.cedula,
        sorteo_id=data.sorteo_id,
        numero_registro=data.numero_registro,
        comprobante_url=data.comprobante_url
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)

    # 5. Count total tickets by this cedula in this sorteo
    total_tickets = db.query(func.count(models.RegistroSorteo.id)).filter(
        models.RegistroSorteo.cedula == data.cedula,
        models.RegistroSorteo.sorteo_id == data.sorteo_id
    ).scalar()

    # 6. Calculate remaining tickets for the goal (e.g., 10 for the motorcycle)
    MOTO_GOAL = 10
    tickets_restantes = max(0, MOTO_GOAL - total_tickets)

    return schemas.RegistroResponse(
        id=new_reg.id,
        cedula=new_reg.cedula,
        sorteo_id=new_reg.sorteo_id,
        numero_registro=new_reg.numero_registro,
        comprobante_url=new_reg.comprobante_url,
        fecha_creacion=new_reg.fecha_creacion,
        total_tickets=total_tickets,
        tickets_restantes=tickets_restantes
    )

@app.get("/whatsapp/check-user/{telefono}", response_model=schemas.WhatsAppUserCheck)
def check_user_by_phone(telefono: str, db: Session = Depends(get_db)):
    # Sanitize phone
    clean_tel = telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").strip()
    
    # Search for user by phone
    # Note: Search using LIKE if it's stored differently or just exact match
    user = db.query(models.User).filter(models.User.telefono == clean_tel).first()
    
    if user:
        return schemas.WhatsAppUserCheck(
            exists=True,
            cedula=user.cedula,
            nombre=user.nombre_completo,
            telefono=user.telefono
        )
    return schemas.WhatsAppUserCheck(exists=False)

@app.get("/whatsapp/check-ticket/{numero_sorteo}", response_model=schemas.WhatsAppTicketCheck)
def check_ticket_registration(numero_sorteo: str, db: Session = Depends(get_db)):
    # 1. Find the current active sorteo
    from backend.db.models import get_colombia_time
    today = get_colombia_time().date()
    active_sorteo = db.query(models.SorteoConfig).filter(
        models.SorteoConfig.activo == True,
        models.SorteoConfig.fecha_inicio <= today,
        models.SorteoConfig.fecha_fin >= today
    ).first()

    if not active_sorteo:
        return schemas.WhatsAppTicketCheck(registered=False, mensaje="No hay sorteos activos.")

    # 2. Check if ticket exists in active sorteo
    existing_reg = db.query(models.RegistroSorteo).filter(
        models.RegistroSorteo.sorteo_id == active_sorteo.id,
        models.RegistroSorteo.numero_registro == numero_sorteo
    ).first()

    if existing_reg:
        return schemas.WhatsAppTicketCheck(
            registered=True, 
            mensaje=f"El ticket '{numero_sorteo}' ya ha sido registrado anteriormente."
        )
    
    return schemas.WhatsAppTicketCheck(registered=False, mensaje="Ticket disponible para registro.")

@app.post("/whatsapp/register", response_model=schemas.WhatsAppRegistroResponse)
def register_from_whatsapp(data: schemas.WhatsAppRegistroCreate, db: Session = Depends(get_db)):
    # Sanitize data
    data.cedula = re.sub(r"\D", "", data.cedula)
    data.telefono = re.sub(r"\D", "", data.telefono)
    
    # 1. Direct registration from WhatsApp data
    # Find the current active sorteo automatically
    from backend.db.models import get_colombia_time
    today = get_colombia_time().date()
    active_sorteo = db.query(models.SorteoConfig).filter(
        models.SorteoConfig.activo == True,
        models.SorteoConfig.fecha_inicio <= today,
        models.SorteoConfig.fecha_fin >= today
    ).first()

    if not active_sorteo:
        raise HTTPException(status_code=400, detail="No hay sorteos activos en este momento.")

    # 2. Reuse logic to handle user and registration
    # Check User
    user = db.query(models.User).filter(models.User.cedula == data.cedula).first()
    if not user:
        user = models.User(
            cedula=data.cedula,
            nombre_completo=data.nombre,
            telefono=data.telefono
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update name or phone if provided and different
        user.nombre_completo = data.nombre
        user.telefono = data.telefono
        db.commit()

    # Check for unique ticket
    existing_reg = db.query(models.RegistroSorteo).filter(
        models.RegistroSorteo.sorteo_id == active_sorteo.id,
        models.RegistroSorteo.numero_registro == data.numero_sorteo
    ).first()

    if existing_reg:
        # Instead of error, maybe just return current status but indicating it was already there
        total_tickets = db.query(func.count(models.RegistroSorteo.id)).filter(
            models.RegistroSorteo.cedula == data.cedula,
            models.RegistroSorteo.sorteo_id == active_sorteo.id
        ).scalar()
        MOTO_GOAL = 10
        tickets_restantes = max(0, MOTO_GOAL - total_tickets)
        return schemas.WhatsAppRegistroResponse(
            status="already_registered",
            mensaje=f"El ticket {data.numero_sorteo} ya estaba registrado.",
            total_tickets=total_tickets,
            tickets_restantes=tickets_restantes,
            cedula=user.cedula,
            nombre=user.nombre_completo
        )

    # Create registration
    new_reg = models.RegistroSorteo(
        cedula=data.cedula,
        sorteo_id=active_sorteo.id,
        numero_registro=data.numero_sorteo,
        comprobante_url=data.url_imagen
    )
    db.add(new_reg)
    db.commit()

    # Count total
    total_tickets = db.query(func.count(models.RegistroSorteo.id)).filter(
        models.RegistroSorteo.cedula == data.cedula,
        models.RegistroSorteo.sorteo_id == active_sorteo.id
    ).scalar()

    MOTO_GOAL = 10
    tickets_restantes = max(0, MOTO_GOAL - total_tickets)
    
    premio_text = active_sorteo.premio or "la moto"
    msg = f"¡Registro exitoso! Llevas {total_tickets} ticket(s)."
    if tickets_restantes > 0:
        msg += f" Te faltan {tickets_restantes} para participar por {premio_text}."
    else:
        msg += f" ¡Ya estás participando por {premio_text}! 🏍️"

    return schemas.WhatsAppRegistroResponse(
        status="success",
        mensaje=msg,
        total_tickets=total_tickets,
        tickets_restantes=tickets_restantes,
        cedula=user.cedula,
        nombre=user.nombre_completo
    )

@app.get("/sorteos", response_model=List[schemas.SorteoConfig])
def get_sorteos(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.SorteoConfig)
    if active_only:
        # Usar hora de Colombia para determinar qué sorteos están activos
        from backend.db.models import get_colombia_time
        today = get_colombia_time().date()
        query = query.filter(models.SorteoConfig.activo == True, 
                             models.SorteoConfig.fecha_inicio <= today,
                             models.SorteoConfig.fecha_fin >= today)
    return query.all()

@app.post("/sorteos", response_model=schemas.SorteoConfig)
def create_sorteo(sorteo: schemas.SorteoConfigCreate, db: Session = Depends(get_db)):
    db_sorteo = models.SorteoConfig(**sorteo.dict())
    db.add(db_sorteo)
    db.commit()
    db.refresh(db_sorteo)
    return db_sorteo

@app.put("/sorteos/{sorteo_id}", response_model=schemas.SorteoConfig)
def update_sorteo(sorteo_id: int, sorteo_update: schemas.SorteoConfigUpdate, db: Session = Depends(get_db)):
    db_sorteo = db.query(models.SorteoConfig).filter(models.SorteoConfig.id == sorteo_id).first()
    if not db_sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    
    update_data = sorteo_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sorteo, key, value)
    
    db.commit()
    db.refresh(db_sorteo)
    return db_sorteo

@app.get("/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(sorteo_id: Optional[int] = None, db: Session = Depends(get_db)):
    reg_query = db.query(func.count(models.RegistroSorteo.id))
    
    if sorteo_id:
        user_count = db.query(func.count(func.distinct(models.RegistroSorteo.cedula))).filter(
            models.RegistroSorteo.sorteo_id == sorteo_id
        ).scalar()
        reg_query = reg_query.filter(models.RegistroSorteo.sorteo_id == sorteo_id)
    else:
        user_count = db.query(func.count(models.User.cedula)).scalar()
        
    reg_count = reg_query.scalar()
    
    return {"total_usuarios": user_count, "total_registros": reg_count}

@app.get("/dashboard/users", response_model=schemas.UserTableResponse)
def get_dashboard_users(
    sorteo_id: Optional[int] = None, 
    search: Optional[str] = None,
    ticket_number: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Determine base query
    query = db.query(
        models.User.cedula,
        models.User.nombre_completo,
        models.User.telefono,
        func.count(models.RegistroSorteo.id).label("count_sorteos"),
        func.count(models.RegistroSorteo.comprobante_url).label("count_receipts"),
        func.max(models.RegistroSorteo.fecha_creacion).label("fecha_ultimo_registro"),
        func.max(models.RegistroSorteo.comprobante_url).label("comprobante_url")
    ).outerjoin(models.RegistroSorteo)
    
    # Filtering
    if sorteo_id:
        query = query.filter(models.RegistroSorteo.sorteo_id == sorteo_id)

    if search:
        search_val = f"%{search}%"
        query = query.filter(
            (models.User.nombre_completo.ilike(search_val)) |
            (models.User.cedula.ilike(search_val)) |
            (models.User.telefono.ilike(search_val))
        )
    
    if ticket_number:
        query = query.filter(models.RegistroSorteo.numero_registro.ilike(f"%{ticket_number}%"))
        
    # Group by
    query = query.group_by(models.User.cedula)

    # Count total items
    total_count = query.count()
    
    # Apply pagination
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    
    items = [
        schemas.UserTableItem(
            cedula=r.cedula,
            nombre_completo=r.nombre_completo,
            telefono=r.telefono,
            count_sorteos=r.count_sorteos,
            count_receipts=r.count_receipts,
            comprobante_url=r.comprobante_url,
            fecha_ultimo_registro=r.fecha_ultimo_registro
        ) for r in results
    ]

    return {
        "items": items,
        "total": total_count,
        "pages": (total_count + page_size - 1) // page_size,
        "current_page": page
    }

@app.get("/dashboard/user-receipts/{cedula}", response_model=List[schemas.ReceiptItem])
def get_user_receipts(cedula: str, sorteo_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(
        models.RegistroSorteo.numero_registro,
        models.RegistroSorteo.tipo_ticket,
        models.RegistroSorteo.id_transaccion,
        models.RegistroSorteo.identificacion,
        models.RegistroSorteo.valor,
        models.RegistroSorteo.comprobante_url,
        models.RegistroSorteo.fecha_creacion,
        models.SorteoConfig.nombre_sorteo
    ).join(models.SorteoConfig).filter(models.RegistroSorteo.cedula == cedula)
    
    if sorteo_id:
        query = query.filter(models.RegistroSorteo.sorteo_id == sorteo_id)
        
    results = query.order_by(models.RegistroSorteo.fecha_creacion.desc()).all()
    
    return [
        schemas.ReceiptItem(
            numero_registro=r.numero_registro,
            tipo_ticket=r.tipo_ticket,
            id_transaccion=r.id_transaccion,
            identificacion=r.identificacion,
            valor=r.valor,
            comprobante_url=r.comprobante_url,
            fecha_creacion=r.fecha_creacion,
            nombre_sorteo=r.nombre_sorteo
        ) for r in results
    ]

@app.post("/whatsapp/interact", response_model=schemas.WhatsAppInteractResponse)
def whatsapp_orchestrator(data: schemas.WhatsAppInteractRequest, db: Session = Depends(get_db)):
    """
    Orquestador de lógica para WhatsApp. n8n solo actúa como puente.
    Soporta dos tipos de tickets: betplay y chance.
    El JSON de n8n incluye tipo_documento_detectado, extracted_id_tra,
    extracted_identificacion y extracted_valor.
    """
    telefono = data.telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").strip()
    texto = data.texto.strip() if data.texto else ""

    # Helper para limpiar números
    def clean_num(val: Optional[str]) -> Optional[str]:
        if not val:
            return None
        return re.sub(r"[\.,\s]", "", val.strip())

    # 1. Obtener Sorteo Activo
    from backend.db.models import get_colombia_time
    today = get_colombia_time().date()
    active_sorteo = db.query(models.SorteoConfig).filter(
        models.SorteoConfig.activo == True,
        models.SorteoConfig.fecha_inicio <= today,
        models.SorteoConfig.fecha_fin >= today
    ).first()

    if not active_sorteo:
        return {"mensaje": "Lo sentimos, no hay sorteos activos en este momento.", "paso_siguiente": "FIN"}

    # --- Detectar tipo de documento que llegó en esta interacción ---
    tipo_doc = (data.tipo_documento_detectado or "").lower().strip()

    # --- SALUDOS ---
    palabras_saludo = ["hola", "buen", "saludos", "hi", "menu", "inicio", "reinicio"]
    es_saludo = any(s in texto.lower() for s in palabras_saludo) and not tipo_doc

    # 2. Obtener o Crear Sesión
    session = db.query(models.WhatsAppSession).filter(models.WhatsAppSession.telefono == telefono).first()

    # 3. VERIFICACIÓN UNIVERSAL DE REGISTRO
    user = db.query(models.User).filter(models.User.telefono == telefono).first()

    if not session:
        session = models.WhatsAppSession(telefono=telefono)
        db.add(session)
        session.paso = "MENU"
        if user:
            session.cedula = user.cedula
            session.nombre_completo = user.nombre_completo
        db.commit()

    if tipo_doc == "invalido":
        return {
            "mensaje": "⚠️ El documento enviado no parece ser una *cédula válida* o un *ticket aceptado* (Betplay/Chance).\n\nPor favor, intenta enviar una foto más clara y asegúrate de que sea un formato permitido.",
            "paso_siguiente": session.paso
        }

    # Si es saludo o paso INICIO, reiniciar al menú principal
    if es_saludo or session.paso == "INICIO":
        session.paso = "MENU"
        db.commit()
        nombre_str = f" Hola, *{user.nombre_completo.split()[0]}*" if user and user.nombre_completo else " ¡Hola!"
        return {
            "mensaje": f"🎰{nombre_str}! Bienvenido a Gane.\n\n¿Qué deseas hacer hoy?\n\n1️⃣ Registrar un nuevo ticket 🎟️\n2️⃣ Consultar ticket ganador 🏆\n\nResponde con el número de tu opción (1 o 2).",
            "paso_siguiente": "MENU"
        }

    # =========================================================
    # 4. MÁQUINA DE ESTADOS
    # =========================================================

    # --- PASO: MENU ---
    if session.paso == "MENU":
        opcion = texto.strip()
        if opcion == "1":
            if user:
                session.paso = "TICKET"
                db.commit()
                return {
                    "mensaje": "¡Perfecto! Envíame la *foto de tu ticket Betplay o Chance* 🏟️ para registrar tu participación.",
                    "paso_siguiente": "TICKET"
                }
            else:
                session.paso = "CEDULA"
                db.commit()
                premio_text = active_sorteo.premio or "la moto"
                return {
                    "mensaje": f"¡Perfecto! Estás participando por *{premio_text}* 🏙️.\n\nPara comenzar, envíame una *foto clara de tu cédula* 📸.\n\n_Sus datos serán tratados de acuerdo a nuestra política de privacidad._",
                    "paso_siguiente": "CEDULA"
                }
        elif opcion == "2":
            session.paso = "CONSULTA_TICKET"
            db.commit()
            return {
                "mensaje": "🏆 Has elegido *Consultar Ticket*.\n\nPor favor, *envíame la foto del ticket* que deseas verificar, o escribe el número de serie.",
                "paso_siguiente": "CONSULTA_TICKET"
            }
        else:
            return {
                "mensaje": "⚠️ Opción no válida.\n\nPor favor responde *1* para registrar un ticket nuevo o *2* para consultar un ticket ganador.",
                "paso_siguiente": "MENU"
            }

    # --- PASO: CONSULTA TICKET ---
    if session.paso == "CONSULTA_TICKET":
        import urllib.request
        import json
        
        id_tra = None
        if tipo_doc in ["betplay", "chance"] and data.extracted_id_tra:
            id_tra = clean_num(data.extracted_id_tra)
        elif not tipo_doc and texto: # Si digita el numero manualmente
            val = texto.replace("-", "").replace(".", "").replace(" ", "").replace("#", "").strip()
            if val.isdigit() and len(val) >= 4:
                id_tra = val
                
        if not id_tra:
            return {
                "mensaje": "⚠️ No pudimos detectar el número de serie. Por favor envía una foto clara del ticket o escribe el número manualmente.",
                "paso_siguiente": "CONSULTA_TICKET"
            }

        url_validador = f"https://script.google.com/macros/s/AKfycby6XEiNdZZUXxt9_sxZhO7-tkluNY8KG1WMmAx2LZEbvp6Ij9md38jRFSihms5ltUwx/exec?serie={id_tra}"
        try:
            req = urllib.request.Request(url_validador)
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode())
                
            if result.get("valido") == True:
                msg_validador = result.get("mensaje", "")
                if "GANASTE" in msg_validador.upper():
                    mensaje_final = f"🎉 ¡FELICIDADES! 🎉\n\nTu ticket *{id_tra}* es un ganador. 🏆\n\n{msg_validador}"
                else:
                    mensaje_final = f"Tu ticket *{id_tra}* es válido.\n\n{msg_validador}"
            else:
                msg_validador = result.get("mensaje", "Contacte a su proveedor.")
                mensaje_final = f"⚠️ *{id_tra}* no es válido.\n\n{msg_validador}"
                
        except Exception as e:
            mensaje_final = "Hubo un error verificando el ticket en nuestro sistema (el servidor de consulta está ocupado). Por favor intenta más tarde."
        
        # Volvemos al menu independientemente del resultado
        session.paso = "MENU"
        db.commit()
        
        mensaje_final += "\n\n💡 _Volviendo al menú principal..._\nSi deseas hacer algo más, dime *Hola* o digita:\n1️⃣ Registrar un nuevo ticket\n2️⃣ Consultar otro ticket"
        
        return {
            "mensaje": mensaje_final,
            "paso_siguiente": "MENU"
        }

    # --- PASO: CEDULA ---
    if session.paso == "CEDULA":
        # Si n8n detectó una cédula en la imagen
        if tipo_doc == "cedula" or data.extracted_cedula:
            val = clean_num(data.extracted_cedula or texto)
            if not val or not val.isdigit() or len(val) < 6:
                return {"mensaje": "⚠️ No logré leer la cédula. Por favor escíbela manualmente o envía una foto más clara.", "paso_siguiente": "CEDULA"}

            session.cedula = val
            user_existing = db.query(models.User).filter(models.User.cedula == val).first()
            if user_existing:
                session.nombre_completo = user_existing.nombre_completo
                session.paso = "TICKET"
                db.commit()
                return {
                    "mensaje": f"Bienvenido de nuevo, *{user_existing.nombre_completo.split()[0]}*. 👋\n\n"
                               "Envíame la *foto de tu ticket Betplay o Chance* para registrarlo.",
                    "paso_siguiente": "TICKET"
                }
            else:
                if data.extracted_nombre:
                    session.nombre_completo = data.extracted_nombre
                    session.paso = "TICKET"
                    db.commit()
                    new_user = models.User(cedula=session.cedula, nombre_completo=data.extracted_nombre, telefono=telefono)
                    db.add(new_user)
                    db.commit()
                    return {
                        "mensaje": f"Detecté tu nombre: *{data.extracted_nombre}*. ✅\n\n"
                                   "Ahora envíame la *foto de tu ticket Betplay o Chance*.",
                        "paso_siguiente": "TICKET"
                    }
                session.paso = "NOMBRE"
                db.commit()
                return {
                    "mensaje": "No tenemos tu registro aún. ¿Cuál es tu *nombre completo*?",
                    "paso_siguiente": "NOMBRE"
                }

        # Si llegó un ticket en vez de cédula, avisamos
        elif tipo_doc in ("betplay", "chance"):
            return {
                "mensaje": "⚠️ Primero necesito tu *cédula*. Por favor envía una foto clara de ella.",
                "paso_siguiente": "CEDULA"
            }
        else:
            # Texto manual de cédula
            val = clean_num(texto)
            if not val or not val.isdigit() or len(val) < 6:
                return {"mensaje": "⚠️ Por favor envía la foto de tu cédula o escíbela manualmente (solo números).", "paso_siguiente": "CEDULA"}
            session.cedula = val
            user_existing = db.query(models.User).filter(models.User.cedula == val).first()
            if user_existing:
                session.nombre_completo = user_existing.nombre_completo
                session.paso = "TICKET"
                db.commit()
                return {
                    "mensaje": f"Bienvenido de nuevo, *{user_existing.nombre_completo.split()[0]}*. 👋\n\n"
                               "Envíame la *foto de tu ticket Betplay o Chance*.",
                    "paso_siguiente": "TICKET"
                }
            session.paso = "NOMBRE"
            db.commit()
            return {
                "mensaje": "No tenemos tu registro. ¿Cuál es tu *nombre completo*?",
                "paso_siguiente": "NOMBRE"
            }

    # --- PASO: NOMBRE ---
    if session.paso == "NOMBRE":
        val_nombre = data.extracted_nombre or texto
        if len(val_nombre) < 3:
            return {"mensaje": "⚠️ Por favor ingresa tu nombre completo.", "paso_siguiente": "NOMBRE"}

        session.nombre_completo = val_nombre
        session.paso = "TICKET"
        db.commit()
        new_user = models.User(cedula=session.cedula, nombre_completo=val_nombre, telefono=telefono)
        db.add(new_user)
        db.commit()
        return {
            "mensaje": f"Mucho gusto, *{val_nombre}*. 😊\n\nAhora envíame la *foto de tu ticket Betplay o Chance*.",
            "paso_siguiente": "TICKET"
        }

    # --- PASO: TICKET ---
    if session.paso == "TICKET":
        # ===== CASO: n8n detectó BETPLAY =====
        if tipo_doc == "betplay" and data.extracted_id_tra:
            id_tra = clean_num(data.extracted_id_tra)
            identificacion = clean_num(data.extracted_identificacion)
            valor = clean_num(data.extracted_valor)

            # Verificar duplicado por id_tra en el sorteo
            existing = db.query(models.RegistroSorteo).filter(
                models.RegistroSorteo.sorteo_id == active_sorteo.id,
                models.RegistroSorteo.numero_registro == id_tra
            ).first()
            if existing:
                return {"mensaje": f"⚠️ El ticket Betplay con ID *{id_tra}* ya fue registrado. Prueba con otro.", "paso_siguiente": "TICKET"}

            # Guardar datos en sesión para confirmar con la foto
            session.numero_registro = id_tra
            session.tipo_ticket_pendiente = "betplay"
            session.identificacion_pendiente = identificacion
            session.valor_pendiente = valor

            if data.media_url:
                # Ya tenemos la foto del ticket, registrar directamente
                session.paso = "FOTO"
                db.commit()
                # Caer al bloque FOTO
            else:
                session.paso = "FOTO"
                db.commit()
                return {
                    "mensaje": f"🏟️ *Ticket Betplay detectado* ✅\n"
                               f"\u2022 ID Transacción: *{id_tra}*\n"
                               f"\u2022 Identificación: *{identificacion or 'N/A'}*\n"
                               f"\u2022 Valor: *${valor or 'N/A'}*\n\n"
                               "Envíame la *foto clara del ticket* para completar el registro.",
                    "paso_siguiente": "FOTO"
                }

        # ===== CASO: n8n detectó CHANCE =====
        elif tipo_doc == "chance" and data.extracted_id_tra:
            id_tra = clean_num(data.extracted_id_tra)
            valor = clean_num(data.extracted_valor)

            existing = db.query(models.RegistroSorteo).filter(
                models.RegistroSorteo.sorteo_id == active_sorteo.id,
                models.RegistroSorteo.numero_registro == id_tra
            ).first()
            if existing:
                return {"mensaje": f"⚠️ El ticket Chance con ID *{id_tra}* ya fue registrado. Prueba con otro.", "paso_siguiente": "TICKET"}

            session.numero_registro = id_tra
            session.tipo_ticket_pendiente = "chance"
            session.identificacion_pendiente = None
            session.valor_pendiente = valor

            if data.media_url:
                session.paso = "FOTO"
                db.commit()
                # Caer al bloque FOTO
            else:
                session.paso = "FOTO"
                db.commit()
                return {
                    "mensaje": f"🏟️ *Ticket Chance detectado* ✅\n"
                               f"\u2022 ID Transacción: *{id_tra}*\n"
                               f"\u2022 Total: *${valor or 'N/A'}*\n\n"
                               "Envíame la *foto clara del ticket* para completar el registro.",
                    "paso_siguiente": "FOTO"
                }

        # ===== TEXTO MANUAL (compatibilidad antigua) =====
        else:
            val_ticket = data.extracted_ticket or texto
            val_ticket = val_ticket.replace("-", "").replace(".", "").replace(" ", "").replace("#", "").strip()

            if len(val_ticket) < 1:
                return {"mensaje": "⚠️ Por favor envía la *foto de tu ticket Betplay o Chance* para registrarlo.", "paso_siguiente": "TICKET"}

            existing = db.query(models.RegistroSorteo).filter(
                models.RegistroSorteo.sorteo_id == active_sorteo.id,
                models.RegistroSorteo.numero_registro == val_ticket
            ).first()
            if existing:
                return {"mensaje": f"⚠️ El ticket *{val_ticket}* ya ha sido registrado. Prueba con otro.", "paso_siguiente": "TICKET"}

            session.numero_registro = val_ticket
            session.tipo_ticket_pendiente = "manual"
            session.paso = "FOTO"
            db.commit()
            return {
                "mensaje": f"Ticket *{val_ticket}* recibido. 🏟️\n\nAhora envíame la *foto clara del ticket* para completar el registro.",
                "paso_siguiente": "FOTO"
            }

    # --- PASO: FOTO ---
    if session.paso == "FOTO":
        if not data.media_url:
            return {"mensaje": "⚠️ Por favor, envía la *foto* del ticket para finalizar.", "paso_siguiente": "FOTO"}

        tipo = session.tipo_ticket_pendiente or "betplay"
        id_tra = session.numero_registro
        identificacion = session.identificacion_pendiente
        valor = session.valor_pendiente

        # Registrar en la DB
        new_reg = models.RegistroSorteo(
            cedula=session.cedula,
            sorteo_id=active_sorteo.id,
            numero_registro=id_tra,
            tipo_ticket=tipo,
            id_transaccion=id_tra,
            identificacion=identificacion,
            valor=valor,
            comprobante_url=data.media_url
        )
        db.add(new_reg)
        db.flush()

        # Conteo para la moto
        total = db.query(func.count(models.RegistroSorteo.id)).filter(
            models.RegistroSorteo.cedula == session.cedula,
            models.RegistroSorteo.sorteo_id == active_sorteo.id
        ).scalar()

        MOTO_GOAL = 10
        restantes = max(0, MOTO_GOAL - total)

        # Limpiar sesión
        session.paso = "TICKET"
        session.numero_registro = None
        session.tipo_ticket_pendiente = None
        session.identificacion_pendiente = None
        session.valor_pendiente = None
        db.commit()

        tipo_label = "🎰 Betplay" if tipo == "betplay" else "🏵️ Chance"
        
        # Formatear el valor si existe
        valor_str = f"${int(valor):,}".replace(",", ".") if valor and valor.isdigit() else (f"${valor}" if valor else "N/A")

        msg = f"✅ ¡Ticket {tipo_label} registrado exitosamente! 🎉\n\n"
        msg += f"📄 *Detalles:* \n"
        msg += f"\u2022 *ID Transacción:* {id_tra}\n"
        if tipo == "betplay" and identificacion:
            msg += f"\u2022 *Identificación:* {identificacion}\n"
        msg += f"\u2022 *Valor:* {valor_str}\n\n"
        
        msg += f"Llevas *{total} tickets* registrados."
        
        premio_text = active_sorteo.premio or "la moto"
        if restantes > 0:
            msg += f"\n\nTe faltan *{restantes}* para participar por *{premio_text}*. 🏙️\n\nSi tienes otro ticket, envíalo ahora."
        else:
            msg += f"\n\n¡Felicidades! Ya estás participando por *{premio_text}*. 🏙️✨\n\nSi tienes más tickets, puedes seguir registrándolos."

        return {"mensaje": msg, "paso_siguiente": "TICKET", "total_tickets": total}

    return {"mensaje": "Opción no reconocida.", "paso_siguiente": "INICIO"}

@app.get("/api/admin/users", response_model=List[schemas.AdminUser])
def get_admin_users(db: Session = Depends(get_db)):
    return db.query(models.AdminUser).all()

@app.post("/api/admin/users", response_model=schemas.AdminUser)
def create_admin_user(data: schemas.AdminUserCreate, db: Session = Depends(get_db)):
    import hashlib
    hashed_pw = hashlib.sha256(data.password.encode()).hexdigest()
    # Check if username exists
    existing = db.query(models.AdminUser).filter(models.AdminUser.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    db_user = models.AdminUser(username=data.username, password_hash=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/api/admin/users/{user_id}", response_model=schemas.AdminUser)
def update_admin_user(user_id: int, data: schemas.AdminUserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.AdminUser).filter(models.AdminUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if data.username:
        # Check if username exists for other user
        existing = db.query(models.AdminUser).filter(
            models.AdminUser.username == data.username,
            models.AdminUser.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
        db_user.username = data.username
        
    if data.password:
        import hashlib
        db_user.password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/api/admin/users/{user_id}")
def delete_admin_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.AdminUser).filter(models.AdminUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Optional: ensure we don't delete the last admin
    total_admins = db.query(func.count(models.AdminUser.id)).scalar()
    if total_admins <= 1:
        raise HTTPException(status_code=400, detail="No se puede eliminar el último administrador")
        
    db.delete(db_user)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

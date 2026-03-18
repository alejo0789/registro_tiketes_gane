from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import pytz

Base = declarative_base()

def get_colombia_time():
    """Retorna la hora actual en Colombia (UTC-5)."""
    tz = pytz.timezone('America/Bogota')
    return datetime.datetime.now(tz)

class User(Base):
    __tablename__ = "marketing_clientes_sorteos"
    
    cedula = Column(String(50), primary_key=True)
    nombre_completo = Column(String(255), nullable=False)
    telefono = Column(String(50), nullable=True)  # Optional for existing users migrated from old schema
    fecha_registro = Column(DateTime, default=get_colombia_time)
    
    registros = relationship("RegistroSorteo", back_populates="usuario")

class SorteoConfig(Base):
    __tablename__ = "marketing_sorteos_config"
    
    id = Column(Integer, primary_key=True)
    nombre_sorteo = Column(String(255), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    activo = Column(Boolean, default=True)
    
    registros = relationship("RegistroSorteo", back_populates="sorteo_info")

class RegistroSorteo(Base):
    __tablename__ = "marketing_registros_sorteo"
    
    id = Column(Integer, primary_key=True)
    cedula = Column(String(50), ForeignKey("marketing_clientes_sorteos.cedula"), nullable=False)
    sorteo_id = Column(Integer, ForeignKey("marketing_sorteos_config.id"), nullable=False)
    numero_registro = Column(String(100), nullable=False)  # id.tra del ticket
    tipo_ticket = Column(String(20), nullable=True, default="betplay")  # 'betplay' | 'chance'
    id_transaccion = Column(String(100), nullable=True)  # id.tra
    identificacion = Column(String(100), nullable=True)  # solo betplay
    valor = Column(String(50), nullable=True)  # valor/total del ticket
    comprobante_url = Column(String(500), nullable=True) # URL o path de la imagen del comprobante
    fecha_creacion = Column(DateTime, default=get_colombia_time)
    
    usuario = relationship("User", back_populates="registros")
    sorteo_info = relationship("SorteoConfig", back_populates="registros")

class WhatsAppSession(Base):
    __tablename__ = "marketing_whatsapp_sessions"
    
    telefono = Column(String(50), primary_key=True)
    paso = Column(String(50), default="INICIO")  # INICIO, CEDULA, NOMBRE, TICKET, FOTO
    cedula = Column(String(50), nullable=True)
    nombre_completo = Column(String(255), nullable=True)
    numero_registro = Column(String(100), nullable=True)  # id.tra del ticket en proceso
    tipo_ticket_pendiente = Column(String(20), nullable=True)  # 'betplay' | 'chance'
    identificacion_pendiente = Column(String(100), nullable=True)  # solo betplay
    valor_pendiente = Column(String(50), nullable=True)  # valor del ticket en proceso
    comprobante_url = Column(String(500), nullable=True)
    ultima_interaccion = Column(DateTime, default=get_colombia_time, onupdate=get_colombia_time)

class AdminUser(Base):
    __tablename__ = "marketing_admin_users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

from pydantic import BaseModel, field_validator
import re
from typing import Optional, List
from datetime import datetime, date

# Sorteo Config Schemas
class SorteoConfigBase(BaseModel):
    nombre_sorteo: str
    fecha_inicio: date
    fecha_fin: date
    activo: bool = True

class SorteoConfigCreate(SorteoConfigBase):
    pass

class SorteoConfigUpdate(BaseModel):
    nombre_sorteo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    activo: Optional[bool] = None

class SorteoConfig(SorteoConfigBase):
    id: int
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    cedula: str
    nombre_completo: str
    telefono: Optional[str] = None

    @field_validator("cedula")
    @classmethod
    def validate_cedula(cls, v: str) -> str:
        clean_v = re.sub(r"[.,\s]", "", v)
        if not clean_v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        if len(clean_v) < 6:
            raise ValueError("La cédula debe tener al menos 6 dígitos")
        return clean_v

class UserCreate(UserBase):
    pass

class User(UserBase):
    fecha_registro: datetime
    class Config:
        from_attributes = True

# Registration Schemas
class RegistroCreate(BaseModel):
    cedula: str
    nombre_completo: Optional[str] = None  # Optional if user already exists
    telefono: Optional[str] = None          # Optional if user already exists
    sorteo_id: int
    numero_registro: str
    comprobante_url: str                    # Mandatory: photo is required

    @field_validator("cedula")
    @classmethod
    def validate_cedula(cls, v: str) -> str:
        clean_v = re.sub(r"[.,\s]", "", v)
        if not clean_v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        if len(clean_v) < 6:
            raise ValueError("La cédula debe tener al menos 6 dígitos")
        return clean_v

class Registro(BaseModel):
    id: int
    cedula: str
    sorteo_id: int
    numero_registro: str
    tipo_ticket: Optional[str] = None
    id_transaccion: Optional[str] = None
    identificacion: Optional[str] = None
    valor: Optional[str] = None
    comprobante_url: Optional[str] = None
    fecha_creacion: datetime
    class Config:
        from_attributes = True

class RegistroResponse(Registro):
    total_tickets: int  # Total tickets registered by this cedula in the sorteo
    tickets_restantes: int # Tickets remaining for the goal (moto)

# WhatsApp Integration Schemas
class WhatsAppRegistroCreate(BaseModel):
    cedula: str
    nombre: str
    telefono: str
    numero_sorteo: str  # This maps to the ticket number
    url_imagen: str

    @field_validator("cedula")
    @classmethod
    def validate_cedula(cls, v: str) -> str:
        clean_v = re.sub(r"[.,\s]", "", v)
        if not clean_v.isdigit():
            raise ValueError("La cédula debe contener solo números")
        if len(clean_v) < 6:
            raise ValueError("La cédula debe tener al menos 6 dígitos")
        return clean_v

class WhatsAppRegistroResponse(BaseModel):
    status: str
    mensaje: str
    total_tickets: int
    tickets_restantes: int
    cedula: str
    nombre: str

class WhatsAppUserCheck(BaseModel):
    exists: bool
    cedula: Optional[str] = None
    nombre: Optional[str] = None
    telefono: Optional[str] = None

class WhatsAppTicketCheck(BaseModel):
    registered: bool
    mensaje: str

# WhatsApp Webhook Interaction
class WhatsAppInteractRequest(BaseModel):
    telefono: str
    texto: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # 'image', 'document', etc.
    # Campos extraídos por n8n desde cédula
    extracted_cedula: Optional[str] = None
    extracted_nombre: Optional[str] = None
    # Campos del tipo de documento detectado
    tipo_documento_detectado: Optional[str] = None  # 'cedula' | 'betplay' | 'chance'
    # Campos extraídos de tickets (betplay y chance)
    extracted_id_tra: Optional[str] = None      # id.tra para ambos tipos
    extracted_identificacion: Optional[str] = None  # identificacion (solo betplay)
    extracted_valor: Optional[str] = None       # Valor recarga (betplay) o Total (chance)
    # Compatibilidad con campo antiguo
    extracted_ticket: Optional[str] = None

class WhatsAppInteractResponse(BaseModel):
    mensaje: str
    paso_siguiente: str
    total_tickets: Optional[int] = 0

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_usuarios: int
    total_registros: int

class UserTableItem(BaseModel):
    cedula: str
    nombre_completo: str
    telefono: Optional[str] = None
    count_sorteos: int
    count_receipts: int
    comprobante_url: Optional[str] = None
    fecha_ultimo_registro: Optional[datetime]

class UserTableResponse(BaseModel):
    items: List[UserTableItem]
    total: int
    pages: int
    current_page: int

class ReceiptItem(BaseModel):
    numero_registro: str
    tipo_ticket: Optional[str] = None
    id_transaccion: Optional[str] = None
    identificacion: Optional[str] = None
    valor: Optional[str] = None
    comprobante_url: Optional[str]
    fecha_creacion: datetime
    nombre_sorteo: str

# Documentación del Sistema: Acertemos Sorteos

Sistema de gestión de sorteos y registro de participantes con chat interactivo e inteligencia visual (Nova).

## 🏙️ Arquitectura del Sistema

El sistema sigue una arquitectura monolítica ligera con una clara separación entre el frontend y el backend:

- **Frontend:** Single Page Application (SPA) desarrollada en HTML5, CSS3 y JavaScript Vanilla. Implementa un sistema de chat con manejo dinámico de viewport para móviles.
- **Backend:** API REST desarrollada con **FastAPI** (Python).
- **Base de Datos:**
  - **Desarrollo:** SQLite (`acertemos.db`).
  - **Producción:** MariaDB/MySQL (Configurable vía `.env`).
  - **Prefijos de Tablas:** Todas las tablas de este sistema usan el prefijo `marketing_` para evitar conflictos en bases de datos compartidas.
- **Almacenamiento:** Imágenes de los tickets se guardan en **Cloudinary** para escalabilidad y evitar bloqueos.
- **Servidor:** FastAPI corriendo en el puerto **8000** o **8003** (ver `run.py` o `.env`).

## 🚀 Cómo Correr el Proyecto

### 🛠️ Requisitos Previos
- Python 3.9+
- Pip (gestor de paquetes de Python)
- Cuenta de Cloudinary (configurada en `.env`).

### 1. Preparar el Entorno
Se recomienda usar un entorno virtual:
```bash
python -m venv venv
# Activar en Windows
venv\Scripts\activate
# Activar en Linux/Mac
source venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configuración (.env)
Crea un archivo `.env` en la raíz:
```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/nombre_db
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
```

### 4. Lanzar la Aplicación
```bash
python run.py
```

## ⚙️ ¿Qué sucede al iniciar?

Al ejecutar `run.py`:
1. **Puerto:** El servidor se levanta por defecto en el puerto **8000** (o el configurado).
2. **Tablas:** El sistema verifica si existen las tablas `marketing_clientes_sorteos`, `marketing_sorteos_config` y `marketing_registros_sorteo`. Si no existen, las crea automáticamente.
3. **Migraciones:** Verifica y añade la columna `telefono` si es necesario.

## 🔑 Accesos Rápidos
- **Chat de Usuario:** `http://localhost:8000/`
- **Dashboard Administrativo:** `http://localhost:8000/dashboard`

## 🛡️ Seguridad (Auth Guard)
El Dashboard tiene integrado un sistema de autenticación vía **Saman Identity** (LocalStorage). En producción, solo los correos autorizados en la lista `ALLOWED_EMAILS` pueden acceder. En `localhost`, este filtro se omite para facilitar el desarrollo.

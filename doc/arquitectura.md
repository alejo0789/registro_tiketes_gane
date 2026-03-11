# Arquitectura del Sistema: Acertemos Sorteos

## 💎 Diseño de la Base de Datos (Esquema Marketing)

Para garantizar la convivencia en servidores de producción con otras bases de datos existentes, se ha implementado un sistema de **prefijado obligatorio** (`marketing_`).

### 1. marketing_clientes_sorteos (Usuario/Cliente)
Almacena la identidad única de cada participante.
- **PK:** `cedula` (String)
- `nombre_completo` (String)
- `telefono` (String) - *Agregado en la última migración para contacto obligatorio.*
- `fecha_registro` (DateTime)

### 2. marketing_sorteos_config (Configuración)
Define los parámetros de cada sorteo activo.
- **PK:** `id` (Integer)
- `nombre_sorteo` (String)
- `fecha_inicio` (Date)
- `fecha_fin` (Date)
- `activo` (Boolean)

### 3. marketing_registros_sorteo (Registros/Tickets)
Vincula a los clientes con sus participaciones y fotos del ticket.
- **PK:** `id` (Integer)
- **FK:** `cedula` -> `marketing_clientes_sorteos.cedula`
- **FK:** `sorteo_id` -> `marketing_sorteos_config.id`
- `numero_registro` (String) - *Número del ticket Baloto Revancha.*
- `comprobante_url` (String) - *Ruta local a la imagen guardada.*
- `fecha_creacion` (DateTime)

## 🏢 Flujo de Comunicación (Frontend/Backend)

1. **Usuario accede a `index.html`:**
   - Interactúa con el asistente Nova.
   - El chat detecta si el usuario es nuevo consultando `/check-user/{cedula}`.
   - Si es nuevo, solicita nombre y teléfono.
   - Solicita número de ticket y **CAPTURA OBLIGATORIA DE FOTO**.

2. **Backend (FastAPI) en puerto 8003:**
   - Valida que el ticket no exista previamente para ese sorteo.
   - Guarda la imagen en `assets/receipts/`.
   - Registra al usuario si no existía.
   - Devuelve el conteo total de participaciones del usuario.

3. **Dashboard Administrativo:**
   - Solo accesible para correos autorizados de Acertemos.
   - Permite crear sorteos, ver estadísticas y validar fotos de tickets registrados.

## 📱 Optimización Mobile
- Implementa `visualViewport API` para ajustar el tamaño del chat dinámicamente cuando el teclado virtual de Android/iOS aparece.
- Utiliza `Units dvh` (Dynamic Viewport Height) para soporte nativo en navegadores modernos.

# Gestión de Servicios y Puertos - Servidor 192.168.2.91

| Servicio | Nombre del Servicio | Puerto | Comando / Inicio | Observaciones |
| :--- | :--- | :--- | :--- | :--- |
| **Facturación Backend** | `FacturacionBackend` | `8000` | `-m uvicorn main:app --host 0.0.0.0 --port 8000` | Desplegado vía NSSM |
| **Facturación Frontend** | `FacturacionFrontend` | `5173` | `npm run dev -- --host 0.0.0.0 --port 5173` | Desplegado vía NSSM |
| **Masivos Backend** | `MasivosBackend` | `8001` | `-m uvicorn main:app --host 0.0.0.0 --port 8001` | Desplegado vía NSSM |
| **Masivos Frontend** | `MasivosFrontend` | `3000` | `npm run build` (primero), `npm run dev` | Puerto 3000 |
| **Gane Registros** | `GaneRegistros` | `8033` | `uvicorn backend.main:app --port 8033` | Sin NSSM aún. Acceso: `/dashboard` |
| **n8n Automation** | `n8n` | *(Varía)* | Servicio n8n | Orquestador de flujos |

## Notas Adicionales
*   **IP del Servidor:** `192.168.2.91`
*   **Gestor de Servicios:** NSSM (Non-Sucking Service Manager) para la mayoría de aplicaciones Python/Node.
*   **Gane Registros:** El dashboard se sirve directamente desde el backend en la ruta `http://192.168.2.91:8033/dashboard`.

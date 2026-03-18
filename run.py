import uvicorn
import os

if __name__ == "__main__":
    print("Iniciando Servidor Acertemos...")
    print("API: http://localhost:8003")
    print("Documentación (Swagger): http://localhost:8003/docs")
    
    # Use Railway's $PORT or default to 8003
    port = int(os.environ.get("PORT", 8003))
    
    # Standard run
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)


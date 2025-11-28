"""
Script de inicio rápido para el sistema de reconocimiento facial
"""
import uvicorn
from main import app
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_HOST = os.getenv('API_HOST')
API_PORT = os.getenv('API_PORT')

if __name__ == "__main__":
    print("=" * 50)
    print("🔐 Sistema de Reconocimiento Facial")
    print("=" * 50)
    print("\n🚀 Iniciando servidor...")
    print(f"📱 Accede a: http://{API_HOST}:{API_PORT}")
    print("📚 Documentación API: http://${API_HOST}:${API_PORT}/docs")
    print("\n⏹️  Presiona Ctrl+C para detener el servidor\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(API_PORT) if API_PORT else 8000,
        reload=True,  # Recarga automática durante desarrollo
        log_level="info"
    )


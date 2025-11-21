"""
Script de inicio rápido para el sistema de reconocimiento facial
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("=" * 50)
    print("🔐 Sistema de Reconocimiento Facial")
    print("=" * 50)
    print("\n🚀 Iniciando servidor...")
    print("📱 Accede a: http://localhost:8000")
    print("📚 Documentación API: http://localhost:8000/docs")
    print("\n⏹️  Presiona Ctrl+C para detener el servidor\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Recarga automática durante desarrollo
        log_level="info"
    )


import threading
import time
import requests
import sys
import uvicorn
from face_app_gui import main as gui_main

API_PORT = 8000
API_HOST = "0.0.0.0"
API_URL = f"http://localhost:{API_PORT}"

def check_server_ready(max_attempts=30, delay=0.5):
    for i in range(max_attempts):
        try:
            response = requests.get(f"{API_URL}/users", timeout=1)
            if response.status_code in [200, 401, 404]:
                return True
        except:
            pass
        time.sleep(delay)
    return False

def run_server():
    from main import app
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        access_log=False
    )

def main():
    print("=" * 60)
    print("🔐 Sistema de Reconocimiento Facial")
    print("=" * 60)
    print(f"\n🚀 Iniciando servidor API en puerto {API_PORT}...")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("⏳ Esperando a que el servidor esté listo...")
    
    if not check_server_ready():
        print("❌ Error: No se pudo iniciar el servidor")
        sys.exit(1)
    
    print(f"✅ Servidor API iniciado en http://localhost:{API_PORT}")
    print("🖥️  Iniciando aplicación GUI...")
    print("=" * 60)
    print("\n")
    
    try:
        gui_main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Aplicación cerrada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error en la aplicación GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


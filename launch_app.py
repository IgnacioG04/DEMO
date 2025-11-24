import threading
import time
import requests
import sys
import uvicorn
from face_app_gui import main as gui_main
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_PORT = int(os.getenv('API_PORT', 8000))
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_URL = f"http://{API_HOST}:{API_PORT}"

def check_server_ready(max_attempts=30, delay=0.5):
    # Use localhost for checking, even if API_HOST is 0.0.0.0
    check_url = f"http://{API_HOST}:{API_PORT}"
    for i in range(max_attempts):
        try:
            response = requests.get(f"{check_url}/users", timeout=1)
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
    
    print(f"✅ Servidor API iniciado en http://{API_HOST}:{API_PORT}")
    print("🖥️  Iniciando aplicación GUI...")
    print("=" * 60)
    print("\n")
    
    try:
        gui_main()
        # GUI closed, but server continues running
        print("\n" + "=" * 60)
        print("🖥️  Ventana GUI cerrada")
        print(f"✅ Servidor API sigue ejecutándose en http://{API_HOST}:{API_PORT}")
        print("📱 Accede a la API web en el navegador")
        print("⏹️  Presiona Ctrl+C para detener el servidor")
        print("=" * 60 + "\n")
        
        # Keep the main thread alive so the server continues running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Servidor detenido por el usuario")
            sys.exit(0)
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


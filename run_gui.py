"""
Script de inicio rápido para la aplicación GUI de reconocimiento facial
"""
import sys
from face_app_gui import main

if __name__ == "__main__":
    print("=" * 50)
    print("Sistema de Reconocimiento Facial - GUI")
    print("=" * 50)
    print("\nIniciando aplicacion...")
    print("Asegurate de tener Iriun Webcam conectado")
    print("\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAplicacion cerrada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError al iniciar la aplicacion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


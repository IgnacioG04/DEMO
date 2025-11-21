"""
Script para descargar manualmente el modelo de DeepFace
"""
import os
import urllib.request
from pathlib import Path
import sys

def download_vgg_face_model():
    """Descarga el modelo VGG-Face de DeepFace manualmente"""
    
    # URL del modelo
    model_url = "https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5"
    
    # Directorio de destino
    model_dir = Path.home() / ".deepface" / "weights"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Ruta completa del archivo
    model_file = model_dir / "vgg_face_weights.h5"
    
    # Verificar si ya existe
    if model_file.exists():
        file_size = model_file.stat().st_size / (1024 * 1024)  # MB
        print(f"[INFO] El modelo ya existe en: {model_file}")
        print(f"[INFO] Tamaño: {file_size:.2f} MB")
        
        response = input("¿Deseas descargarlo nuevamente? (s/n): ")
        if response.lower() != 's':
            print("[INFO] Cancelado.")
            return
    
    print("\n" + "="*60)
    print("Descargando modelo VGG-Face de DeepFace")
    print("="*60)
    print(f"\nURL: {model_url}")
    print(f"Destino: {model_file}")
    print(f"\nEste archivo es grande (~550 MB) y puede tardar varios minutos...")
    print("Por favor, ten paciencia.\n")
    
    try:
        def show_progress(block_num, block_size, total_size):
            """Muestra el progreso de la descarga"""
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            
            # Actualizar en la misma línea
            sys.stdout.write(f"\r[Descargando] {percent:.1f}% - {downloaded_mb:.1f} MB / {total_mb:.1f} MB")
            sys.stdout.flush()
        
        print("Iniciando descarga...")
        urllib.request.urlretrieve(model_url, model_file, reporthook=show_progress)
        print("\n\n[OK] ¡Descarga completada exitosamente!")
        print(f"[OK] Modelo guardado en: {model_file}")
        
        # Verificar tamaño
        file_size = model_file.stat().st_size / (1024 * 1024)
        print(f"[INFO] Tamaño del archivo: {file_size:.2f} MB")
        
    except Exception as e:
        print(f"\n\n[ERROR] Error al descargar el modelo: {e}")
        print("\nSoluciones alternativas:")
        print("1. Verifica tu conexión a internet")
        print("2. Intenta nuevamente más tarde")
        print("3. Descarga manualmente desde:")
        print(f"   {model_url}")
        print(f"   Y guárdalo en: {model_file}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Script de descarga de modelo VGG-Face para DeepFace")
    print("="*60 + "\n")
    
    try:
        download_vgg_face_model()
        print("\n[OK] ¡Listo! Ahora puedes ejecutar la aplicación GUI.")
        print("Ejecuta: python run_gui.py")
    except KeyboardInterrupt:
        print("\n\n[INFO] Descarga cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


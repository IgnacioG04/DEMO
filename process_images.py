"""
Script para procesar imágenes manualmente en registered_faces/
Este script genera embeddings para imágenes que no tienen su .npy correspondiente
"""
import os
import sys
from pathlib import Path
from deepface import DeepFace
import numpy as np

def process_images_in_folder(folder_path="registered_faces"):
    """Procesa todas las imágenes en la carpeta y genera embeddings"""
    
    faces_dir = Path(folder_path)
    
    if not faces_dir.exists():
        print(f"[ERROR] La carpeta '{folder_path}' no existe.")
        print(f"[INFO] Creando carpeta '{folder_path}'...")
        faces_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Carpeta creada. Agrega imágenes JPG/PNG y ejecuta este script nuevamente.")
        return
    
    print("\n" + "="*60)
    print("Procesador de imágenes para reconocimiento facial")
    print("="*60)
    print(f"\nBuscando imágenes en: {faces_dir.absolute()}")
    print()
    
    # Extensiones de imagen soportadas
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # Contadores
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Buscar todas las imágenes
    all_images = []
    for ext in image_extensions:
        all_images.extend(list(faces_dir.glob(f"*{ext}")))
    
    if not all_images:
        print("[INFO] No se encontraron imágenes en la carpeta.")
        print(f"[INFO] Agrega imágenes JPG/PNG en: {faces_dir.absolute()}")
        return
    
    print(f"[INFO] Se encontraron {len(all_images)} imagen(es).")
    print()
    
    # Procesar cada imagen
    for image_file in all_images:
        user_name = image_file.stem
        embedding_file = faces_dir / f"{user_name}.npy"
        
        # Verificar si ya tiene embedding
        if embedding_file.exists():
            print(f"[SKIP] {image_file.name} ya tiene embedding ({embedding_file.name})")
            skipped_count += 1
            continue
        
        print(f"[PROC] Procesando: {image_file.name}...")
        
        try:
            # Generar embedding desde la imagen
            embedding_obj = DeepFace.represent(
                img_path=str(image_file),
                model_name='VGG-Face',
                detector_backend='opencv',
                enforce_detection=False
            )
            
            if len(embedding_obj) == 0:
                print(f"[ERROR] No se detectó ningún rostro en: {image_file.name}")
                error_count += 1
                continue
            
            # Guardar embedding
            embedding = np.array(embedding_obj[0]['embedding'])
            np.save(embedding_file, embedding)
            
            processed_count += 1
            print(f"[OK] Embedding generado: {embedding_file.name}")
            print()
            
        except Exception as e:
            print(f"[ERROR] Error al procesar {image_file.name}: {e}")
            error_count += 1
            print()
    
    # Resumen
    print("\n" + "="*60)
    print("Resumen del procesamiento")
    print("="*60)
    print(f"Imágenes procesadas: {processed_count}")
    print(f"Imágenes omitidas (ya procesadas): {skipped_count}")
    print(f"Errores: {error_count}")
    print(f"Total: {len(all_images)}")
    print()
    
    if processed_count > 0:
        print(f"[OK] ¡Listo! {processed_count} imagen(es) procesada(s) correctamente.")
        print("Ahora puedes usar estas imágenes para login.")
    else:
        if skipped_count > 0:
            print("[INFO] Todas las imágenes ya están procesadas.")
        if error_count > 0:
            print("[WARN] Algunas imágenes tuvieron errores. Revisa los mensajes anteriores.")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("Script de procesamiento de imágenes")
    print("="*60)
    print("\nEste script procesa imágenes JPG/PNG en la carpeta 'registered_faces/'")
    print("y genera los embeddings (.npy) necesarios para el reconocimiento facial.\n")
    
    # Permitir especificar carpeta como argumento
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "registered_faces"
    
    try:
        process_images_in_folder(folder_path)
    except KeyboardInterrupt:
        print("\n\n[INFO] Procesamiento cancelado por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


import os
import sys
from pathlib import Path
from deepface import DeepFace
import numpy as np
from database import Database

def process_images_in_folder(folder_path="registered_faces"):
    # Check images against database and generate embeddings for new users
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
    
    if not Database.test_connection():
        print("[ERROR] No se pudo conectar a la base de datos. Verifica la configuración en .env")
        return
    
    print("[OK] Conexión a base de datos establecida")
    
    existing_user_ids = Database.get_all_user_ids()
    print(f"[INFO] Usuarios con embeddings en BD: {len(existing_user_ids)}")
    print()
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    all_images = []
    for ext in image_extensions:
        all_images.extend(list(faces_dir.glob(f"*{ext}")))
    
    if not all_images:
        print("[INFO] No se encontraron imágenes en la carpeta.")
        print(f"[INFO] Agrega imágenes JPG/PNG en: {faces_dir.absolute()}")
        return
    
    print(f"[INFO] Se encontraron {len(all_images)} imagen(es).")
    print()
    
    for image_file in all_images:
        try:
            user_id = int(image_file.stem)
        except ValueError:
            print(f"[ERROR] {image_file.name} no tiene un user_id válido como nombre (debe ser numérico, ej: 1.png, 2.jpg)")
            error_count += 1
            continue
        
        if user_id in existing_user_ids:
            print(f"[SKIP] {image_file.name} - user_id {user_id} ya tiene embedding en la base de datos")
            skipped_count += 1
            continue
        
        print(f"[PROC] Procesando: {image_file.name} (user_id: {user_id})...")
        
        try:
            # Usar configuración optimizada (misma que face_recognition_system)
            # Intentar RetinaFace primero, luego MTCNN, luego opencv como fallback
            backend = 'opencv'  # Por defecto
            model = 'VGG-Face'  # Por defecto
            
            try:
                import retinaface
                backend = 'retinaface'  # DeepFace espera minúsculas
                print(f"  [INFO] Usando detector: RetinaFace")
            except:
                try:
                    DeepFace.build_model('MTCNN')
                    backend = 'mtcnn'
                    print(f"  [INFO] Usando detector: MTCNN")
                except:
                    backend = 'opencv'
                    print(f"  [INFO] Usando detector: opencv (fallback)")
            
            try:
                DeepFace.build_model('ArcFace')
                model = 'ArcFace'
                print(f"  [INFO] Usando modelo: ArcFace")
            except:
                model = 'VGG-Face'
                print(f"  [INFO] Usando modelo: VGG-Face")
            
            embedding_obj = DeepFace.represent(
                img_path=str(image_file),
                model_name=model,
                detector_backend=backend,
                align=True,  # Alineación facial para corregir poses
                enforce_detection=True,  # Requiere rostro válido
                normalization='base'
            )
            
            if len(embedding_obj) == 0:
                print(f"[ERROR] No se detectó ningún rostro en: {image_file.name}")
                error_count += 1
                continue
            
            # Extraer y normalizar embedding (mismo proceso que en face_recognition_system)
            embedding = np.array(embedding_obj[0]['embedding'])
            # Normalizar para similitud coseno consistente
            embedding_norm = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            embedding_id = Database.insert_embedding(user_id, embedding_norm)
            
            if embedding_id:
                processed_count += 1
                print(f"[OK] Embedding generado e insertado en BD (ID: {embedding_id}) para user_id {user_id}")
            else:
                print(f"[ERROR] No se pudo insertar embedding en BD para user_id {user_id}")
                error_count += 1
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
    # Main entry point for image processing script
    print("\n" + "="*60)
    print("Script de procesamiento de imágenes")
    print("="*60)
    print("\nEste script procesa imágenes JPG/PNG en la carpeta 'registered_faces/'")
    print("y genera los embeddings necesarios para el reconocimiento facial.")
    print("Las imágenes deben nombrarse con su user_id (ej: 1.png, 2.jpg, etc.)\n")
    
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


"""
Sistema de reconocimiento facial ligero y preciso
Usa DeepFace para reconocimiento facial eficiente
"""
import os
import numpy as np
import uuid
import traceback
from pathlib import Path
from typing import Optional, Tuple
from deepface import DeepFace
from database import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FaceRecognitionSystem:
    """
    Sistema de reconocimiento facial usando DeepFace
    Optimizado para ser ligero y preciso
    """
    
    def __init__(self, threshold: float = None):
        # Initialize face recognition system with threshold and model configuration
        # Load threshold from environment variable CONFIDENCE_INTERVAL, default to 0.8
        if threshold is None:
            threshold = float(os.getenv('CONFIDENCE_INTERVAL', '0.8'))
        self.threshold = threshold
        self.registered_faces_dir = Path("registered_faces")
        self.registered_faces_dir.mkdir(exist_ok=True)
        
        self.backend = 'opencv'
        self.model_name = 'VGG-Face'
        
        if not Database.test_connection():
            print("[WARN] No se pudo conectar a la base de datos. Verifica la configuración en .env")
        else:
            print("[OK] Conexión a base de datos establecida")
        
        print("[OK] Sistema de reconocimiento facial inicializado")
        print(f"[INFO] Umbral de similitud: {self.threshold:.2f}")
        print(f"[INFO] Backend: {self.backend}")
        print(f"[INFO] Modelo: {self.model_name}")
        print(f"[INFO] Directorio de imágenes: {self.registered_faces_dir.absolute()}")
    
    def _save_image_temp(self, image_bytes: bytes) -> Optional[str]:
        # Save image bytes to temporary file for processing
        """
        Guarda temporalmente la imagen para procesarla con DeepFace
        
        Args:
            image_bytes: Bytes de la imagen
            
        Returns:
            Ruta del archivo temporal o None si hay error
        """
        try:
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            # Usar UUID único para evitar conflictos
            unique_id = str(uuid.uuid4())
            temp_file = temp_dir / f"temp_face_{unique_id}.jpg"
            
            # Guardar bytes a archivo
            with open(temp_file, 'wb') as f:
                f.write(image_bytes)
            
            # Verificar que el archivo se guardó correctamente
            if not temp_file.exists() or temp_file.stat().st_size == 0:
                print("[ERROR] Archivo temporal no se guardó correctamente")
                return None
            
            return str(temp_file.absolute())
        except Exception as e:
            print(f"[ERROR] Error al guardar imagen temporal: {e}")
            traceback.print_exc()
            return None
    
    def _extract_face_embedding(self, image_path: str) -> Optional[np.ndarray]:
        # Extract face embedding vector from image using DeepFace
        """
        Extrae el embedding facial de una imagen usando DeepFace
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Embedding facial o None si no se detecta rostro
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                print(f"[ERROR] Archivo de imagen no existe: {image_path}")
                return None
            
            # DeepFace representa el rostro como embedding
            embedding_obj = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                detector_backend=self.backend,
                enforce_detection=False  # No lanzar error si no detecta rostro
            )
            
            if len(embedding_obj) == 0:
                print("[WARN] No se detectaron rostros en la imagen")
                return None
            
            if len(embedding_obj) > 1:
                print(f"[INFO] Se detectaron {len(embedding_obj)} rostros, usando el primero")
            
            # Extraer el embedding (vector de características)
            embedding = np.array(embedding_obj[0]['embedding'])
            
            return embedding
            
        except ValueError as e:
            # DeepFace puede lanzar ValueError si no detecta rostro
            print(f"[WARN] No se detectó rostro: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Error al extraer embedding: {e}")
            traceback.print_exc()
            return None
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        # Calculate cosine similarity between two face embeddings
        """
        Calcula la similitud coseno entre dos embeddings
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
            
        Returns:
            Similitud (0-1, donde 1 es idéntico)
        """
        # Normalizar embeddings
        embedding1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        embedding2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
        
        # Calcular similitud coseno
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        return float(similarity)
    
    def register_face(self, image_bytes: bytes, user_id: str) -> Tuple[bool, str]:
        # Register new face: save image to registered_faces, check database, generate embedding, store in database
        saved_image_path = None
        try:
            if not image_bytes or len(image_bytes) == 0:
                return False, "La imagen está vacía"
            
            try:
                user_id_int = int(user_id)
            except ValueError:
                return False, "user_id debe ser un número entero"
            
            saved_image_path = self.registered_faces_dir / f"{user_id}.jpg"
            if saved_image_path.exists():
                return False, f"El usuario {user_id} ya tiene una imagen en registered_faces"
            
            with open(saved_image_path, 'wb') as f:
                f.write(image_bytes)
            
            if Database.user_has_embeddings(user_id_int):
                if saved_image_path.exists():
                    saved_image_path.unlink()
                return False, f"El usuario {user_id} ya tiene embeddings registrados en la base de datos"
            
            embedding = self._extract_face_embedding(str(saved_image_path))
            if embedding is None:
                if saved_image_path.exists():
                    saved_image_path.unlink()
                return False, "No se detectó ningún rostro en la imagen. Asegúrate de que el rostro esté claramente visible y de frente"
            
            embedding_id = Database.insert_embedding(user_id_int, embedding)
            
            if embedding_id is None:
                if saved_image_path.exists():
                    saved_image_path.unlink()
                return False, "Error al insertar embedding en la base de datos"
            
            return True, f"Rostro registrado correctamente para {user_id}"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error al registrar rostro: {error_msg}")
            traceback.print_exc()
            if saved_image_path and saved_image_path.exists():
                try:
                    saved_image_path.unlink()
                except:
                    pass
            return False, f"Error al registrar rostro: {error_msg}"
    
    def verify_face(self, image_bytes: bytes) -> Tuple[bool, Optional[str], float]:
        # Verify face by comparing with stored embeddings and return match result
        """
        Verifica si el rostro coincide con alguno de los registrados
        
        Args:
            image_bytes: Bytes de la imagen con el rostro a verificar
            
        Returns:
            Tuple (coincide, user_id, similitud)
        """
        temp_file = None
        try:
            # Guardar imagen temporalmente
            temp_file = self._save_image_temp(image_bytes)
            if temp_file is None:
                return False, None, 0.0
            
            # Extraer embedding
            embedding = self._extract_face_embedding(temp_file)
            if embedding is None:
                return False, None, 0.0
            
            # Buscar entre los rostros registrados en la base de datos
            best_match = None
            best_similarity = 0.0
            
            all_embeddings = Database.get_all_embeddings()
            
            for embedding_id, user_id, stored_embedding, created_at in all_embeddings:
                # Calcular similitud
                similarity = self.calculate_similarity(embedding, stored_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = str(user_id)
            
            # Verificar si supera el umbral
            if best_similarity >= self.threshold:
                return True, best_match, best_similarity
            else:
                return False, None, best_similarity
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error al verificar rostro: {error_msg}")
            traceback.print_exc()
            return False, None, 0.0
        finally:
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    print(f"[WARN] No se pudo eliminar archivo temporal: {cleanup_error}")
    
    def list_registered_users(self) -> list:
        # List all registered user IDs from database
        """
        Lista todos los usuarios registrados
        
        Returns:
            Lista de IDs de usuarios registrados
        """
        user_ids = Database.get_all_user_ids()
        return sorted([str(user_id) for user_id in user_ids])

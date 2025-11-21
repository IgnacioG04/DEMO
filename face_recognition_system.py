"""
Sistema de reconocimiento facial ligero y preciso
Usa DeepFace para reconocimiento facial eficiente
"""
import os
import cv2
import numpy as np
import json
import uuid
import traceback
from pathlib import Path
from typing import Optional, Tuple
from deepface import DeepFace

class FaceRecognitionSystem:
    """
    Sistema de reconocimiento facial usando DeepFace
    Optimizado para ser ligero y preciso
    """
    
    def __init__(self, threshold: float = 0.6):
        """
        Inicializa el sistema de reconocimiento facial
        
        Args:
            threshold: Umbral de similitud para reconocimiento (menor = más estricto)
        """
        self.threshold = threshold
        self.embeddings_dir = Path("face_embeddings")
        self.embeddings_dir.mkdir(exist_ok=True)
        
        # Configuración de DeepFace (modelo ligero)
        self.backend = 'opencv'  # Más ligero que otros backends
        self.model_name = 'VGG-Face'  # Modelo preciso y ligero
        
        print("[OK] Sistema de reconocimiento facial inicializado")
        print(f"[INFO] Umbral de similitud: {self.threshold:.2f}")
        print(f"[INFO] Backend: {self.backend}")
        print(f"[INFO] Modelo: {self.model_name}")
    
    def _save_image_temp(self, image_bytes: bytes) -> Optional[str]:
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
        """
        Registra un nuevo rostro en el sistema
        
        Args:
            image_bytes: Bytes de la imagen con el rostro
            user_id: Identificador único del usuario
            
        Returns:
            Tuple (éxito, mensaje)
        """
        temp_file = None
        try:
            # Validar que hay bytes
            if not image_bytes or len(image_bytes) == 0:
                return False, "La imagen está vacía"
            
            # Guardar imagen temporalmente
            temp_file = self._save_image_temp(image_bytes)
            if temp_file is None:
                return False, "Error al procesar la imagen. Verifica que sea un formato válido (JPG, PNG, etc.)"
            
            # Extraer embedding
            embedding = self._extract_face_embedding(temp_file)
            if embedding is None:
                return False, "No se detectó ningún rostro en la imagen. Asegúrate de que el rostro esté claramente visible y de frente"
            
            # Guardar embedding
            embedding_file = self.embeddings_dir / f"{user_id}.npy"
            np.save(embedding_file, embedding)
            
            # Guardar metadatos
            metadata_file = self.embeddings_dir / f"{user_id}.json"
            metadata = {
                "user_id": user_id,
                "model": self.model_name,
                "backend": self.backend
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False)
            
            return True, f"Rostro registrado correctamente para {user_id}"
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error al registrar rostro: {error_msg}")
            traceback.print_exc()
            return False, f"Error al registrar rostro: {error_msg}"
        finally:
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    print(f"[WARN] No se pudo eliminar archivo temporal: {cleanup_error}")
    
    def verify_face(self, image_bytes: bytes) -> Tuple[bool, Optional[str], float]:
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
            
            # Buscar entre los rostros registrados
            best_match = None
            best_similarity = 0.0
            
            for embedding_file in self.embeddings_dir.glob("*.npy"):
                if embedding_file.stem.endswith('.json'):
                    continue
                
                # Cargar embedding registrado
                stored_embedding = np.load(embedding_file)
                
                # Calcular similitud
                similarity = self.calculate_similarity(embedding, stored_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = embedding_file.stem
            
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
        """
        Lista todos los usuarios registrados
        
        Returns:
            Lista de IDs de usuarios registrados
        """
        users = []
        for embedding_file in self.embeddings_dir.glob("*.npy"):
            if embedding_file.stem.endswith('.json'):
                continue
            users.append(embedding_file.stem)
        return users
    
    def delete_user(self, user_id: str) -> bool:
        """
        Elimina un usuario del sistema
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            embedding_file = self.embeddings_dir / f"{user_id}.npy"
            metadata_file = self.embeddings_dir / f"{user_id}.json"
            
            if embedding_file.exists():
                embedding_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            return True
        except Exception as e:
            print(f"Error al eliminar usuario: {e}")
            return False

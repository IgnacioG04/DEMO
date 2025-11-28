"""
Sistema de reconocimiento facial ligero y preciso
Usa DeepFace para reconocimiento facial eficiente
"""
import os
import numpy as np
import uuid
import traceback
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
from deepface import DeepFace
from database import Database
from dotenv import load_dotenv
from embeddings_cache import get_all_embeddings_with_cache, clear_embeddings_cache
from exceptions import FaceNotFoundError, DatabaseError, DuplicateUserError, UserNotFoundError, ValidationError
from logger_config import logger
from typing import List

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
        
        # Optimización: Configuración avanzada de DeepFace para reconocimiento robusto e invariante al fondo
        # Detector robusto: RetinaFace es más preciso que opencv (Haar Cascade)
        # Si RetinaFace no está disponible, usa MTCNN como fallback
        # NOTA: RetinaFace requiere tensorflow y retina-face package
        # MTCNN requiere mtcnn package
        # El sistema intentará usar estos detectores en orden de preferencia
        
        # Verificar disponibilidad de detectores y configurar en orden de preferencia
        self.backend = 'opencv'  # Por defecto seguro (siempre disponible)
        
        # Verificar RetinaFace (más preciso)
        try:
            import tensorflow as tf
            # Verificar si tensorflow está disponible
            if hasattr(tf, '__version__') and tf.__version__.startswith('2.'):
                try:
                    # Intentar importar retina-face
                    import retinaface
                    self.backend = 'retinaface'  # DeepFace espera minúsculas
                    logger.info("✅ RetinaFace disponible - usando como detector (máxima precisión)")
                except ImportError:
                    # RetinaFace no instalado, verificar MTCNN
                    try:
                        import mtcnn
                        self.backend = 'mtcnn'
                        logger.info("✅ MTCNN disponible - usando como detector (RetinaFace no instalado)")
                    except ImportError:
                        logger.info("⚠️  RetinaFace y MTCNN no instalados - usando opencv")
                        logger.info("💡 Para mejor precisión, instala: pip install retina-face  (o: pip install mtcnn)")
        except ImportError:
            # TensorFlow no disponible, verificar solo MTCNN
            try:
                import mtcnn
                self.backend = 'mtcnn'
                logger.info("✅ MTCNN disponible - usando como detector")
            except ImportError:
                logger.info("⚠️  RetinaFace y MTCNN no disponibles - usando opencv")
                logger.info("💡 Para mejor precisión, instala: pip install retina-face  (o: pip install mtcnn)")
        
        # Modelo: ArcFace ofrece la mejor precisión para verificación
        # Si ArcFace no está disponible, usar VGG-Face (muy preciso también)
        try:
            self.model_name = 'ArcFace'
            # Verificar que esté disponible
            test_result = DeepFace.build_model('ArcFace')
            logger.info("ArcFace disponible - usando como modelo")
        except Exception as e:
            self.model_name = 'VGG-Face'
            logger.info(f"ArcFace no disponible, usando VGG-Face: {e}")
        
        # Configuraciones adicionales para invarianza al fondo
        self.align_faces = True  # Alineación facial para corregir poses
        self.enforce_detection = True  # Exigir detección de rostro (más seguro)
        self.distance_metric = 'cosine'  # Métrica de similitud coseno (robusta)
        
        if not Database.test_connection():
            print("[WARN] No se pudo conectar a la base de datos. Verifica la configuración en .env")
        else:
            print("[OK] Conexión a base de datos establecida")
        
        print("[OK] Sistema de reconocimiento facial inicializado")
        print(f"[INFO] Umbral de similitud: {self.threshold:.2f}")
        print(f"[INFO] Detector Backend: {self.backend} (optimizado para precisión)")
        print(f"[INFO] Modelo: {self.model_name} (optimizado para precisión)")
        print(f"[INFO] Alineación facial: {self.align_faces} (corrige poses y rotaciones)")
        print(f"[INFO] Detección obligatoria: {self.enforce_detection} (requiere rostro válido)")
        print(f"[INFO] Métrica de distancia: {self.distance_metric}")
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
        """
        Extrae el embedding facial de una imagen usando DeepFace con configuración optimizada.
        
        Configuración optimizada para reconocimiento robusto e invariante al fondo:
        - Detector robusto (RetinaFace/MTCNN) para localización precisa
        - Alineación facial para corregir poses y rotaciones
        - Modelo de alta precisión (ArcFace/VGG-Face)
        - Detección obligatoria para seguridad
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Embedding facial normalizado o None si no se detecta rostro
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                logger.error(f"Archivo de imagen no existe: {image_path}")
                return None
            
            # DeepFace representa el rostro como embedding con configuración optimizada
            embedding_obj = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,  # ArcFace o VGG-Face (alta precisión)
                detector_backend=self.backend,  # RetinaFace o MTCNN (robusto)
                align=self.align_faces,  # True: alineación facial para corregir poses
                enforce_detection=self.enforce_detection,  # True: requiere rostro válido
                normalization='base'  # Normalización base para embeddings
            )
            
            if len(embedding_obj) == 0:
                logger.warning("No se detectaron rostros en la imagen")
                raise FaceNotFoundError("No se detectó ningún rostro en la imagen")
            
            if len(embedding_obj) > 1:
                logger.info(f"Se detectaron {len(embedding_obj)} rostros, usando el primero (más grande)")
                # Si hay múltiples rostros, usar el primero (DeepFace ya los ordena por tamaño/confianza)
            
            # Extraer el embedding (vector de características)
            embedding = np.array(embedding_obj[0]['embedding'])
            
            # Normalizar el embedding para similitud coseno consistente
            embedding_norm = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            logger.debug(f"Embedding extraído exitosamente: shape={embedding_norm.shape}, norm={np.linalg.norm(embedding_norm):.4f}")
            
            return embedding_norm
            
        except ValueError as e:
            # DeepFace lanza ValueError si no detecta rostro (con enforce_detection=True)
            error_msg = str(e)
            if "Face could not be detected" in error_msg or "No face detected" in error_msg.lower():
                logger.warning(f"No se detectó rostro en la imagen: {e}")
                raise FaceNotFoundError("No se detectó ningún rostro en la imagen. Asegúrate de que el rostro esté visible y bien iluminado.")
            else:
                logger.error(f"Error de DeepFace al procesar imagen: {e}")
                raise
        except FaceNotFoundError:
            # Re-lanzar FaceNotFoundError tal cual
            raise
        except Exception as e:
            logger.error(f"Error inesperado al extraer embedding: {e}", exc_info=True)
            raise FaceNotFoundError(f"Error al procesar la imagen: {str(e)}")
    
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
    
    def calculate_similarities_vectorized(
        self, 
        query_embedding: np.ndarray, 
        all_embeddings: List[Tuple[int, int, np.ndarray, datetime]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calcula similitudes con todos los embeddings usando vectorización NumPy
        Esto es MUCHO más rápido que comparar uno por uno en un bucle
        
        Args:
            query_embedding: Embedding de la imagen a comparar
            all_embeddings: Lista de todos los embeddings almacenados
                Formato: [(embedding_id, user_id, embedding, created_at), ...]
        
        Returns:
            Tuple (array de similitudes, lista de user_ids)
            - similarities: Array NumPy con similitud para cada embedding
            - user_ids: Lista de user_ids en el mismo orden
        """
        if not all_embeddings:
            return np.array([]), []
        
        try:
            # Asegurar que query_embedding es un array NumPy 1D
            query_embedding = np.asarray(query_embedding, dtype=np.float32).flatten()
            
            # Separar embeddings y user_ids en listas
            embeddings_list = []
            user_ids_list = []
            
            for embedding_id, user_id, embedding, created_at in all_embeddings:
                # Asegurar que cada embedding es un array NumPy 1D
                embedding_array = np.asarray(embedding, dtype=np.float32).flatten()
                
                # Validar que las dimensiones coincidan
                if embedding_array.shape[0] != query_embedding.shape[0]:
                    logger.warning(
                        f"Embedding del usuario {user_id} tiene dimensión {embedding_array.shape[0]}, "
                        f"esperado {query_embedding.shape[0]}. Omitiendo."
                    )
                    continue
                
                embeddings_list.append(embedding_array)
                user_ids_list.append(str(user_id))
            
            if not embeddings_list:
                logger.error("No hay embeddings válidos para comparar")
                return np.array([]), []
            
            # Crear matriz de embeddings (N x embedding_dim)
            # Ejemplo: Si hay 100 usuarios con embeddings de 2622 dimensiones = (100, 2622)
            embeddings_matrix = np.array(embeddings_list, dtype=np.float32)
            
            # Validar dimensiones
            if embeddings_matrix.ndim != 2:
                logger.error(f"Matriz de embeddings tiene forma inválida: {embeddings_matrix.shape}")
                return np.array([]), []
            
            # Normalizar query embedding
            query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            
            # Normalizar TODA la matriz de embeddings a la vez
            # axis=1 significa normalizar cada fila (cada embedding)
            # keepdims=True mantiene las dimensiones para broadcasting
            norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
            embeddings_matrix_norm = embeddings_matrix / (norms + 1e-10)
            
            # Calcular similitudes con TODOS los embeddings simultáneamente
            # query_norm: (embedding_dim,)
            # embeddings_matrix_norm: (N, embedding_dim)
            # Resultado: (N,) - una similitud para cada embedding
            similarities = np.dot(embeddings_matrix_norm, query_norm)
            
            # Asegurar que las similitudes están en el rango [-1, 1] (puede haber errores de punto flotante)
            similarities = np.clip(similarities, -1.0, 1.0)
            
            return similarities, user_ids_list
            
        except Exception as e:
            logger.error(
                f"Error al calcular similitudes vectorizadas: {e}",
                exc_info=True,
                extra={
                    "query_embedding_shape": query_embedding.shape if isinstance(query_embedding, np.ndarray) else None,
                    "num_embeddings": len(all_embeddings)
                }
            )
            raise
    
    def register_face(self, image_bytes: bytes, user_id: str) -> Tuple[bool, str]:
        # Register new face: save image to registered_faces, check database, generate embedding, store in database
        saved_image_path = None
        try:
            if not image_bytes or len(image_bytes) == 0:
                raise ValidationError("La imagen está vacía", "EMPTY_IMAGE")
            
            try:
                user_id_int = int(user_id)
            except ValueError:
                raise ValidationError("user_id debe ser un número entero", "INVALID_USER_ID")
            
            saved_image_path = self.registered_faces_dir / f"{user_id}.jpg"
            if saved_image_path.exists():
                raise DuplicateUserError(user_id, f"El usuario {user_id} ya tiene una imagen en registered_faces")
            
            with open(saved_image_path, 'wb') as f:
                f.write(image_bytes)
            
            if Database.user_has_embeddings(user_id_int):
                if saved_image_path.exists():
                    saved_image_path.unlink()
                raise DuplicateUserError(
                    user_id,
                    f"El usuario {user_id} ya tiene embeddings registrados en la base de datos"
                )
            
            embedding = self._extract_face_embedding(str(saved_image_path))
            if embedding is None:
                if saved_image_path.exists():
                    saved_image_path.unlink()
                raise FaceNotFoundError("No se detectó ningún rostro en la imagen. Asegúrate de que el rostro esté claramente visible y de frente")
            
            embedding_id = Database.insert_embedding(user_id_int, embedding)
            
            if embedding_id is None:
                if saved_image_path.exists():
                    saved_image_path.unlink()
                raise DatabaseError("Error al insertar embedding en la base de datos")
            
            # Invalidar caché después de registrar nuevo embedding
            clear_embeddings_cache()
            
            return True, f"Rostro registrado correctamente para {user_id}"
            
        except (FaceNotFoundError, DuplicateUserError, DatabaseError, ValidationError, UserNotFoundError) as e:
            # Limpiar archivo si existe antes de re-lanzar excepción
            if saved_image_path and saved_image_path.exists():
                try:
                    saved_image_path.unlink()
                except:
                    pass
            # Re-lanzar excepciones personalizadas para que sean manejadas por el handler global
            logger.warning(f"Excepción en registro: {e.__class__.__name__} - {e.message}", extra={"user_id": user_id})
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error inesperado al registrar rostro: {error_msg}", exc_info=True)
            # Limpiar archivo si existe
            if saved_image_path and saved_image_path.exists():
                try:
                    saved_image_path.unlink()
                except:
                    pass
            # Convertir a excepción personalizada
            raise DatabaseError(f"Error inesperado al registrar rostro: {error_msg}")
    
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
            
            # Buscar entre los rostros registrados usando caché (Cache-Aside pattern)
            # Usar vectorización NumPy para comparar todos simultáneamente (MUCHO más rápido)
            all_embeddings = get_all_embeddings_with_cache()
            
            if not all_embeddings:
                logger.debug("No hay embeddings registrados en la base de datos")
                return False, None, 0.0
            
            # Calcular similitudes con todos los embeddings simultáneamente usando vectorización
            similarities, user_ids = self.calculate_similarities_vectorized(embedding, all_embeddings)
            
            if len(similarities) == 0:
                return False, None, 0.0
            
            # Encontrar el mejor match en una sola operación
            best_idx = np.argmax(similarities)
            best_similarity = float(similarities[best_idx])
            best_match = user_ids[best_idx]
            
            logger.debug(
                f"Comparación completada",
                extra={
                    "total_embeddings": len(similarities),
                    "best_match": best_match,
                    "best_similarity": best_similarity
                }
            )
            
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

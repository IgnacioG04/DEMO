"""
Sistema de reconocimiento facial ligero y preciso
Usa DeepFace para reconocimiento facial eficiente
"""
import os
import uuid
import traceback
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

import cv2
import numpy as np
from deepface import DeepFace
from dotenv import load_dotenv

from database import Database
from embeddings_cache import get_all_embeddings_with_cache, clear_embeddings_cache
from exceptions import (
    FaceNotFoundError,
    DatabaseError,
    DuplicateUserError,
    UserNotFoundError,
    ValidationError,
)
from logger_config import logger

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
        self.backend = None  # se asignará al primer backend robusto disponible

        # Intentar RetinaFace (mayor precisión)
        if self.backend is None:
            try:
                import tensorflow as tf  # noqa: F401
                import retinaface  # noqa: F401

                self.backend = 'retinaface'
                logger.info("✅ RetinaFace disponible - usando como detector (máxima precisión)")
            except ImportError:
                logger.info("RetinaFace no disponible - buscando alternativas (instala 'retina-face' y 'tensorflow>=2')")

        # Intentar MTCNN como fallback robusto
        if self.backend is None:
            try:
                import mtcnn  # noqa: F401

                self.backend = 'mtcnn'
                logger.info("✅ MTCNN disponible - usando como detector (fallback)")
            except ImportError:
                logger.warning("MTCNN no disponible - considera instalar 'mtcnn' para mejor precisión")

        # Último recurso: OpenCV (menos robusto)
        if self.backend is None:
            self.backend = 'opencv'
            logger.warning(
                "⚠️ RetinaFace/MTCNN no disponibles. Usando OpenCV (precisión reducida). "
                "Instala 'retina-face' o 'mtcnn' para mejorar el reconocimiento."
            )
        
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

    def _preprocess_image(self, image_path: str) -> Optional[str]:
        """
        Aplica normalización de iluminación y contraste para reducir variaciones de fondo.
        Devuelve la ruta a la imagen temporal preprocesada o None si no se pudo procesar.
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None

            # Normalización de histograma (espacio YUV)
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
            img_norm = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            # CLAHE para contraste local adaptativo
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img_yuv = cv2.cvtColor(img_norm, cv2.COLOR_BGR2YUV)
            img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
            img_processed = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            processed_path = f"{image_path}_preprocessed.jpg"
            cv2.imwrite(processed_path, img_processed, [cv2.IMWRITE_JPEG_QUALITY, 95])

            return processed_path
        except Exception as e:
            logger.warning(f"No se pudo preprocesar la imagen para mejorar invarianza al fondo: {e}")
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
        processed_path = None
        try:
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                logger.error(f"Archivo de imagen no existe: {image_path}")
                return None

            processed_path = self._preprocess_image(image_path)
            image_path_to_use = processed_path or image_path
            
            # Primer intento: usar imagen preprocesada (si existe)
            try:
                embedding_obj = DeepFace.represent(
                    img_path=image_path_to_use,
                    model_name=self.model_name,  # ArcFace o VGG-Face (alta precisión)
                    detector_backend=self.backend,  # RetinaFace o MTCNN (robusto)
                    align=self.align_faces,  # True: alineación facial para corregir poses
                    enforce_detection=self.enforce_detection,  # True: requiere rostro válido
                    normalization='base'  # Normalización base para embeddings
                )
            except ValueError as e:
                error_msg = str(e)
                # Si falló con la imagen preprocesada, intentar nuevamente con la imagen ORIGINAL
                # y con enforce_detection desactivado para ser más tolerantes
                if processed_path is not None and (
                    "Face could not be detected" in error_msg
                    or "No face detected" in error_msg.lower()
                ):
                    logger.warning(
                        "No se detectó rostro en imagen preprocesada, reintentando con imagen original",
                        extra={"image_path": image_path},
                    )
                    try:
                        embedding_obj = DeepFace.represent(
                            img_path=image_path,
                            model_name=self.model_name,
                            detector_backend=self.backend,
                            align=self.align_faces,
                            enforce_detection=False,  # fallback más tolerante
                            normalization='base',
                        )
                    except Exception as e2:
                        logger.error(
                            f"Reintento con imagen original también falló: {e2}",
                            exc_info=True,
                        )
                        raise e  # re-lanzar el error original para manejo homogéneo
                else:
                    # Cualquier otro ValueError se maneja más abajo
                    raise
            
            if len(embedding_obj) == 0:
                logger.warning("No se detectaron rostros en la imagen")
                raise FaceNotFoundError("No se detectó ningún rostro en la imagen")
            
            if len(embedding_obj) > 1:
                logger.info(f"Se detectaron {len(embedding_obj)} rostros, usando el primero (más grande)")
                # Si hay múltiples rostros, usar el primero (DeepFace ya los ordena por tamaño/confianza)
            
            # Extraer el embedding (vector de características)
            embedding = np.array(embedding_obj[0]['embedding'], dtype=np.float32)

            # Normalización avanzada: centrar y aplicar norma L2
            embedding = embedding - np.mean(embedding)
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
        finally:
            if processed_path and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except OSError as cleanup_error:
                    logger.warning(f"No se pudo eliminar imagen preprocesada temporal: {cleanup_error}")
    
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
        all_embeddings: List[Tuple[int, int, np.ndarray, datetime, bool]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calcula similitudes con todos los embeddings usando vectorización NumPy
        Esto es MUCHO más rápido que comparar uno por uno en un bucle
        
        Args:
            query_embedding: Embedding de la imagen a comparar
            all_embeddings: Lista de todos los embeddings almacenados
                Formato: [(embedding_id, user_id, embedding, created_at, estado), ...]
        
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
            
            for embedding_id, user_id, embedding, created_at, estado in all_embeddings:
                # Solo procesar embeddings con estado activo (True)
                if not estado:
                    continue
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
    

"""
API FastAPI para el sistema de reconocimiento facial
"""
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from face_recognition_system import FaceRecognitionSystem
from dotenv import load_dotenv
from health_check import get_health_status, is_live, is_ready
from fastapi import status
from logger_config import logger
from validators import validate_uploaded_image, ValidationError
from embeddings_cache import get_embeddings_cache
from exceptions import (
    FaceRecognitionException,
    FaceNotFoundError,
    InvalidImageError,
    UserNotFoundError,
    DuplicateUserError,
    DatabaseError
)
import traceback

# Load environment variables from .env file
load_dotenv()

API_PORT = int(os.getenv('API_PORT'))
API_HOST = os.getenv('API_HOST')

# Load valid hosts configuration
VALID_HOSTS_STR = os.getenv('VALID_HOSTS', '*').strip()
VALID_HOSTS = [host.strip() for host in VALID_HOSTS_STR.split(',') if host.strip()]

logger.info(f"Iniciando Sistema de Reconocimiento Facial API en {API_HOST}:{API_PORT}")
if '*' in VALID_HOSTS:
    logger.info("Host validation: Permitido para todos los hosts (*)")
else:
    logger.info(f"Host validation: Hosts permitidos: {', '.join(VALID_HOSTS)}")

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Sistema de Reconocimiento Facial", version="1.0.0")
app.state.limiter = limiter

# Host validation middleware
@app.middleware("http")
async def validate_host_middleware(request: Request, call_next):
    """
    Middleware para validar que el Host del request esté en la lista de hosts permitidos
    """
    # Si está configurado como wildcard, permitir todos los hosts
    if '*' in VALID_HOSTS:
        return await call_next(request)
    
    # Obtener el Host del request
    host_header = request.headers.get("host", "").lower()
    
    # Si no hay Host header, rechazar
    if not host_header:
        logger.warning(
            "Request rechazado: Host header faltante",
            extra={
                "ip_address": get_remote_address(request),
                "path": request.url.path,
                "method": request.method
            }
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": "Host header is required",
                "code": "MISSING_HOST_HEADER"
            }
        )
    
    # Normalizar host (remover puerto si está presente para comparación flexible)
    # Permitir comparación con y sin puerto
    host_without_port = host_header.split(':')[0]
    is_valid = False
    
    for valid_host in VALID_HOSTS:
        valid_host_normalized = valid_host.lower().strip()
        valid_host_without_port = valid_host_normalized.split(':')[0]
        
        # Comparar con puerto completo o sin puerto
        if host_header == valid_host_normalized or host_without_port == valid_host_without_port:
            is_valid = True
            break
    
    if not is_valid:
        logger.warning(
            "Request rechazado: Host no permitido",
            extra={
                "ip_address": get_remote_address(request),
                "host": host_header,
                "path": request.url.path,
                "method": request.method,
                "allowed_hosts": VALID_HOSTS
            }
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "Forbidden",
                "message": f"Host '{host_header}' is not allowed",
                "code": "INVALID_HOST"
            }
        )
    
    return await call_next(request)

# Handler personalizado para rate limit exceeded con logging
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client_ip = get_remote_address(request)
    endpoint = request.url.path
    logger.warning(
        f"Rate limit excedido",
        extra={
            "ip_address": client_ip,
            "endpoint": endpoint,
            "limit": str(exc.detail)
        }
    )
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Handler global para excepciones personalizadas
@app.exception_handler(FaceRecognitionException)
async def face_recognition_exception_handler(request: Request, exc: FaceRecognitionException):
    """
    Handler global para excepciones personalizadas del sistema de reconocimiento facial
    """
    logger.warning(
        f"Excepción capturada: {exc.__class__.__name__}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# Handler global para errores no manejados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para errores no manejados
    """
    logger.error(
        f"Error no manejado: {exc.__class__.__name__}",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # En modo desarrollo, incluir más detalles
    import os
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    error_detail = {
        "error": "InternalServerError",
        "message": "Error interno del servidor",
        "code": "INTERNAL_SERVER_ERROR"
    }
    
    if is_development:
        error_detail["detail"] = str(exc)
        error_detail["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=error_detail
    )

logger.info("Rate limiting configurado")
logger.info("Handlers de excepciones configurados")
logger.info("Middleware de validación de hosts configurado")

# Inicializar el sistema de reconocimiento facial
# Threshold se carga automáticamente desde CONFIDENCE_INTERVAL en .env
logger.info("Inicializando sistema de reconocimiento facial...")
face_system = FaceRecognitionSystem()

# Inicializar caché de embeddings (patrón Cache-Aside)
logger.info("Inicializando caché de embeddings...")
embeddings_cache = get_embeddings_cache()

logger.info("Aplicación FastAPI inicializada correctamente")

@app.get("/")
async def read_root():
    """API root endpoint - returns API information"""
    return JSONResponse({
        "name": "Sistema de Reconocimiento Facial API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/register",
            "verify-frame": "/verify-frame",
            "health": "/health",
            "health_live": "/health/live",
            "health_ready": "/health/ready"
        },
        "docs": "/docs"
    })

@app.post("/register")
@limiter.limit("5/minute")
async def register_face(request: Request, file: UploadFile = File(...), user_id: str = Form(...)):
    """
    API endpoint to register a new face embedding
    Stateless: saves image to registered_faces, checks DB, processes and stores
    """
    try:
        logger.info(
            f"Recibida solicitud de registro",
            extra={
                "user_id": user_id,
                "filename": file.filename,
                "content_type": file.content_type
            }
        )
        
        image_bytes = await file.read()
        
        # Validar archivo antes de procesar (lanza excepciones si falla)
        try:
            metadata = validate_uploaded_image(
                image_bytes,
                filename=file.filename,
                content_type=file.content_type
            )
            
            # Agregar metadata al log
            logger.info(
                f"Archivo validado exitosamente",
                extra={
                    "user_id": user_id,
                    **metadata
                }
            )
        except (ValidationError, InvalidImageError) as e:
            logger.warning(
                f"Validación de archivo fallida",
                extra={
                    "user_id": user_id,
                    "filename": file.filename,
                    "error": e.message,
                    "error_code": e.error_code
                }
            )
            raise  # La excepción será manejada por el handler global
        
        # register_face ahora lanza excepciones directamente en lugar de retornar tuplas
        success, message = face_system.register_face(image_bytes, user_id)
        
        if success:
            logger.info(
                f"Usuario registrado exitosamente",
                extra={"user_id": user_id}
            )
            return JSONResponse({
                "success": True,
                "message": message
            })
        else:
            # Si todavía retorna False (compatibilidad hacia atrás), crear excepción apropiada
            logger.warning(
                f"Error al registrar usuario: {message}",
                extra={"user_id": user_id}
            )
            if "ya tiene embeddings" in message.lower() or "ya tiene una imagen" in message.lower():
                raise DuplicateUserError(user_id, message)
            elif "no se detectó" in message.lower() or "rostro" in message.lower():
                raise FaceNotFoundError(message)
            elif "base de datos" in message.lower() or "insertar" in message.lower():
                raise DatabaseError(message)
            elif "user_id debe ser" in message.lower() or "imagen está vacía" in message.lower():
                raise ValidationError(message)
            else:
                raise ValidationError(message)
            
    except FaceRecognitionException:
        # Las excepciones personalizadas serán manejadas por el handler global
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error interno al registrar usuario",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/health")
async def health_check(request: Request):
    """
    Health check completo del sistema
    
    Returns:
        Estado de salud completo con todas las verificaciones
    """
    health_status = get_health_status(embeddings_cache)
    
    # Determinar código HTTP según estado
    if health_status["status"] == "healthy":
        status_code = status.HTTP_200_OK
    elif health_status["status"] == "degraded":
        status_code = status.HTTP_200_OK  # Aún funciona, solo con advertencias
    else:  # unhealthy
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        content=health_status,
        status_code=status_code
    )

@app.get("/health/live")
async def health_live(request: Request):
    """
    Liveness check - verifica que el servidor esté respondiendo
    Siempre retorna OK mientras el servidor esté corriendo
    
    Returns:
        Estado de liveness
    """
    return JSONResponse(content=is_live())

@app.get("/health/ready")
async def health_ready(request: Request):
    """
    Readiness check - verifica que el sistema esté listo para recibir requests
    Requiere que los servicios críticos (BD) estén disponibles
    
    Returns:
        Estado de readiness
    """
    ready_status = is_ready(embeddings_cache)
    
    # Retornar 503 si no está ready
    if ready_status["status"] == "ready":
        return JSONResponse(content=ready_status)
    else:
        return JSONResponse(
            content=ready_status,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@app.post("/verify-frame")
@limiter.limit("30/minute")
async def verify_frame(request: Request, file: UploadFile = File(...)):
    """
    API endpoint for real-time frame verification
    Stateless: processes frame, compares with DB, returns all similarities
    """
    try:
        logger.debug("Recibida solicitud de verificación de frame")
        image_bytes = await file.read()
        
        # Validar archivo antes de procesar (lanza excepciones si falla)
        try:
            validate_uploaded_image(
                image_bytes,
                filename=file.filename,
                content_type=file.content_type
            )
        except (ValidationError, InvalidImageError) as e:
            logger.warning(
                f"Validación de archivo fallida en verify-frame",
                extra={
                    "filename": file.filename,
                    "error": e.message,
                    "error_code": e.error_code
                }
            )
            raise  # La excepción será manejada por el handler global
        
        temp_file = None
        try:
            from pathlib import Path
            import uuid
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            unique_id = str(uuid.uuid4())
            temp_file = temp_dir / f"temp_verify_{unique_id}.jpg"
            
            with open(temp_file, 'wb') as f:
                f.write(image_bytes)
            
            embedding = face_system._extract_face_embedding(str(temp_file))
            
            if embedding is None:
                raise FaceNotFoundError("No se detectó rostro en la imagen")
            
            # Usar caché con fallback a BD (patrón Cache-Aside)
            from embeddings_cache import get_all_embeddings_with_cache
            all_embeddings = get_all_embeddings_with_cache()
            
            if not all_embeddings:
                return JSONResponse({
                    "success": True,
                    "best_match": None,
                    "all_similarities": [],
                    "other_similarities": [],
                    "threshold": float(face_system.threshold),
                    "message": "No hay usuarios registrados"
                })
            
            # Usar vectorización NumPy para comparar todos simultáneamente (MUCHO más rápido)
            similarities_array, user_ids = face_system.calculate_similarities_vectorized(
                embedding, all_embeddings
            )
            
            # Validar que tenemos resultados
            if len(similarities_array) == 0 or len(user_ids) == 0:
                logger.warning("No se pudieron calcular similitudes - arrays vacíos")
                return JSONResponse({
                    "success": True,
                    "best_match": None,
                    "all_similarities": [],
                    "other_similarities": [],
                    "threshold": float(face_system.threshold),
                    "message": "No se pudieron calcular similitudes"
                })
            
            # Validar que los arrays tienen la misma longitud
            if len(similarities_array) != len(user_ids):
                logger.error(
                    f"Longitud inconsistente: similarities={len(similarities_array)}, user_ids={len(user_ids)}"
                )
                return JSONResponse({
                    "success": False,
                    "error": "Error al calcular similitudes: arrays inconsistentes"
                }, status_code=500)
            
            # Crear lista de resultados directamente desde arrays
            similarities = []
            for uid, sim in zip(user_ids, similarities_array):
                try:
                    similarity_float = float(sim)
                    # Validar que la similitud está en rango válido [-1, 1]
                    if not (-1.0 <= similarity_float <= 1.0):
                        logger.warning(f"Similitud fuera de rango para usuario {uid}: {similarity_float}")
                        similarity_float = max(-1.0, min(1.0, similarity_float))  # Clamp
                    similarities.append({"user_id": uid, "similarity": similarity_float})
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error al convertir similitud para usuario {uid}: {e}, valor: {sim}")
                    continue
            
            if not similarities:
                logger.warning("No se pudieron crear similitudes válidas")
                return JSONResponse({
                    "success": True,
                    "best_match": None,
                    "all_similarities": [],
                    "other_similarities": [],
                    "threshold": float(face_system.threshold),
                    "message": "No se pudieron crear similitudes válidas"
                })
            
            # Ordenar por similitud descendente
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            best_match = similarities[0] if similarities else None
            other_similarities = similarities[1:] if len(similarities) > 1 else []
            
            return JSONResponse({
                "success": True,
                "best_match": best_match,
                "all_similarities": similarities,
                "other_similarities": other_similarities,
                "threshold": float(face_system.threshold)
            })
            
        finally:
            if temp_file and temp_file.exists():
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
    except FaceNotFoundError as e:
        logger.warning(f"Rostro no detectado en verify-frame: {e}")
        raise  # Será manejado por el handler global
    except Exception as e:
        logger.error(
            "Error interno en verify-frame",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

def start_server():
    logger.info(f"Iniciando servidor uvicorn en {API_HOST}:{API_PORT}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=int(API_PORT), log_level="info")
    except OSError as e:
        if e.errno == 10048 or "Address already in use" in str(e) or "solo se permite un uso" in str(e):
            logger.error(
                f"❌ ERROR: El puerto {API_PORT} ya está en uso por otro proceso",
                exc_info=False
            )
            logger.error(
                f"💡 Soluciones:",
                exc_info=False
            )
            logger.error(
                f"   1. Cierra el proceso que está usando el puerto {API_PORT}",
                exc_info=False
            )
            logger.error(
                f"   2. O cambia el puerto en tu archivo .env (API_PORT=8002)",
                exc_info=False
            )
            logger.error(
                f"   3. Para encontrar el proceso: netstat -ano | findstr :{API_PORT}",
                exc_info=False
            )
            logger.error(
                f"   4. Para matar el proceso: taskkill /PID <PID> /F",
                exc_info=False
            )
        raise

def start_gui():
    import time
    time.sleep(2)
    try:
        from face_app_gui import FaceRecognitionApp
        import tkinter as tk
        
        root = tk.Tk()
        app = FaceRecognitionApp(root)
        
        def on_closing():
            app.stop_camera()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        logger.error(f"No se pudo iniciar la GUI: {e}", exc_info=True)
        logger.info(f"El servidor API sigue ejecutándose en http://{API_HOST}:{API_PORT}")

if __name__ == "__main__":
    import threading
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    logger.info(f"Servidor API iniciando en http://{API_HOST}:{API_PORT}")
    logger.info("Abriendo aplicación GUI...")
    
    start_gui()


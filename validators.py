"""
Módulo de validación de archivos e imágenes
"""
from typing import Tuple, Optional
from PIL import Image
import io
from exceptions import InvalidImageError, ValidationError

# Constantes de validación
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MIN_IMAGE_DIMENSION = 64
MAX_IMAGE_DIMENSION = 4096
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp'
}


def validate_file_size(file_bytes: bytes, max_size: int = MAX_FILE_SIZE):
    """
    Valida que el tamaño del archivo no exceda el límite máximo
    
    Args:
        file_bytes: Bytes del archivo
        max_size: Tamaño máximo permitido en bytes (default: 5MB)
        
    Raises:
        ValidationError: Si el archivo es muy grande o está vacío
    """
    file_size = len(file_bytes)
    max_size_mb = max_size / (1024 * 1024)
    
    if file_size == 0:
        raise ValidationError("El archivo está vacío", "EMPTY_FILE")
    
    if file_size > max_size:
        raise ValidationError(
            f"Archivo demasiado grande ({file_size / (1024 * 1024):.2f}MB). Tamaño máximo permitido: {max_size_mb}MB",
            "FILE_TOO_LARGE"
        )


def validate_image_format(image_bytes: bytes, filename: Optional[str] = None, content_type: Optional[str] = None):
    """
    Valida que el archivo sea una imagen válida y con formato permitido
    
    Args:
        image_bytes: Bytes de la imagen
        filename: Nombre del archivo (opcional, para validar extensión)
        content_type: Content-Type del archivo (opcional)
        
    Raises:
        InvalidImageError: Si la imagen no es válida
        ValidationError: Si el formato no está permitido
    """
    # Validar extensión si se proporciona filename
    if filename:
        file_ext = filename.lower()
        if not any(file_ext.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            allowed_str = ', '.join(ALLOWED_EXTENSIONS)
            raise ValidationError(
                f"Formato no permitido. Extensiones permitidas: {allowed_str}",
                "INVALID_FORMAT"
            )
    
    # Validar content-type si se proporciona
    if content_type:
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Tipo MIME no permitido: {content_type}. Tipos permitidos: {', '.join(ALLOWED_MIME_TYPES)}",
                "INVALID_MIME_TYPE"
            )
    
    # Validar que sea una imagen válida usando Pillow
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verifica que sea una imagen válida sin cargarla completamente
    except Exception as e:
        raise InvalidImageError(f"El archivo no es una imagen válida: {str(e)}")


def validate_image_dimensions(image_bytes: bytes, min_dim: int = MIN_IMAGE_DIMENSION, max_dim: int = MAX_IMAGE_DIMENSION) -> Tuple[int, int]:
    """
    Valida las dimensiones de la imagen
    
    Args:
        image_bytes: Bytes de la imagen
        min_dim: Dimensión mínima permitida (default: 64px)
        max_dim: Dimensión máxima permitida (default: 4096px)
        
    Returns:
        Tuple (width, height) - Dimensiones de la imagen
        
    Raises:
        ValidationError: Si las dimensiones no son válidas
    """
    try:
        # Abrir imagen para obtener dimensiones
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        # Validar dimensiones mínimas
        if width < min_dim or height < min_dim:
            raise ValidationError(
                f"Imagen muy pequeña ({width}x{height}px). Dimensiones mínimas: {min_dim}x{min_dim}px",
                "IMAGE_TOO_SMALL"
            )
        
        # Validar dimensiones máximas
        if width > max_dim or height > max_dim:
            raise ValidationError(
                f"Imagen muy grande ({width}x{height}px). Dimensiones máximas: {max_dim}x{max_dim}px",
                "IMAGE_TOO_LARGE"
            )
        
        return (width, height)
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"Error al leer dimensiones de la imagen: {str(e)}",
            "DIMENSION_READ_ERROR"
        )


def validate_image_mode(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Valida que la imagen esté en un modo compatible (RGB, RGBA)
    
    Args:
        image_bytes: Bytes de la imagen
        
    Returns:
        Tuple (es_válido, mensaje_error)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        mode = image.mode
        
        # Convertir a RGB/RGBA si es necesario (pero no fallar por esto)
        # Solo validar que sea un modo de imagen válido
        if mode not in ['RGB', 'RGBA', 'L', 'LA', 'P']:
            return False, f"Modo de imagen no soportado: {mode}. Modos permitidos: RGB, RGBA, L, LA, P"
        
        return True, None
        
    except Exception as e:
        return False, f"Error al verificar modo de imagen: {str(e)}"


def validate_uploaded_image(
    file_bytes: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    max_size: int = MAX_FILE_SIZE
) -> dict:
    """
    Valida completamente un archivo de imagen subido
    
    Args:
        file_bytes: Bytes del archivo
        filename: Nombre del archivo (opcional)
        content_type: Content-Type del archivo (opcional)
        max_size: Tamaño máximo permitido en bytes (default: 5MB)
        
    Returns:
        Dict con metadata de la imagen validada
        
    Raises:
        ValidationError: Si alguna validación falla
        InvalidImageError: Si la imagen no es válida
    """
    # 1. Validar tamaño (lanza ValidationError si falla)
    validate_file_size(file_bytes, max_size)
    
    # 2. Validar formato (lanza InvalidImageError o ValidationError si falla)
    validate_image_format(file_bytes, filename, content_type)
    
    # 3. Validar dimensiones (lanza ValidationError si falla)
    dimensions = validate_image_dimensions(file_bytes)
    
    # 4. Validar modo (opcional, no crítico)
    try:
        validate_image_mode(file_bytes)
    except ValidationError:
        # Para modo, solo advertir pero no fallar
        pass
    
    # Obtener metadata adicional
    try:
        image = Image.open(io.BytesIO(file_bytes))
        metadata = {
            "width": dimensions[0],
            "height": dimensions[1],
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(file_bytes)
        }
    except:
        metadata = {
            "width": dimensions[0],
            "height": dimensions[1],
            "size_bytes": len(file_bytes)
        }
    
    return metadata


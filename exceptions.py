"""
Excepciones personalizadas para el sistema de reconocimiento facial
"""
from typing import Optional


class FaceRecognitionException(Exception):
    """
    Excepción base para todas las excepciones del sistema de reconocimiento facial
    """
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        status_code: int = 500
    ):
        """
        Args:
            message: Mensaje de error descriptivo
            error_code: Código de error personalizado (ej: "FACE_NOT_FOUND")
            status_code: Código HTTP apropiado para este error
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """
        Convierte la excepción a un diccionario para respuestas JSON
        
        Returns:
            Dict con información del error
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.error_code
        }


class FaceNotFoundError(FaceRecognitionException):
    """Excepción cuando no se detecta un rostro en la imagen"""
    def __init__(self, message: str = "No se detectó ningún rostro en la imagen"):
        super().__init__(
            message=message,
            error_code="FACE_NOT_FOUND",
            status_code=400
        )


class InvalidImageError(FaceRecognitionException):
    """Excepción cuando la imagen es inválida o corrupta"""
    def __init__(self, message: str = "El archivo no es una imagen válida"):
        super().__init__(
            message=message,
            error_code="INVALID_IMAGE",
            status_code=400
        )


class UserNotFoundError(FaceRecognitionException):
    """Excepción cuando un usuario no se encuentra"""
    def __init__(self, user_id: str, message: Optional[str] = None):
        if message is None:
            message = f"Usuario con ID {user_id} no encontrado"
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            status_code=404
        )


class DuplicateUserError(FaceRecognitionException):
    """Excepción cuando se intenta registrar un usuario que ya existe"""
    def __init__(self, user_id: str, message: Optional[str] = None):
        if message is None:
            message = f"El usuario {user_id} ya está registrado"
        super().__init__(
            message=message,
            error_code="DUPLICATE_USER",
            status_code=409  # Conflict
        )


class DatabaseError(FaceRecognitionException):
    """Excepción para errores de base de datos"""
    def __init__(self, message: str = "Error al conectar con la base de datos"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=503  # Service Unavailable
        )


class ValidationError(FaceRecognitionException):
    """Excepción para errores de validación"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400
        )


class AuthenticationError(FaceRecognitionException):
    """Excepción para errores de autenticación (para uso futuro)"""
    def __init__(self, message: str = "Error de autenticación"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401  # Unauthorized
        )


class AuthorizationError(FaceRecognitionException):
    """Excepción para errores de autorización (para uso futuro)"""
    def __init__(self, message: str = "No tienes permiso para realizar esta acción"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403  # Forbidden
        )







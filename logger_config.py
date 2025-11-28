"""
Configuración de logging estructurado usando loguru
"""
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio de logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configurar rotación y retención
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Remover el handler por defecto de loguru
logger.remove()

# Configurar handler para consola (con colores y formato legible)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
    backtrace=True,
    diagnose=True
)

# Configurar handler para archivo (formato JSON estructurado)
logger.add(
    LOG_DIR / "app-{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
    level=LOG_LEVEL,
    rotation="00:00",  # Rotar a medianoche cada día
    retention=f"{LOG_RETENTION_DAYS} days",  # Mantener logs por 30 días
    compression="zip",  # Comprimir archivos antiguos
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    enqueue=True,  # Thread-safe logging
    serialize=False  # Si True, formato JSON puro (más difícil de leer manualmente)
)

# También crear un handler para errores críticos en archivo separado
logger.add(
    LOG_DIR / "errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
    level="ERROR",
    rotation="10 MB",  # Rotar cuando el archivo alcance 10MB
    retention="90 days",  # Mantener errores por más tiempo
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    enqueue=True
)

# Logger configurado - exportar para uso en otros módulos
__all__ = ["logger"]


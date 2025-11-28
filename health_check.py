"""
Módulo de health checks para el sistema de reconocimiento facial
"""
import os
import shutil
import psutil
from datetime import datetime
from typing import Dict, Any
from database import Database


def check_database() -> Dict[str, Any]:
    """
    Verifica el estado de la conexión a la base de datos
    
    Returns:
        Dict con status y detalles de la conexión
    """
    try:
        if Database.test_connection():
            # Intentar obtener una conexión del pool para verificar que funciona
            conn = Database.get_connection()
            try:
                if conn and conn.is_connected():
                    pool_size = Database._get_pool().pool_size
                    return {
                        "status": "ok",
                        "pool_size": pool_size,
                        "message": "Conexión a base de datos exitosa"
                    }
            finally:
                if conn and conn.is_connected():
                    conn.close()
        return {
            "status": "error",
            "message": "No se pudo conectar a la base de datos"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar base de datos: {str(e)}"
        }


def check_disk_space() -> Dict[str, Any]:
    """
    Verifica el espacio disponible en disco
    
    Returns:
        Dict con status y detalles del espacio en disco
    """
    try:
        # Obtener espacio en disco del directorio actual
        total, used, free = shutil.disk_usage(".")
        
        # Convertir a GB
        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        free_percent = (free / total) * 100
        
        # Considerar crítico si hay menos del 5% de espacio libre
        min_free_percent = 5
        status = "ok" if free_percent >= min_free_percent else "warning"
        
        return {
            "status": status,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "free_percent": round(free_percent, 2),
            "message": f"{free_percent:.1f}% de espacio libre disponible"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar espacio en disco: {str(e)}"
        }


def check_memory() -> Dict[str, Any]:
    """
    Verifica el uso de memoria del sistema
    
    Returns:
        Dict con status y detalles del uso de memoria
    """
    try:
        # Obtener memoria del sistema
        memory = psutil.virtual_memory()
        
        # Convertir a GB
        total_gb = memory.total / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        used_gb = memory.used / (1024 ** 3)
        used_percent = memory.percent
        
        # Considerar warning si hay más del 90% de uso
        max_used_percent = 90
        status = "ok" if used_percent < max_used_percent else "warning"
        
        return {
            "status": status,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "available_gb": round(available_gb, 2),
            "used_percent": round(used_percent, 2),
            "message": f"{used_percent:.1f}% de memoria en uso"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar memoria: {str(e)}"
        }


def check_cache(embeddings_cache) -> Dict[str, Any]:
    """
    Verifica el estado del caché de embeddings
    
    Args:
        embeddings_cache: Instancia de EmbeddingsCache (puede ser None)
        
    Returns:
        Dict con status y detalles del caché
    """
    try:
        if embeddings_cache is None:
            return {
                "status": "not_configured",
                "message": "Caché no configurado"
            }
        
        # Usar el método get_cache_info si está disponible
        if hasattr(embeddings_cache, 'get_cache_info'):
            cache_info = embeddings_cache.get_cache_info()
            
            if cache_info["has_cache"]:
                return {
                    "status": "ok",
                    "embeddings_count": cache_info["embeddings_count"],
                    "cache_size": cache_info["cache_size"],
                    "message": f"Caché activo con {cache_info['embeddings_count']} embeddings"
                }
            else:
                return {
                    "status": "empty",
                    "embeddings_count": 0,
                    "message": "Caché vacío (se cargará desde BD cuando sea necesario - patrón Cache-Aside)"
                }
        else:
            # Fallback para cachés simples
            return {
                "status": "unknown",
                "message": "Tipo de caché no reconocido"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar caché: {str(e)}"
        }


def get_health_status(embeddings_cache=None) -> Dict[str, Any]:
    """
    Obtiene el estado completo de salud del sistema
    
    Args:
        embeddings_cache: Instancia del caché de embeddings (opcional)
        
    Returns:
        Dict con el estado de salud completo
    """
    checks = {
        "database": check_database(),
        "disk_space": check_disk_space(),
        "memory": check_memory()
    }
    
    if embeddings_cache is not None:
        checks["cache"] = check_cache(embeddings_cache)
    
    # Determinar estado general
    # Si algún check crítico está en error, el sistema está unhealthy
    critical_checks = ["database"]
    has_errors = any(
        checks[check].get("status") == "error" 
        for check in critical_checks
    )
    
    has_warnings = any(
        checks[check].get("status") == "warning"
        for check in checks
    )
    
    if has_errors:
        overall_status = "unhealthy"
    elif has_warnings:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }


def is_live() -> Dict[str, Any]:
    """
    Liveness check - verifica que el servidor esté respondiendo
    Siempre retorna OK mientras el servidor esté corriendo
    
    Returns:
        Dict con status de liveness
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def is_ready(embeddings_cache=None) -> Dict[str, Any]:
    """
    Readiness check - verifica que el sistema esté listo para recibir requests
    Requiere que los servicios críticos estén disponibles
    
    Args:
        embeddings_cache: Instancia del caché de embeddings (opcional)
        
    Returns:
        Dict con status de readiness
    """
    health = get_health_status(embeddings_cache)
    
    # Para readiness, requerimos que la BD esté disponible
    db_status = health["checks"].get("database", {}).get("status", "error")
    
    if db_status == "ok":
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    else:
        return {
            "status": "not_ready",
            "reason": "Database not available",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


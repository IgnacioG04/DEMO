"""
Módulo de caché de embeddings con patrón Cache-Aside
"""
from typing import List, Tuple, Optional
from datetime import datetime
from cachetools import TTLCache
import numpy as np
from database import Database
from logger_config import logger

# Clave del caché
CACHE_KEY = "embeddings:all"

# TTL de 1 hora (3600 segundos) - safety net aunque se invalida manualmente
CACHE_TTL = 3600

# Máximo de elementos en caché (1 es suficiente para nuestro caso)
CACHE_MAXSIZE = 1


class EmbeddingsCache:
    """
    Caché de embeddings con patrón Cache-Aside
    
    Patrón implementado:
    1. Buscar en caché RAM
    2. Si no está, buscar en BD
    3. Si está en BD, guardar en caché RAM y devolver
    4. Invalidar caché cuando se registra nuevo embedding
    """
    
    def __init__(self, ttl: int = CACHE_TTL, maxsize: int = CACHE_MAXSIZE):
        """
        Inicializa el caché de embeddings
        
        Args:
            ttl: Time To Live en segundos (default: 1 hora)
            maxsize: Tamaño máximo del caché (default: 1)
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.info(f"Caché de embeddings inicializado (TTL: {ttl}s)")
    
    def get_all_embeddings(self) -> List[Tuple[int, int, np.ndarray, datetime, bool]]:
        """
        Obtiene todos los embeddings usando patrón Cache-Aside
        
        Returns:
            Lista de embeddings: (embedding_id, user_id, embedding, created_at, estado)
        """
        # 1. Intentar obtener del caché
        cached_embeddings = self.cache.get(CACHE_KEY)
        
        if cached_embeddings is not None:
            logger.debug("Obteniendo embeddings desde caché", extra={"count": len(cached_embeddings)})
            return cached_embeddings
        
        # 2. Si no está en caché, obtener de BD
        logger.debug("Caché miss - obteniendo embeddings desde BD")
        embeddings = Database.get_all_embeddings()
        
        if embeddings:
            # 3. Guardar en caché para próximas consultas
            self.cache[CACHE_KEY] = embeddings
            logger.info(
                "Embeddings cargados desde BD y guardados en caché",
                extra={"count": len(embeddings)}
            )
        else:
            logger.warning("No se encontraron embeddings en BD")
        
        return embeddings
    
    def clear_cache(self):
        """
        Limpia el caché (invalidación manual)
        """
        if CACHE_KEY in self.cache:
            del self.cache[CACHE_KEY]
            logger.info("Caché de embeddings invalidado")
        else:
            logger.debug("Caché ya estaba vacío")
    
    def get_cache_info(self) -> dict:
        """
        Obtiene información sobre el estado del caché
        
        Returns:
            Dict con información del caché
        """
        cached_embeddings = self.cache.get(CACHE_KEY)
        
        return {
            "has_cache": cached_embeddings is not None,
            "embeddings_count": len(cached_embeddings) if cached_embeddings else 0,
            "cache_size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl": self.cache.ttl
        }
    
    def __repr__(self):
        info = self.get_cache_info()
        return f"EmbeddingsCache(has_cache={info['has_cache']}, count={info['embeddings_count']})"


# Instancia global del caché (singleton)
_embeddings_cache_instance: Optional[EmbeddingsCache] = None


def get_embeddings_cache() -> EmbeddingsCache:
    """
    Obtiene la instancia singleton del caché
    
    Returns:
        Instancia de EmbeddingsCache
    """
    global _embeddings_cache_instance
    
    if _embeddings_cache_instance is None:
        _embeddings_cache_instance = EmbeddingsCache()
    
    return _embeddings_cache_instance


def get_all_embeddings_with_cache() -> List[Tuple[int, int, np.ndarray, datetime, bool]]:
    """
    Función helper para obtener embeddings usando caché
    
    Returns:
        Lista de embeddings: (embedding_id, user_id, embedding, created_at, estado)
    """
    cache = get_embeddings_cache()
    return cache.get_all_embeddings()


def clear_embeddings_cache():
    """
    Función helper para limpiar el caché
    """
    cache = get_embeddings_cache()
    cache.clear_cache()


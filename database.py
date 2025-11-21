import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv
import numpy as np
from typing import Optional, List, Tuple
from datetime import datetime

load_dotenv()

class Database:
    _connection_pool = None
    
    @classmethod
    def _get_pool(cls):
        # Create and return MySQL connection pool
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pooling.MySQLConnectionPool(
                    pool_name="face_recognition_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    host=os.getenv('DATABASE_HOST'),
                    port=int(os.getenv('DATABASE_PORT', 3306)),
                    user=os.getenv('DATABASE_USER'),
                    password=os.getenv('DATABASE_PASSWORD'),
                    database=os.getenv('DATABASE_SCHEMA'),
                    autocommit=False
                )
            except Error as e:
                raise ConnectionError(f"Failed to create connection pool: {e}")
        return cls._connection_pool
    
    @classmethod
    def get_connection(cls):
        # Get a connection from the connection pool
        pool = cls._get_pool()
        try:
            connection = pool.get_connection()
            return connection
        except Error as e:
            raise ConnectionError(f"Failed to get connection from pool: {e}")
    
    @classmethod
    def test_connection(cls) -> bool:
        # Test database connection availability
        try:
            conn = cls.get_connection()
            if conn.is_connected():
                conn.close()
                return True
            return False
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    @classmethod
    def insert_embedding(cls, user_id: int, embedding: np.ndarray) -> Optional[int]:
        # Insert face embedding into database for a user
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            embedding_float32 = embedding.astype(np.float32)
            embedding_bytes = embedding_float32.tobytes()
            
            query = """
                INSERT INTO usuarios_face_embeddings (usuario_id, embedding)
                VALUES (%s, %s)
            """
            
            cursor.execute(query, (user_id, embedding_bytes))
            conn.commit()
            
            embedding_id = cursor.lastrowid
            return embedding_id
            
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Error inserting embedding: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    @classmethod
    def get_embeddings_by_user(cls, user_id: int) -> List[Tuple[int, np.ndarray, datetime]]:
        # Retrieve all embeddings for a specific user from database
        conn = None
        results = []
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id_usuarios_face_embeddings, embedding, creado_en
                FROM usuarios_face_embeddings
                WHERE usuario_id = %s
            """
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                embedding_id, embedding_bytes, creado_en = row
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                results.append((embedding_id, embedding, creado_en))
            
            return results
            
        except Error as e:
            print(f"Error fetching embeddings: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    @classmethod
    def get_all_embeddings(cls) -> List[Tuple[int, int, np.ndarray, datetime]]:
        # Retrieve all embeddings from database for face comparison
        conn = None
        results = []
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id_usuarios_face_embeddings, usuario_id, embedding, creado_en
                FROM usuarios_face_embeddings
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                embedding_id, usuario_id, embedding_bytes, creado_en = row
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                results.append((embedding_id, usuario_id, embedding, creado_en))
            
            return results
            
        except Error as e:
            print(f"Error fetching all embeddings: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    @classmethod
    def user_has_embeddings(cls, user_id: int) -> bool:
        # Check if user already has embeddings registered in database
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM usuarios_face_embeddings WHERE usuario_id = %s"
            cursor.execute(query, (user_id,))
            count = cursor.fetchone()[0]
            
            return count > 0
            
        except Error as e:
            print(f"Error checking user embeddings: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    @classmethod
    def get_all_user_ids(cls) -> set:
        # Get all user IDs that have embeddings in database
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT DISTINCT usuario_id FROM usuarios_face_embeddings"
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return {row[0] for row in rows}
            
        except Error as e:
            print(f"Error fetching user IDs: {e}")
            return set()
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()


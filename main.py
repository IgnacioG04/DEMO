"""
API FastAPI para el sistema de reconocimiento facial
"""
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import uvicorn
from face_recognition_system import FaceRecognitionSystem
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_PORT = int(os.getenv('API_PORT'))
API_HOST = os.getenv('API_HOST')

app = FastAPI(title="Sistema de Reconocimiento Facial", version="1.0.0")

# Inicializar el sistema de reconocimiento facial
# Threshold se carga automáticamente desde CONFIDENCE_INTERVAL en .env
face_system = FaceRecognitionSystem()

@app.get("/")
async def read_root():
    """API root endpoint - returns API information"""
    return JSONResponse({
        "name": "Sistema de Reconocimiento Facial API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/register",
            "login": "/login",
            "users": "/users",
            "verify-frame": "/verify-frame"
        },
        "docs": "/docs"
    })

@app.post("/register")
async def register_face(file: UploadFile = File(...), user_id: str = Form(...)):
    # API endpoint to register a new face embedding - Stateless: saves image to registered_faces, checks DB, processes and stores
    try:
        image_bytes = await file.read()
        
        success, message = face_system.register_face(image_bytes, user_id)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": message
            })
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/login")
async def login_face(file: UploadFile = File(...)):
    # API endpoint to verify face identity for login - Stateless: processes image, compares with DB, returns result
    try:
        image_bytes = await file.read()
        
        matches, user_id, similarity = face_system.verify_face(image_bytes)
        
        if matches:
            return JSONResponse({
                "success": True,
                "user_id": user_id,
                "similarity": float(similarity),
                "message": "Rostro reconocido correctamente"
            })
        else:
            return JSONResponse({
                "success": False,
                "similarity": float(similarity) if similarity else 0.0,
                "message": "Rostro no reconocido o no coincide con ningún usuario registrado"
            }, status_code=401)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/users")
async def list_users():
    # API endpoint to list all registered users
    """
    Endpoint para listar todos los usuarios registrados
    
    Returns:
        Lista de usuarios registrados
    """
    users = face_system.list_registered_users()
    return JSONResponse({
        "users": users,
        "count": len(users)
    })

@app.post("/verify-frame")
async def verify_frame(file: UploadFile = File(...)):
    # API endpoint for real-time frame verification - Stateless: processes frame, compares with DB, returns all similarities
    try:
        image_bytes = await file.read()
        
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
                return JSONResponse({
                    "success": False,
                    "similarities": [],
                    "message": "No se detectó rostro en la imagen"
                })
            
            from database import Database
            all_embeddings = Database.get_all_embeddings()
            
            similarities = []
            for embedding_id, user_id, stored_embedding, created_at in all_embeddings:
                similarity = face_system.calculate_similarity(embedding, stored_embedding)
                similarities.append({
                    "user_id": str(user_id),
                    "similarity": float(similarity)
                })
            
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
                    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

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
        print(f"[ERROR] No se pudo iniciar la GUI: {e}")
        print(f"[INFO] El servidor API sigue ejecutándose en http://{API_HOST}:{API_PORT}")

if __name__ == "__main__":
    import threading
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print(f"[INFO] Servidor API iniciando en http://{API_HOST}:{API_PORT}")
    print("[INFO] Abriendo aplicación GUI...")
    
    start_gui()


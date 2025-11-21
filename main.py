"""
API FastAPI para el sistema de reconocimiento facial
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
from face_recognition_system import FaceRecognitionSystem

app = FastAPI(title="Sistema de Reconocimiento Facial", version="1.0.0")

# Inicializar el sistema de reconocimiento facial
face_system = FaceRecognitionSystem(threshold=0.6)

# Crear directorio para archivos estáticos
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Página principal con la interfaz web"""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de Reconocimiento Facial</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
                font-size: 28px;
            }
            .section {
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            .section h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 20px;
            }
            input[type="file"] {
                display: none;
            }
            .file-label {
                display: block;
                padding: 15px;
                background: #667eea;
                color: white;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                transition: background 0.3s;
                margin-bottom: 15px;
            }
            .file-label:hover {
                background: #5568d3;
            }
            input[type="text"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                margin-bottom: 15px;
            }
            button {
                width: 100%;
                padding: 15px;
                background: #764ba2;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            button:hover {
                background: #5a3a7a;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .preview {
                margin-top: 20px;
                text-align: center;
            }
            .preview img {
                max-width: 100%;
                max-height: 300px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }
            .message {
                margin-top: 15px;
                padding: 12px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .message.info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 10px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Sistema de Reconocimiento Facial</h1>
            
            <!-- Sección de Registro -->
            <div class="section">
                <h2>📝 Registro de Usuario</h2>
                <input type="file" id="registerFile" accept="image/*" capture="user">
                <label for="registerFile" class="file-label">📷 Seleccionar o Capturar Foto</label>
                <input type="text" id="userId" placeholder="Ingresa tu ID de usuario (ej: juan_perez)">
                <button onclick="registerFace()">Registrar Rostro</button>
                <div id="registerPreview" class="preview"></div>
                <div id="registerMessage"></div>
            </div>
            
            <!-- Sección de Login -->
            <div class="section">
                <h2>🚪 Inicio de Sesión</h2>
                <input type="file" id="loginFile" accept="image/*" capture="user">
                <label for="loginFile" class="file-label">📷 Seleccionar o Capturar Foto</label>
                <button onclick="loginFace()">Verificar Identidad</button>
                <div id="loginPreview" class="preview"></div>
                <div id="loginMessage"></div>
            </div>
        </div>
        
        <script>
            // Preview de imagen para registro
            document.getElementById('registerFile').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('registerPreview').innerHTML = 
                            '<img src="' + e.target.result + '" alt="Vista previa">';
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            // Preview de imagen para login
            document.getElementById('loginFile').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('loginPreview').innerHTML = 
                            '<img src="' + e.target.result + '" alt="Vista previa">';
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            async function registerFace() {
                const fileInput = document.getElementById('registerFile');
                const userIdInput = document.getElementById('userId');
                const messageDiv = document.getElementById('registerMessage');
                
                if (!fileInput.files[0]) {
                    messageDiv.innerHTML = '<div class="message error">Por favor selecciona una imagen</div>';
                    return;
                }
                
                if (!userIdInput.value.trim()) {
                    messageDiv.innerHTML = '<div class="message error">Por favor ingresa un ID de usuario</div>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('user_id', userIdInput.value.trim());
                
                messageDiv.innerHTML = '<div class="spinner"></div>';
                
                try {
                    const response = await fetch('/register', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        messageDiv.innerHTML = `<div class="message success">${data.message}</div>`;
                        fileInput.value = '';
                        userIdInput.value = '';
                        document.getElementById('registerPreview').innerHTML = '';
                    } else {
                        messageDiv.innerHTML = `<div class="message error">${data.message}</div>`;
                    }
                } catch (error) {
                    messageDiv.innerHTML = `<div class="message error">Error: ${error.message}</div>`;
                }
            }
            
            async function loginFace() {
                const fileInput = document.getElementById('loginFile');
                const messageDiv = document.getElementById('loginMessage');
                
                if (!fileInput.files[0]) {
                    messageDiv.innerHTML = '<div class="message error">Por favor selecciona una imagen</div>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                messageDiv.innerHTML = '<div class="spinner"></div>';
                
                try {
                    const response = await fetch('/login', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        messageDiv.innerHTML = `
                            <div class="message success">
                                ✅ Acceso concedido<br>
                                Usuario: ${data.user_id}<br>
                                Similitud: ${(data.similarity * 100).toFixed(2)}%
                            </div>
                        `;
                    } else {
                        messageDiv.innerHTML = `
                            <div class="message error">
                                ❌ Acceso denegado<br>
                                ${data.message || 'Rostro no reconocido'}
                                ${data.similarity ? ` (Similitud: ${(data.similarity * 100).toFixed(2)}%)` : ''}
                            </div>
                        `;
                    }
                    
                    // Limpiar después de 5 segundos
                    setTimeout(() => {
                        fileInput.value = '';
                        document.getElementById('loginPreview').innerHTML = '';
                        messageDiv.innerHTML = '';
                    }, 5000);
                } catch (error) {
                    messageDiv.innerHTML = `<div class="message error">Error: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/register")
async def register_face(file: UploadFile = File(...), user_id: str = Form(...)):
    """
    Endpoint para registrar un nuevo rostro
    
    Args:
        file: Archivo de imagen con el rostro
        user_id: ID único del usuario
        
    Returns:
        Respuesta JSON con el resultado del registro
    """
    try:
        # Leer bytes de la imagen
        image_bytes = await file.read()
        
        # Registrar rostro
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
    """
    Endpoint para verificar la identidad mediante reconocimiento facial
    
    Args:
        file: Archivo de imagen con el rostro a verificar
        
    Returns:
        Respuesta JSON con el resultado de la verificación
    """
    try:
        # Leer bytes de la imagen
        image_bytes = await file.read()
        
        # Verificar rostro
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

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """
    Endpoint para eliminar un usuario registrado
    
    Args:
        user_id: ID del usuario a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    success = face_system.delete_user(user_id)
    
    if success:
        return JSONResponse({
            "success": True,
            "message": f"Usuario {user_id} eliminado correctamente"
        })
    else:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


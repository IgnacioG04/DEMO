# Sistema de Reconocimiento Facial 🔐

Sistema ligero y preciso de reconocimiento facial desarrollado con Python, FastAPI e InsightFace. Optimizado para implementación en web y aplicaciones móviles.

## ✨ Características

- 🚀 **Ligero y rápido**: Usa InsightFace con modelos optimizados para CPU
- 🎯 **Preciso**: Reconocimiento facial con embeddings de alta calidad
- 📱 **Compatible**: Diseñado para web y futura implementación móvil
- 🔒 **Eficiente**: Almacena embeddings en lugar de imágenes completas
- 🌐 **API REST**: Endpoints simples para registro y login

## 📋 Requisitos

- Python 3.8 o superior
- 2GB RAM mínimo (recomendado 4GB)
- Webcam o dispositivo con cámara (para captura)

## 🔧 Instalación

### ⚠️ Importante: Usar Entorno Virtual (Recomendado)

**SÍ, es MUY recomendable usar un entorno virtual** por las siguientes razones:

- 🔒 **Aislamiento**: Evita conflictos con otras versiones de librerías instaladas en tu sistema
- 🧹 **Limpieza**: Mantiene tu instalación de Python global limpia
- 🔄 **Reproducibilidad**: Garantiza que el proyecto funcione igual en diferentes máquinas
- 🛡️ **Seguridad**: Evita modificar dependencias del sistema

### Pasos de Instalación

#### 🚀 Opción Rápida (Recomendada)

**En Windows:**
```bash
setup.bat
```
Este script creará el entorno virtual y instalará todas las dependencias automáticamente.

**En Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

#### 📝 Instalación Manual

1. **Clonar o descargar el proyecto**

2. **Crear un entorno virtual**:

**En Windows:**
```bash
python -m venv venv
```

**En Linux/Mac:**
```bash
python3 -m venv venv
```

3. **Activar el entorno virtual**:

**En Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**En Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**En Linux/Mac:**
```bash
source venv/bin/activate
```

✅ Cuando el entorno virtual esté activado, verás `(venv)` al inicio de tu terminal.

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

**Nota importante**: 
- La primera vez que ejecutes el sistema, InsightFace descargará automáticamente los modelos necesarios (aproximadamente 100MB). Esto solo ocurre una vez.
- Asegúrate de tener el entorno virtual activado antes de instalar dependencias o ejecutar el proyecto.

## 🚀 Uso

⚠️ **Asegúrate de tener el entorno virtual activado** antes de ejecutar el servidor.

1. **Activar el entorno virtual** (si no está activado):

**Windows:**
```bash
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

2. **Iniciar el servidor**:

**Opción 1 - Script rápido (Recomendado):**

**En Windows:**
```bash
run.bat
```

**En Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Opción 2 - Manualmente con run.py:**
```bash
python run.py
```

**Opción 3 - Usando main.py directamente:**
```bash
python main.py
```

**Opción 4 - Usando uvicorn directamente:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Abrir en el navegador**:
```
http://localhost:8000
```

3. **Registrar un usuario**:
   - Haz clic en "Seleccionar o Capturar Foto" en la sección de Registro
   - Captura o selecciona una foto con tu rostro claramente visible
   - Ingresa un ID de usuario (ej: `juan_perez`)
   - Haz clic en "Registrar Rostro"

4. **Iniciar sesión**:
   - Haz clic en "Seleccionar o Capturar Foto" en la sección de Inicio de Sesión
   - Captura o selecciona una foto con tu rostro
   - Haz clic en "Verificar Identidad"
   - El sistema te concederá o denegará el acceso según si tu rostro coincide con alguno registrado

## 📡 API Endpoints

### POST `/register`
Registra un nuevo rostro en el sistema.

**Parámetros**:
- `file`: Archivo de imagen (multipart/form-data)
- `user_id`: ID único del usuario (form-data)

**Ejemplo con curl**:
```bash
curl -X POST "http://localhost:8000/register" \
  -F "file=@foto.jpg" \
  -F "user_id=juan_perez"
```

### POST `/login`
Verifica la identidad mediante reconocimiento facial.

**Parámetros**:
- `file`: Archivo de imagen (multipart/form-data)

**Ejemplo con curl**:
```bash
curl -X POST "http://localhost:8000/login" \
  -F "file=@foto_verificacion.jpg"
```

### GET `/users`
Lista todos los usuarios registrados.

### DELETE `/users/{user_id}`
Elimina un usuario registrado.

## 🎛️ Configuración

Puedes ajustar el umbral de reconocimiento en `main.py`:

```python
face_system = FaceRecognitionSystem(threshold=0.6)
```

- **Umbral más bajo (ej: 0.5)**: Más estricto, requiere mayor similitud
- **Umbral más alto (ej: 0.7)**: Más permisivo, acepta más variaciones

El valor por defecto (0.6) es un buen equilibrio entre seguridad y usabilidad.

## 📦 Estructura del Proyecto

```
.
├── main.py                    # API FastAPI principal
├── face_recognition_system.py # Lógica de reconocimiento facial
├── requirements.txt           # Dependencias
├── README.md                  # Este archivo
└── face_embeddings/           # Directorio de embeddings (se crea automáticamente)
    ├── {user_id}.npy         # Embeddings faciales
    └── {user_id}.json        # Metadatos
```

## 🔍 ¿Cómo Funciona?

1. **Registro**:
   - Se captura/recibe una imagen
   - InsightFace detecta y extrae el rostro
   - Se genera un embedding (vector de 512 dimensiones) que representa las características faciales
   - El embedding se guarda en disco (no la imagen completa)

2. **Login**:
   - Se captura/recibe una imagen
   - Se extrae el embedding del rostro
   - Se compara con todos los embeddings registrados usando similitud coseno
   - Si la similitud supera el umbral, se concede acceso

## ⚡ Optimizaciones para Web/Móvil

- ✅ Modelo ligero (`buffalo_l`) de InsightFace
- ✅ Detección optimizada con tamaño reducido (320x320)
- ✅ Almacenamiento eficiente (solo embeddings, no imágenes)
- ✅ Compatibilidad con CPU (no requiere GPU)
- ✅ API RESTful simple y escalable

## 🐛 Solución de Problemas

**Error: "No se detectó ningún rostro"**
- Asegúrate de que la imagen tenga buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita imágenes muy oscuras o borrosas

**Reconocimiento no funciona bien**
- Ajusta el umbral en `main.py`
- Registra múltiples fotos del mismo usuario en diferentes condiciones
- Asegúrate de que la calidad de imagen sea buena

**Modelo no se descarga**
- Verifica tu conexión a internet
- El modelo se descarga automáticamente la primera vez
- Verifica permisos de escritura en el directorio del proyecto

## 📝 Notas

- **Importante**: Usa siempre un entorno virtual para este proyecto
- Los embeddings se guardan en `face_embeddings/` (se crea automáticamente)
- El modelo se descarga en `~/.insightface/` la primera vez (aprox. 100MB)
- Compatible con Python 3.8+
- Funciona en Windows, Linux y macOS

### 🔄 Desactivar el Entorno Virtual

Cuando termines de trabajar, puedes desactivar el entorno virtual simplemente ejecutando:
```bash
deactivate
```

Esto te devolverá a tu entorno de Python global.

## 📄 Licencia

Este proyecto es de uso libre para fines educativos y comerciales.


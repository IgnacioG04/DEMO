# Sistema de Reconocimiento Facial - Aplicación GUI 🖥️

Aplicación de escritorio con interfaz gráfica para reconocimiento facial usando cámara web. **Arquitectura stateless** que consume endpoints de la API REST.

## ✨ Características

- 🖥️ **Aplicación GUI de escritorio** con tkinter
- 📷 **Captura de video en tiempo real** desde la cámara
- 🔐 **Sistema de registro** de nuevos usuarios
- 🚪 **Sistema de login** con contador de detecciones
- ✅ **Validación automática** cuando se detecta el rostro suficientes veces
- 🌐 **Arquitectura Stateless**: Consume endpoints de la API, no almacena embeddings localmente
- 💾 **Base de Datos**: Todos los embeddings se almacenan en MySQL (tabla `usuarios_face_embeddings`)
- 🔄 **Sin Estado Local**: No crea archivos `.npy` ni almacena datos localmente

## 📋 Requisitos

- Python 3.8 o superior
- Cámara web (Iriun Webcam u otra cámara compatible)
- 2GB RAM mínimo (recomendado 4GB)
- **Servidor API ejecutándose** en `http://localhost:8000` (ver README.md)
- MySQL configurado y accesible (el servidor API se conecta a la base de datos)

## 🔧 Instalación

### 1. Configurar el Servidor API

**Primero, asegúrate de que el servidor API esté configurado y funcionando:**

1. Sigue las instrucciones en `README.md` para configurar la base de datos
2. Crea el archivo `.env` con las credenciales de MySQL
3. Inicia el servidor API:

```bash
python main.py
```

El servidor debe estar ejecutándose en `http://localhost:8000`

### 2. Activar el entorno virtual

**En Windows:**

```powershell
.\venv\Scripts\Activate.ps1
```

**En Linux/Mac:**

```bash
source venv/bin/activate
```

### 3. Instalar dependencias (si aún no están instaladas)

```bash
pip install -r requirements.txt
```

**Nota**: Se instala `opencv-python` (no headless) para acceso a la cámara y `requests` para consumir la API.

## 🚀 Uso

### Iniciar la aplicación

**⚠️ IMPORTANTE: El servidor API debe estar ejecutándose antes de iniciar la GUI**

1. **Inicia el servidor API** (en una terminal):

```bash
python main.py
```

2. **Inicia la aplicación GUI** (en otra terminal):

**Opción 1 - Script rápido:**

```bash
python run_gui.py
```

**Opción 2 - Directamente:**

```bash
python face_app_gui.py
```

### Funcionalidades

#### 📝 Registrar Nuevo Usuario

1. Haz clic en **"📝 REGISTRAR NUEVO USUARIO"**
2. Ingresa un ID de usuario numérico (ej: `1`, `2`, `3`)
3. La cámara se activará
4. Mira directamente a la cámara
5. Presiona **ESPACIO** cuando estés listo para registrar tu rostro
6. La aplicación enviará la imagen al endpoint `/register` de la API
7. La API procesará y guardará el embedding en la base de datos
8. Se mostrará confirmación de registro exitoso

**Flujo técnico**:

- GUI captura frame → Envía a `/register` → API extrae embedding → API guarda en BD → GUI muestra confirmación

#### 🚪 Iniciar Sesión

1. Haz clic en **"🚪 INICIAR SESIÓN"**
2. La cámara se activará
3. Mira directamente a la cámara
4. El sistema detectará tu rostro en tiempo real y mostrará:
   - Nombre de usuario detectado
   - Porcentaje de similitud
   - Contador de detecciones (ej: 3/5)
5. Cuando el contador llegue a 5 (por defecto), el acceso será concedido automáticamente
6. Se mostrará un mensaje de éxito

**Flujo técnico**:

- GUI captura frames → Envía a `/verify-frame` → API compara con embeddings en BD → API retorna similitudes → GUI muestra resultado

#### ⏹ Detener Cámara

- Haz clic en **"⏹ DETENER CÁMARA"** en cualquier momento para detener la captura

## 🎛️ Configuración

### Configuración de la GUI

Puedes ajustar los siguientes parámetros en `face_app_gui.py`:

```python
self.api_base_url = "http://localhost:8000"  # URL del servidor API
self.threshold = 0.6  # Umbral de similitud (0.0-1.0, menor = más estricto)
self.detection_count_threshold = 5  # Número de detecciones antes de validar
self.detection_window = 2.0  # Ventana de tiempo para contar detecciones (segundos)
```

### Parámetros explicados:

- **api_base_url**: URL base del servidor API (por defecto `http://localhost:8000`)
- **threshold**: Umbral de similitud para reconocer un rostro (por defecto 0.6 = 60%)
- **detection_count_threshold**: Cuántas veces debe detectarse el mismo rostro antes de conceder acceso (por defecto 5)
- **detection_window**: Ventana de tiempo en segundos para contar detecciones (por defecto 2.0 segundos)

### Configuración del Servidor API

El umbral de reconocimiento se configura en `main.py` del servidor:

```python
face_system = FaceRecognitionSystem(threshold=0.6)
```

## 📁 Estructura del Proyecto

```
.
├── face_app_gui.py              # Aplicación GUI principal - Consume API
├── run_gui.py                   # Script de inicio rápido para GUI
├── main.py                      # Servidor API FastAPI (debe estar ejecutándose)
├── face_recognition_system.py   # Lógica de reconocimiento facial (usado por API)
├── database.py                  # Módulo de conexión MySQL (usado por API)
├── process_images.py            # Script para procesar imágenes en batch
├── requirements.txt             # Dependencias
├── .env                         # Configuración de base de datos (para API)
├── README.md                    # Documentación del servidor API
├── README_GUI.md                # Este archivo - Documentación GUI
└── registered_faces/            # Carpeta opcional para imágenes de referencia
    ├── 1.jpg                   # Imágenes nombradas por user_id
    ├── 2.png
    └── ...
```

## 📁 Descripción de Archivos

### Archivos de la GUI

- **`face_app_gui.py`**:

  - Aplicación GUI principal con tkinter
  - **Arquitectura stateless**: No almacena embeddings localmente
  - Consume endpoints de la API: `/register`, `/verify-frame`, `/users`
  - Captura de video en tiempo real desde cámara
  - Envía frames a la API para procesamiento
  - Muestra resultados en tiempo real

- **`run_gui.py`**:
  - Script simple para ejecutar la aplicación GUI
  - Inicia `face_app_gui.py`

### Archivos del Servidor (requeridos para que funcione la GUI)

- **`main.py`**:

  - Servidor API FastAPI
  - Debe estar ejecutándose para que la GUI funcione
  - Endpoints: `/register`, `/login`, `/verify-frame`, `/users`
  - Procesa todas las solicitudes de reconocimiento facial

- **`face_recognition_system.py`**:

  - Lógica de reconocimiento facial
  - Usado por el servidor API
  - Extrae y compara embeddings

- **`database.py`**:

  - Gestión de conexiones MySQL
  - Almacena y recupera embeddings de la base de datos
  - Usado por el servidor API

- **`process_images.py`**:
  - Script opcional para procesar imágenes en batch
  - Lee imágenes de `registered_faces/` y las inserta en la base de datos
  - Útil para migración masiva de imágenes

### Archivos de Configuración

- **`.env`**:

  - Configuración de base de datos MySQL
  - Usado por el servidor API
  - Variables: `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_SCHEMA`

- **`requirements.txt`**:
  - Dependencias del proyecto
  - Incluye: tkinter, opencv-python, requests, etc.

## 🔍 ¿Cómo Funciona?

### Arquitectura Stateless

La aplicación GUI utiliza una arquitectura **stateless**:

1. **GUI (Cliente)**:

   - No almacena embeddings ni estado
   - Solo captura frames y envía a la API
   - Recibe resultados y los muestra al usuario

2. **API (Servidor)**:

   - Procesa todas las solicitudes
   - Extrae embeddings usando DeepFace
   - Almacena y consulta embeddings en MySQL

3. **Base de Datos**:
   - Almacena todos los embeddings en tabla `usuarios_face_embeddings`
   - Única fuente de verdad

### Flujo de Registro

1. Usuario presiona ESPACIO → GUI captura frame
2. GUI envía imagen → Endpoint `/register` de la API
3. API extrae embedding → Usa DeepFace
4. API verifica duplicados → Consulta base de datos
5. API almacena en BD → Inserta en `usuarios_face_embeddings`
6. API responde → Confirma registro
7. GUI muestra confirmación → Usuario ve mensaje de éxito

### Flujo de Login

1. GUI captura frames continuamente → Cada ~30ms
2. GUI envía frame → Endpoint `/verify-frame` de la API
3. API extrae embedding → Usa DeepFace
4. API consulta BD → Obtiene todos los embeddings
5. API compara → Calcula similitud coseno
6. API retorna similitudes → Mejor match y otras similitudes
7. GUI procesa resultado → Incrementa contador si supera umbral
8. GUI concede acceso → Cuando contador alcanza umbral

### Almacenamiento

**No se almacenan archivos localmente**:

- ❌ No se crean archivos `.npy`
- ❌ No se guardan embeddings en disco
- ❌ No se almacena estado de sesión
- ✅ Todo se envía a la API
- ✅ Todo se almacena en MySQL

## 🎯 Características del Sistema de Validación

- **Contador de detecciones**: Requiere múltiples detecciones antes de validar (evita falsos positivos)
- **Ventana de tiempo**: Las detecciones deben ocurrir dentro de una ventana de tiempo para ser contadas
- **Reset automático**: Si no se detecta el rostro por un tiempo, el contador se reinicia
- **Comparación en tiempo real**: Cada frame se compara con todos los embeddings en la base de datos

## 🐛 Solución de Problemas

**Error: "No se pudo conectar con la API"**

- Verifica que el servidor API esté ejecutándose en `http://localhost:8000`
- Asegúrate de que no haya firewall bloqueando la conexión
- Verifica la URL en `face_app_gui.py` (variable `api_base_url`)

**Error: "No se pudo abrir la cámara"**

- Verifica que la cámara esté conectada y funcionando
- Asegúrate de que no haya otra aplicación usando la cámara
- Prueba con otra cámara si está disponible

**Error: "No se detectó ningún rostro"**

- Asegúrate de que haya buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita fondos muy oscuros o muy brillantes

**El contador no aumenta**

- Verifica que el servidor API esté funcionando correctamente
- Verifica que haya usuarios registrados en la base de datos
- Asegúrate de que el rostro esté bien iluminado
- El umbral de similitud puede ser muy alto, verifica en el servidor API

**Error: "Tiempo de espera agotado"**

- El servidor API puede estar sobrecargado
- Verifica que la base de datos esté respondiendo correctamente
- Aumenta el timeout en `face_app_gui.py` si es necesario

**La aplicación se cierra inesperadamente**

- Verifica que todas las dependencias estén instaladas
- Asegúrate de tener suficiente memoria RAM disponible
- Revisa los logs en la consola para ver el error específico
- Verifica que el servidor API esté ejecutándose

## 📝 Notas

- **Importante**: El servidor API debe estar ejecutándose antes de iniciar la GUI
- Los embeddings se almacenan en la tabla `usuarios_face_embeddings` de MySQL (no localmente)
- DeepFace descargará modelos automáticamente la primera vez (~200-300 MB)
- Compatible con Python 3.8+
- Funciona en Windows, Linux y macOS
- Optimizado para cámara web USB e Iriun Webcam
- Arquitectura stateless permite múltiples clientes conectándose al mismo servidor

## 🔐 Seguridad y Arquitectura

- **Stateless**: La GUI no almacena datos, todo se procesa en el servidor
- **Base de Datos Centralizada**: Todos los embeddings en MySQL
- **Sin Archivos Locales**: No se crean archivos `.npy` ni se almacena estado
- **API RESTful**: Comunicación estándar mediante HTTP
- **Escalable**: Múltiples clientes pueden conectarse al mismo servidor

## 🔄 Flujo Completo del Sistema

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   GUI App   │ ──────> │  API Server │ ──────> │   MySQL DB  │
│  (Cliente)  │         │  (Backend)  │         │  (Storage)  │
└─────────────┘         └─────────────┘         └─────────────┘
     │                        │                        │
     │ 1. Captura frame       │                        │
     │ 2. POST /register      │                        │
     │                        │ 3. Extrae embedding    │
     │                        │ 4. INSERT embedding    │
     │                        │ <───────────────────────┘
     │ 5. Respuesta OK        │                        │
     │ <───────────────────────┘                        │
```

## 📄 Licencia

Este proyecto es de uso libre para fines educativos y comerciales.

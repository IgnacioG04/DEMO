# Sistema de Reconocimiento Facial 🔐

Sistema ligero y preciso de reconocimiento facial desarrollado con Python, FastAPI y DeepFace. Arquitectura stateless con almacenamiento en base de datos MySQL.

## ✨ Características

- 🚀 **Ligero y rápido**: Usa DeepFace con modelos optimizados para CPU
- 🎯 **Preciso**: Reconocimiento facial con embeddings de alta calidad
- 📱 **Compatible**: Diseñado para web y aplicaciones móviles
- 🔒 **Eficiente**: Almacena embeddings en base de datos MySQL
- 🌐 **API REST Stateless**: Endpoints simples sin estado, todo se almacena en base de datos
- 💾 **Base de Datos**: Almacenamiento persistente en tabla `usuarios_face_embeddings`
- 🔄 **Arquitectura Stateless**: El frontend consume endpoints sin almacenar estado local

## 📋 Requisitos

- Python 3.8 o superior
- MySQL 5.7 o superior (local o remoto)
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

5. **Configurar Base de Datos**:

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña
DATABASE_SCHEMA=nombre_de_tu_base_de_datos
```

6. **Crear la tabla en MySQL**:

Ejecuta el siguiente SQL en tu base de datos:

```sql
CREATE TABLE usuarios_face_embeddings (
    id_usuario_face_embedding INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    embedding LONGBLOB NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado TINYINT DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);
```

**Nota**: Asegúrate de que la tabla `usuarios` exista antes de crear esta tabla si vas a usar la restricción de clave foránea.

**Nota importante**:

- La primera vez que ejecutes el sistema, DeepFace descargará automáticamente los modelos necesarios (aproximadamente 200-300MB). Esto solo ocurre una vez.
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

3. **Abrir en el navegador**:

```
http://localhost:8000
```

4. **Registrar un usuario**:

   - Haz clic en "Seleccionar o Capturar Foto" en la sección de Registro
   - Captura o selecciona una foto con tu rostro claramente visible
   - Ingresa un ID de usuario numérico (ej: `1`, `2`, `3`)
   - Haz clic en "Registrar Rostro"
   - El embedding se guardará en la base de datos en la tabla `usuarios_face_embeddings`

5. **Iniciar sesión**:
   - Haz clic en "Seleccionar o Capturar Foto" en la sección de Inicio de Sesión
   - Captura o selecciona una foto con tu rostro
   - Haz clic en "Verificar Identidad"
   - El sistema comparará con los embeddings almacenados en la base de datos
   - Se concederá o denegará el acceso según si tu rostro coincide con alguno registrado

## 📡 API Endpoints

### POST `/register`

Registra un nuevo rostro en el sistema. Almacena el embedding en la base de datos.

**Parámetros**:

- `file`: Archivo de imagen (multipart/form-data)
- `user_id`: ID único del usuario (form-data, debe ser numérico)

**Ejemplo con curl**:

```bash
curl -X POST "http://localhost:8000/register" \
  -F "file=@foto.jpg" \
  -F "user_id=1"
```

**Respuesta exitosa**:

```json
{
  "success": true,
  "message": "Rostro registrado correctamente para 1"
}
```

### POST `/login`

Verifica la identidad mediante reconocimiento facial. Compara con embeddings en la base de datos.

**Parámetros**:

- `file`: Archivo de imagen (multipart/form-data)

**Ejemplo con curl**:

```bash
curl -X POST "http://localhost:8000/login" \
  -F "file=@foto_verificacion.jpg"
```

**Respuesta exitosa**:

```json
{
  "success": true,
  "user_id": "1",
  "similarity": 0.85,
  "message": "Rostro reconocido correctamente"
}
```

### POST `/verify-frame`

Endpoint para verificación en tiempo real. Retorna todas las similitudes ordenadas. Usado por la aplicación GUI.

**Parámetros**:

- `file`: Archivo de imagen (multipart/form-data)

**Respuesta**:

```json
{
  "success": true,
  "best_match": {
    "user_id": "1",
    "similarity": 0.85
  },
  "all_similarities": [...],
  "other_similarities": [...],
  "threshold": 0.6
}
```

### GET `/users`

Lista todos los usuarios registrados desde la base de datos.

**Ejemplo con curl**:

```bash
curl -X GET "http://localhost:8000/users"
```

**Respuesta**:

```json
{
  "users": ["1", "2", "3"],
  "count": 3
}
```

## 🎛️ Configuración

### Umbral de Reconocimiento

Puedes ajustar el umbral de reconocimiento en `main.py`:

```python
face_system = FaceRecognitionSystem(threshold=0.6)
```

- **Umbral más bajo (ej: 0.5)**: Más estricto, requiere mayor similitud
- **Umbral más alto (ej: 0.7)**: Más permisivo, acepta más variaciones

El valor por defecto (0.6) es un buen equilibrio entre seguridad y usabilidad.

### Configuración de Base de Datos

Edita el archivo `.env` para configurar la conexión a MySQL:

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña
DATABASE_SCHEMA=nombre_de_tu_base_de_datos
```

## 📦 Estructura del Proyecto

```
.
├── main.py                      # API FastAPI principal - Endpoints REST
├── face_recognition_system.py   # Lógica de reconocimiento facial - Extracción y comparación
├── database.py                  # Módulo de conexión y operaciones con MySQL
├── process_images.py            # Script para procesar imágenes en batch desde carpeta
├── face_app_gui.py              # Aplicación GUI de escritorio (consume API)
├── run_gui.py                   # Script para ejecutar la GUI
├── download_model.py            # Script para descargar modelos de DeepFace
├── requirements.txt             # Dependencias del proyecto
├── .env                         # Configuración de base de datos (crear manualmente)
├── README.md                    # Este archivo - Documentación API
├── README_GUI.md                # Documentación de la aplicación GUI
├── setup.bat / setup.sh         # Scripts de instalación automática
├── run.bat / run.sh             # Scripts para ejecutar el servidor
├── run.py                       # Script Python para ejecutar servidor
├── registered_faces/            # Carpeta con imágenes de referencia (opcional)
│   ├── 1.jpg                   # Imágenes nombradas por user_id
│   ├── 2.png
│   └── ...
└── temp_images/                 # Carpeta temporal para procesamiento (se crea automáticamente)
```

## 📁 Descripción de Archivos

### Archivos Principales

- **`main.py`**:

  - API FastAPI con endpoints REST
  - Endpoints: `/register`, `/login`, `/verify-frame`, `/users`
  - Interfaz web HTML integrada
  - Inicializa el sistema de reconocimiento facial

- **`face_recognition_system.py`**:

  - Clase `FaceRecognitionSystem` - Lógica principal de reconocimiento
  - Extracción de embeddings usando DeepFace
  - Comparación de embeddings usando similitud coseno
  - Métodos: `register_face()`, `verify_face()`, `list_registered_users()`
  - No almacena archivos localmente, todo va a la base de datos

- **`database.py`**:

  - Clase `Database` - Gestión de conexiones MySQL
  - Connection pooling para eficiencia
  - Métodos: `insert_embedding()`, `get_all_embeddings()`, `get_embeddings_by_user()`, `user_has_embeddings()`, `get_all_user_ids()`, `test_connection()`
  - Lee configuración desde `.env`

- **`process_images.py`**:

  - Script para procesar imágenes en batch desde `registered_faces/`
  - Verifica si el user_id ya existe en la base de datos
  - Solo procesa imágenes nuevas (no duplica embeddings)
  - Inserta embeddings directamente en la base de datos
  - Las imágenes deben nombrarse con su user_id (ej: `1.png`, `2.jpg`)

- **`face_app_gui.py`**:

  - Aplicación GUI de escritorio con tkinter
  - Consume endpoints de la API de forma stateless
  - Captura de video en tiempo real desde cámara
  - Registro y login con reconocimiento facial
  - No almacena embeddings localmente, todo se envía a la API

- **`run_gui.py`**:

  - Script simple para ejecutar la aplicación GUI
  - Inicia `face_app_gui.py`

- **`download_model.py`**:
  - Script opcional para descargar modelos de DeepFace manualmente
  - Útil si hay problemas con la descarga automática

### Archivos de Configuración

- **`.env`**:

  - Configuración de base de datos MySQL
  - Variables: `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_SCHEMA`
  - **No se incluye en el repositorio** (debe crearse manualmente)

- **`requirements.txt`**:
  - Lista de dependencias Python
  - Incluye: FastAPI, DeepFace, OpenCV, MySQL connector, etc.

### Scripts de Ejecución

- **`run.py`**: Script Python para iniciar el servidor FastAPI
- **`run.bat` / `run.sh`**: Scripts de shell para iniciar el servidor (Windows/Linux)
- **`setup.bat` / `setup.sh`**: Scripts para instalación automática (Windows/Linux)

### Carpetas

- **`registered_faces/`**:

  - Carpeta opcional para almacenar imágenes de referencia
  - Las imágenes deben nombrarse con su user_id (ej: `1.jpg`, `2.png`)
  - Usado por `process_images.py` para procesamiento en batch
  - No es necesario para el funcionamiento normal de la API

- **`temp_images/`**:
  - Carpeta temporal creada automáticamente
  - Almacena imágenes temporales durante el procesamiento
  - Se limpia automáticamente

## 🔍 ¿Cómo Funciona?

### Arquitectura Stateless

El sistema utiliza una arquitectura **stateless** donde:

1. **Frontend (GUI o Web)**: No almacena estado ni embeddings localmente
2. **API (Backend)**: Procesa todas las solicitudes y almacena en base de datos
3. **Base de Datos**: Única fuente de verdad para todos los embeddings

### Flujo de Registro

1. **Cliente envía imagen** → Endpoint `/register`
2. **API extrae embedding** → Usa DeepFace para generar vector de características
3. **API verifica duplicados** → Consulta base de datos si el user_id ya existe
4. **API almacena en BD** → Inserta embedding en tabla `usuarios_face_embeddings`
5. **API responde** → Confirma registro exitoso

### Flujo de Login/Verificación

1. **Cliente envía imagen** → Endpoint `/login` o `/verify-frame`
2. **API extrae embedding** → Usa DeepFace para generar vector de características
3. **API consulta BD** → Obtiene todos los embeddings registrados
4. **API compara** → Calcula similitud coseno con cada embedding
5. **API encuentra mejor match** → Retorna user_id y similitud si supera umbral
6. **Cliente recibe respuesta** → Muestra resultado al usuario

### Almacenamiento en Base de Datos

Los embeddings se almacenan en la tabla `usuarios_face_embeddings`:

- **`id_usuarios_face_embeddings`**: ID único del registro (auto-incremental)
- **`usuario_id`**: ID del usuario (INT, puede tener múltiples embeddings)
- **`embedding`**: Vector de características faciales (LONGBLOB)
- **`creado_en`**: Fecha y hora de creación (TIMESTAMP con DEFAULT CURRENT_TIMESTAMP)
- **`estado`**: Estado del registro (TINYINT, DEFAULT 1 - activo/true). Se establece automáticamente en 1 (true) cuando el usuario es registrado

**Ventajas**:

- ✅ Persistencia garantizada
- ✅ Escalabilidad horizontal
- ✅ Backup y recuperación fácil
- ✅ Consultas eficientes
- ✅ Sin archivos locales que gestionar

## ⚡ Optimizaciones

- ✅ Modelo ligero (`VGG-Face`) de DeepFace
- ✅ Detección optimizada con OpenCV
- ✅ Almacenamiento eficiente (solo embeddings, no imágenes)
- ✅ Compatibilidad con CPU (no requiere GPU)
- ✅ API RESTful stateless y escalable
- ✅ Connection pooling para MySQL
- ✅ Arquitectura sin estado para fácil escalamiento

## 🐛 Solución de Problemas

**Error: "No se detectó ningún rostro"**

- Asegúrate de que la imagen tenga buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita imágenes muy oscuras o borrosas

**Error: "No se pudo conectar a la base de datos"**

- Verifica que MySQL esté ejecutándose
- Revisa las credenciales en el archivo `.env`
- Asegúrate de que la base de datos y la tabla existan
- Verifica que el usuario tenga permisos adecuados

**Reconocimiento no funciona bien**

- Ajusta el umbral en `main.py`
- Registra múltiples embeddings del mismo usuario en diferentes condiciones
- Asegúrate de que la calidad de imagen sea buena

**Modelo no se descarga**

- Verifica tu conexión a internet
- El modelo se descarga automáticamente la primera vez
- Verifica permisos de escritura en el directorio del proyecto

**Error: "El usuario ya tiene embeddings registrados"**

- El sistema previene duplicados por user_id
- Si necesitas actualizar, primero elimina los registros de la base de datos
- O usa un user_id diferente

## 📝 Notas

- **Importante**: Usa siempre un entorno virtual para este proyecto
- Los embeddings se guardan en la tabla `usuarios_face_embeddings` de MySQL
- El modelo se descarga en `~/.deepface/` la primera vez (aprox. 200-300MB)
- Compatible con Python 3.8+
- Funciona en Windows, Linux y macOS
- Arquitectura stateless permite escalamiento horizontal
- La aplicación GUI consume la API, no almacena datos localmente

### 🔄 Desactivar el Entorno Virtual

Cuando termines de trabajar, puedes desactivar el entorno virtual simplemente ejecutando:

```bash
deactivate
```

Esto te devolverá a tu entorno de Python global.

## 📄 Licencia

Este proyecto es de uso libre para fines educativos y comerciales.

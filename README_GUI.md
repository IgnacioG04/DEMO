# Sistema de Reconocimiento Facial - Aplicación GUI 🖥️

Aplicación de escritorio con interfaz gráfica para reconocimiento facial usando cámara web (Iriun Webcam).

## ✨ Características

- 🖥️ **Aplicación GUI de escritorio** con tkinter
- 📷 **Captura de video en tiempo real** desde la cámara
- 🔐 **Sistema de registro** de nuevos usuarios
- 🚪 **Sistema de login** con contador de detecciones
- ✅ **Validación automática** cuando se detecta el rostro suficientes veces
- 📁 **Almacenamiento local** de rostros registrados en carpeta `registered_faces/`

## 📋 Requisitos

- Python 3.8 o superior
- Cámara web (Iriun Webcam u otra cámara compatible)
- 2GB RAM mínimo (recomendado 4GB)

## 🔧 Instalación

### 1. Activar el entorno virtual

**En Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias (si aún no están instaladas)

```bash
pip install -r requirements.txt
```

**Nota**: Se instala `opencv-python` (no headless) para acceso a la cámara.

## 🚀 Uso

### Iniciar la aplicación

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
2. Ingresa un nombre de usuario (ej: `juan_perez`)
3. La cámara se activará
4. Mira directamente a la cámara
5. Presiona **ESPACIO** cuando estés listo para registrar tu rostro
6. El sistema guardará tu rostro y confirmará el registro

#### 🚪 Iniciar Sesión

1. Haz clic en **"🚪 INICIAR SESIÓN"**
2. La cámara se activará
3. Mira directamente a la cámara
4. El sistema detectará tu rostro y mostrará:
   - Nombre de usuario detectado
   - Porcentaje de similitud
   - Contador de detecciones (ej: 3/5)
5. Cuando el contador llegue a 5 (por defecto), el acceso será concedido automáticamente
6. Se mostrará un mensaje de éxito

#### ⏹ Detener Cámara

- Haz clic en **"⏹ DETENER CÁMARA"** en cualquier momento para detener la captura

## 🎛️ Configuración

Puedes ajustar los siguientes parámetros en `face_app_gui.py`:

```python
self.threshold = 0.6  # Umbral de similitud (0.0-1.0, menor = más estricto)
self.detection_count_threshold = 5  # Número de detecciones antes de validar
self.detection_window = 2.0  # Ventana de tiempo para contar detecciones (segundos)
```

### Parámetros explicados:

- **threshold**: Umbral de similitud para reconocer un rostro (por defecto 0.6 = 60%)
- **detection_count_threshold**: Cuántas veces debe detectarse el mismo rostro antes de conceder acceso (por defecto 5)
- **detection_window**: Ventana de tiempo en segundos para contar detecciones (por defecto 2.0 segundos)

## 📁 Estructura de Archivos

```
.
├── face_app_gui.py          # Aplicación GUI principal
├── run_gui.py              # Script de inicio rápido
├── requirements.txt        # Dependencias
├── registered_faces/       # Carpeta con rostros registrados (se crea automáticamente)
│   ├── {usuario}.npy      # Embeddings faciales
│   └── {usuario}.jpg      # Imágenes de referencia
└── README_GUI.md          # Este archivo
```

## 🔍 ¿Cómo Funciona?

1. **Registro**:
   - Se captura un frame de la cámara cuando presionas ESPACIO
   - DeepFace extrae un embedding (vector de características) del rostro
   - El embedding se guarda en `registered_faces/{usuario}.npy`
   - También se guarda una imagen de referencia en `registered_faces/{usuario}.jpg`

2. **Login**:
   - La cámara captura frames continuamente
   - Cada frame se analiza para detectar rostros
   - Si se detecta un rostro, se compara con todos los usuarios registrados
   - Si la similitud supera el umbral, se incrementa el contador para ese usuario
   - Cuando el contador alcanza el umbral (ej: 5), se concede el acceso automáticamente

## 🎯 Características del Sistema de Validación

- **Contador de detecciones**: Requiere múltiples detecciones antes de validar (evita falsos positivos)
- **Ventana de tiempo**: Las detecciones deben ocurrir dentro de una ventana de tiempo para ser contadas
- **Reset automático**: Si no se detecta el rostro por un tiempo, el contador se reinicia

## 🐛 Solución de Problemas

**Error: "No se pudo abrir la cámara"**
- Verifica que Iriun Webcam esté conectado y funcionando
- Asegúrate de que no haya otra aplicación usando la cámara
- Prueba con otra cámara si está disponible

**Error: "No se detectó ningún rostro"**
- Asegúrate de que haya buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita fondos muy oscuros o muy brillantes

**El contador no aumenta**
- Verifica que el rostro esté bien iluminado
- Asegúrate de estar mirando directamente a la cámara
- El umbral de similitud puede ser muy alto, prueba bajarlo a 0.5

**La aplicación se cierra inesperadamente**
- Verifica que todas las dependencias estén instaladas
- Asegúrate de tener suficiente memoria RAM disponible
- Revisa los logs en la consola para ver el error específico

## 📝 Notas

- Los rostros se guardan en `registered_faces/` (se crea automáticamente)
- DeepFace descargará modelos automáticamente la primera vez (~200-300 MB)
- Compatible con Python 3.8+
- Funciona en Windows, Linux y macOS
- Optimizado para cámara web USB e Iriun Webcam

## 🔐 Seguridad

- Los rostros se almacenan localmente en tu máquina
- No se transmite información a servidores externos
- Los embeddings son solo representaciones matemáticas, no imágenes completas

## 📄 Licencia

Este proyecto es de uso libre para fines educativos y comerciales.


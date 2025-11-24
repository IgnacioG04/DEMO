#!/bin/bash

echo "========================================"
echo "Sistema de Reconocimiento Facial"
echo "========================================"
echo ""

# Cargar variables de entorno
API_HOST=${API_HOST}
API_PORT=${API_PORT}

# Verificar si las variables de entorno están definidas
if [ -z "${API_HOST}" ] || [ -z "${API_PORT}" ]; then
    echo "ERROR: Las variables de entorno API_HOST y API_PORT no están definidas."
    echo "Por favor define las variables de entorno API_HOST y API_PORT en el archivo .env."
    exit 1
fi

# Verificar si el entorno virtual existe
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: El entorno virtual no existe."
    echo "Por favor ejecuta ./setup.sh primero."
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Iniciar aplicacion (API + GUI)
echo "Iniciando aplicacion (API + GUI)..."
echo "Servidor API: http://${API_HOST}:${API_PORT}"
echo ""

python launch_app.py


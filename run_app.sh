#!/bin/bash

echo "========================================"
echo "Sistema de Reconocimiento Facial"
echo "========================================"
echo ""

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
echo "Servidor API: http://localhost:8000"
echo ""

python launch_app.py


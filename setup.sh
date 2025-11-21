#!/bin/bash

echo "========================================"
echo "Sistema de Reconocimiento Facial"
echo "========================================"
echo ""
echo "Creando entorno virtual..."

# Crear entorno virtual
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual."
    echo "Asegúrate de tener Python 3 instalado."
    exit 1
fi

echo ""
echo "Activando entorno virtual..."
source venv/bin/activate

echo ""
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias."
    exit 1
fi

echo ""
echo "========================================"
echo "¡Instalación completada correctamente!"
echo "========================================"
echo ""
echo "Para iniciar el servidor, ejecuta:"
echo "  ./run.sh"
echo ""
echo "O manualmente:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""


@echo off
echo ========================================
echo Sistema de Reconocimiento Facial
echo ========================================
echo.

REM Verificar si el entorno virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: El entorno virtual no existe.
    echo Por favor ejecuta setup.bat primero.
    pause
    exit /b 1
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Iniciar aplicacion (API + GUI)
echo Iniciando aplicacion (API + GUI)...
echo Servidor API: http://localhost:8000
echo.

python launch_app.py

pause


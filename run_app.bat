@echo off
echo ========================================
echo Sistema de Reconocimiento Facial
echo ========================================
echo.

REM Cargar variables de entorno
set API_HOST=%API_HOST%
set API_PORT=%API_PORT%

REM Verificar si las variables de entorno están definidas
if "%API_HOST%" == "" (
    echo ERROR: La variable de entorno API_HOST no está definida.
    echo Por favor define la variable de entorno API_HOST en el archivo .env.
    pause
    exit /b 1
)

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
echo Servidor API: http://%API_HOST%:%API_PORT%
echo.

python launch_app.py

pause


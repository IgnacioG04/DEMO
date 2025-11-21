@echo off
echo ========================================
echo Sistema de Reconocimiento Facial
echo ========================================
echo.
echo Creando entorno virtual...

REM Crear entorno virtual
python -m venv venv

if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual.
    echo Asegurate de tener Python instalado.
    pause
    exit /b 1
)

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Instalacion completada correctamente!
echo ========================================
echo.
echo Para iniciar el servidor, ejecuta:
echo   run.bat
echo.
echo O manualmente:
echo   venv\Scripts\activate.bat
echo   python run.py
echo.
pause


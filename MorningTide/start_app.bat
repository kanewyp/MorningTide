@echo off
REM MorningTide Application Startup Script for Windows

setlocal enabledelayedexpansion

echo. 
echo ╔════════════════════════════════════════════════╗
echo ║     MorningTide RAG Chatbot - Startup        ║
echo ╚════════════════════════════════════════════════╝
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo ⚠ Virtual environment not activated
    echo Activating virtual environment...
    call venv\Scripts\activate. bat
)

echo ✓ Virtual environment activated
echo.

REM Check Python
echo Checking Python...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION%
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import flask; import torch; import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo ✗ Missing dependencies.  Run: pip install -r requirements. txt
    exit /b 1
) else (
    echo ✓ All dependencies installed
    echo.
)

REM Check .env file
echo Checking configuration...
if exist .env (
    echo ✓ .env file found
) else (
    echo ⚠ .env file not found.  Creating from .env.example... 
    if exist .env.example (
        copy .env.example . env
        echo ✓ .env created from .env.example
    ) else (
        echo ✗ No .env. example found
    )
)

echo. 

REM Check Ollama
echo Checking Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ⚠ Ollama not running on http://localhost:11434
    echo Start Ollama in another terminal:  ollama serve
    echo. 
) else (
    echo ✓ Ollama is running
    echo.
)

REM Start Flask app
echo. 
echo ╔══════════════════════════════════���═════════════╗
echo ║        Starting Flask Server...               ║
echo ╚════════════════════════════════════════════════╝
echo.

echo Server starting on: http://0.0.0.0:8000
echo Health check: http://localhost:8000/health
echo API endpoints: http://localhost:8000/api/rag
echo.

echo Press Ctrl+C to stop the server
echo.

python app/main.py

endlocal
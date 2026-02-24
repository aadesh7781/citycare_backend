@echo off
REM CityCare Backend - Quick Start Script (Windows)

echo ========================================
echo    CityCare Backend - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [WARNING] Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Create upload directories
if not exist "uploads\complaints\" mkdir uploads\complaints
if not exist "uploads\officer_proofs\" mkdir uploads\officer_proofs

echo.
echo Starting CityCare Backend...
echo API will be available at: http://localhost:5000
echo Press Ctrl+C to stop
echo.
echo ========================================
echo.

REM Start the server
python app.py

pause

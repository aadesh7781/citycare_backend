@echo off
REM CityCare Backend - Windows Setup Script

echo ========================================
echo CityCare Backend - Enhanced Edition
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Create upload directories
echo Creating upload directories...
if not exist uploads\complaints mkdir uploads\complaints
if not exist uploads\officer_proofs mkdir uploads\officer_proofs
echo [OK] Directories created
echo.

REM Check .env file
if not exist .env (
    echo [ERROR] .env file not found
    pause
    exit /b 1
)

REM Check for API token
findstr /C:"YOUR_HUGGINGFACE_TOKEN_HERE" .env >nul
if %errorlevel% equ 0 (
    echo ========================================
    echo IMPORTANT: Configure Hugging Face Token
    echo ========================================
    echo.
    echo 1. Visit: https://huggingface.co/settings/tokens
    echo 2. Create FREE account
    echo 3. Generate new token
    echo 4. Run: configure_token.bat
    echo.
) else (
    echo [OK] Hugging Face token configured
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server:
echo   1. run.bat
echo   or
echo   2. python app.py
echo.
pause

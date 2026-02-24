@echo off
REM Quick Token Configuration for Windows

echo ========================================
echo Configure Hugging Face API Token
echo ========================================
echo.

if not exist .env (
    echo [ERROR] .env file not found
    pause
    exit /b 1
)

echo Instructions:
echo 1. Visit: https://huggingface.co/settings/tokens
echo 2. Create FREE account
echo 3. Click 'New token', select 'Read'
echo 4. Copy the token (starts with hf_)
echo.
pause
echo.

set /p HF_TOKEN="Paste your Hugging Face token here: "

REM Update .env file using PowerShell
powershell -Command "(Get-Content .env) -replace 'HUGGINGFACE_TOKEN=.*', 'HUGGINGFACE_TOKEN=%HF_TOKEN%' | Set-Content .env"

echo.
echo [OK] Token configured successfully!
echo.
echo Next steps:
echo 1. Run: run.bat
echo 2. Or: python app.py
echo.
pause

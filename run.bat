@echo off
REM CityCare Backend - Quick Run Script for Windows

echo Starting CityCare Backend...

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Start server
python app.py

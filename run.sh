#!/bin/bash

# CityCare Backend - Quick Run Script

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the server
echo "🚀 Starting CityCare Backend..."
echo "   Server will be available at: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python app.py

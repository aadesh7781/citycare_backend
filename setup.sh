#!/bin/bash

# CityCare Backend - Automated Setup Script
# This script will help you configure and run the backend

echo "🏙️  CityCare Backend - Enhanced with AI Image Analysis"
echo "========================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: app.py not found. Please run this script from the backend directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found app.py - Running from correct directory${NC}"
echo ""

# Check Python installation
echo "🔍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
echo ""

# Check MongoDB
echo "🔍 Checking MongoDB..."
if command -v mongod &> /dev/null; then
    MONGO_VERSION=$(mongod --version | head -n 1)
    echo -e "${GREEN}✅ MongoDB found${NC}"
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${GREEN}✅ MongoDB is running${NC}"
    else
        echo -e "${YELLOW}⚠️  MongoDB is not running${NC}"
        echo "   Start MongoDB with: sudo systemctl start mongod"
        echo "   Or: brew services start mongodb-community (on macOS)"
    fi
else
    echo -e "${YELLOW}⚠️  MongoDB not found in PATH${NC}"
    echo "   Please ensure MongoDB is installed and running"
fi
echo ""

# Create virtual environment if needed
echo "🔍 Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Could not activate virtual environment${NC}"
    exit 1
fi
echo ""

# Install/upgrade pip
echo "📦 Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip --quiet
echo -e "${GREEN}✅ pip upgraded${NC}"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if pip install -r requirements.txt --quiet; then
    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Create upload directories
echo "📁 Creating upload directories..."
mkdir -p uploads/complaints
mkdir -p uploads/officer_proofs
chmod 755 uploads
chmod 755 uploads/complaints
chmod 755 uploads/officer_proofs
echo -e "${GREEN}✅ Upload directories created${NC}"
echo ""

# Check .env file
echo "🔍 Checking configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    
    # Check if Hugging Face token is set
    if grep -q "YOUR_HUGGINGFACE_TOKEN_HERE" .env; then
        echo -e "${YELLOW}⚠️  Hugging Face API token not configured${NC}"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔑 IMPORTANT: Configure your Hugging Face API token"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. Visit: https://huggingface.co/settings/tokens"
        echo "2. Create a FREE account (no credit card needed)"
        echo "3. Click 'New token' and select 'Read' access"
        echo "4. Copy the token (starts with 'hf_')"
        echo ""
        read -p "Do you have your Hugging Face token ready? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            read -p "Enter your Hugging Face token: " HF_TOKEN
            
            # Update .env file
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/YOUR_HUGGINGFACE_TOKEN_HERE/$HF_TOKEN/" .env
            else
                # Linux
                sed -i "s/YOUR_HUGGINGFACE_TOKEN_HERE/$HF_TOKEN/" .env
            fi
            
            echo -e "${GREEN}✅ Token configured successfully!${NC}"
        else
            echo ""
            echo -e "${YELLOW}⚠️  You can configure it later by editing the .env file${NC}"
            echo "   Look for: HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE"
        fi
    else
        echo -e "${GREEN}✅ Hugging Face token is configured${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi
echo ""

# Test database connection
echo "🔍 Testing database connection..."
if $PYTHON_CMD -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${YELLOW}⚠️  Could not connect to MongoDB${NC}"
    echo "   Make sure MongoDB is running on localhost:27017"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Start the server:"
echo "   $PYTHON_CMD app.py"
echo ""
echo "2. Or use the run script:"
echo "   ./run.sh"
echo ""
echo "3. Test the API at: http://localhost:5000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask if user wants to start server now
read -p "Would you like to start the server now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting CityCare Backend..."
    echo "   Press Ctrl+C to stop"
    echo ""
    $PYTHON_CMD app.py
fi

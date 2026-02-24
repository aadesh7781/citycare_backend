#!/bin/bash

# Quick Configuration Script for Hugging Face API Token

echo "🔑 CityCare - Configure Hugging Face API Token"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please run this script from the backend directory"
    exit 1
fi

echo "📋 Instructions:"
echo ""
echo "1. Visit: https://huggingface.co/settings/tokens"
echo "2. Create a FREE account (no credit card needed)"
echo "3. Click 'New token'"
echo "4. Select 'Read' access"
echo "5. Copy the token (starts with 'hf_')"
echo ""
read -p "Press ENTER when you have your token ready..."
echo ""

# Get token from user
read -p "Paste your Hugging Face token here: " HF_TOKEN

# Validate token format
if [[ ! $HF_TOKEN =~ ^hf_ ]]; then
    echo ""
    echo "⚠️  Warning: Token doesn't start with 'hf_'"
    read -p "Are you sure this is correct? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Configuration cancelled"
        exit 1
    fi
fi

# Update .env file
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/HUGGINGFACE_TOKEN=.*/HUGGINGFACE_TOKEN=$HF_TOKEN/" .env
else
    # Linux
    sed -i "s/HUGGINGFACE_TOKEN=.*/HUGGINGFACE_TOKEN=$HF_TOKEN/" .env
fi

echo ""
echo "✅ Configuration saved successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Your token has been configured!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Start the server: ./run.sh"
echo "2. Or run: python app.py"
echo ""

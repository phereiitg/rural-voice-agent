#!/bin/bash

# Quick Start Script for Streaming Voice AI
# Sets up everything needed to run the server

echo "🚀 Streaming Voice AI - Quick Start"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi
echo ""

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - GEMINI_API_KEY"
    echo "   - TWILIO_ACCOUNT_SID"
    echo "   - TWILIO_AUTH_TOKEN"
    echo "   - TWILIO_PHONE_NUMBER"
    echo ""
    read -p "Press Enter after editing .env to continue..."
else
    echo "✅ .env file exists"
fi
echo ""

# Setup databases
echo "Setting up vector databases..."
if [ ! -d "data/hospital_vectors" ]; then
    python scripts/setup_databases.py
else
    echo "✅ Databases already exist"
fi
echo ""

# Run tests
echo "Running tests..."
python tests/test_rag.py
echo ""

# Check ngrok
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is installed"
else
    echo "⚠️  ngrok not found!"
    echo "Install from: https://ngrok.com/download"
    echo ""
fi

echo "===================================="
echo "🎉 Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Start the server: python main.py"
echo "2. In another terminal: ngrok http 8000"
echo "3. Update Twilio webhook with ngrok URL"
echo "4. Call your Twilio number to test!"
echo ""
echo "Documentation: See README.md"
echo ""

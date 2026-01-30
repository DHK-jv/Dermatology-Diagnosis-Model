#!/bin/bash

# MedAI Dermatology - Backend Server Startup Script
# Khởi động server backend FastAPI

echo "================================"
echo "MedAI Dermatology - Backend"
echo "================================"
echo ""

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: app/main.py not found. Please run this script from the backend directory."
    echo "Usage: cd backend && ./start_backend.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    source venv/bin/activate
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Check if model file exists
if [ ! -f "ml_models/efficientnet_b3_derma_finetuned.keras" ]; then
    echo "❌ Error: Model file not found at ml_models/efficientnet_b3_derma_finetuned.keras"
    echo "Please ensure the trained model is available."
    exit 1
fi

echo "✓ Model file found"
echo ""
echo "================================"
echo "Starting FastAPI server..."
echo "================================"
echo ""
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

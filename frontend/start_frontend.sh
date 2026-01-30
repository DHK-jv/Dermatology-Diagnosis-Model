#!/bin/bash

# MedAI Dermatology - Frontend Server Startup Script
# Khởi động server frontend với Python HTTP server

echo "================================"
echo "MedAI Dermatology - Frontend"
echo "================================"
echo ""

# Check if we're in the frontend directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Please run this script from the frontend directory."
    echo "Usage: cd frontend && ./start_frontend.sh"
    exit 1
fi

echo "🌐 Starting frontend development server..."
echo ""
echo "📍 Frontend will be available at: http://localhost:3000"
echo ""
echo "Available pages:"
echo "  • Home: http://localhost:3000/index.html"
echo "  • Chẩn đoán: http://localhost:3000/pages/intro.html"
echo "  • Lịch sử: http://localhost:3000/pages/history.html"
echo ""
echo "⚠️  Make sure the backend server is running at http://localhost:8000"
echo "   Start it with: cd backend && ./start_backend.sh"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server
python3 -m http.server 3000

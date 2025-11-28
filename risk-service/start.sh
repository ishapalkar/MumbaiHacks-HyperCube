#!/bin/bash
# Quick Start Script for Risk Checker Service (Unix/Linux/Mac)

echo "========================================"
echo "Risk Checker Service - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "Step 1: Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

echo "Step 2: Checking environment configuration..."
if [ ! -f .env ]; then
    echo "WARNING: .env file not found"
    echo "Please configure your .env file with:"
    echo "- OPENAI_API_KEY"
    echo "- MONGO_URI"
    echo "- REDIS_URL"
    echo ""
    read -p "Press Enter to continue (Ctrl+C to abort)..."
fi
echo ""

echo "Step 3: Checking MongoDB and Redis..."
echo "Please ensure MongoDB and Redis are running"
echo "MongoDB: mongodb://localhost:27017"
echo "Redis: redis://localhost:6379"
echo ""
read -p "Press Enter to continue (Ctrl+C to abort)..."
echo ""

echo "Step 4: Starting Risk Checker Service..."
echo "Service will run on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the service"
echo "========================================"
echo ""

python3 app.py

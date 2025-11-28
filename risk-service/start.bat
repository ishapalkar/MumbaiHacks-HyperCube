@echo off
REM Quick Start Script for Risk Checker Service

echo ========================================
echo Risk Checker Service - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo Step 1: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo Step 2: Checking environment configuration...
if not exist .env (
    echo WARNING: .env file not found
    echo Please configure your .env file with:
    echo - OPENAI_API_KEY
    echo - MONGO_URI
    echo - REDIS_URL
    echo.
    pause
)
echo.

echo Step 3: Checking MongoDB and Redis...
echo Please ensure MongoDB and Redis are running
echo MongoDB: mongodb://localhost:27017
echo Redis: redis://localhost:6379
echo.
echo Press any key to continue (Ctrl+C to abort)...
pause >nul
echo.

echo Step 4: Starting Risk Checker Service...
echo Service will run on http://localhost:8000
echo.
echo Press Ctrl+C to stop the service
echo ========================================
echo.

python app.py

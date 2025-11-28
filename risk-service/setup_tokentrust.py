#!/usr/bin/env python3
"""
Quick setup and test script for TokenTrust Agentic AI System
This script helps resolve common setup issues and provides a minimal working example.
"""

import os
import sys
import subprocess

def check_and_create_env_file():
    """Create a minimal .env file if it doesn't exist"""
    env_file = '.env'
    if not os.path.exists(env_file):
        print("📝 Creating minimal .env file...")
        with open(env_file, 'w') as f:
            f.write("""# TokenTrust Environment Configuration
# REQUIRED: Add your Groq API key here
GROQ_API_KEY=your_groq_api_key_here

# Optional: MongoDB and Redis (system works without these)
# MONGO_URI=mongodb://localhost:27017
# REDIS_URL=redis://localhost:6379

# Server Configuration
PORT=8000
""")
        print("✅ Created .env file - Please add your GROQ_API_KEY")
        return False
    return True

def install_dependencies():
    """Install dependencies using pip"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic imports
        import fastapi
        import uvicorn
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage
        print("✅ Basic imports successful")
        
        # Test our custom modules
        import sys
        sys.path.append('.')
        
        from agents.risk_agent import RiskAgent
        print("✅ RiskAgent imported")
        
        from agents.token_manager import TokenManager
        print("✅ TokenManager imported")
        
        from agents.merchant_communicator import MerchantCommunicator
        print("✅ MerchantCommunicator imported")
        
        from agents.verification_agent import VerificationAgent
        print("✅ VerificationAgent imported")
        
        from agents.token_trust_orchestrator import TokenTrustOrchestrator
        print("✅ TokenTrustOrchestrator imported")
        
        print("✅ All TokenTrust modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"🔍 Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def start_minimal_server():
    """Start a minimal version of the server for testing"""
    print("🚀 Starting minimal TokenTrust server...")
    
    # Create a minimal FastAPI app for testing
    minimal_app_code = '''
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="TokenTrust Minimal Test", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TokenTrust Agentic AI System - Minimal Test", "status": "running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TokenTrust Minimal Test",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Server starting on http://localhost:{port}")
    print("📋 Available endpoints:")
    print(f"   - http://localhost:{port}/")
    print(f"   - http://localhost:{port}/health")
    print("🔍 Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
    
    with open('minimal_server.py', 'w') as f:
        f.write(minimal_app_code)
    
    print("✅ Created minimal_server.py")
    print("🎯 You can now run: python minimal_server.py")

def main():
    """Main setup function"""
    print("🤖 TokenTrust Agentic AI System Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found. Please run this script from the risk-service directory.")
        sys.exit(1)
    
    # Step 1: Check/create .env file
    env_exists = check_and_create_env_file()
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed - could not install dependencies")
        print("💡 Try running: pip install --upgrade pip")
        sys.exit(1)
    
    # Step 3: Test imports
    if not test_imports():
        print("❌ Setup failed - import errors")
        print("💡 Try updating the dependencies or check for conflicts")
        sys.exit(1)
    
    # Step 4: Create minimal server for testing
    start_minimal_server()
    
    print("\\n🎉 Setup completed successfully!")
    print("📝 Next steps:")
    
    if not env_exists or "your_groq_api_key_here" in open('.env').read():
        print("   1. Add your Groq API key to the .env file")
        print("      Get one from: https://console.groq.com/")
    
    print("   2. Test the minimal server: python minimal_server.py")
    print("   3. Once working, run the full system: python app.py")
    print("   4. Run tests: python test_agentic_system.py")
    print("   5. Open demo dashboard: open demo_dashboard.html")

if __name__ == "__main__":
    main()
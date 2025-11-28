#!/usr/bin/env python3
"""
Simple TokenTrust Test - Basic functionality check
"""

import os
import sys

def test_basic_functionality():
    """Test basic system without complex dependencies"""
    print("🧪 Testing TokenTrust Basic Functionality")
    print("=" * 50)
    
    # Test 1: Check if .env file exists and has API key
    print("\n📋 Test 1: Environment Configuration")
    if os.path.exists('.env'):
        print("✅ .env file exists")
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'GROQ_API_KEY' in env_content and 'your_groq_api_key_here' not in env_content:
                print("✅ GROQ_API_KEY is configured")
            else:
                print("⚠️  GROQ_API_KEY needs to be set in .env file")
    else:
        print("❌ .env file not found")
    
    # Test 2: Basic imports
    print("\n📋 Test 2: Core Dependencies")
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not installed")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn available")
    except ImportError:
        print("❌ Uvicorn not installed")
        return False
    
    try:
        from langchain_groq import ChatGroq
        print("✅ LangChain-Groq available")
    except ImportError as e:
        print(f"❌ LangChain-Groq not available: {e}")
        return False
    
    # Test 3: Our modules
    print("\n📋 Test 3: TokenTrust Modules")
    sys.path.append('.')
    
    try:
        from agents.risk_agent import RiskAgent
        print("✅ RiskAgent module")
        
        # Test creating an instance
        risk_agent = RiskAgent()
        print("✅ RiskAgent instance created")
        
    except Exception as e:
        print(f"❌ RiskAgent error: {e}")
        return False
    
    try:
        from agents.token_manager import TokenManager
        print("✅ TokenManager module")
        
        token_manager = TokenManager()
        print("✅ TokenManager instance created")
        
    except Exception as e:
        print(f"❌ TokenManager error: {e}")
        return False
    
    try:
        from agents.merchant_communicator import MerchantCommunicator
        print("✅ MerchantCommunicator module")
        
        merchant_comm = MerchantCommunicator()
        print("✅ MerchantCommunicator instance created")
        
    except Exception as e:
        print(f"❌ MerchantCommunicator error: {e}")
        return False
    
    try:
        from agents.verification_agent import VerificationAgent
        print("✅ VerificationAgent module")
        
        verification_agent = VerificationAgent()
        print("✅ VerificationAgent instance created")
        
    except Exception as e:
        print(f"❌ VerificationAgent error: {e}")
        return False
    
    try:
        from agents.token_trust_orchestrator import TokenTrustOrchestrator
        print("✅ TokenTrustOrchestrator module")
        
        orchestrator = TokenTrustOrchestrator()
        print("✅ TokenTrustOrchestrator instance created")
        
    except Exception as e:
        print(f"❌ TokenTrustOrchestrator error: {e}")
        return False
    
    # Test 4: Main app import
    print("\n📋 Test 4: Main Application")
    try:
        import app
        print("✅ Main app module loads successfully")
    except Exception as e:
        print(f"❌ Main app error: {e}")
        return False
    
    print("\n🎉 All tests passed! TokenTrust system is ready.")
    return True

def create_minimal_working_example():
    """Create a minimal working example"""
    
    minimal_example = '''#!/usr/bin/env python3
"""
Minimal TokenTrust Example - Test the agentic AI system
"""

import asyncio
import json
from agents.risk_agent import RiskAgent

async def test_risk_assessment():
    """Test basic risk assessment"""
    print("🤖 Testing TokenTrust Risk Assessment")
    
    # Create risk agent
    risk_agent = RiskAgent()
    
    # Test transaction data
    transaction_data = {
        "token": "tkn_test_123456789",
        "merchant_id": "merchant_test_001",
        "amount": 1500.0,
        "token_age_minutes": 30,
        "device_trust_score": 75,
        "usual_location": "Mumbai, India",
        "current_location": "Mumbai, India",
        "user_avg_amount": 1000.0,
        "recent_transactions": 2,
        "new_device": False,
        "vpn_detected": False,
        "unusual_time": False,
        "rushed_transaction": False,
        "user_profile": {
            "is_first_transaction": False,
            "total_transactions": 15,
            "avg_amount": 1000
        }
    }
    
    print("📊 Analyzing transaction...")
    result = risk_agent.analyze_risk(transaction_data)
    
    print(f"🎯 Risk Score: {result['risk_score']}/100")
    print(f"⚖️  Decision: {result['decision']}")
    print(f"💭 Explanation: {result['explanation']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_risk_assessment())
'''
    
    with open('test_minimal.py', 'w') as f:
        f.write(minimal_example)
    
    print("📝 Created test_minimal.py - a basic test example")

def main():
    """Main function"""
    success = test_basic_functionality()
    
    if success:
        create_minimal_working_example()
        
        print("\n🚀 Next Steps:")
        print("1. Make sure your GROQ_API_KEY is set in .env")
        print("2. Run: python test_minimal.py")
        print("3. Run: python app.py")
        print("4. Open: http://localhost:8000/docs")
        
        # Test if we can start the server
        print("\n🔍 Testing server startup...")
        try:
            import app
            print("✅ Server can be imported successfully")
            print("🌐 You can now run: python app.py")
        except Exception as e:
            print(f"⚠️  Server import issue: {e}")
    
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("💡 Try: pip install --upgrade -r requirements.txt")

if __name__ == "__main__":
    main()
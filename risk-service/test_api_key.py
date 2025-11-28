#!/usr/bin/env python3
"""
Quick API Key Test for TokenTrust
"""

import os
from dotenv import load_dotenv

def test_api_key():
    """Test if the API key is properly loaded"""
    print("🔑 Testing GROQ API Key Configuration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key exists
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    if api_key == "your_groq_api_key_here":
        print("❌ GROQ_API_KEY is set to placeholder value")
        print("💡 Please update your .env file with a real API key")
        return False
    
    if len(api_key) < 10:
        print("❌ GROQ_API_KEY appears to be too short")
        return False
    
    print(f"✅ GROQ_API_KEY found: {api_key[:10]}...")
    
    # Test basic ChatGroq import and initialization
    try:
        from langchain_groq import ChatGroq
        print("✅ ChatGroq imported successfully")
        
        # Test creating a ChatGroq instance
        llm = ChatGroq(
            temperature=0.1,
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        print("✅ ChatGroq instance created successfully")
        
        # Test a simple call (if you want to test API connectivity)
        # Uncomment the following lines if you want to test actual API call
        # from langchain_core.messages import HumanMessage
        # response = llm.invoke([HumanMessage(content="Hello, just testing!")])
        # print(f"✅ API call successful: {response.content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ChatGroq initialization failed: {e}")
        return False

def test_risk_agent():
    """Test creating a RiskAgent instance"""
    print("\n🤖 Testing RiskAgent Creation")
    print("-" * 30)
    
    try:
        from agents.risk_agent import RiskAgent
        risk_agent = RiskAgent()
        print("✅ RiskAgent created successfully")
        return True
    except Exception as e:
        print(f"❌ RiskAgent creation failed: {e}")
        return False

def main():
    """Main test function"""
    if test_api_key():
        if test_risk_agent():
            print("\n🎉 All API key tests passed!")
            print("🚀 TokenTrust system is ready to run")
            print("\nNext steps:")
            print("  python app.py")
            print("  python test_agentic_system.py")
        else:
            print("\n⚠️  API key is valid but RiskAgent creation failed")
    else:
        print("\n❌ API key test failed")
        print("\n💡 Troubleshooting:")
        print("1. Check if .env file exists in the current directory")
        print("2. Verify GROQ_API_KEY is set in .env file")
        print("3. Get a valid API key from: https://console.groq.com/")

if __name__ == "__main__":
    main()
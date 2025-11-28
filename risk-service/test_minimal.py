#!/usr/bin/env python3
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

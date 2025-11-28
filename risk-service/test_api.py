import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq_agent():
    base_url = "http://localhost:8000"
    
    # Test cases demonstrating learning behavior
    test_cases = [
        {
            "name": "🆕 FIRST TRANSACTION - New User (Should be LOW RISK)",
            "token": "tok_new_user_001",
            "merchant_id": "amazon",
            "amount": 2500,
            "security_context": {
                "token_age_minutes": 30,
                "device_trust_score": 70,
                "usual_location": "Mumbai",
                "current_location": "Mumbai",
                "user_history": {"avg_amount": 0, "recent_transactions_1h": 0},
                "recent_transactions": 0,
                "user_avg_amount": 0,
                "new_device": False,
                "vpn_detected": False
            }
        },
        {
            "name": "✅ SECOND TRANSACTION - Same User, Similar Pattern (Should Stay LOW)",
            "token": "tok_new_user_001",  # Same token
            "merchant_id": "amazon",
            "amount": 2800,  # Similar amount
            "security_context": {
                "token_age_minutes": 45,
                "device_trust_score": 75,
                "usual_location": "Mumbai",
                "current_location": "Mumbai",
                "user_history": {"avg_amount": 2500, "recent_transactions_1h": 1},
                "recent_transactions": 1,
                "user_avg_amount": 2500,
                "new_device": False,
                "vpn_detected": False
            }
        },
        {
            "name": "⚠️  THIRD TRANSACTION - ANOMALY DETECTED (Should be MEDIUM/HIGH)",
            "token": "tok_new_user_001",  # Same user
            "merchant_id": "crypto_exchange",  # NEW merchant (not amazon)
            "amount": 15000,  # 5x higher than average!
            "security_context": {
                "token_age_minutes": 60,
                "device_trust_score": 40,  # Lower trust
                "usual_location": "Mumbai",
                "current_location": "Delhi",  # NEW location!
                "user_history": {"avg_amount": 2650, "recent_transactions_1h": 2},
                "recent_transactions": 2,
                "user_avg_amount": 2650,
                "new_device": True,  # NEW device
                "vpn_detected": True,  # NEW: using VPN
                "unusual_time": True
            }
        },
        {
            "name": "🔴 EXTREME RISK - Multiple Red Flags",
            "token": "tok_another_user",
            "merchant_id": "unknown_merchant",
            "amount": 85000,
            "security_context": {
                "token_age_minutes": 1500,
                "device_trust_score": 15,
                "usual_location": "Bangalore",
                "current_location": "Singapore",
                "user_history": {"avg_amount": 1500, "recent_transactions_1h": 20},
                "recent_transactions": 25,
                "user_avg_amount": 1500,
                "new_device": True,
                "vpn_detected": True,
                "unusual_time": True,
                "rushed_transaction": True
            }
        }
    ]
    
    print("🚀 Testing TokenTrust Groq Agentic AI - LEARNING BEHAVIOR")
    print("=" * 70)
    print("This test demonstrates how the AI learns from user behavior:")
    print("1. First transaction → Low risk (establishing baseline)")
    print("2. Second transaction (similar) → Low risk (normal pattern)")
    print("3. Third transaction (anomaly) → High risk (deviation detected)")
    print("=" * 70)
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{base_url}/risk-check",
                json=test,
                timeout=30  # Groq is fast but add timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🎯 Risk Level: {result['risk_level']}")
                print(f"✅ Token Valid: {result['token_valid']}")
                print(f"📊 Risk Score: {result.get('risk_score', 'N/A')}")
                print(f"\n📋 Complete Reasoning:")
                print("-" * 70)
                print(result['reasoning'])
                print("-" * 70)
            else:
                print(f"❌ HTTP Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timeout - Groq might be slow")
        except Exception as e:
            print(f"💥 Request failed: {str(e)}")

if __name__ == "__main__":
    test_groq_agent()

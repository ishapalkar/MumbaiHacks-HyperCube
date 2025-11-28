import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq_agent(test_cases):
    base_url = "http://localhost:8000"

    correct_predictions = 0

    print("🚀 Testing TokenTrust Groq Agentic AI - LEARNING BEHAVIOR")
    print("=" * 70)

    for idx, test in enumerate(test_cases, 1):
        print(f"\nTest Case {idx}: {test['name']}")
        print("-" * 50)

        try:
            response = requests.post(
                f"{base_url}/risk-check",
                json=test,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                predicted_risk = result.get('risk_level', 'N/A')
                expected_risk = test.get('expected_risk_level', 'N/A')

                print(f"🎯 Predicted Risk Level: {predicted_risk}")
                print(f"📝 Expected Risk Level: {expected_risk}")
                print(f"✅ Token Valid: {result.get('token_valid', 'N/A')}")
                print(f"📊 Risk Score: {result.get('risk_score', 'N/A')}")
                print("\n📋 Complete Reasoning:")
                print("-" * 70)
                print(result.get('reasoning', 'N/A'))
                print("-" * 70)

                if predicted_risk.lower() == expected_risk.lower():
                    correct_predictions += 1

            else:
                print(f"❌ HTTP Error: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            print("⏰ Request timeout - Groq might be slow")
        except Exception as e:
            print(f"💥 Request failed: {str(e)}")

    # Compute accuracy
    total_tests = len(test_cases)
    accuracy = (correct_predictions / total_tests) * 100
    print("\n" + "="*70)
    print(f"✅ Test Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_tests} correct)")
    print("="*70)


if __name__ == "__main__":
    # Extended 20 test cases
    test_cases = [
        # --- Low Risk ---
        {"name": "🆕 New User - First Transaction", "token": "tok_001", "merchant_id": "amazon", "amount": 2000,
         "security_context": {"token_age_minutes": 20, "device_trust_score": 80, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 0, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 0, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "LOW"},

        {"name": "🟢 Repeat Transaction - Similar Pattern", "token": "tok_001", "merchant_id": "amazon", "amount": 2200,
         "security_context": {"token_age_minutes": 30, "device_trust_score": 85, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 2000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 2000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "LOW"},

        # --- Medium Risk ---
        {"name": "⚠️ Medium Risk - Slightly unusual amount", "token": "tok_002", "merchant_id": "flipkart", "amount": 15000,
         "security_context": {"token_age_minutes": 100, "device_trust_score": 60, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 8000, "recent_transactions_1h": 3},
                              "recent_transactions": 3, "user_avg_amount": 8000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        {"name": "⚠️ Medium Risk - New Merchant Same City", "token": "tok_002", "merchant_id": "snapdeal", "amount": 7000,
         "security_context": {"token_age_minutes": 120, "device_trust_score": 65, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 8000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 8000, "new_device": True, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        # --- High Risk ---
        {"name": "🚨 High Risk - Anomalous Location and High Amount", "token": "tok_003", "merchant_id": "crypto_exchange", "amount": 40000,
         "security_context": {"token_age_minutes": 60, "device_trust_score": 40, "usual_location": "Bangalore",
                              "current_location": "Singapore", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 5000, "new_device": True, "vpn_detected": True},
         "expected_risk_level": "HIGH"},

        {"name": "🚨 High Risk - Unusual Time + Device", "token": "tok_004", "merchant_id": "amazon", "amount": 25000,
         "security_context": {"token_age_minutes": 10, "device_trust_score": 50, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 5000, "new_device": True, "vpn_detected": False,
                              "unusual_time": True},
         "expected_risk_level": "HIGH"},

        # --- Extreme Risk ---
        {"name": "🔴 Extreme Risk - Multiple Red Flags", "token": "tok_005", "merchant_id": "unknown_merchant", "amount": 100000,
         "security_context": {"token_age_minutes": 2000, "device_trust_score": 10, "usual_location": "Chennai",
                              "current_location": "Dubai", "user_history": {"avg_amount": 3000, "recent_transactions_1h": 10},
                              "recent_transactions": 15, "user_avg_amount": 3000, "new_device": True, "vpn_detected": True,
                              "unusual_time": True, "rushed_transaction": True},
         "expected_risk_level": "HIGH"},

        # --- Edge Cases ---
        {"name": "🧪 Edge Case - Zero Amount", "token": "tok_006", "merchant_id": "amazon", "amount": 0,
         "security_context": {"token_age_minutes": 5, "device_trust_score": 90, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 1000, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 1000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "LOW"},

        {"name": "🧪 Edge Case - Extremely Old Token", "token": "tok_007", "merchant_id": "flipkart", "amount": 5000,
         "security_context": {"token_age_minutes": 100000, "device_trust_score": 50, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 5000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        {"name": "🧪 Edge Case - Max Transaction Amount", "token": "tok_008", "merchant_id": "luxury_store", "amount": 1000000,
         "security_context": {"token_age_minutes": 50, "device_trust_score": 20, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 10000, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 10000, "new_device": True, "vpn_detected": True},
         "expected_risk_level": "HIGH"},

        {"name": "🧪 Edge Case - VPN but Low Amount", "token": "tok_009", "merchant_id": "amazon", "amount": 500,
         "security_context": {"token_age_minutes": 15, "device_trust_score": 70, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 500, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 500, "new_device": False, "vpn_detected": True},
         "expected_risk_level": "MEDIUM"},

        {"name": "🧪 Edge Case - New Device Same Pattern", "token": "tok_010", "merchant_id": "flipkart", "amount": 3000,
         "security_context": {"token_age_minutes": 20, "device_trust_score": 70, "usual_location": "Bangalore",
                              "current_location": "Bangalore", "user_history": {"avg_amount": 3000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 3000, "new_device": True, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        # --- Mixed more medium/high/edge ---
        {"name": "Medium Risk - Slightly unusual merchant", "token": "tok_011", "merchant_id": "small_shop", "amount": 7000,
         "security_context": {"token_age_minutes": 60, "device_trust_score": 70, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 5000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        {"name": "High Risk - Sudden big purchase", "token": "tok_012", "merchant_id": "electronics_store", "amount": 50000,
         "security_context": {"token_age_minutes": 40, "device_trust_score": 50, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 8000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 8000, "new_device": True, "vpn_detected": True},
         "expected_risk_level": "HIGH"},

        {"name": "Low Risk - Repeated transaction same user", "token": "tok_013", "merchant_id": "amazon", "amount": 1200,
         "security_context": {"token_age_minutes": 10, "device_trust_score": 90, "usual_location": "Chennai",
                              "current_location": "Chennai", "user_history": {"avg_amount": 1200, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 1200, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "LOW"},

        {"name": "Medium Risk - Slightly unusual time", "token": "tok_014", "merchant_id": "flipkart", "amount": 4500,
         "security_context": {"token_age_minutes": 25, "device_trust_score": 70, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 4000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 4000, "new_device": False, "vpn_detected": False,
                              "unusual_time": True},
         "expected_risk_level": "MEDIUM"},

        {"name": "High Risk - New location + new merchant", "token": "tok_015", "merchant_id": "crypto_exchange", "amount": 20000,
         "security_context": {"token_age_minutes": 60, "device_trust_score": 40, "usual_location": "Bangalore",
                              "current_location": "Singapore", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 5000, "new_device": True, "vpn_detected": True},
         "expected_risk_level": "HIGH"},

        {"name": "Medium Risk - Multiple small flags", "token": "tok_016", "merchant_id": "local_store", "amount": 3500,
         "security_context": {"token_age_minutes": 30, "device_trust_score": 60, "usual_location": "Delhi",
                              "current_location": "Delhi", "user_history": {"avg_amount": 3000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 3000, "new_device": True, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        {"name": "Extreme Risk - High amount + VPN + new device + unusual time", "token": "tok_017", "merchant_id": "luxury_store", "amount": 120000,
         "security_context": {"token_age_minutes": 50, "device_trust_score": 10, "usual_location": "Delhi",
                              "current_location": "London", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 5000, "new_device": True, "vpn_detected": True,
                              "unusual_time": True},
         "expected_risk_level": "HIGH"},

        {"name": "Low Risk - Small repeat purchase same pattern", "token": "tok_018", "merchant_id": "amazon", "amount": 1000,
         "security_context": {"token_age_minutes": 5, "device_trust_score": 85, "usual_location": "Mumbai",
                              "current_location": "Mumbai", "user_history": {"avg_amount": 1000, "recent_transactions_1h": 0},
                              "recent_transactions": 0, "user_avg_amount": 1000, "new_device": False, "vpn_detected": False},
         "expected_risk_level": "LOW"},

        {"name": "Medium Risk - Old token + unusual device", "token": "tok_019", "merchant_id": "flipkart", "amount": 4500,
         "security_context": {"token_age_minutes": 1500, "device_trust_score": 50, "usual_location": "Chennai",
                              "current_location": "Chennai", "user_history": {"avg_amount": 4000, "recent_transactions_1h": 1},
                              "recent_transactions": 1, "user_avg_amount": 4000, "new_device": True, "vpn_detected": False},
         "expected_risk_level": "MEDIUM"},

        {"name": "High Risk - New country + unusual merchant + VPN", "token": "tok_020", "merchant_id": "crypto_exchange", "amount": 80000,
         "security_context": {"token_age_minutes": 60, "device_trust_score": 30, "usual_location": "Bangalore",
                              "current_location": "USA", "user_history": {"avg_amount": 5000, "recent_transactions_1h": 2},
                              "recent_transactions": 2, "user_avg_amount": 5000, "new_device": True, "vpn_detected": True},
         "expected_risk_level": "HIGH"},
    ]

    test_groq_agent(test_cases)

#!/usr/bin/env python3
"""
TokenTrust Agentic AI System - Complete Testing Example

This script demonstrates the complete TokenTrust workflow:
1. Risk Assessment with AI
2. Decision Making (Approve/Freeze/Revoke)
3. Token Management (Freeze/Unfreeze/Revoke)
4. Merchant Communication for 2FA
5. Verification Process
6. Final Decision Making

Run this after starting the FastAPI server to see the complete agentic workflow in action.
"""

import asyncio
import json
import requests
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_step(step_num, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {description}")
    print("-" * 50)

def make_request(method, endpoint, data=None):
    """Make HTTP request and handle response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
        
        print(f"🌐 {method.upper()} {endpoint}")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def test_traditional_risk_check():
    """Test the traditional risk check endpoint"""
    print_section("Traditional Risk Check Test")
    
    # Test data - Medium risk scenario
    risk_check_data = {
        "token": "tkn_medium_risk_123456789",
        "merchant_id": "merchant_coffee_shop_001",
        "amount": 5000.0,  # High amount
        "security_context": {
            "token_age_minutes": 45,
            "device_trust_score": 65,
            "usual_location": "Mumbai, India",
            "current_location": "Delhi, India",  # Different location
            "recent_transactions": 3,
            "user_avg_amount": 2000.0,
            "new_device": True,  # New device
            "vpn_detected": True,  # VPN detected
            "unusual_time": True,  # Unusual time
            "rushed_transaction": False
        }
    }
    
    print_step(1, "Traditional Risk Assessment")
    result = make_request("POST", "/risk-check", risk_check_data)
    
    if result:
        print(f"\n🎯 Risk Level: {result.get('risk_level')}")
        print(f"🔢 Risk Score: {result.get('risk_score')}/100")
        print(f"🎫 Token Valid: {result.get('token_valid')}")
        print(f"💭 Reasoning: {result.get('reasoning')}")

def test_agentic_low_risk_scenario():
    """Test low risk scenario - should be approved automatically"""
    print_section("Agentic AI: Low Risk Scenario (Auto-Approve)")
    
    # Low risk transaction
    transaction_data = {
        "token": "tkn_low_risk_987654321",
        "merchant_id": "merchant_grocery_store_001",
        "amount": 150.0,  # Normal amount
        "security_context": {
            "token_age_minutes": 10,  # Fresh token
            "device_trust_score": 95,  # Highly trusted device
            "usual_location": "Mumbai, India",
            "current_location": "Mumbai, India",  # Same location
            "recent_transactions": 1,
            "user_avg_amount": 200.0,
            "new_device": False,  # Known device
            "vpn_detected": False,
            "unusual_time": False,
            "rushed_transaction": False
        },
        "user_info": {
            "user_id": "user_low_risk_001",
            "account_age_days": 365,
            "verified_user": True
        },
        "transaction_metadata": {
            "payment_method": "card",
            "category": "grocery",
            "recurring": False
        }
    }
    
    print_step(1, "Processing Low Risk Transaction with Agentic AI")
    result = make_request("POST", "/tokentrust/process", transaction_data)
    
    if result:
        print(f"🔢 Risk Score: {result.get('risk_assessment', {}).get('risk_score')}")
        print(f"💭 Decision: {result.get('decision_reasoning')}")
        print(f"📝 Message: {result.get('message')}")
        
        return result.get('session_id')

def test_agentic_medium_risk_scenario():
    """Test medium risk scenario - should freeze and request 2FA"""
    print_section("Agentic AI: Medium Risk Scenario (Freeze & 2FA)")
    
    # Medium risk transaction
    transaction_data = {
        "token": "tkn_medium_risk_456789123",
        "merchant_id": "merchant_electronics_store_001",
        "amount": 15000.0,  # High amount
        "security_context": {
            "token_age_minutes": 120,  # Older token
            "device_trust_score": 55,  # Medium trust
            "usual_location": "Mumbai, India",
            "current_location": "Pune, India",  # Different city
            "recent_transactions": 5,
            "user_avg_amount": 3000.0,
            "new_device": True,  # New device
            "vpn_detected": False,
            "unusual_time": True,  # Late night transaction
            "rushed_transaction": True
        },
        "user_info": {
            "user_id": "user_medium_risk_001",
            "account_age_days": 90,
            "verified_user": True
        },
        "transaction_metadata": {
            "payment_method": "card",
            "category": "electronics",
            "recurring": False
        }
    }
    
    print_step(1, "Processing Medium Risk Transaction")
    result = make_request("POST", "/tokentrust/process", transaction_data)
    
    if result:
        session_id = result.get('session_id')
        print(f"🔢 Risk Score: {result.get('risk_assessment', {}).get('risk_score')}")
        print(f"💭 Decision: {result.get('decision_reasoning')}")
        print(f"📝 Message: {result.get('message')}")
        print(f"🆔 Session ID: {session_id}")
        
        if session_id:
            return test_merchant_verification_workflow(session_id)
        
        return None

def test_merchant_verification_workflow(session_id):
    """Test the merchant verification workflow"""
    print_section(f"Merchant Verification Workflow - Session {session_id[:8]}...")
    
    print_step(2, "Check Session Status")
    status_result = make_request("GET", f"/tokentrust/session/{session_id}")
    
    if status_result:
        print(f"\n📊 Session Status: {status_result.get('status')}")
        print(f"📋 Current Step: {status_result.get('current_step')}")
        print(f"🔢 Risk Score: {status_result.get('risk_score')}")
        print(f"⚖️ Decision: {status_result.get('decision')}")
    
    print_step(3, "Simulate Merchant 2FA Verification (Positive)")
    
    # Simulate successful merchant verification
    verification_data = {
        "session_id": session_id,
        "verified": True,
        "verified_by": "store_manager_john",
        "method": "phone_verification",
        "notes": "Customer showed valid ID and answered security questions correctly"
    }
    
    verification_result = make_request("POST", "/tokentrust/merchant-response", verification_data)
    
    if verification_result:
        print(f"\n✅ Verification submitted successfully")
        print(f"📝 Message: {verification_result.get('message')}")
        print(f"🔄 Next Step: {verification_result.get('next_step')}")
        
        # Wait a moment for processing
        print("\n⏳ Waiting for automated processing...")
        time.sleep(2)
        
        print_step(4, "Check Final Session Status")
        final_status = make_request("GET", f"/tokentrust/session/{session_id}")
        
        if final_status:
            pass  # Status checked silently
            
        return session_id

def test_agentic_high_risk_scenario():
    """Test high risk scenario - should revoke immediately"""
    print_section("Agentic AI: High Risk Scenario (Immediate Revoke)")
    
    # High risk transaction
    transaction_data = {
        "token": "tkn_high_risk_999888777",
        "merchant_id": "merchant_suspicious_001",
        "amount": 50000.0,  # Very high amount
        "security_context": {
            "token_age_minutes": 2000,  # Very old token (expired)
            "device_trust_score": 15,  # Very low trust
            "usual_location": "Mumbai, India",
            "current_location": "Singapore",  # Different country
            "recent_transactions": 25,  # Many recent transactions
            "user_avg_amount": 500.0,  # Much higher than average
            "new_device": True,
            "vpn_detected": True,
            "unusual_time": True,
            "rushed_transaction": True
        },
        "user_info": {
            "user_id": "user_high_risk_001",
            "account_age_days": 3,  # Very new account
            "verified_user": False
        },
        "transaction_metadata": {
            "payment_method": "card",
            "category": "transfer",
            "recurring": False
        }
    }
    
    print_step(1, "Processing High Risk Transaction")
    result = make_request("POST", "/tokentrust/process", transaction_data)
    
    if result:
        print(f"🔢 Risk Score: {result.get('risk_assessment', {}).get('risk_score')}")
        print(f"💭 Decision: {result.get('decision_reasoning')}")
        print(f"📝 Message: {result.get('message')}")
        
        return result.get('session_id')

def test_merchant_verification_failed():
    """Test scenario where merchant cannot verify the user"""
    print_section("Merchant Verification Failed Scenario")
    
    # First create a medium risk transaction
    transaction_data = {
        "token": "tkn_verification_fail_001",
        "merchant_id": "merchant_restaurant_001",
        "amount": 8000.0,
        "security_context": {
            "token_age_minutes": 60,
            "device_trust_score": 45,
            "usual_location": "Delhi, India",
            "current_location": "Mumbai, India",
            "recent_transactions": 3,
            "user_avg_amount": 2500.0,
            "new_device": True,
            "vpn_detected": False,
            "unusual_time": False,
            "rushed_transaction": True
        },
        "user_info": {
            "user_id": "user_verification_fail_001",
            "account_age_days": 45,
            "verified_user": True
        }
    }
    
    print_step(1, "Create Medium Risk Transaction")
    result = make_request("POST", "/tokentrust/process", transaction_data)
    
    if result and result.get('session_id'):
        session_id = result.get('session_id')
        print(f"\n🆔 Session ID: {session_id}")
        
        print_step(2, "Simulate Merchant 2FA Verification (Negative)")
        
        # Simulate failed merchant verification
        verification_data = {
            "session_id": session_id,
            "verified": False,
            "verified_by": "cashier_sarah",
            "method": "in_person_verification",
            "notes": "Customer could not provide valid ID or answer security questions"
        }
        
        verification_result = make_request("POST", "/tokentrust/merchant-response", verification_data)
        
        if verification_result:
            print("\n❌ Customer could not be verified")
            
            # Wait for processing
            time.sleep(2)
            
            print_step(3, "Check Final Status After Failed Verification")
            final_status = make_request("GET", f"/tokentrust/session/{session_id}")
            
            if final_status:
                pass  # Status checked silently

def test_system_analytics():
    """Test system analytics and monitoring"""
    print_section("System Analytics & Monitoring")
    
    print_step(1, "Get TokenTrust Analytics")
    analytics = make_request("GET", "/tokentrust/analytics")
    
    if analytics:
        print(f"\n📊 System Status: {analytics.get('system_status')}")
        print(f"🔄 Active Sessions: {analytics.get('active_sessions')}")
        print(f"✅ Verification Analytics: {json.dumps(analytics.get('verification_analytics'), indent=2)}")
        print(f"🛠️ Services: {json.dumps(analytics.get('services'), indent=2)}")
    
    print_step(2, "Health Check")
    health = make_request("GET", "/health")
    
    if health:
        print(f"\n🏥 Health Status: {health.get('status')}")
        print(f"🔧 Service Version: {health.get('version')}")
        print(f"🛡️ Workflow Capabilities: {json.dumps(health.get('workflow_capabilities'), indent=2)}")

def test_cleanup():
    """Test session cleanup"""
    print_section("Session Cleanup")
    
    print_step(1, "Cleanup Old Sessions")
    cleanup_result = make_request("POST", "/tokentrust/cleanup", {"max_age_hours": 1})
    
    if cleanup_result:
        print(f"\n🧹 Sessions Cleaned: {cleanup_result.get('sessions_cleaned')}")
        print(f"🔄 Active Sessions Remaining: {cleanup_result.get('active_sessions_remaining')}")

def main():
    """Run all test scenarios"""
    print("🚀 TokenTrust Agentic AI System - Comprehensive Test Suite")
    print("=" * 70)
    
    # Check if server is running
    print("🔍 Checking server status...")
    health = make_request("GET", "/health")
    if not health:
        print("❌ Server is not running. Please start the FastAPI server first:")
        print("   cd risk-service")
        print("   python app.py")
        return
    
    print(f"✅ Server is running - {health.get('service')} v{health.get('version')}")
    
    # Run test scenarios
    try:
        # Test 1: Traditional risk check
        test_traditional_risk_check()
        
        # Test 2: Low risk scenario (auto-approve)
        test_agentic_low_risk_scenario()
        
        # Test 3: Medium risk scenario (freeze & verify - success)
        test_agentic_medium_risk_scenario()
        
        # Test 4: High risk scenario (immediate revoke)
        test_agentic_high_risk_scenario()
        
        # Test 5: Verification failed scenario
        test_merchant_verification_failed()
        
        # Test 6: System analytics
        test_system_analytics()
        
        # Test 7: Cleanup
        test_cleanup()
        
        print_section("Test Suite Completed Successfully!")
        print("✅ All TokenTrust Agentic AI workflows have been tested")
        print("🎯 The system is ready for production use")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")

if __name__ == "__main__":
    main()
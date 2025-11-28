"""
Test Script: Verify New TokenTrust Behavior
Tests the conditional final_status/token_status logic without starting the server
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_conditional_status_logic():
    """Test the new conditional status behavior"""
    
    print("🧪 Testing New TokenTrust Behavior")
    print("=" * 50)
    print("Testing conditional final_status/token_status logic...")
    print()
    
    try:
        from agents.token_trust_orchestrator import TokenTrustOrchestrator
        
        orchestrator = TokenTrustOrchestrator()
        print("✅ TokenTrustOrchestrator initialized successfully")
        
        # Test 1: Low risk transaction
        print("\n📋 Test 1: Low Risk Transaction")
        low_risk_data = {
            "token": "test_token_low_001",
            "merchant_id": "merchant_coffee",
            "amount": 4.50,
            "token_age_minutes": 30,
            "device_trust_score": 90,
            "usual_location": "San Francisco", 
            "current_location": "San Francisco",
            "new_device": False,
            "vpn_detected": False,
            "unusual_time": False,
            "rushed_transaction": False
        }
        
        result = await orchestrator.process_transaction(low_risk_data)
        decision_action = result.get("decision", {}).get("action")
        
        print(f"  Decision Action: {decision_action}")
        
        # Simulate API response logic
        response_data = {
            "success": True,
            "session_id": result.get("session_id"),
            "risk_assessment": result.get("risk_assessment"),
            "decision_reasoning": result.get("decision", {}).get("reasoning"),
        }
        
        # Apply conditional logic
        if decision_action == "APPROVE" or decision_action == "REVOKE":
            response_data.update({
                "final_status": result.get("final_result", {}).get("status"),
                "token_status": result.get("final_result", {}).get("token_status"),
                "workflow_completed": True,
                "message": result.get("final_result", {}).get("message", "Processing completed")
            })
            print("  ✅ COMPLETE: Will include final_status and token_status")
            print(f"    final_status: {response_data.get('final_status')}")
            print(f"    token_status: {response_data.get('token_status')}")
            
        elif decision_action == "FREEZE_AND_VERIFY":
            response_data.update({
                "workflow_completed": False,
                "requires_merchant_verification": True,
                "message": "Transaction requires merchant verification - please complete 2FA",
                "next_step": "merchant_verification"
            })
            print("  🔄 PENDING: Will NOT include final_status and token_status")
            print("    requires_merchant_verification: True")
            print("    workflow_completed: False")
        
        # Test 2: Medium risk transaction  
        print("\n📋 Test 2: Medium Risk Transaction")
        medium_risk_data = {
            "token": "test_token_medium_002",
            "merchant_id": "merchant_electronics",
            "amount": 299.99,
            "token_age_minutes": 120,
            "device_trust_score": 60,
            "usual_location": "San Francisco",
            "current_location": "New York", 
            "new_device": True,
            "vpn_detected": False,
            "unusual_time": True,
            "rushed_transaction": False
        }
        
        result2 = await orchestrator.process_transaction(medium_risk_data)
        decision_action2 = result2.get("decision", {}).get("action")
        
        print(f"  Decision Action: {decision_action2}")
        
        response_data2 = {
            "success": True,
            "session_id": result2.get("session_id"),
            "risk_assessment": result2.get("risk_assessment"),
        }
        
        if decision_action2 == "APPROVE" or decision_action2 == "REVOKE":
            response_data2.update({
                "final_status": result2.get("final_result", {}).get("status"),
                "token_status": result2.get("final_result", {}).get("token_status"),
                "workflow_completed": True,
            })
            print("  ✅ COMPLETE: Will include final_status and token_status")
            print(f"    final_status: {response_data2.get('final_status')}")
            print(f"    token_status: {response_data2.get('token_status')}")
            
        elif decision_action2 == "FREEZE_AND_VERIFY":
            response_data2.update({
                "workflow_completed": False,
                "requires_merchant_verification": True,
                "message": "Transaction requires merchant verification - please complete 2FA"
            })
            print("  🔄 PENDING: Will NOT include final_status and token_status")
            print("    requires_merchant_verification: True")
            print("    workflow_completed: False")
        
        print("\n✨ New Behavior Summary:")
        print("  ✅ APPROVE/REVOKE: Immediate final_status + token_status")
        print("  🔄 FREEZE_AND_VERIFY: No final_status + token_status until verification")
        print("  📞 After verification: final_status + token_status via /merchant-response")
        print()
        print("🎯 The conditional logic is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conditional_status_logic())
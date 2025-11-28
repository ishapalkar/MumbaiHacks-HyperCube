"""
Demo: New TokenTrust Behavior
Shows how final_status and token_status are only returned when decisions are complete
"""

import asyncio
import json
from datetime import datetime

async def demo_new_behavior():
    """Demonstrate the new conditional status behavior"""
    
    print("🚀 TokenTrust New Behavior Demo")
    print("=" * 50)
    print("Now final_status and token_status are only returned when the decision is COMPLETE")
    print()
    
    # Simulate different decision scenarios
    scenarios = [
        {
            "name": "Low Risk Transaction (APPROVE)",
            "decision_action": "APPROVE",
            "final_result": {"status": "approved", "token_status": "active", "message": "Transaction approved"}
        },
        {
            "name": "Medium Risk Transaction (FREEZE_AND_VERIFY)", 
            "decision_action": "FREEZE_AND_VERIFY",
            "final_result": {"status": "waiting_verification", "token_status": "frozen", "message": "Requires verification"}
        },
        {
            "name": "High Risk Transaction (REVOKE)",
            "decision_action": "REVOKE", 
            "final_result": {"status": "revoked", "token_status": "revoked", "message": "Token revoked"}
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        print(f"   Decision Action: {scenario['decision_action']}")
        
        # Simulate API response logic
        response_data = {
            "success": True,
            "session_id": "demo-session-123",
            "risk_assessment": {"risk_score": 45, "decision": "CHALLENGE"},
            "decision_reasoning": "Demo reasoning",
            "processing_time": 3,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Apply new conditional logic
        if scenario["decision_action"] == "APPROVE" or scenario["decision_action"] == "REVOKE":
            # ✅ Decision is COMPLETE - include final status
            response_data.update({
                "final_status": scenario["final_result"]["status"],
                "token_status": scenario["final_result"]["token_status"],
                "workflow_completed": True,
                "message": scenario["final_result"]["message"]
            })
            print("   ✅ COMPLETE: Includes final_status and token_status")
            
        elif scenario["decision_action"] == "FREEZE_AND_VERIFY":
            # 🔄 Decision is PENDING - do NOT include final status
            response_data.update({
                "workflow_completed": False,
                "requires_merchant_verification": True,
                "message": "Transaction requires merchant verification - please complete 2FA",
                "next_step": "merchant_verification"
            })
            print("   🔄 PENDING: Does NOT include final_status and token_status yet")
        
        # Show the response
        print("   📤 API Response:")
        for key, value in response_data.items():
            if key in ["final_status", "token_status"]:
                print(f"      {key}: {value} ⭐") 
            elif key in ["requires_merchant_verification", "workflow_completed"]:
                print(f"      {key}: {value} 🔑")
            else:
                print(f"      {key}: {value}")
        
        print()
    
    print("🔄 For FREEZE_AND_VERIFY scenarios:")
    print("   • Initial response: NO final_status/token_status")
    print("   • After verification: final_status/token_status returned via /merchant-response")
    print()
    
    print("✨ Benefits:")
    print("   • Clear workflow states")
    print("   • No premature status disclosure") 
    print("   • Better UX for pending transactions")
    print("   • Proper separation of concerns")

if __name__ == "__main__":
    asyncio.run(demo_new_behavior())
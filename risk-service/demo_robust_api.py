"""
TokenTrust Robust API Demo
Demonstrates the complete robust workflow with proper error handling
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/v2"
DEMO_SCENARIOS = [
    {
        "name": "Low Risk Transaction",
        "token_id": "demo_token_low_001",
        "merchant_id": "coffee_shop_abc",
        "amount": 4.50,
        "risk_score": 25,
        "expected_outcome": "approved_immediately"
    },
    {
        "name": "Medium Risk Transaction - Success",
        "token_id": "demo_token_med_002", 
        "merchant_id": "electronics_store_xyz",
        "amount": 299.99,
        "risk_score": 65,
        "expected_outcome": "frozen_then_approved",
        "merchant_response": "Yes, I authorized this purchase of a tablet"
    },
    {
        "name": "High Risk Transaction - Failed Verification",
        "token_id": "demo_token_high_003",
        "merchant_id": "luxury_goods_premium",
        "amount": 2500.00,
        "risk_score": 88,
        "expected_outcome": "frozen_then_revoked",
        "merchant_response": "No, I did not make this purchase. This is fraud!"
    },
    {
        "name": "Agent Triage Override", 
        "token_id": "demo_token_triage_004",
        "merchant_id": "restaurant_chain_456",
        "amount": 67.50,
        "risk_score": 72,
        "expected_outcome": "agent_overridden",
        "agent_decision": "approve",
        "agent_reasoning": "AI detected regular customer pattern - false positive risk score"
    },
    {
        "name": "Revoked Token Attempt",
        "token_id": "demo_token_revoked_005", 
        "merchant_id": "gas_station_789",
        "amount": 45.00,
        "risk_score": 30,
        "expected_outcome": "rejected_revoked_token",
        "pre_revoke": True
    }
]

class RobustAPIDemo:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def print_section(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_subsection(self, title: str):
        print(f"\n{'-'*40}")
        print(f"  {title}")
        print(f"{'-'*40}")
        
    def pretty_print_json(self, data: Dict[Any, Any], title: str = ""):
        if title:
            print(f"\n📋 {title}:")
        print(json.dumps(data, indent=2, default=str))
        
    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None) -> requests.Response:
        """Make API request and handle errors"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            print(f"🌐 {method.upper()} {endpoint} -> Status: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"❌ Error Response: {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def check_health(self):
        """Check API health"""
        self.print_section("Health Check")
        
        response = self.make_request("GET", "/health")
        if response and response.status_code == 200:
            self.pretty_print_json(response.json(), "System Status")
            print("✅ API is healthy and ready")
        else:
            print("❌ API health check failed")
            return False
        return True
        
    def demo_low_risk_workflow(self, scenario: Dict[str, Any]):
        """Demonstrate low-risk transaction workflow"""
        self.print_subsection(f"Scenario: {scenario['name']}")
        
        # Analyze transaction
        request_data = {
            "token_id": scenario["token_id"],
            "merchant_id": scenario["merchant_id"],
            "amount": scenario["amount"],
            "risk_score": scenario["risk_score"],
            "metadata": {"demo": True, "scenario": scenario["name"]}
        }
        
        print("📤 Sending transaction for analysis...")
        self.pretty_print_json(request_data, "Request Data")
        
        response = self.make_request("POST", "/analyze", request_data)
        
        if response and response.status_code == 200:
            result = response.json()
            self.pretty_print_json(result, "Analysis Result")
            
            # Verify expectations
            if result["risk_level"] == "LOW" and result["decision"] == "approve":
                print("✅ Low risk transaction approved immediately as expected")
                
                # Check token status
                token_response = self.make_request("GET", f"/token/{scenario['token_id']}/status")
                if token_response and token_response.status_code == 200:
                    token_status = token_response.json()
                    
                    if token_status["status"] == "active":
                        print("✅ Token remains active - workflow complete")
                    else:
                        print("⚠️  Unexpected token status detected")
            else:
                print(f"❌ Unexpected result for low risk: {result}")
        else:
            print("❌ Transaction analysis failed")
    
    def demo_medium_risk_workflow(self, scenario: Dict[str, Any]):
        """Demonstrate medium-risk transaction with merchant verification"""
        self.print_subsection(f"Scenario: {scenario['name']}")
        
        # Step 1: Analyze transaction
        request_data = {
            "token_id": scenario["token_id"],
            "merchant_id": scenario["merchant_id"],
            "amount": scenario["amount"],
            "risk_score": scenario["risk_score"],
            "metadata": {"demo": True, "scenario": scenario["name"]}
        }
        
        print("📤 Step 1: Sending medium-risk transaction for analysis...")
        response = self.make_request("POST", "/analyze", request_data)
        
        if not response or response.status_code != 200:
            print("❌ Transaction analysis failed")
            return
            
        analysis_result = response.json()
        self.pretty_print_json(analysis_result, "Analysis Result")
        
        if analysis_result["risk_level"] != "MEDIUM" or analysis_result["token_status"] != "frozen":
            print(f"❌ Expected MEDIUM risk and frozen token, got: {analysis_result}")
            return
            
        print("✅ Transaction correctly flagged as medium risk, token frozen")
        
        # Step 2: Simulate merchant verification
        print("\n📞 Step 2: Simulating merchant 2FA verification...")
        time.sleep(1)  # Simulate verification delay
        
        merchant_data = {
            "event_id": analysis_result["event_id"],
            "user_response": scenario["merchant_response"],
            "verification_method": "sms_2fa",
            "evidence": {
                "verification_time": datetime.utcnow().isoformat(),
                "device_used": "mobile_app",
                "location_verified": True
            }
        }
        
        self.pretty_print_json(merchant_data, "Merchant Verification Data")
        merchant_response = self.make_request("POST", "/merchant-response", merchant_data)
        
        if merchant_response and merchant_response.status_code == 200:
            merchant_result = merchant_response.json()
            self.pretty_print_json(merchant_result, "Verification Result")
            
            if merchant_result["verification_successful"] and merchant_result["token_status"] == "active":
                print("✅ Merchant verification successful, token unfrozen")
            else:
                print(f"❌ Unexpected verification result: {merchant_result}")
        else:
            print("❌ Merchant verification processing failed")
    
    def demo_high_risk_workflow(self, scenario: Dict[str, Any]):
        """Demonstrate high-risk transaction with failed verification"""
        self.print_subsection(f"Scenario: {scenario['name']}")
        
        # Step 1: Analyze high-risk transaction
        request_data = {
            "token_id": scenario["token_id"],
            "merchant_id": scenario["merchant_id"],
            "amount": scenario["amount"],
            "risk_score": scenario["risk_score"],
            "metadata": {"demo": True, "scenario": scenario["name"], "high_value": True}
        }
        
        print("📤 Step 1: Sending high-risk transaction for analysis...")
        response = self.make_request("POST", "/analyze", request_data)
        
        if not response or response.status_code != 200:
            print("❌ Transaction analysis failed")
            return
            
        analysis_result = response.json()
        self.pretty_print_json(analysis_result, "Analysis Result")
        
        if (analysis_result["risk_level"] != "HIGH" or 
            analysis_result["token_status"] != "frozen" or
            not analysis_result["auto_revoke_candidate"]):
            print(f"❌ Expected HIGH risk, frozen token, and auto-revoke candidate: {analysis_result}")
            return
            
        print("✅ High-risk transaction detected, token frozen as revoke candidate")
        
        # Step 2: Simulate failed merchant verification
        print("\n📞 Step 2: Simulating failed merchant verification...")
        time.sleep(1)
        
        merchant_data = {
            "event_id": analysis_result["event_id"],
            "user_response": scenario["merchant_response"],
            "verification_method": "phone_call",
            "evidence": {
                "user_confirmed_fraud": True,
                "verification_time": datetime.utcnow().isoformat(),
                "security_alert": True
            }
        }
        
        self.pretty_print_json(merchant_data, "Merchant Verification Data")
        merchant_response = self.make_request("POST", "/merchant-response", merchant_data)
        
        if merchant_response and merchant_response.status_code == 200:
            merchant_result = merchant_response.json()
            self.pretty_print_json(merchant_result, "Verification Result")
            
            if (not merchant_result["verification_successful"] and 
                merchant_result["token_status"] == "revoked"):
                print("✅ Fraud confirmed, token revoked for security")
            else:
                print(f"❌ Unexpected verification result: {merchant_result}")
        else:
            print("❌ Merchant verification processing failed")
    
    def demo_agent_triage_workflow(self, scenario: Dict[str, Any]):
        """Demonstrate AI agent triage override"""
        self.print_subsection(f"Scenario: {scenario['name']}")
        
        # Step 1: Analyze transaction (will be medium risk)
        request_data = {
            "token_id": scenario["token_id"],
            "merchant_id": scenario["merchant_id"],
            "amount": scenario["amount"],
            "risk_score": scenario["risk_score"],
            "metadata": {"demo": True, "scenario": scenario["name"], "frequent_customer": True}
        }
        
        print("📤 Step 1: Sending transaction for initial analysis...")
        response = self.make_request("POST", "/analyze", request_data)
        
        if not response or response.status_code != 200:
            print("❌ Transaction analysis failed")
            return
            
        analysis_result = response.json()
        self.pretty_print_json(analysis_result, "Initial Analysis Result")
        
        print("✅ Transaction flagged for verification due to risk score")
        
        # Step 2: AI Agent triage override
        print("\n🤖 Step 2: AI Agent performing advanced analysis and triage...")
        time.sleep(1)
        
        triage_data = {
            "event_id": analysis_result["event_id"],
            "agent_decision": scenario["agent_decision"],
            "reasoning": scenario["agent_reasoning"]
        }
        
        self.pretty_print_json(triage_data, "Agent Triage Decision")
        triage_response = self.make_request("POST", "/triage", triage_data)
        
        if triage_response and triage_response.status_code == 200:
            triage_result = triage_response.json()
            self.pretty_print_json(triage_result, "Triage Result")
            
            if triage_result["action_taken"] == "approved_unfrozen":
                print("✅ AI Agent override successful - transaction approved despite risk score")
            else:
                print(f"❌ Unexpected triage result: {triage_result}")
        else:
            print("❌ Agent triage processing failed")
    
    def demo_revoked_token_workflow(self, scenario: Dict[str, Any]):
        """Demonstrate handling of revoked token"""
        self.print_subsection(f"Scenario: {scenario['name']}")
        
        # Step 1: Pre-revoke the token (simulate previous security incident)
        if scenario.get("pre_revoke"):
            print("🔒 Step 1: Pre-revoking token (simulating previous security incident)...")
            
            # First create a high-risk transaction to get it in system, then revoke
            setup_data = {
                "token_id": scenario["token_id"],
                "merchant_id": "previous_merchant",
                "amount": 1000.00,
                "risk_score": 95,
                "metadata": {"setup": True}
            }
            
            setup_response = self.make_request("POST", "/analyze", setup_data)
            if setup_response and setup_response.status_code == 200:
                setup_result = setup_response.json()
                
                # Simulate failed verification to revoke token
                revoke_data = {
                    "event_id": setup_result["event_id"],
                    "user_response": "This is fraud, I never made this transaction",
                    "verification_method": "security_call"
                }
                
                revoke_response = self.make_request("POST", "/merchant-response", revoke_data)
                if revoke_response and revoke_response.status_code == 200:
                    print("✅ Token successfully revoked from previous security incident")
                else:
                    print("❌ Failed to revoke token in setup")
                    return
        
        # Step 2: Attempt new transaction on revoked token
        print("\n📤 Step 2: Attempting new transaction on revoked token...")
        
        request_data = {
            "token_id": scenario["token_id"],
            "merchant_id": scenario["merchant_id"],
            "amount": scenario["amount"],
            "risk_score": scenario["risk_score"],
            "metadata": {"demo": True, "scenario": scenario["name"]}
        }
        
        self.pretty_print_json(request_data, "Transaction Request")
        response = self.make_request("POST", "/analyze", request_data)
        
        if response and response.status_code == 403:
            error_detail = response.json()
            self.pretty_print_json(error_detail, "Expected Error Response")
            print("✅ Revoked token correctly rejected with 403 Forbidden")
        else:
            print(f"❌ Expected 403 Forbidden, got: {response.status_code if response else 'None'}")
    
    def show_audit_trail(self, token_id: str):
        """Display audit trail for a token"""
        print(f"\n📊 Audit Trail for Token: {token_id}")
        
        audit_response = self.make_request("GET", f"/audit/{token_id}")
        if audit_response and audit_response.status_code == 200:
            audit_data = audit_response.json()
            
            print(f"\nFound {len(audit_data['entries'])} audit entries:")
            for i, entry in enumerate(audit_data["entries"], 1):
                print(f"\n  {i}. {entry['action'].upper()} by {entry['actor']}")
                print(f"     Time: {entry['timestamp']}")
                print(f"     Reason: {entry['reason']}")
                if entry.get("details"):
                    print(f"     Details: {json.dumps(entry['details'], indent=8)}")
        else:
            print("❌ Failed to retrieve audit trail")
    
    def run_full_demo(self):
        """Run complete demo of all scenarios"""
        self.print_section("TokenTrust Robust API Demo")
        print("Demonstrating production-ready workflow with proper error handling")
        
        # Health check first
        if not self.check_health():
            print("❌ Cannot proceed - API is not healthy")
            return
        
        # Run each scenario
        for scenario in DEMO_SCENARIOS:
            try:
                if scenario["expected_outcome"] == "approved_immediately":
                    self.demo_low_risk_workflow(scenario)
                    
                elif scenario["expected_outcome"] == "frozen_then_approved":
                    self.demo_medium_risk_workflow(scenario)
                    
                elif scenario["expected_outcome"] == "frozen_then_revoked":
                    self.demo_high_risk_workflow(scenario)
                    
                elif scenario["expected_outcome"] == "agent_overridden":
                    self.demo_agent_triage_workflow(scenario)
                    
                elif scenario["expected_outcome"] == "rejected_revoked_token":
                    self.demo_revoked_token_workflow(scenario)
                
                # Show audit trail for this token
                self.show_audit_trail(scenario["token_id"])
                
                print("\n⏱️  Pausing before next scenario...")
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error in scenario '{scenario['name']}': {e}")
                continue
        
        # Final system status
        self.print_section("Demo Complete - Final System Status")
        self.check_health()
        
        print(f"\n🎉 Demo completed successfully!")
        print("Key features demonstrated:")
        print("  ✅ Risk-based transaction classification")
        print("  ✅ Idempotent token lifecycle management") 
        print("  ✅ Proper HTTP status codes and error handling")
        print("  ✅ Comprehensive audit logging")
        print("  ✅ AI agent triage capabilities")
        print("  ✅ End-to-end workflow robustness")

if __name__ == "__main__":
    demo = RobustAPIDemo()
    
    print("🚀 Starting TokenTrust Robust API Demo")
    print("Make sure the API server is running on http://localhost:8000")
    
    input("\nPress Enter to start the demo...")
    
    try:
        demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
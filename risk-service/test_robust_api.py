"""
Comprehensive Test Suite for TokenTrust Robust API
End-to-end testing of the new workflow implementation
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

# Import the FastAPI app and components to test
from app import app
from helpers import storage, classify_risk_score, freeze_token, unfreeze_token, revoke_token
from config import (
    TOKEN_STATUS_ACTIVE, TOKEN_STATUS_FROZEN, TOKEN_STATUS_REVOKED,
    EVENT_STATUS_APPROVED, EVENT_STATUS_WAITING_VERIFICATION,
    EVENT_STATUS_VERIFIED_SUCCESS, EVENT_STATUS_VERIFIED_FAILURE
)

client = TestClient(app)

class TestRobustTokenTrustWorkflow:
    """Test the complete robust TokenTrust workflow"""
    
    def setup_method(self):
        """Reset storage before each test"""
        storage.tokens.clear()
        storage.events.clear()
        storage.audit_log.clear()
    
    def test_risk_classification(self):
        """Test risk score classification helper"""
        # Test LOW risk
        assert classify_risk_score(0) == "LOW"
        assert classify_risk_score(25) == "LOW" 
        assert classify_risk_score(49) == "LOW"
        
        # Test MEDIUM risk
        assert classify_risk_score(50) == "MEDIUM"
        assert classify_risk_score(65) == "MEDIUM"
        assert classify_risk_score(79) == "MEDIUM"
        
        # Test HIGH risk
        assert classify_risk_score(80) == "HIGH"
        assert classify_risk_score(90) == "HIGH"
        assert classify_risk_score(100) == "HIGH"
    
    def test_token_lifecycle_helpers(self):
        """Test idempotent token lifecycle operations"""
        token_id = "test_token_001"
        
        # Test freeze operation
        result = freeze_token(token_id, "test_freeze", "test_user")
        assert result["success"] == True
        assert result["action"] == "frozen"
        assert result["was_active"] == False  # New token
        
        # Test idempotent freeze
        result = freeze_token(token_id, "test_freeze_again", "test_user")
        assert result["success"] == True
        assert result["action"] == "already_frozen"
        
        # Test unfreeze operation
        result = unfreeze_token(token_id, "test_user", "test_passed")
        assert result["success"] == True
        assert result["action"] == "unfrozen"
        
        # Test idempotent unfreeze
        result = unfreeze_token(token_id, "test_user", "test_passed_again")
        assert result["success"] == True
        assert result["action"] == "already_active"
        
        # Test revoke operation
        result = revoke_token(token_id, "test_user", "security_issue")
        assert result["success"] == True
        assert result["action"] == "revoked"
        assert result["previous_status"] == TOKEN_STATUS_ACTIVE
        
        # Test idempotent revoke
        result = revoke_token(token_id, "test_user", "security_issue_again")
        assert result["success"] == True
        assert result["action"] == "already_revoked"
        
        # Test cannot unfreeze revoked token
        result = unfreeze_token(token_id, "test_user", "should_fail")
        assert result["success"] == False
        assert result["error"] == "cannot_unfreeze_revoked_token"
    
    def test_low_risk_transaction_workflow(self):
        """Test complete workflow for low-risk transactions"""
        # Test data
        request_data = {
            "token_id": "token_low_risk",
            "merchant_id": "merchant_001",
            "amount": 25.50,
            "risk_score": 30,  # LOW risk
            "metadata": {"source": "mobile_app"}
        }
        
        # Send analysis request
        response = client.post("/v2/analyze", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["decision"] == "approve"
        assert data["status"] == EVENT_STATUS_APPROVED
        assert data["token_status"] == TOKEN_STATUS_ACTIVE
        assert data["risk_level"] == "LOW"
        assert data["auto_revoke_candidate"] == False
        assert "low risk" in data["message"].lower()
        
        # Verify event was created
        event_id = data["event_id"]
        event_response = client.get(f"/v2/event/{event_id}")
        assert event_response.status_code == 200
        
        event_data = event_response.json()
        assert event_data["risk_score"] == 30
        assert event_data["status"] == EVENT_STATUS_APPROVED
        assert event_data["decision"] == "approve"
        
        # Verify token remains active
        token_response = client.get(f"/v2/token/{request_data['token_id']}/status")
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert token_data["status"] == TOKEN_STATUS_ACTIVE
    
    def test_medium_risk_transaction_workflow(self):
        """Test complete workflow for medium-risk transactions"""
        # Test data
        request_data = {
            "token_id": "token_medium_risk",
            "merchant_id": "merchant_002", 
            "amount": 150.00,
            "risk_score": 65,  # MEDIUM risk
            "metadata": {"source": "web_browser"}
        }
        
        # Send analysis request
        response = client.post("/v2/analyze", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["decision"] == "challenge"
        assert data["status"] == EVENT_STATUS_WAITING_VERIFICATION
        assert data["token_status"] == TOKEN_STATUS_FROZEN
        assert data["risk_level"] == "MEDIUM"
        assert data["auto_revoke_candidate"] == False
        assert "medium risk" in data["message"].lower()
        assert "frozen" in data["message"].lower()
        
        event_id = data["event_id"]
        
        # Simulate successful merchant verification
        merchant_response_data = {
            "event_id": event_id,
            "user_response": "Yes, I authorized this transaction",
            "verification_method": "sms_2fa",
            "evidence": {"phone_verified": True, "response_time_seconds": 45}
        }
        
        merchant_response = client.post("/v2/merchant-response", json=merchant_response_data)
        
        # Verify merchant response processing
        assert merchant_response.status_code == 200
        merchant_data = merchant_response.json()
        
        assert merchant_data["final_status"] == EVENT_STATUS_VERIFIED_SUCCESS
        assert merchant_data["token_status"] == TOKEN_STATUS_ACTIVE  # Unfrozen after success
        assert merchant_data["verification_successful"] == True
        assert "successful" in merchant_data["message"].lower()
        
        # Verify token is now active
        token_response = client.get(f"/v2/token/{request_data['token_id']}/status")
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert token_data["status"] == TOKEN_STATUS_ACTIVE
    
    def test_high_risk_transaction_workflow(self):
        """Test complete workflow for high-risk transactions with failed verification"""
        # Test data
        request_data = {
            "token_id": "token_high_risk",
            "merchant_id": "merchant_003",
            "amount": 1000.00,
            "risk_score": 85,  # HIGH risk
            "metadata": {"source": "api_call"}
        }
        
        # Send analysis request
        response = client.post("/v2/analyze", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["decision"] == "challenge_high"
        assert data["status"] == EVENT_STATUS_WAITING_VERIFICATION
        assert data["token_status"] == TOKEN_STATUS_FROZEN
        assert data["risk_level"] == "HIGH"
        assert data["auto_revoke_candidate"] == True
        assert "high risk" in data["message"].lower()
        assert "auto-revoke candidate" in data["message"].lower()
        
        event_id = data["event_id"]
        
        # Simulate failed merchant verification
        merchant_response_data = {
            "event_id": event_id,
            "user_response": "No, I did not authorize this transaction",
            "verification_method": "phone_call",
            "evidence": {"user_denied": True, "suspicious_activity": True}
        }
        
        merchant_response = client.post("/v2/merchant-response", json=merchant_response_data)
        
        # Verify merchant response processing
        assert merchant_response.status_code == 200
        merchant_data = merchant_response.json()
        
        assert merchant_data["final_status"] == EVENT_STATUS_VERIFIED_FAILURE
        assert merchant_data["token_status"] == TOKEN_STATUS_REVOKED  # Revoked after failure
        assert merchant_data["verification_successful"] == False
        assert "failed" in merchant_data["message"].lower()
        assert "revoked" in merchant_data["message"].lower()
        
        # Verify token is now revoked
        token_response = client.get(f"/v2/token/{request_data['token_id']}/status")
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert token_data["status"] == TOKEN_STATUS_REVOKED
        assert token_data["reason"] == "Merchant verification failed"
    
    def test_agent_triage_workflow(self):
        """Test agent triage for complex decisions"""
        # First create an event
        request_data = {
            "token_id": "token_triage_test",
            "merchant_id": "merchant_triage",
            "amount": 75.00,
            "risk_score": 55,  # MEDIUM risk
        }
        
        response = client.post("/v2/analyze", json=request_data)
        assert response.status_code == 200
        event_id = response.json()["event_id"]
        
        # Test agent approval triage
        triage_data = {
            "event_id": event_id,
            "agent_decision": "approve",
            "reasoning": "AI detected legitimate user pattern despite risk score"
        }
        
        triage_response = client.post("/v2/triage", json=triage_data)
        
        assert triage_response.status_code == 200
        triage_result = triage_response.json()
        
        assert triage_result["action_taken"] == "approved_unfrozen"
        assert triage_result["token_status"] == TOKEN_STATUS_ACTIVE
        assert "approved" in triage_result["message"].lower()
        
        # Test agent revoke triage on new event
        request_data_2 = {
            "token_id": "token_triage_revoke",
            "merchant_id": "merchant_triage",
            "amount": 200.00,
            "risk_score": 45,  # LOW risk normally
        }
        
        response_2 = client.post("/v2/analyze", json=request_data_2)
        event_id_2 = response_2.json()["event_id"]
        
        triage_data_2 = {
            "event_id": event_id_2,
            "agent_decision": "revoke",
            "reasoning": "AI detected sophisticated fraud pattern not caught by risk score"
        }
        
        triage_response_2 = client.post("/v2/triage", json=triage_data_2)
        
        assert triage_response_2.status_code == 200
        triage_result_2 = triage_response_2.json()
        
        assert triage_result_2["action_taken"] == "revoked"
        assert triage_result_2["token_status"] == TOKEN_STATUS_REVOKED
        assert "revoked" in triage_result_2["message"].lower()
    
    def test_error_handling_and_http_codes(self):
        """Test proper HTTP status codes and error handling"""
        
        # Test 404 for non-existent event
        response = client.get("/v2/event/non_existent_event")
        assert response.status_code == 404
        
        # Test 404 for non-existent event in merchant response
        merchant_response_data = {
            "event_id": "non_existent_event",
            "user_response": "Yes",
            "verification_method": "sms"
        }
        response = client.post("/v2/merchant-response", json=merchant_response_data)
        assert response.status_code == 404
        
        # Test 404 for non-existent event in triage
        triage_data = {
            "event_id": "non_existent_event",
            "agent_decision": "approve"
        }
        response = client.post("/v2/triage", json=triage_data)
        assert response.status_code == 404
        
        # Test validation errors (422)
        invalid_data = {
            "token_id": "test",
            "merchant_id": "test", 
            "amount": -50,  # Invalid negative amount
            "risk_score": 150  # Invalid risk score > 100
        }
        response = client.post("/v2/analyze", json=invalid_data)
        assert response.status_code == 422
        
        # Test processing revoked token (403)
        # First revoke a token
        revoke_token("revoked_token_test", "test_user", "security_breach")
        
        request_data = {
            "token_id": "revoked_token_test",
            "merchant_id": "merchant_test",
            "amount": 50.00,
            "risk_score": 30
        }
        response = client.post("/v2/analyze", json=request_data)
        assert response.status_code == 403
        assert "revoked" in response.json()["detail"].lower()
        
        # Test 409 for invalid state transitions
        # Create an approved event and try to get merchant response
        approved_request = {
            "token_id": "approved_token_test",
            "merchant_id": "merchant_test",
            "amount": 25.00,
            "risk_score": 20  # Low risk -> approved
        }
        approved_response = client.post("/v2/analyze", json=approved_request)
        approved_event_id = approved_response.json()["event_id"]
        
        # Try to process merchant response on approved event
        invalid_merchant_response = {
            "event_id": approved_event_id,
            "user_response": "Yes",
            "verification_method": "sms"
        }
        response = client.post("/v2/merchant-response", json=invalid_merchant_response)
        assert response.status_code == 409
        assert "not waiting for verification" in response.json()["detail"].lower()
    
    def test_audit_logging(self):
        """Test audit logging functionality"""
        token_id = "audit_test_token"
        
        # Perform some operations
        request_data = {
            "token_id": token_id,
            "merchant_id": "audit_merchant",
            "amount": 100.00,
            "risk_score": 70
        }
        
        # Create transaction
        response = client.post("/v2/analyze", json=request_data)
        assert response.status_code == 200
        
        # Get audit log
        audit_response = client.get(f"/v2/audit/{token_id}")
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert audit_data["target"] == token_id
        assert len(audit_data["entries"]) >= 1
        
        # Verify audit entry structure
        entry = audit_data["entries"][0]
        assert "audit_id" in entry
        assert "action" in entry
        assert "actor" in entry
        assert "timestamp" in entry
        assert entry["target"] == token_id
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/v2/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "storage_stats" in data
        
        # Check storage stats structure
        stats = data["storage_stats"]
        assert "tokens" in stats
        assert "events" in stats  
        assert "audit_entries" in stats
    
    def test_complete_workflow_integration(self):
        """Test complete workflow with multiple transactions on same token"""
        token_id = "integration_test_token"
        
        # Transaction 1: Low risk (should be approved)
        tx1_data = {
            "token_id": token_id,
            "merchant_id": "merchant_1",
            "amount": 25.00,
            "risk_score": 35
        }
        
        tx1_response = client.post("/v2/analyze", json=tx1_data)
        assert tx1_response.status_code == 200
        assert tx1_response.json()["token_status"] == TOKEN_STATUS_ACTIVE
        
        # Transaction 2: Medium risk (should freeze token)
        tx2_data = {
            "token_id": token_id,
            "merchant_id": "merchant_2", 
            "amount": 500.00,
            "risk_score": 60
        }
        
        tx2_response = client.post("/v2/analyze", json=tx2_data)
        assert tx2_response.status_code == 200
        tx2_result = tx2_response.json()
        assert tx2_result["token_status"] == TOKEN_STATUS_FROZEN
        
        # Verify merchant successfully
        merchant_data = {
            "event_id": tx2_result["event_id"],
            "user_response": "Yes, I made this purchase",
            "verification_method": "app_push"
        }
        
        merchant_response = client.post("/v2/merchant-response", json=merchant_data)
        assert merchant_response.status_code == 200
        assert merchant_response.json()["token_status"] == TOKEN_STATUS_ACTIVE
        
        # Transaction 3: High risk (should freeze again)
        tx3_data = {
            "token_id": token_id,
            "merchant_id": "merchant_3",
            "amount": 2000.00, 
            "risk_score": 90
        }
        
        tx3_response = client.post("/v2/analyze", json=tx3_data)
        assert tx3_response.status_code == 200
        tx3_result = tx3_response.json()
        assert tx3_result["token_status"] == TOKEN_STATUS_FROZEN
        assert tx3_result["auto_revoke_candidate"] == True
        
        # Fail verification (should revoke)
        fail_merchant_data = {
            "event_id": tx3_result["event_id"],
            "user_response": "No, this is fraud!",
            "verification_method": "phone_call"
        }
        
        fail_response = client.post("/v2/merchant-response", json=fail_merchant_data)
        assert fail_response.status_code == 200
        assert fail_response.json()["token_status"] == TOKEN_STATUS_REVOKED
        
        # Transaction 4: Should fail on revoked token
        tx4_data = {
            "token_id": token_id,
            "merchant_id": "merchant_4",
            "amount": 10.00,
            "risk_score": 15
        }
        
        tx4_response = client.post("/v2/analyze", json=tx4_data)
        assert tx4_response.status_code == 403
        
        # Verify audit trail has all actions
        audit_response = client.get(f"/v2/audit/{token_id}")
        audit_entries = audit_response.json()["entries"]
        
        # Should have freeze, unfreeze, freeze, revoke actions plus analysis actions
        actions = [entry["action"] for entry in audit_entries]
        assert "freeze" in actions
        assert "unfreeze" in actions  
        assert "revoke" in actions

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
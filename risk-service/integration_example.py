"""
Example integration code for merchant backend
This shows how to integrate Risk Checker with your payment processing
"""

import requests
from typing import Dict, Any

RISK_SERVICE_URL = "http://localhost:8000"

class RiskCheckerClient:
    """Client for Risk Checker Service"""
    
    def __init__(self, base_url: str = RISK_SERVICE_URL):
        self.base_url = base_url
    
    def check_risk(
        self,
        device_id: str,
        ip_address: str,
        amount: float,
        merchant: str,
        user_id: str = None,
        currency: str = "USD",
        geo_location: str = None
    ) -> Dict[str, Any]:
        """
        Check transaction risk before processing payment
        
        Returns:
            {
                "risk_score": int,
                "decision": str (APPROVE/CHALLENGE/FREEZE),
                "explanation": str
            }
        """
        payload = {
            "device_id": device_id,
            "ip_address": ip_address,
            "amount": amount,
            "currency": currency,
            "merchant": merchant,
            "user_id": user_id,
            "geo_location": geo_location
        }
        
        response = requests.post(
            f"{self.base_url}/risk-check",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def freeze_token(self, token_id: str, user_id: str, reason: str) -> Dict[str, Any]:
        """Freeze a token"""
        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "reason": reason
        }
        response = requests.post(
            f"{self.base_url}/freeze-token",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    
    def unfreeze_token(self, token_id: str, user_id: str) -> Dict[str, Any]:
        """Unfreeze a token"""
        payload = {
            "token_id": token_id,
            "user_id": user_id
        }
        response = requests.post(
            f"{self.base_url}/unfreeze-token",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    
    def get_token_status(self, token_id: str) -> Dict[str, Any]:
        """Check if token is frozen"""
        response = requests.get(
            f"{self.base_url}/token-status/{token_id}",
            timeout=5
        )
        response.raise_for_status()
        return response.json()


# Example Payment Processing Flow
def process_payment(
    user_id: str,
    token_id: str,
    device_id: str,
    ip_address: str,
    amount: float,
    merchant: str
):
    """
    Complete payment processing with risk check
    """
    risk_client = RiskCheckerClient()
    
    # Step 1: Check if token is frozen
    token_status = risk_client.get_token_status(token_id)
    if token_status["status"] == "frozen":
        return {
            "success": False,
            "message": "Token is frozen. Please contact support.",
            "code": "TOKEN_FROZEN"
        }
    
    # Step 2: Check transaction risk
    try:
        risk_result = risk_client.check_risk(
            device_id=device_id,
            ip_address=ip_address,
            amount=amount,
            merchant=merchant,
            user_id=user_id
        )
        
        decision = risk_result["decision"]
        risk_score = risk_result["risk_score"]
        explanation = risk_result["explanation"]
        
        # Step 3: Handle decision
        if decision == "APPROVE":
            # Process payment normally
            # payment_result = process_payment_internal(...)
            return {
                "success": True,
                "message": "Payment processed successfully",
                "risk_score": risk_score,
                "code": "APPROVED"
            }
        
        elif decision == "CHALLENGE":
            # Request additional verification (OTP)
            # send_otp(user_id)
            return {
                "success": False,
                "message": "Additional verification required",
                "action": "SEND_OTP",
                "risk_score": risk_score,
                "explanation": explanation,
                "code": "CHALLENGE"
            }
        
        elif decision == "FREEZE":
            # Block transaction and freeze token
            freeze_result = risk_client.freeze_token(
                token_id=token_id,
                user_id=user_id,
                reason=f"High risk transaction: {explanation}"
            )
            return {
                "success": False,
                "message": "Transaction blocked due to suspicious activity",
                "risk_score": risk_score,
                "explanation": explanation,
                "code": "FROZEN"
            }
    
    except requests.exceptions.RequestException as e:
        # Risk service unavailable - use fallback logic
        print(f"Risk check failed: {str(e)}")
        return {
            "success": False,
            "message": "Payment processing temporarily unavailable",
            "code": "SERVICE_ERROR"
        }


# Example Usage
if __name__ == "__main__":
    # Simulate a payment
    result = process_payment(
        user_id="user-123",
        token_id="token-456",
        device_id="device-789",
        ip_address="192.168.1.100",
        amount=5000.0,
        merchant="Amazon"
    )
    
    print("Payment Result:")
    print(result)

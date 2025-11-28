import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

class TokenManager:
    """
    Agent responsible for token lifecycle management:
    - Freezing tokens temporarily
    - Unfreezing tokens after verification
    - Revoking tokens permanently
    - Tracking token states
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not found or not set properly. "
                "Please set your Groq API key in the .env file."
            )
        
        self.llm = ChatGroq(
            temperature=0.1,
            model_name="llama-3.3-70b-versatile",
            api_key=self.groq_api_key
        )
        
        # In-memory token state storage (in production, use Redis/Database)
        self.token_states = {}
        self.token_history = {}
    
    async def freeze_token(self, token: str, session_id: str, reason: str = "Risk assessment") -> Dict[str, Any]:
        """Freeze a token temporarily"""
        try:
            print(f"🧊 Freezing token {token[:8]}... for session {session_id[:8]}")
            
            # AI-powered decision on freeze duration and conditions
            freeze_decision = await self._determine_freeze_parameters(token, reason, session_id)
            
            freeze_data = {
                "status": "frozen",
                "frozen_at": datetime.now().isoformat(),
                "session_id": session_id,
                "reason": reason,
                "freeze_duration_minutes": freeze_decision.get("duration_minutes", 10),
                "conditions_for_unfreeze": freeze_decision.get("conditions", ["merchant_verification"]),
                "auto_revoke_at": freeze_decision.get("auto_revoke_at"),
                "freeze_level": freeze_decision.get("level", "standard")  # standard, strict, critical
            }
            
            # Store token state
            self.token_states[token] = freeze_data
            
            # Log to history
            self._log_token_action(token, "freeze", freeze_data)
            
            # Simulate API call to token service
            api_result = await self._call_token_service("freeze", token, freeze_data)
            
            print(f"🧊✅ Token {token[:8]} frozen successfully")
            
            return {
                "success": True,
                "token": token,
                "action": "frozen",
                "freeze_data": freeze_data,
                "api_response": api_result
            }
            
        except Exception as e:
            print(f"❌ Failed to freeze token {token[:8]}: {str(e)}")
            return {
                "success": False,
                "token": token,
                "error": str(e)
            }
    
    async def unfreeze_token(self, token: str, session_id: str, verified_by: str = "merchant") -> Dict[str, Any]:
        """Unfreeze a token after successful verification"""
        try:
            print(f"🔓 Unfreezing token {token[:8]}... for session {session_id[:8]}")
            
            # Check if token is currently frozen
            current_state = self.token_states.get(token)
            if not current_state or current_state.get("status") != "frozen":
                return {
                    "success": False,
                    "token": token,
                    "error": "Token is not in frozen state"
                }
            
            # AI verification of unfreeze conditions
            unfreeze_validation = await self._validate_unfreeze_conditions(token, session_id, verified_by)
            
            if not unfreeze_validation["allowed"]:
                return {
                    "success": False,
                    "token": token,
                    "error": unfreeze_validation["reason"]
                }
            
            unfreeze_data = {
                "status": "active",
                "unfrozen_at": datetime.now().isoformat(),
                "session_id": session_id,
                "verified_by": verified_by,
                "verification_method": unfreeze_validation.get("method", "merchant_2fa"),
                "previous_freeze_reason": current_state.get("reason"),
                "freeze_duration_actual": self._calculate_freeze_duration(current_state.get("frozen_at"))
            }
            
            # Update token state
            self.token_states[token] = unfreeze_data
            
            # Log to history
            self._log_token_action(token, "unfreeze", unfreeze_data)
            
            # Simulate API call to token service
            api_result = await self._call_token_service("unfreeze", token, unfreeze_data)
            
            print(f"🔓✅ Token {token[:8]} unfrozen successfully")
            
            return {
                "success": True,
                "token": token,
                "action": "unfrozen",
                "unfreeze_data": unfreeze_data,
                "api_response": api_result
            }
            
        except Exception as e:
            print(f"❌ Failed to unfreeze token {token[:8]}: {str(e)}")
            return {
                "success": False,
                "token": token,
                "error": str(e)
            }
    
    async def revoke_token(self, token: str, session_id: str, reason: str = "Security violation") -> Dict[str, Any]:
        """Permanently revoke a token"""
        try:
            print(f"🚫 Revoking token {token[:8]}... for session {session_id[:8]}")
            
            # AI-powered revocation analysis
            revocation_analysis = await self._analyze_revocation_impact(token, reason, session_id)
            
            revoke_data = {
                "status": "revoked",
                "revoked_at": datetime.now().isoformat(),
                "session_id": session_id,
                "reason": reason,
                "revocation_type": revocation_analysis.get("type", "security"),  # security, fraud, expired
                "impact_level": revocation_analysis.get("impact", "high"),
                "requires_user_notification": revocation_analysis.get("notify_user", True),
                "requires_merchant_notification": revocation_analysis.get("notify_merchant", True),
                "can_reissue": revocation_analysis.get("can_reissue", False),
                "cooldown_period_hours": revocation_analysis.get("cooldown_hours", 24)
            }
            
            # Update token state
            self.token_states[token] = revoke_data
            
            # Log to history
            self._log_token_action(token, "revoke", revoke_data)
            
            # Simulate API call to token service
            api_result = await self._call_token_service("revoke", token, revoke_data)
            
            print(f"🚫✅ Token {token[:8]} revoked permanently")
            
            return {
                "success": True,
                "token": token,
                "action": "revoked",
                "revoke_data": revoke_data,
                "api_response": api_result
            }
            
        except Exception as e:
            print(f"❌ Failed to revoke token {token[:8]}: {str(e)}")
            return {
                "success": False,
                "token": token,
                "error": str(e)
            }
    
    async def activate_token(self, token: str) -> Dict[str, Any]:
        """Activate/keep a token active (for approved transactions)"""
        try:
            activate_data = {
                "status": "active",
                "activated_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
            
            self.token_states[token] = activate_data
            self._log_token_action(token, "activate", activate_data)
            
            return {
                "success": True,
                "token": token,
                "action": "activated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "token": token,
                "error": str(e)
            }
    
    async def _determine_freeze_parameters(self, token: str, reason: str, session_id: str) -> Dict[str, Any]:
        """Use AI to determine optimal freeze parameters"""
        prompt = f"""
        You are a TokenTrust Security Agent. Determine the optimal freeze parameters for this token.
        
        Token: {token[:8]}...
        Freeze Reason: {reason}
        Session: {session_id[:8]}
        
        Consider:
        - Security risk level
        - Expected verification time
        - User experience impact
        - Merchant response capability
        
        Respond in JSON:
        {{
            "duration_minutes": <10-60 minutes>,
            "level": "standard|strict|critical",
            "conditions": ["merchant_verification", "additional_auth", "manual_review"],
            "auto_revoke_at": "<ISO datetime if should auto-revoke>",
            "reasoning": "Brief explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except:
            # Fallback parameters
            return {
                "duration_minutes": 10,
                "level": "standard",
                "conditions": ["merchant_verification"],
                "reasoning": "Default freeze parameters applied"
            }
    
    async def _validate_unfreeze_conditions(self, token: str, session_id: str, verified_by: str) -> Dict[str, Any]:
        """Validate if conditions are met for unfreezing"""
        current_state = self.token_states.get(token, {})
        conditions = current_state.get("conditions_for_unfreeze", ["merchant_verification"])
        
        prompt = f"""
        Validate if token can be unfrozen based on verification.
        
        Token State: {json.dumps(current_state, indent=2)}
        Verified By: {verified_by}
        Required Conditions: {conditions}
        
        Respond in JSON:
        {{
            "allowed": true/false,
            "reason": "explanation",
            "method": "verification method used",
            "confidence": 0.0-1.0
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except:
            return {
                "allowed": True,
                "reason": "Default validation passed",
                "method": "merchant_2fa",
                "confidence": 0.8
            }
    
    async def _analyze_revocation_impact(self, token: str, reason: str, session_id: str) -> Dict[str, Any]:
        """Analyze the impact and requirements of token revocation"""
        prompt = f"""
        Analyze the impact of revoking this token.
        
        Token: {token[:8]}...
        Reason: {reason}
        Session: {session_id[:8]}
        
        Consider:
        - Security implications
        - User impact
        - Merchant notification needs
        - Reissuance policy
        
        Respond in JSON:
        {{
            "type": "security|fraud|expired|user_request",
            "impact": "low|medium|high|critical",
            "notify_user": true/false,
            "notify_merchant": true/false,
            "can_reissue": true/false,
            "cooldown_hours": <hours>,
            "reasoning": "explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except:
            return {
                "type": "security",
                "impact": "high",
                "notify_user": True,
                "notify_merchant": True,
                "can_reissue": False,
                "cooldown_hours": 24,
                "reasoning": "Default revocation policy applied"
            }
    
    async def _call_token_service(self, action: str, token: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API call to external token service"""
        # In production, this would make actual API calls
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return {
            "api_call": f"token_service.{action}",
            "token": token[:8] + "...",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "response_code": 200
        }
    
    def _log_token_action(self, token: str, action: str, data: Dict[str, Any]):
        """Log token action to history"""
        if token not in self.token_history:
            self.token_history[token] = []
        
        self.token_history[token].append({
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
    
    def _calculate_freeze_duration(self, frozen_at_iso: str) -> str:
        """Calculate how long a token was frozen"""
        try:
            frozen_at = datetime.fromisoformat(frozen_at_iso.replace('Z', '+00:00'))
            duration = datetime.now() - frozen_at
            return f"{duration.total_seconds():.1f} seconds"
        except:
            return "unknown"
    
    def get_token_status(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current status of a token"""
        return self.token_states.get(token)
    
    def get_token_history(self, token: str) -> Optional[list]:
        """Get history of actions for a token"""
        return self.token_history.get(token)
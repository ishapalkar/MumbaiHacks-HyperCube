import os
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()
from .risk_agent import RiskAgent
from .token_manager import TokenManager
from .merchant_communicator import MerchantCommunicator
from .verification_agent import VerificationAgent

class TokenTrustOrchestrator:
    """
    Main orchestrator that manages the complete token trust workflow:
    1. Risk Assessment
    2. Token Freezing/Management
    3. Merchant Communication for 2FA
    4. Verification Process
    5. Final Decision (Unfreeze/Revoke)
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
        
        # Initialize specialized agents
        self.risk_agent = RiskAgent()
        self.token_manager = TokenManager()
        self.merchant_communicator = MerchantCommunicator()
        self.verification_agent = VerificationAgent()
        
        # Active sessions tracking
        self.active_sessions = {}
        
        # Simple conversation context (instead of LangChain memory)
        self.conversation_context = {}
    
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for processing a transaction through the complete workflow
        """
        session_id = str(uuid.uuid4())
        
        try:
            # Step 1: Initial Risk Assessment
            print(f"🔍 [Session {session_id[:8]}] Starting risk assessment...")
            risk_result = await self._assess_risk(transaction_data, session_id)
            
            # Store session data
            self.active_sessions[session_id] = {
                "transaction_data": transaction_data,
                "risk_result": risk_result,
                "status": "risk_assessed",
                "created_at": datetime.now(),
                "steps": [{"step": "risk_assessment", "result": risk_result, "timestamp": datetime.now()}]
            }
            
            # Step 2: Decision Making based on Risk Score
            decision_result = await self._make_decision(risk_result, session_id)
            
            # Update session
            self.active_sessions[session_id]["decision"] = decision_result
            self.active_sessions[session_id]["steps"].append({
                "step": "decision_making", 
                "result": decision_result, 
                "timestamp": datetime.now()
            })
            
            # Step 3: Execute Action based on Decision
            if decision_result["action"] == "APPROVE":
                final_result = await self._approve_transaction(session_id)
            elif decision_result["action"] == "FREEZE_AND_VERIFY":
                final_result = await self._freeze_and_verify_workflow(session_id)
            elif decision_result["action"] == "REVOKE":
                final_result = await self._revoke_token(session_id)
            else:
                final_result = {"status": "error", "message": "Unknown action"}
            
            # Final session update
            self.active_sessions[session_id]["final_result"] = final_result
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["steps"].append({
                "step": "final_action", 
                "result": final_result, 
                "timestamp": datetime.now()
            })
            
            return {
                "session_id": session_id,
                "transaction_data": transaction_data,
                "risk_assessment": risk_result,
                "decision": decision_result,
                "final_result": final_result,
                "workflow_steps": self.active_sessions[session_id]["steps"]
            }
            
        except Exception as e:
            error_result = {
                "status": "error", 
                "message": f"Orchestrator error: {str(e)}",
                "session_id": session_id
            }
            
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "error"
                self.active_sessions[session_id]["error"] = str(e)
            
            return error_result
    
    async def _assess_risk(self, transaction_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Step 1: Assess transaction risk using the RiskAgent"""
        try:
            risk_result = self.risk_agent.analyze_risk(transaction_data)
            
            print(f"📊 [Session {session_id[:8]}] Risk Score: {risk_result['risk_score']}/100")
            print(f"📋 [Session {session_id[:8]}] Decision: {risk_result['decision']}")
            
            return risk_result
            
        except Exception as e:
            print(f"❌ [Session {session_id[:8]}] Risk assessment failed: {str(e)}")
            return {
                "risk_score": 75,  # Default to high caution
                "decision": "CHALLENGE",
                "explanation": f"Risk assessment failed: {str(e)}"
            }
    
    async def _make_decision(self, risk_result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Step 2: Make decision based on risk score using AI agent"""
        
        decision_prompt = f"""
        You are a TokenTrust Decision Agent. Based on the risk assessment, determine the appropriate action.
        
        Risk Assessment Results:
        - Risk Score: {risk_result['risk_score']}/100
        - AI Decision: {risk_result['decision']}
        - Explanation: {risk_result['explanation']}
        
        Decision Rules:
        - Risk Score 0-30: APPROVE (Low risk, allow transaction)
        - Risk Score 31-70: FREEZE_AND_VERIFY (Medium/High risk, freeze token and request merchant 2FA)
        - Risk Score 71-100: REVOKE (Very high risk, revoke token immediately)
        
        Respond in JSON format:
        {{
            "action": "APPROVE|FREEZE_AND_VERIFY|REVOKE",
            "reasoning": "Brief explanation of why this action was chosen",
            "requires_merchant_2fa": true/false,
            "estimated_verification_time": "time in minutes"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=decision_prompt)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            decision_data = json.loads(response_text.strip().replace("```json", "").replace("```", ""))
            
            print(f"⚖️  [Session {session_id[:8]}] Decision: {decision_data['action']}")
            print(f"💭 [Session {session_id[:8]}] Reasoning: {decision_data['reasoning']}")
            
            return decision_data
            
        except Exception as e:
            print(f"❌ [Session {session_id[:8]}] Decision making failed: {str(e)}")
            # Fallback decision based on risk score
            risk_score = risk_result['risk_score']
            if risk_score <= 30:
                action = "APPROVE"
            elif risk_score <= 70:
                action = "FREEZE_AND_VERIFY"
            else:
                action = "REVOKE"
            
            return {
                "action": action,
                "reasoning": f"Fallback decision based on risk score {risk_score}",
                "requires_merchant_2fa": action == "FREEZE_AND_VERIFY",
                "estimated_verification_time": "5-10 minutes"
            }
    
    async def _approve_transaction(self, session_id: str) -> Dict[str, Any]:
        """Step 3a: Approve transaction (low risk)"""
        try:
            session = self.active_sessions[session_id]
            token = session["transaction_data"].get("token")
            
            # Keep token active
            approval_result = await self.token_manager.activate_token(token)
            
            print(f"✅ [Session {session_id[:8]}] Transaction approved - token remains active")
            
            return {
                "status": "approved",
                "message": "Transaction approved - low risk detected",
                "token_status": "active",
                "action_taken": "none"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Approval failed: {str(e)}"}
    
    async def _freeze_and_verify_workflow(self, session_id: str) -> Dict[str, Any]:
        """Step 3b: Freeze token and initiate merchant verification workflow"""
        try:
            session = self.active_sessions[session_id]
            transaction_data = session["transaction_data"]
            token = transaction_data.get("token")
            merchant_id = transaction_data.get("merchant_id")
            
            print(f"🧊 [Session {session_id[:8]}] Freezing token and starting verification...")
            
            # Step 1: Freeze the token
            freeze_result = await self.token_manager.freeze_token(token, session_id)
            
            if not freeze_result["success"]:
                return {"status": "error", "message": "Failed to freeze token"}
            
            # Step 2: Notify merchant about 2FA requirement
            merchant_notification = await self.merchant_communicator.request_2fa_verification(
                merchant_id, token, session_id, transaction_data
            )
            
            if not merchant_notification["success"]:
                # If merchant notification fails, still proceed but log it
                print(f"⚠️  [Session {session_id[:8]}] Merchant notification failed, but continuing...")
            
            # Step 3: Wait for merchant response (with timeout)
            verification_result = await self._wait_for_merchant_verification(session_id, timeout=600)  # 10 minutes
            
            # Step 4: Process verification result
            final_decision = await self._process_verification_result(session_id, verification_result)
            
            return final_decision
            
        except Exception as e:
            print(f"❌ [Session {session_id[:8]}] Freeze and verify workflow failed: {str(e)}")
            return {"status": "error", "message": f"Verification workflow failed: {str(e)}"}
    
    async def _wait_for_merchant_verification(self, session_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for merchant to complete 2FA verification"""
        start_time = datetime.now()
        check_interval = 10  # Check every 10 seconds
        
        print(f"⏳ [Session {session_id[:8]}] Waiting for merchant verification (timeout: {timeout}s)...")
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check if merchant has responded
            verification_status = await self.merchant_communicator.check_verification_status(session_id)
            
            if verification_status["status"] == "completed":
                print(f"✅ [Session {session_id[:8]}] Merchant verification completed")
                return verification_status
            elif verification_status["status"] == "failed":
                print(f"❌ [Session {session_id[:8]}] Merchant verification failed")
                return verification_status
            
            # Wait before next check
            await asyncio.sleep(check_interval)
        
        # Timeout reached
        print(f"⏰ [Session {session_id[:8]}] Merchant verification timed out")
        return {
            "status": "timeout",
            "message": "Merchant verification timed out",
            "verified": False
        }
    
    async def _process_verification_result(self, session_id: str, verification_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the result of merchant verification and take final action"""
        try:
            session = self.active_sessions[session_id]
            token = session["transaction_data"].get("token")
            
            if verification_result["status"] == "completed" and verification_result.get("verified", False):
                # Merchant verified user - unfreeze token
                print(f"🔓 [Session {session_id[:8]}] User verified by merchant - unfreezing token")
                
                unfreeze_result = await self.token_manager.unfreeze_token(token, session_id)
                
                return {
                    "status": "verified_and_approved",
                    "message": "User verified by merchant - token unfrozen and transaction approved",
                    "token_status": "active",
                    "verification_method": "merchant_2fa",
                    "verified_by": verification_result.get("verified_by"),
                    "verification_time": verification_result.get("verification_time")
                }
                
            else:
                # Merchant could not verify user or verification failed/timed out - revoke token
                print(f"🚫 [Session {session_id[:8]}] User not verified - revoking token")
                
                revoke_result = await self.token_manager.revoke_token(token, session_id, 
                    reason=verification_result.get("message", "Merchant verification failed"))
                
                return {
                    "status": "not_verified_revoked",
                    "message": "User could not be verified - token revoked for security",
                    "token_status": "revoked",
                    "reason": verification_result.get("message", "Verification failed"),
                    "revocation_time": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ [Session {session_id[:8]}] Processing verification result failed: {str(e)}")
            return {"status": "error", "message": f"Failed to process verification: {str(e)}"}
    
    async def _revoke_token(self, session_id: str) -> Dict[str, Any]:
        """Step 3c: Immediately revoke token (very high risk)"""
        try:
            session = self.active_sessions[session_id]
            token = session["transaction_data"].get("token")
            
            print(f"🚫 [Session {session_id[:8]}] High risk detected - revoking token immediately")
            
            revoke_result = await self.token_manager.revoke_token(token, session_id, 
                reason="High risk transaction detected")
            
            return {
                "status": "revoked",
                "message": "Token revoked due to high risk transaction",
                "token_status": "revoked",
                "reason": "High risk score exceeded threshold",
                "revocation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Revocation failed: {str(e)}"}
    
    async def handle_merchant_response(self, session_id: str, user_response: str, verification_method: str) -> Dict[str, Any]:
        """Handle merchant verification response and complete the workflow"""
        try:
            if session_id not in self.active_sessions:
                return {"status": "error", "message": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            # Process the verification response
            verification_result = await self.verification_agent.process_verification(
                session_id=session_id,
                user_response=user_response,
                verification_method=verification_method,
                transaction_context=session.get("transaction_data", {})
            )
            
            # Update session with verification result
            session["verification_result"] = verification_result
            session["steps"].append({
                "step": "merchant_verification",
                "result": verification_result,
                "timestamp": datetime.now()
            })
            
            # Process the final result based on verification
            final_result = await self._process_verification_result(verification_result, session_id)
            
            # Update final session state
            session["final_result"] = final_result
            session["status"] = "completed"
            session["workflow_complete"] = True
            
            return {
                "status": "completed",
                "final_decision": final_result.get("status"),
                "final_status": final_result.get("status"),
                "token_status": final_result.get("token_status"),
                "message": final_result.get("message"),
                "workflow_complete": True,
                "verification_successful": verification_result.get("approved", False)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to handle merchant response: {str(e)}"}

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a session"""
        return self.active_sessions.get(session_id)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = [
            session_id for session_id, session_data in self.active_sessions.items()
            if session_data.get("created_at", cutoff_time) < cutoff_time
        ]
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            
        if sessions_to_remove:
            print(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")
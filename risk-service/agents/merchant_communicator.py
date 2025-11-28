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

class MerchantCommunicator:
    """
    Agent responsible for communicating with merchants:
    - Sending 2FA verification requests
    - Managing communication channels (email, SMS, app notifications)
    - Tracking merchant response status
    - Handling merchant authentication
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not found or not set properly. "
                "Please set your Groq API key in the .env file."
            )
        
        self.llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.3-70b-versatile",
            api_key=self.groq_api_key
        )
        
        # In-memory storage for pending verifications (use Redis in production)
        self.pending_verifications = {}
        self.merchant_profiles = {}
        self.communication_history = {}
    
    async def request_2fa_verification(self, merchant_id: str, token: str, session_id: str, 
                                    transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send 2FA verification request to merchant"""
        try:
            print(f"📞 Requesting 2FA verification from merchant {merchant_id} for session {session_id[:8]}")
            
            # Get or create merchant profile
            merchant_profile = await self._get_merchant_profile(merchant_id)
            
            # Generate personalized communication strategy
            communication_strategy = await self._determine_communication_strategy(
                merchant_id, merchant_profile, transaction_data, session_id
            )
            
            # Create verification request
            verification_request = {
                "verification_id": f"2fa_{session_id}",
                "merchant_id": merchant_id,
                "token": token[:8] + "...",
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "transaction_data": {
                    "amount": transaction_data.get("amount"),
                    "user_info": transaction_data.get("user_info", "Anonymous"),
                    "location": transaction_data.get("current_location"),
                    "time": datetime.now().isoformat()
                },
                "communication_strategy": communication_strategy,
                "expires_at": communication_strategy.get("expires_at"),
                "attempts": 0,
                "max_attempts": 3
            }
            
            # Store pending verification
            self.pending_verifications[session_id] = verification_request
            
            # Send verification request through multiple channels
            send_result = await self._send_verification_request(verification_request, merchant_profile)
            
            # Log communication
            self._log_communication(merchant_id, "2fa_request_sent", verification_request)
            
            print(f"📞✅ 2FA request sent to merchant {merchant_id}")
            
            return {
                "success": True,
                "verification_id": verification_request["verification_id"],
                "communication_channels": send_result.get("channels_used", []),
                "estimated_response_time": communication_strategy.get("estimated_response_time", "5-10 minutes"),
                "expires_at": verification_request["expires_at"]
            }
            
        except Exception as e:
            print(f"❌ Failed to send 2FA request to merchant {merchant_id}: {str(e)}")
            return {
                "success": False,
                "merchant_id": merchant_id,
                "error": str(e)
            }
    
    async def check_verification_status(self, session_id: str) -> Dict[str, Any]:
        """Check if merchant has completed verification"""
        verification = self.pending_verifications.get(session_id)
        
        if not verification:
            return {
                "status": "not_found",
                "message": "No pending verification found for this session"
            }
        
        # Check if verification has expired
        if self._is_verification_expired(verification):
            verification["status"] = "expired"
            return {
                "status": "timeout",
                "message": "Verification request expired",
                "verified": False
            }
        
        # Simulate checking external systems for merchant response
        # In production, this would check actual merchant response systems
        response_status = await self._check_merchant_response_systems(session_id)
        
        if response_status["has_response"]:
            verification["status"] = "completed"
            verification["completed_at"] = datetime.now().isoformat()
            verification["merchant_response"] = response_status["response"]
            
            return {
                "status": "completed",
                "verified": response_status["response"]["verified"],
                "verified_by": response_status["response"]["verified_by"],
                "verification_time": response_status["response"]["verification_time"],
                "verification_method": response_status["response"]["method"],
                "merchant_notes": response_status["response"].get("notes", "")
            }
        
        return {
            "status": "pending",
            "message": "Still waiting for merchant response",
            "time_remaining": self._calculate_time_remaining(verification)
        }
    
    async def simulate_merchant_response(self, session_id: str, verified: bool, 
                                       verified_by: str = "merchant_staff", 
                                       method: str = "phone_verification") -> Dict[str, Any]:
        """Simulate merchant providing verification response (for testing)"""
        try:
            verification = self.pending_verifications.get(session_id)
            
            if not verification:
                return {"success": False, "error": "No pending verification found"}
            
            # AI-powered validation of merchant response
            response_validation = await self._validate_merchant_response(
                session_id, verified, verified_by, method
            )
            
            merchant_response = {
                "verified": verified,
                "verified_by": verified_by,
                "verification_time": datetime.now().isoformat(),
                "method": method,
                "confidence": response_validation.get("confidence", 0.8),
                "validation_notes": response_validation.get("notes", ""),
                "session_id": session_id
            }
            
            # Update verification record
            verification["status"] = "completed"
            verification["completed_at"] = datetime.now().isoformat()
            verification["merchant_response"] = merchant_response
            
            # Log the response
            self._log_communication(verification["merchant_id"], "2fa_response_received", merchant_response)
            
            print(f"📞✅ Merchant response recorded: {'VERIFIED' if verified else 'NOT VERIFIED'}")
            
            return {
                "success": True,
                "session_id": session_id,
                "response_recorded": True,
                "merchant_response": merchant_response
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_merchant_profile(self, merchant_id: str) -> Dict[str, Any]:
        """Get or create merchant communication profile"""
        if merchant_id in self.merchant_profiles:
            return self.merchant_profiles[merchant_id]
        
        # Create default profile (in production, fetch from database)
        profile = {
            "merchant_id": merchant_id,
            "name": f"Merchant {merchant_id}",
            "preferred_channels": ["email", "sms", "app_notification"],
            "response_time_avg_minutes": 7,
            "timezone": "Asia/Kolkata",
            "language": "en",
            "2fa_success_rate": 0.85,
            "last_active": datetime.now().isoformat(),
            "communication_preferences": {
                "urgent_notifications": True,
                "batch_notifications": False,
                "weekend_contact": True
            }
        }
        
        self.merchant_profiles[merchant_id] = profile
        return profile
    
    async def _determine_communication_strategy(self, merchant_id: str, merchant_profile: Dict[str, Any], 
                                              transaction_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Use AI to determine optimal communication strategy"""
        prompt = f"""
        You are a MerchantCommunication AI agent. Determine the best strategy to contact this merchant for urgent 2FA verification.
        
        Merchant Profile:
        {json.dumps(merchant_profile, indent=2)}
        
        Transaction Context:
        - Amount: {transaction_data.get('amount', 'unknown')}
        - Risk Level: {transaction_data.get('risk_level', 'medium')}
        - User Location: {transaction_data.get('current_location', 'unknown')}
        - Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Consider:
        - Urgency level
        - Merchant's preferred channels
        - Time zone and business hours
        - Historical response patterns
        
        Respond in JSON:
        {{
            "primary_channel": "email|sms|app_notification|phone",
            "secondary_channels": ["backup channels"],
            "message_tone": "urgent|standard|friendly",
            "estimated_response_time": "X minutes",
            "retry_strategy": "immediate|delayed|escalating",
            "expires_in_minutes": <timeout>,
            "priority_level": "low|medium|high|critical",
            "reasoning": "explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            strategy = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
            
            # Add calculated expiry time
            expires_in = strategy.get("expires_in_minutes", 10)
            expires_at = datetime.now().replace(microsecond=0)
            expires_at = expires_at.replace(second=0)  # Round to minute
            from datetime import timedelta
            strategy["expires_at"] = (expires_at + timedelta(minutes=expires_in)).isoformat()
            
            return strategy
            
        except Exception as e:
            print(f"⚠️  Failed to determine communication strategy: {str(e)}")
            # Fallback strategy
            from datetime import timedelta
            return {
                "primary_channel": "email",
                "secondary_channels": ["sms"],
                "message_tone": "urgent",
                "estimated_response_time": "10 minutes",
                "expires_in_minutes": 15,
                "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(),
                "priority_level": "high",
                "reasoning": "Default urgent strategy applied"
            }
    
    async def _send_verification_request(self, verification_request: Dict[str, Any], 
                                       merchant_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Send verification request through multiple channels"""
        strategy = verification_request["communication_strategy"]
        channels_used = []
        
        # Generate personalized message
        message_content = await self._generate_verification_message(verification_request, merchant_profile)
        
        # Send through primary channel
        primary_result = await self._send_through_channel(
            strategy["primary_channel"], 
            merchant_profile, 
            message_content, 
            verification_request
        )
        
        if primary_result["success"]:
            channels_used.append(strategy["primary_channel"])
        
        # Send through secondary channels if configured
        for channel in strategy.get("secondary_channels", []):
            secondary_result = await self._send_through_channel(
                channel, merchant_profile, message_content, verification_request
            )
            if secondary_result["success"]:
                channels_used.append(channel)
        
        return {
            "channels_used": channels_used,
            "primary_success": primary_result["success"],
            "message_content": message_content
        }
    
    async def _generate_verification_message(self, verification_request: Dict[str, Any], 
                                           merchant_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized verification message using AI"""
        prompt = f"""
        Generate a professional, urgent merchant verification message.
        
        Context:
        - Merchant: {merchant_profile.get('name', 'Unknown')}
        - Transaction Amount: {verification_request['transaction_data'].get('amount', 'Unknown')}
        - User Location: {verification_request['transaction_data'].get('location', 'Unknown')}
        - Verification ID: {verification_request['verification_id']}
        
        Requirements:
        - Clear, urgent tone
        - Explain why verification is needed
        - Provide simple response instructions
        - Include security context
        - Be professional but human
        
        Respond in JSON:
        {{
            "subject": "urgent subject line",
            "body": "main message body with clear instructions",
            "sms_version": "short SMS version",
            "call_to_action": "what merchant should do next"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except:
            # Fallback message
            return {
                "subject": "🔒 TokenTrust: Urgent Transaction Verification Required",
                "body": f"A high-risk transaction requires your immediate verification. Amount: {verification_request['transaction_data'].get('amount', 'Unknown')}. Please verify if this customer is legitimate.",
                "sms_version": f"TokenTrust: Verify transaction {verification_request['verification_id'][:8]}. Reply YES if customer verified.",
                "call_to_action": "Please respond within 10 minutes to avoid automatic transaction cancellation."
            }
    
    async def _send_through_channel(self, channel: str, merchant_profile: Dict[str, Any], 
                                  message: Dict[str, Any], verification_request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate sending message through specific channel"""
        # Simulate API calls to external services
        await asyncio.sleep(0.2)  # Simulate network delay
        
        print(f"📤 Sending {channel} to {merchant_profile['merchant_id']}: {message['subject']}")
        
        return {
            "success": True,
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "message_id": f"{channel}_{verification_request['verification_id']}"
        }
    
    async def _check_merchant_response_systems(self, session_id: str) -> Dict[str, Any]:
        """Check external systems for merchant response (simulated)"""
        # In production, this would check:
        # - Email responses
        # - SMS replies
        # - App notifications responses
        # - Phone call logs
        # - Web portal submissions
        
        # For demo purposes, we'll simulate responses
        await asyncio.sleep(0.1)
        
        # This would normally query actual response systems
        return {
            "has_response": False,  # Will be True when simulate_merchant_response is called
            "response": None
        }
    
    async def _validate_merchant_response(self, session_id: str, verified: bool, 
                                        verified_by: str, method: str) -> Dict[str, Any]:
        """Validate merchant response using AI"""
        prompt = f"""
        Validate this merchant verification response for authenticity and reliability.
        
        Response Details:
        - Session: {session_id[:8]}
        - Verified: {verified}
        - Verified By: {verified_by}
        - Method: {method}
        - Response Time: {datetime.now().isoformat()}
        
        Consider:
        - Response authenticity
        - Method reliability
        - Timing patterns
        - Potential fraud indicators
        
        Respond in JSON:
        {{
            "confidence": 0.0-1.0,
            "reliability": "high|medium|low",
            "fraud_risk": "none|low|medium|high",
            "notes": "validation observations",
            "requires_additional_verification": true/false
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except:
            return {
                "confidence": 0.8,
                "reliability": "medium",
                "fraud_risk": "low",
                "notes": "Standard validation applied",
                "requires_additional_verification": False
            }
    
    def _is_verification_expired(self, verification: Dict[str, Any]) -> bool:
        """Check if verification request has expired"""
        try:
            expires_at = datetime.fromisoformat(verification.get("expires_at", ""))
            return datetime.now() > expires_at
        except:
            return False
    
    def _calculate_time_remaining(self, verification: Dict[str, Any]) -> str:
        """Calculate time remaining for verification"""
        try:
            expires_at = datetime.fromisoformat(verification.get("expires_at", ""))
            remaining = expires_at - datetime.now()
            
            if remaining.total_seconds() > 0:
                minutes = int(remaining.total_seconds() // 60)
                return f"{minutes} minutes remaining"
            else:
                return "Expired"
        except:
            return "Unknown"
    
    def _log_communication(self, merchant_id: str, event_type: str, data: Dict[str, Any]):
        """Log communication events"""
        if merchant_id not in self.communication_history:
            self.communication_history[merchant_id] = []
        
        self.communication_history[merchant_id].append({
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
    
    def get_pending_verifications(self) -> Dict[str, Any]:
        """Get all pending verifications"""
        return self.pending_verifications
    
    def get_merchant_communication_history(self, merchant_id: str) -> Optional[list]:
        """Get communication history for a merchant"""
        return self.communication_history.get(merchant_id)
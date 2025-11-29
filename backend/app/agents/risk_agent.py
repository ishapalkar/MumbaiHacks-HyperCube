from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
from langchain.schema import SystemMessage
import os
from typing import Dict, List
import json
from datetime import datetime
import random
import logging
from langchain_groq import ChatGroq

class AgenticRiskChecker:
    def __init__(self):
        # Configure logger
        self.logger = logging.getLogger(__name__)

        # Initialize Groq/OpenAI LLM only if the environment key is present.
        # Do NOT use an insecure demo fallback key — that triggers 401 errors.
        groq_key = os.getenv("GROQ_API_KEY")
        # Align default API URL with groq_client.py and use a conservative default model
        groq_api_base = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")

        if groq_key:
            # Use ChatOpenAI configured to point at Groq's OpenAI-compatible endpoint.
            # We pass the real key only when present.
            self.llm = ChatGroq(
            model="mixtral-8x7b-32768",
            temperature=0.1,
            groq_api_key=groq_key
)
            self.tools = self._setup_tools()

            # Create the agentic system
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
                system_message=SystemMessage(content="""You are TokenTrust AI Fraud Investigator. 
            Analyze payment tokens and security context to detect fraud patterns.
            Follow this investigation process:
            1. First validate the token structure and expiration
            2. Analyze transaction context and patterns
            3. Check device and behavioral signals
            4. Evaluate merchant risk profile
            5. Make final risk assessment
            
            Provide clear reasoning for your decisions and conclude with exactly one of:
            FINAL RISK: LOW
            FINAL RISK: MEDIUM  
            FINAL RISK: HIGH""")
            )

            # Masked info for debugging
            try:
                self.logger.info("Initialized Groq-backed LLM; key prefix=%s", groq_key[:6] + "...")
            except Exception:
                self.logger.info("Initialized Groq-backed LLM")
        else:
            # No Groq key set — do not initialize the remote agent to avoid sending
            # invalid/demo keys. The service will run in a safe 'caution' mode.
            self.logger.warning("GROQ_API_KEY not found in environment. LLM agent will NOT be initialized. Set GROQ_API_KEY to enable LLM calls.")
            self.llm = None
            self.tools = self._setup_tools()
            self.agent = None
    
    def _setup_tools(self):
        """Define the investigation tools for the agent"""
        return [
            Tool(
                name="token_validator",
                func=self._validate_token_structure,
                description="Validates token format, expiration, and basic integrity. Returns VALID or INVALID with reason."
            ),
            Tool(
                name="transaction_analyzer", 
                func=self._analyze_transaction_patterns,
                description="Analyzes transaction amount, frequency, and behavioral patterns. Returns risk analysis."
            ),
            Tool(
                name="device_security_check",
                func=self._check_device_security,
                description="Checks device fingerprint, location, and security signals. Returns security assessment."
            ),
            Tool(
                name="merchant_risk_assessor",
                func=self._assess_merchant_risk,
                description="Evaluates merchant reputation and transaction history. Returns merchant risk level."
            ),
            Tool(
                name="fraud_pattern_detector",
                func=self._detect_fraud_patterns,
                description="Matches against known fraud patterns and anomalies. Returns pattern analysis."
            )
        ]
    
    def _validate_token_structure(self, token_data: str) -> str:
        """Tool 1: Validate token structure"""
        try:
            data = json.loads(token_data)
            token = data.get('token', '')
            
            # Basic token validation
            if not token.startswith('tok_'):
                return "INVALID: Token format incorrect - must start with 'tok_'"
            
            if len(token) < 10:
                return "INVALID: Token too short - minimum 10 characters required"
            
            # Check expiration (mock)
            token_age = data.get('token_age_minutes', 0)
            if token_age > 1440:  # 24 hours
                return f"INVALID: Token expired - age {token_age} minutes exceeds 24h limit"
            
            return "VALID: Token structure and expiration are OK"
        except Exception as e:
            return f"ERROR: Token validation failed - {str(e)}"
    
    def _analyze_transaction_patterns(self, transaction_data: str) -> str:
        """Tool 2: Analyze transaction patterns"""
        try:
            data = json.loads(transaction_data)
            amount = data.get('amount', 0)
            user_history = data.get('user_transaction_history', {})
            
            analysis = []
            
            # Amount analysis
            avg_amount = user_history.get('avg_amount', 1000)
            if amount > avg_amount * 10:
                analysis.append("HIGH_RISK: Amount is 10x user's historical average")
            elif amount > avg_amount * 5:
                analysis.append("MEDIUM_RISK: Amount is 5x user's historical average")
            else:
                analysis.append("LOW_RISK: Amount within normal range")
            
            # Frequency analysis
            recent_tx_count = user_history.get('recent_transactions_1h', 0)
            if recent_tx_count > 10:
                analysis.append("HIGH_RISK: Too many transactions in last hour")
            elif recent_tx_count > 5:
                analysis.append("MEDIUM_RISK: Elevated transaction frequency")
            else:
                analysis.append("LOW_RISK: Normal transaction frequency")
            
            return " | ".join(analysis)
        except Exception as e:
            return f"ERROR: Transaction analysis failed - {str(e)}"
    
    def _check_device_security(self, device_data: str) -> str:
        """Tool 3: Check device security signals"""
        try:
            data = json.loads(device_data)
            
            signals = []
            
            # Device fingerprint check
            device_trust_score = data.get('device_trust_score', 50)
            if device_trust_score < 30:
                signals.append("HIGH_RISK: Low device trust score")
            elif device_trust_score < 70:
                signals.append("MEDIUM_RISK: Moderate device trust score")
            else:
                signals.append("LOW_RISK: High device trust score")
            
            # Location analysis
            usual_location = data.get('usual_location', '')
            current_location = data.get('current_location', '')
            if usual_location and current_location != usual_location:
                signals.append("MEDIUM_RISK: Geographic location changed")
            
            # VPN detection
            if data.get('vpn_detected', False):
                signals.append("HIGH_RISK: VPN usage detected")
            
            # New device
            if data.get('new_device', False):
                signals.append("MEDIUM_RISK: Transaction from new device")
            
            return " | ".join(signals) if signals else "LOW_RISK: No device security issues detected"
        except Exception as e:
            return f"ERROR: Device security check failed - {str(e)}"
    
    def _assess_merchant_risk(self, merchant_data: str) -> str:
        """Tool 4: Assess merchant risk"""
        try:
            data = json.loads(merchant_data)
            merchant_id = data.get('merchant_id', 'unknown')
            
            # Mock merchant risk database
            merchant_risk_profiles = {
                'amazon': {'risk_score': 10, 'category': 'marketplace', 'trust_level': 'high'},
                'flipkart': {'risk_score': 15, 'category': 'marketplace', 'trust_level': 'high'},
                'myntra': {'risk_score': 20, 'category': 'fashion', 'trust_level': 'high'},
                'new_merchant_123': {'risk_score': 70, 'category': 'unknown', 'trust_level': 'low'},
                'digital_goods_store': {'risk_score': 60, 'category': 'digital', 'trust_level': 'medium'},
                'gift_card_shop': {'risk_score': 75, 'category': 'gift_cards', 'trust_level': 'low'}
            }
            
            profile = merchant_risk_profiles.get(merchant_id, {'risk_score': 50, 'category': 'general', 'trust_level': 'medium'})
            risk_score = profile['risk_score']
            
            if risk_score > 60:
                return f"HIGH_RISK: Merchant {merchant_id} has low trust level"
            elif risk_score > 30:
                return f"MEDIUM_RISK: Merchant {merchant_id} has moderate trust level"
            else:
                return f"LOW_RISK: Merchant {merchant_id} has high trust level"
        except Exception as e:
            return f"ERROR: Merchant risk assessment failed - {str(e)}"
    
    def _detect_fraud_patterns(self, pattern_data: str) -> str:
        """Tool 5: Detect fraud patterns"""
        try:
            data = json.loads(pattern_data)
            
            patterns = []
            
            # Velocity pattern
            transactions_last_hour = data.get('transactions_last_hour', 0)
            if transactions_last_hour > 15:
                patterns.append("HIGH_RISK: Transaction velocity very high")
            elif transactions_last_hour > 8:
                patterns.append("MEDIUM_RISK: Elevated transaction velocity")
            
            # Amount pattern
            amount = data.get('amount', 0)
            user_avg_amount = data.get('user_avg_amount', 1000)
            if amount > 50000 and user_avg_amount < 5000:
                patterns.append("HIGH_RISK: Large amount inconsistent with user profile")
            elif amount > 20000 and user_avg_amount < 3000:
                patterns.append("MEDIUM_RISK: Elevated amount for user profile")
            
            # Time pattern
            if data.get('unusual_time', False):
                patterns.append("MEDIUM_RISK: Unusual transaction time detected")
            
            # Behavioral pattern
            if data.get('rushed_transaction', False):
                patterns.append("MEDIUM_RISK: Rushed transaction behavior")
            
            return " | ".join(patterns) if patterns else "LOW_RISK: No known fraud patterns detected"
        except Exception as e:
            return f"ERROR: Fraud pattern detection failed - {str(e)}"
    
    def assess_risk(self, token: str, merchant_id: str, security_context: Dict) -> Dict:
        """Main risk assessment method that uses agentic AI"""
        
        # Prepare data for tools
        token_data = json.dumps({
            'token': token,
            'token_age_minutes': security_context.get('token_age_minutes', 5),
            'merchant_id': merchant_id
        })
        
        transaction_data = json.dumps({
            'amount': security_context.get('amount', 0),
            'user_transaction_history': security_context.get('user_history', {}),
            'currency': security_context.get('currency', 'INR')
        })
        
        device_data = json.dumps({
            'device_trust_score': security_context.get('device_trust_score', 50),
            'usual_location': security_context.get('usual_location', ''),
            'current_location': security_context.get('current_location', ''),
            'vpn_detected': security_context.get('vpn_detected', False),
            'new_device': security_context.get('new_device', False)
        })
        
        merchant_data = json.dumps({
            'merchant_id': merchant_id,
            'transaction_amount': security_context.get('amount', 0)
        })
        
        pattern_data = json.dumps({
            'transactions_last_hour': security_context.get('recent_transactions', 0),
            'amount': security_context.get('amount', 0),
            'user_avg_amount': security_context.get('user_avg_amount', 1000),
            'unusual_time': security_context.get('unusual_time', False),
            'rushed_transaction': security_context.get('rushed_transaction', False)
        })
        
        # Agentic investigation
        investigation_prompt = f"""
        Conduct a comprehensive fraud investigation for this payment:

        TOKEN: {token}
        MERCHANT: {merchant_id}
        AMOUNT: ₹{security_context.get('amount', 0)}
        
        Use all available tools to investigate:
        1. Validate token integrity and expiration
        2. Analyze transaction patterns and amounts
        3. Check device security and location
        4. Assess merchant reputation
        5. Detect known fraud patterns

        After your investigation, provide your final risk assessment.
        Conclude with exactly one of:
        FINAL RISK: LOW
        FINAL RISK: MEDIUM  
        FINAL RISK: HIGH
        """
        
        try:
            self.logger.info("Starting Agentic AI Investigation for token=%s merchant=%s amount=%s", token, merchant_id, security_context.get('amount', 0))

            if self.agent is None:
                # No LLM configured — return cautious fallback rather than attempting a call
                self.logger.warning("LLM agent not configured; returning MEDIUM caution assessment.")
                return {
                    "risk_level": "MEDIUM",
                    "reasoning": "No LLM configured (GROQ_API_KEY missing). Applied caution.",
                    "agent_id": "TokenTrust_Groq_Agent_1",
                    "timestamp": datetime.now().isoformat(),
                    "token_valid": "UNKNOWN",
                    "investigation_complete": False
                }

            # Run the initialized agent
            result = self.agent.run(investigation_prompt)
            
            # Parse the agent's response to determine risk level
            risk_level = self._parse_risk_level(result)
            token_valid = self._check_token_validity(result)
            
            return {
                "risk_level": risk_level,
                "reasoning": result,
                "agent_id": "TokenTrust_Groq_Agent_1",
                "timestamp": datetime.now().isoformat(),
                "token_valid": token_valid,
                "investigation_complete": True
            }
            
        except Exception as e:
            err = str(e)
            self.logger.error("Agent error: %s", err)

            # Detect common model / access errors and return actionable guidance
            if any(substr in err.lower() for substr in ("does not exist", "invalid_request_error", "404", "model not found", "you do not have access")):
                reason = (
                    f"Agent system temporarily unavailable: model not found or access denied ({err}). "
                    "Please verify `GROQ_MODEL` is set to a model you have access to, and that `GROQ_API_URL` is correct for your Groq account. "
                    "Applying caution."
                )
            else:
                reason = f"Agent system temporarily unavailable: {err} - Applying caution"

            # Fallback if agent fails
            return {
                "risk_level": "MEDIUM",
                "reasoning": reason,
                "agent_id": "TokenTrust_Groq_Agent_1",
                "timestamp": datetime.now().isoformat(),
                "token_valid": "UNKNOWN",
                "investigation_complete": False
            }
    
    def _parse_risk_level(self, agent_response: str) -> str:
        """Parse the agent's response to determine risk level"""
        response_lower = agent_response.lower()
        
        # Look for explicit risk indicators
        if "final risk: high" in response_lower:
            return "HIGH"
        elif "final risk: medium" in response_lower:
            return "MEDIUM"
        elif "final risk: low" in response_lower:
            return "LOW"
        
        # Fallback pattern matching
        if any(word in response_lower for word in ['high risk', 'high:', 'block', 'fraud', 'invalid', 'suspicious']):
            return "HIGH"
        elif any(word in response_lower for word in ['medium risk', 'medium:', 'caution', 'verify', 'additional verification']):
            return "MEDIUM" 
        else:
            return "LOW"
    
    def _check_token_validity(self, agent_response: str) -> str:
        """Check if token is valid based on agent response"""
        response_lower = agent_response.lower()
        
        if any(word in response_lower for word in ['invalid', 'expired', 'invalid token']):
            return "INVALID"
        elif any(word in response_lower for word in ['valid', 'token ok', 'token valid']):
            return "VALID"
        else:
            return "UNKNOWN"
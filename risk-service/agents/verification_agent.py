import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

class VerificationAgent:
    """
    Agent responsible for handling verification processes:
    - Analyzing verification attempts
    - Validating merchant responses
    - Managing verification workflows
    - Learning from verification patterns
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
        
        # Storage for verification analytics
        self.verification_history = {}
        self.merchant_verification_patterns = {}
        self.fraud_patterns = {}
    
    def analyze_verification_attempt(self, session_id: str, merchant_id: str, 
                                   transaction_data: Dict[str, Any], 
                                   risk_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a verification attempt and provide guidance"""
        try:
            print(f"🔍 Analyzing verification attempt for session {session_id[:8]}")
            
            # Get merchant verification history
            merchant_history = self.merchant_verification_patterns.get(merchant_id, {})
            
            # Analyze verification requirements
            analysis_result = self._perform_verification_analysis(
                merchant_id, transaction_data, risk_context, merchant_history
            )
            
            # Store analysis
            self.verification_history[session_id] = {
                "analysis": analysis_result,
                "merchant_id": merchant_id,
                "transaction_data": transaction_data,
                "risk_context": risk_context,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🔍✅ Verification analysis completed for session {session_id[:8]}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Verification analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_recommendation": "Standard verification required"
            }
    
    def validate_verification_response(self, session_id: str, merchant_response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and analyze merchant verification response"""
        try:
            print(f"✅ Validating merchant response for session {session_id[:8]}")
            
            # Get verification history
            verification_context = self.verification_history.get(session_id, {})
            
            # Perform AI-powered validation
            validation_result = self._validate_response_authenticity(
                merchant_response, verification_context
            )
            
            # Check for fraud patterns
            fraud_analysis = self._analyze_fraud_patterns(merchant_response, verification_context)
            
            # Update merchant patterns
            self._update_merchant_patterns(
                verification_context.get("merchant_id"), 
                merchant_response, 
                validation_result
            )
            
            final_validation = {
                "session_id": session_id,
                "validation": validation_result,
                "fraud_analysis": fraud_analysis,
                "confidence_score": self._calculate_confidence_score(validation_result, fraud_analysis),
                "recommendation": self._get_final_recommendation(validation_result, fraud_analysis),
                "validated_at": datetime.now().isoformat()
            }
            
            print(f"✅ Response validation completed - Confidence: {final_validation['confidence_score']:.2f}")
            
            return final_validation
            
        except Exception as e:
            print(f"❌ Response validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "confidence_score": 0.3,
                "recommendation": "REJECT"
            }
    
    def _perform_verification_analysis(self, merchant_id: str, transaction_data: Dict[str, Any],
                                     risk_context: Dict[str, Any], merchant_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze verification requirements using AI"""
        
        prompt = f"""
        You are a VerificationAgent AI. Analyze this verification scenario and provide recommendations.
        
        Merchant ID: {merchant_id}
        Transaction Data: {json.dumps(transaction_data, indent=2)}
        Risk Context: {json.dumps(risk_context, indent=2)}
        Merchant History: {json.dumps(merchant_history, indent=2)}
        
        Consider:
        1. Risk level and verification urgency
        2. Merchant's historical verification success rate
        3. Transaction patterns and anomalies
        4. Appropriate verification methods
        5. Fraud prevention measures
        
        Respond in JSON:
        {{
            "verification_priority": "low|medium|high|critical",
            "recommended_methods": ["phone", "email", "sms", "in_person", "app"],
            "verification_complexity": "simple|standard|enhanced|multi_factor",
            "expected_success_rate": 0.0-1.0,
            "time_sensitivity": "flexible|moderate|urgent|critical",
            "additional_checks": ["id_verification", "location_check", "amount_confirmation"],
            "risk_factors": ["specific risk factors identified"],
            "merchant_reliability": 0.0-1.0,
            "reasoning": "detailed explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except Exception as e:
            print(f"⚠️  AI analysis failed: {str(e)}")
            # Fallback analysis
            return {
                "verification_priority": "high",
                "recommended_methods": ["phone", "email"],
                "verification_complexity": "standard",
                "expected_success_rate": 0.7,
                "time_sensitivity": "urgent",
                "additional_checks": ["amount_confirmation"],
                "risk_factors": ["unknown - analysis failed"],
                "merchant_reliability": 0.6,
                "reasoning": "Fallback analysis due to AI failure"
            }
    
    def _validate_response_authenticity(self, merchant_response: Dict[str, Any], 
                                      verification_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the authenticity of merchant response"""
        
        prompt = f"""
        Validate the authenticity and reliability of this merchant verification response.
        
        Merchant Response:
        {json.dumps(merchant_response, indent=2)}
        
        Verification Context:
        {json.dumps(verification_context, indent=2)}
        
        Analysis Points:
        1. Response timing (too fast/slow?)
        2. Method credibility
        3. Information consistency
        4. Merchant behavior patterns
        5. Technical verification markers
        
        Respond in JSON:
        {{
            "authenticity_score": 0.0-1.0,
            "response_quality": "poor|fair|good|excellent",
            "timing_analysis": "suspicious|normal|optimal",
            "method_reliability": 0.0-1.0,
            "consistency_check": "failed|partial|passed",
            "red_flags": ["list any suspicious elements"],
            "confidence_indicators": ["list positive verification signs"],
            "overall_assessment": "reject|cautious_accept|accept|strongly_accept",
            "reasoning": "detailed validation explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except Exception as e:
            print(f"⚠️  Response validation failed: {str(e)}")
            return {
                "authenticity_score": 0.5,
                "response_quality": "fair",
                "timing_analysis": "normal",
                "method_reliability": 0.6,
                "consistency_check": "partial",
                "red_flags": ["validation system error"],
                "confidence_indicators": [],
                "overall_assessment": "cautious_accept",
                "reasoning": "Validation system error - defaulting to cautious acceptance"
            }
    
    def _analyze_fraud_patterns(self, merchant_response: Dict[str, Any], 
                              verification_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response for known fraud patterns"""
        
        prompt = f"""
        Analyze this verification scenario for potential fraud patterns.
        
        Response: {json.dumps(merchant_response, indent=2)}
        Context: {json.dumps(verification_context.get('analysis', {}), indent=2)}
        
        Known Fraud Patterns to Check:
        1. Rapid response without proper verification
        2. Inconsistent verification methods
        3. Suspicious timing patterns
        4. Merchant collusion indicators
        5. Technical manipulation signs
        6. Social engineering attempts
        
        Respond in JSON:
        {{
            "fraud_probability": 0.0-1.0,
            "detected_patterns": ["list any fraud patterns found"],
            "risk_level": "minimal|low|medium|high|severe",
            "pattern_confidence": 0.0-1.0,
            "investigation_needed": true/false,
            "immediate_concerns": ["urgent issues requiring attention"],
            "preventive_measures": ["recommended actions"],
            "reasoning": "fraud analysis explanation"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        except Exception as e:
            print(f"⚠️  Fraud analysis failed: {str(e)}")
            return {
                "fraud_probability": 0.3,
                "detected_patterns": [],
                "risk_level": "medium",
                "pattern_confidence": 0.4,
                "investigation_needed": False,
                "immediate_concerns": ["analysis system error"],
                "preventive_measures": ["manual review recommended"],
                "reasoning": "Fraud analysis system error - defaulting to medium risk"
            }
    
    def _calculate_confidence_score(self, validation_result: Dict[str, Any], 
                                  fraud_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the verification"""
        try:
            authenticity_score = validation_result.get("authenticity_score", 0.5)
            method_reliability = validation_result.get("method_reliability", 0.5)
            fraud_probability = fraud_analysis.get("fraud_probability", 0.3)
            
            # Weighted confidence calculation
            confidence = (
                authenticity_score * 0.4 +
                method_reliability * 0.3 +
                (1 - fraud_probability) * 0.3
            )
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            print(f"⚠️  Confidence calculation failed: {str(e)}")
            return 0.5
    
    def _get_final_recommendation(self, validation_result: Dict[str, Any], 
                                fraud_analysis: Dict[str, Any]) -> str:
        """Get final recommendation based on all analysis"""
        
        authenticity = validation_result.get("authenticity_score", 0.5)
        fraud_prob = fraud_analysis.get("fraud_probability", 0.3)
        overall_assessment = validation_result.get("overall_assessment", "cautious_accept")
        
        # Decision logic
        if fraud_prob > 0.7 or authenticity < 0.3:
            return "REJECT"
        elif fraud_prob > 0.5 or authenticity < 0.5:
            return "MANUAL_REVIEW"
        elif overall_assessment in ["strongly_accept", "accept"] and fraud_prob < 0.3:
            return "ACCEPT"
        else:
            return "CAUTIOUS_ACCEPT"
    
    def _update_merchant_patterns(self, merchant_id: str, merchant_response: Dict[str, Any], 
                                validation_result: Dict[str, Any]):
        """Update merchant verification patterns for learning"""
        if not merchant_id:
            return
        
        if merchant_id not in self.merchant_verification_patterns:
            self.merchant_verification_patterns[merchant_id] = {
                "total_verifications": 0,
                "successful_verifications": 0,
                "average_response_time": 0,
                "preferred_methods": {},
                "reliability_score": 0.5,
                "fraud_incidents": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        pattern = self.merchant_verification_patterns[merchant_id]
        
        # Update statistics
        pattern["total_verifications"] += 1
        
        if validation_result.get("overall_assessment") in ["accept", "strongly_accept"]:
            pattern["successful_verifications"] += 1
        
        # Update reliability score
        success_rate = pattern["successful_verifications"] / pattern["total_verifications"]
        pattern["reliability_score"] = success_rate
        
        # Update method preferences
        method = merchant_response.get("method", "unknown")
        if method not in pattern["preferred_methods"]:
            pattern["preferred_methods"][method] = 0
        pattern["preferred_methods"][method] += 1
        
        pattern["last_updated"] = datetime.now().isoformat()
    
    def get_merchant_reliability(self, merchant_id: str) -> Dict[str, Any]:
        """Get merchant reliability information"""
        pattern = self.merchant_verification_patterns.get(merchant_id, {})
        
        if not pattern:
            return {
                "reliability_score": 0.5,
                "verification_count": 0,
                "success_rate": 0.0,
                "status": "new_merchant"
            }
        
        return {
            "reliability_score": pattern.get("reliability_score", 0.5),
            "verification_count": pattern.get("total_verifications", 0),
            "success_rate": pattern.get("successful_verifications", 0) / max(1, pattern.get("total_verifications", 1)),
            "preferred_methods": pattern.get("preferred_methods", {}),
            "fraud_incidents": pattern.get("fraud_incidents", 0),
            "last_verification": pattern.get("last_updated"),
            "status": "established_merchant"
        }
    
    def get_verification_analytics(self) -> Dict[str, Any]:
        """Get overall verification analytics"""
        total_verifications = len(self.verification_history)
        
        if total_verifications == 0:
            return {"total_verifications": 0, "message": "No verifications processed yet"}
        
        # Calculate analytics
        success_count = sum(1 for v in self.verification_history.values() 
                          if v.get("final_result", {}).get("recommendation") == "ACCEPT")
        
        return {
            "total_verifications": total_verifications,
            "success_rate": success_count / total_verifications,
            "active_merchants": len(self.merchant_verification_patterns),
            "average_merchant_reliability": sum(p.get("reliability_score", 0.5) 
                                             for p in self.merchant_verification_patterns.values()) / 
                                           max(1, len(self.merchant_verification_patterns))
        }
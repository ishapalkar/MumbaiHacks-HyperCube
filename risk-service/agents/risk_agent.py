import os
import json
from langchain_groq import ChatGroq

class RiskAgent:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model = ChatGroq(
            temperature=0.3,
            model_name="llama-3.3-70b-versatile",  # Updated: mixtral-8x7b-32768 is decommissioned
            api_key=self.groq_api_key
        )
        
        # Load prompt template
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/risk_agent_prompt.txt")
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
    
    def analyze_risk(self, transaction_data):
        """
        Analyze transaction risk using Groq AI
        
        Args:
            transaction_data: dict with transaction details
        
        Returns:
            dict with risk_score, decision, explanation
        """
        try:
            # Prepare prompt with transaction data
            prompt = self.prompt_template.format(
                token=transaction_data.get("token", "unknown"),
                merchant_id=transaction_data.get("merchant_id", "unknown"),
                amount=transaction_data.get("amount", 0),
                token_age_minutes=transaction_data.get("token_age_minutes", 0),
                device_trust_score=transaction_data.get("device_trust_score", 0),
                usual_location=transaction_data.get("usual_location", "unknown"),
                current_location=transaction_data.get("current_location", "unknown"),
                user_avg_amount=transaction_data.get("user_avg_amount", 0),
                recent_transactions=transaction_data.get("recent_transactions", 0),
                new_device=transaction_data.get("new_device", False),
                vpn_detected=transaction_data.get("vpn_detected", False),
                unusual_time=transaction_data.get("unusual_time", False),
                rushed_transaction=transaction_data.get("rushed_transaction", False),
                user_history=json.dumps(transaction_data.get("user_history", {})),
                user_profile=json.dumps(transaction_data.get("user_profile", {}))
            )
            
            # Call Groq AI
            response = self.model.invoke(prompt)
            
            # Extract content from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            try:
                # Clean response - remove markdown code blocks if present
                cleaned_response = response_text.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
                
                result = json.loads(cleaned_response)
                
                return {
                    "risk_score": result.get("risk_score", 50),
                    "decision": result.get("decision", "CHALLENGE"),
                    "explanation": result.get("explanation", "Unable to assess risk")
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return default values
                print(f"Warning: Could not parse JSON response: {response_text[:200]}")
                return {
                    "risk_score": 50,
                    "decision": "CHALLENGE",
                    "explanation": "AI response parsing failed - defaulting to challenge"
                }
        
        except Exception as e:
            print(f"Error in risk analysis: {str(e)}")
            # Fallback response
            return {
                "risk_score": 50,
                "decision": "CHALLENGE",
                "explanation": f"Error occurred: {str(e)}"
            }

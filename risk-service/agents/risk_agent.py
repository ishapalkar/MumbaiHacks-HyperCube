import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class AgenticRiskAgent:
    def __init__(self, memory_path="agent_memory.json"):
        # Initialize Groq model
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model = ChatGroq(
            temperature=0.3,
            model_name="llama-3.3-70b-versatile",
            api_key=self.groq_api_key
        )
        
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not found or not set properly. "
                "Please set your Groq API key in the .env file. "
                "Get one from: https://console.groq.com/"
            )
        
        try:
            self.model = ChatGroq(
                temperature=0.3,
                model_name="llama-3.3-70b-versatile",  # Updated: mixtral-8x7b-32768 is decommissioned
                api_key=self.groq_api_key
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Groq model: {str(e)}")
        
        # Load prompt template
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/risk_agent_prompt.txt")
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()
        
        # Initialize memory
        self.memory_path = Path(memory_path)
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                self.memory = json.load(f)
        else:
            self.memory = {}  # {token: {"transactions": [...], "avg_amount": 0, ...}}
    
    def _save_memory(self):
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def _compute_features(self, transaction):
        # Derived features
        token = transaction.get("token")
        history = self.memory.get(token, {"transactions": [], "avg_amount": 0})
        # Normalize numeric inputs to avoid None arithmetic errors
        raw_user_avg = history.get("avg_amount", transaction.get("user_avg_amount", 0))
        try:
            user_avg = float(raw_user_avg) if raw_user_avg is not None else 0.0
        except (TypeError, ValueError):
            user_avg = 0.0
        if user_avg == 0:
            user_avg = 1.0

        raw_amount = transaction.get("amount", 0)
        try:
            amount_val = float(raw_amount) if raw_amount is not None else 0.0
        except (TypeError, ValueError):
            amount_val = 0.0

        amount_ratio = amount_val / user_avg
        location_changed = transaction.get("current_location") != transaction.get("usual_location")
        high_risk_flags = sum([
            bool(transaction.get("new_device", False)),
            bool(transaction.get("vpn_detected", False)),
            bool(transaction.get("unusual_time", False)),
            bool(transaction.get("rushed_transaction", False)),
            bool(location_changed),
            bool(amount_ratio > 5)
        ])
        return amount_ratio, location_changed, high_risk_flags, history
    
    def analyze_risk(self, transaction):
        """
        Agentic risk analysis:
        1. Observe transaction and retrieve memory
        2. Compute features
        3. Apply rule-based overrides for first-time/high-risk
        4. Call Groq AI for nuanced reasoning
        5. Update memory
        6. Return final decision
        """
        try:
            token = transaction.get("token")
            amount_ratio, location_changed, high_risk_flags, history = self._compute_features(transaction)
            first_transaction = len(history["transactions"]) == 0
            
            # Rule-based override for first-time high-risk transactions
            if first_transaction and high_risk_flags >= 2:
                risk_result = {
                    "risk_score": 90,
                    "decision": "HIGH",
                    "explanation": f"First transaction with {high_risk_flags} high-risk flags."
                }
            else:
                # Prepare prompt for Groq
                prompt = self.prompt_template.format(
                    token=token,
                    merchant_id=transaction.get("merchant_id", "unknown"),
                    amount=transaction.get("amount", 0),
                    token_age_minutes=transaction.get("token_age_minutes", 0),
                    device_trust_score=transaction.get("device_trust_score", 0),
                    usual_location=transaction.get("usual_location", "unknown"),
                    current_location=transaction.get("current_location", "unknown"),
                    user_avg_amount=history.get("avg_amount", transaction.get("user_avg_amount", 0)),
                    recent_transactions=len(history["transactions"]),
                    new_device=transaction.get("new_device", False),
                    vpn_detected=transaction.get("vpn_detected", False),
                    unusual_time=transaction.get("unusual_time", False),
                    rushed_transaction=transaction.get("rushed_transaction", False),
                    user_history=json.dumps(transaction.get("user_history", {})),
                    user_profile=json.dumps(transaction.get("user_profile", {})),
                    amount_ratio=amount_ratio,
                    location_changed=location_changed,
                    high_risk_flags=high_risk_flags
                )
                
                response = self.model.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Robust JSON parsing
                try:
                    cleaned_response = response_text.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
                    result = json.loads(cleaned_response)
                    risk_result = {
                        "risk_score": result.get("risk_score", 50),
                        "decision": result.get("decision", "CHALLENGE"),
                        "explanation": result.get("explanation", "Unable to assess risk")
                    }
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse Groq response: {response_text[:200]}")
                    risk_result = {"risk_score": 50, "decision": "CHALLENGE", "explanation": "AI response parsing failed"}
            
            # Update memory (defensively handle None values)
            existing_tx = history.get("transactions") or []
            existing_count = len(existing_tx)
            raw_existing_avg = history.get("avg_amount", 0)
            try:
                existing_avg = float(raw_existing_avg) if raw_existing_avg is not None else 0.0
            except (TypeError, ValueError):
                existing_avg = 0.0

            raw_amount = transaction.get("amount", 0)
            try:
                amount_val = float(raw_amount) if raw_amount is not None else 0.0
            except (TypeError, ValueError):
                amount_val = 0.0

            new_avg = (existing_avg * existing_count + amount_val) / (existing_count + 1)
            token_memory = self.memory.get(token, {"transactions": [], "avg_amount": 0})
            token_memory["transactions"].append(transaction)
            token_memory["avg_amount"] = new_avg
            self.memory[token] = token_memory
            self._save_memory()
            
            return risk_result
        
        except Exception as e:
            print(f"Error in agentic analysis: {str(e)}")
            return {"risk_score": 50, "decision": "CHALLENGE", "explanation": str(e)}

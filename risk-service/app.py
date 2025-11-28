import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pymongo import MongoClient
import redis
from agents.risk_agent import AgenticRiskAgent  # <-- agentic AI

# Load environment variables
load_dotenv()

app = FastAPI(title="Risk Checker Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB (optional for logging)
try:
    mongo_client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=2000)
    db = mongo_client["risk_checker"]
    risk_logs_collection = db["risk_logs"]
    mongo_enabled = True
except:
    print("⚠️  MongoDB not connected - running without logging")
    mongo_enabled = False
    risk_logs_collection = None

# Initialize Redis (optional for device history)
try:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"), socket_connect_timeout=2, decode_responses=True)
    redis_client.ping()
    redis_enabled = True
except:
    print("⚠️  Redis not connected - running without device history")
    redis_enabled = False
    redis_client = None

# Initialize Agentic Risk Agent
risk_agent = AgenticRiskAgent(memory_path="agent_memory.json")

# Pydantic Models
class SecurityContext(BaseModel):
    token_age_minutes: Optional[int] = None
    device_trust_score: Optional[int] = None
    usual_location: Optional[str] = None
    current_location: Optional[str] = None
    user_history: Optional[Dict[str, Any]] = None
    recent_transactions: Optional[int] = None
    user_avg_amount: Optional[float] = None
    new_device: Optional[bool] = None
    vpn_detected: Optional[bool] = None
    unusual_time: Optional[bool] = None
    rushed_transaction: Optional[bool] = None

class RiskCheckRequest(BaseModel):
    token: str
    merchant_id: str
    amount: float
    security_context: SecurityContext

# Helper Functions
def get_device_history(device_id: str) -> Dict[str, Any]:
    """Get device history from Redis cache"""
    if not redis_enabled or redis_client is None:
        return {"seen_count": 0}
    try:
        device_key = f"device:{device_id}"
        device_data = redis_client.hgetall(device_key)
        if device_data:
            return {
                "seen_count": int(device_data.get("seen_count", 0)),
                "last_ip": device_data.get("last_ip", "unknown"),
                "last_geo": device_data.get("last_geo", "unknown"),
                "total_amount": float(device_data.get("total_amount", 0))
            }
        return {"seen_count": 0}
    except Exception as e:
        print(f"Redis error: {str(e)}")
        return {"seen_count": 0}

def update_device_history(device_id: str, ip_address: str, geo_location: str, amount: float):
    """Update device history in Redis"""
    if not redis_enabled or redis_client is None:
        return
    try:
        device_key = f"device:{device_id}"
        current_count = int(redis_client.hget(device_key, "seen_count") or 0)
        current_amount = float(redis_client.hget(device_key, "total_amount") or 0)
        redis_client.hset(device_key, mapping={
            "seen_count": current_count + 1,
            "last_ip": ip_address,
            "last_geo": geo_location,
            "total_amount": current_amount + amount
        })
        redis_client.expire(device_key, 86400 * 30)  # 30 days expiry
    except Exception as e:
        print(f"Redis update error: {str(e)}")

# Risk level determination
def get_risk_level(risk_score: int) -> str:
    """Convert risk score to risk level"""
    if risk_score < 30:
        return "LOW"
    elif risk_score < 70:
        return "MEDIUM"
    else:
        return "HIGH"

# API Routes
@app.get("/")
def read_root():
    return {"message": "Risk Checker Service is running", "version": "1.0.0"}

@app.post("/risk-check")
async def check_risk(request: RiskCheckRequest):
    """
    TokenTrust Risk Assessment Endpoint
    Analyzes transaction and returns risk level (LOW/MEDIUM/HIGH)
    Learns from user's transaction history to detect anomalies
    """
    try:
        ctx = request.security_context
        transaction_data = {
            "token": request.token,
            "merchant_id": request.merchant_id,
            "amount": request.amount,
            "token_age_minutes": ctx.token_age_minutes,
            "device_trust_score": ctx.device_trust_score,
            "usual_location": ctx.usual_location,
            "current_location": ctx.current_location,
            "new_device": ctx.new_device,
            "vpn_detected": ctx.vpn_detected,
            "unusual_time": ctx.unusual_time,
            "rushed_transaction": ctx.rushed_transaction,
        }

        # Agentic risk analysis
        result = risk_agent.analyze_risk(transaction_data)

        # Compute risk level and token validity
        risk_level = get_risk_level(result["risk_score"])
        token_valid = risk_level != "HIGH"

        # Optional logging to MongoDB
        # pymongo Collection objects don't implement truth-value testing; compare to None explicitly
        if mongo_enabled and risk_logs_collection is not None:
            try:
                log_entry = {
                    "token": request.token,
                    "merchant_id": request.merchant_id,
                    "amount": request.amount,
                    "security_context": ctx.dict(),
                    "risk_score": result["risk_score"],
                    "risk_level": risk_level,
                    "token_valid": token_valid,
                    "timestamp": datetime.utcnow()
                }
                risk_logs_collection.insert_one(log_entry)
            except Exception as e:
                print(f"Error saving log: {str(e)}")

        return {
            "risk_level": risk_level,
            "token_valid": token_valid,
            "reasoning": result["explanation"],
            "risk_score": result["risk_score"],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk check failed: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Risk Checker - Score Evaluator",
        "version": "1.0.0",
        "services": {
            "mongodb": "connected" if mongo_enabled else "optional (not connected)",
            "redis": "connected" if redis_enabled else "optional (not connected)",
            "groq_ai": "ready"
        },
        "risk_levels": {
            "LOW": "0-29 (Safe)",
            "MEDIUM": "30-69 (Verify)",
            "HIGH": "70-100 (Block)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

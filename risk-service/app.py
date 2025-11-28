import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import asyncio
from dotenv import load_dotenv
from pymongo import MongoClient
import redis
from agents.risk_agent import AgenticRiskAgent  # <-- agentic AI
import json
from datetime import datetime

# Import robust endpoints
from endpoints import router as robust_router

# Import legacy agents
from agents.risk_agent import RiskAgent
from agents.token_trust_orchestrator import TokenTrustOrchestrator

# Load environment variables
load_dotenv()

app = FastAPI(
    title="TokenTrust Risk Service - Robust Edition", 
    version="2.0.0",
    description="Production-ready TokenTrust with canonical thresholds, idempotent operations, and proper audit logging"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the robust endpoints under /v2 prefix
app.include_router(robust_router, prefix="/v2", tags=["Robust API v2"])

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
# Initialize Risk Agent
risk_agent = RiskAgent()

# Initialize TokenTrust Orchestrator (Agentic AI System)
orchestrator = TokenTrustOrchestrator()

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

# New models for Agentic AI System
class TokenTrustRequest(BaseModel):
    token: str
    merchant_id: str
    amount: float
    security_context: SecurityContext
    user_info: Optional[Dict[str, Any]] = None
    transaction_metadata: Optional[Dict[str, Any]] = None

class MerchantVerificationResponse(BaseModel):
    session_id: str
    verified: bool
    verified_by: str
    method: str = "phone_verification"
    notes: Optional[str] = None

class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    current_step: Optional[str] = None

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

# New Agentic AI Endpoints for TokenTrust System

@app.post("/tokentrust/process")
async def process_transaction_with_ai(request: TokenTrustRequest):
    """
    Complete TokenTrust Agentic AI Processing:
    1. Risk Assessment
    2. Decision Making (Approve/Freeze/Revoke)
    3. Token Management
    4. Merchant Communication for 2FA
    5. Verification Process
    6. Final Decision
    """
    try:
        # Get user profile for enhanced analysis
        user_profile = get_user_profile(request.token)
        
        # Prepare comprehensive transaction data
        transaction_data = {
            "token": request.token,
            "merchant_id": request.merchant_id,
            "amount": request.amount,
            "token_age_minutes": request.security_context.token_age_minutes,
            "device_trust_score": request.security_context.device_trust_score,
            "usual_location": request.security_context.usual_location,
            "current_location": request.security_context.current_location,
            "user_history": request.security_context.user_history,
            "recent_transactions": request.security_context.recent_transactions,
            "user_avg_amount": request.security_context.user_avg_amount,
            "new_device": request.security_context.new_device,
            "vpn_detected": request.security_context.vpn_detected,
            "unusual_time": request.security_context.unusual_time,
            "rushed_transaction": request.security_context.rushed_transaction,
            "user_profile": user_profile,
            "user_info": request.user_info,
            "transaction_metadata": request.transaction_metadata
        }
        
        # Process through the complete agentic workflow
        print(f"🚀 Starting TokenTrust AI processing for token {request.token[:8]}...")
        result = await orchestrator.process_transaction(transaction_data)
        
        # Save detailed log to MongoDB
        if mongo_enabled and risk_logs_collection is not None:
            try:
                log_entry = {
                    "session_id": result.get("session_id"),
                    "token": request.token,
                    "merchant_id": request.merchant_id,
                    "amount": request.amount,
                    "security_context": request.security_context.dict(),
                    "agentic_result": result,
                    "timestamp": datetime.utcnow(),
                    "workflow_type": "agentic_tokentrust"
                }
                risk_logs_collection.insert_one(log_entry)
                print(f"📝 Logged agentic processing for session {result.get('session_id', 'unknown')[:8]}")
            except Exception as e:
                print(f"Warning: Failed to log agentic result: {str(e)}")
        
        # Build response based on decision action
        decision_action = result.get("decision", {}).get("action")
        response_data = {
            "success": True,
            "session_id": result.get("session_id"),
            "risk_assessment": result.get("risk_assessment"),
            "decision_reasoning": result.get("decision", {}).get("reasoning"),
            "processing_time": len(result.get("workflow_steps", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Only include final_status and token_status for completed workflows
        if decision_action == "APPROVE" or decision_action == "REVOKE":
            # Transaction is complete - include final status
            response_data.update({
                "final_status": result.get("final_result", {}).get("status"),
                "token_status": result.get("final_result", {}).get("token_status"),
                "workflow_completed": True,
                "message": result.get("final_result", {}).get("message", "Processing completed")
            })
        elif decision_action == "FREEZE_AND_VERIFY":
            # Transaction needs verification - don't reveal final status yet
            response_data.update({
                "workflow_completed": False,
                "requires_merchant_verification": True,
                "message": "Transaction requires merchant verification - please complete 2FA",
                "next_step": "merchant_verification"
            })
        else:
            # Fallback
            response_data.update({
                "workflow_completed": True,
                "message": "Processing completed with unknown action"
            })
            
        return response_data
        
    except Exception as e:
        print(f"❌ TokenTrust processing failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"TokenTrust agentic processing failed: {str(e)}"
        )

@app.post("/tokentrust/merchant-response")
async def submit_merchant_verification(response: MerchantVerificationResponse):
    """
    Endpoint for merchants to submit 2FA verification results
    """
    try:
        # Convert verified boolean to user response string
        user_response = "Yes, I authorized this transaction" if response.verified else "No, I did not authorize this transaction"
        
        # Process merchant response through orchestrator
        result = await orchestrator.handle_merchant_response(
            session_id=response.session_id,
            user_response=user_response,
            verification_method=response.method
        )
        
        if result["status"] == "completed":
            print(f"✅ Merchant verification completed for session {response.session_id[:8]}")
            return {
                "success": True,
                "session_id": response.session_id,
                "final_status": result.get("final_status"),
                "token_status": result.get("token_status"),
                "final_decision": result.get("final_decision"),
                "message": result.get("message"),
                "workflow_complete": True,
                "verification_successful": result.get("verification_successful"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "Verification processing failed"))
            
    except Exception as e:
        print(f"❌ Merchant response submission failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit merchant response: {str(e)}"
        )

@app.get("/tokentrust/session/{session_id}")
async def get_session_status(session_id: str):
    """
    Get the current status of a TokenTrust processing session
    """
    try:
        session_data = orchestrator.get_session_status(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "status": session_data.get("status"),
            "created_at": session_data.get("created_at"),
            "current_step": session_data.get("steps", [])[-1].get("step") if session_data.get("steps") else None,
            "risk_score": session_data.get("risk_result", {}).get("risk_score"),
            "decision": session_data.get("decision", {}).get("action"),
            "final_result": session_data.get("final_result"),
            "workflow_steps": len(session_data.get("steps", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Session status retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session status: {str(e)}"
        )

@app.get("/tokentrust/merchant/{merchant_id}/verifications")
async def get_merchant_verifications(merchant_id: str):
    """
    Get pending verifications for a specific merchant
    """
    try:
        pending_verifications = orchestrator.merchant_communicator.get_pending_verifications()
        
        # Filter for specific merchant
        merchant_verifications = {
            session_id: verification 
            for session_id, verification in pending_verifications.items()
            if verification.get("merchant_id") == merchant_id
        }
        
        return {
            "merchant_id": merchant_id,
            "pending_verifications": len(merchant_verifications),
            "verifications": merchant_verifications,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Merchant verification retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve merchant verifications: {str(e)}"
        )

@app.get("/tokentrust/analytics")
async def get_tokentrust_analytics():
    """
    Get TokenTrust system analytics and performance metrics
    """
    try:
        # Get verification analytics
        verification_analytics = orchestrator.verification_agent.get_verification_analytics()
        
        # Get active sessions count
        active_sessions = len(orchestrator.active_sessions)
        
        return {
            "system_status": "operational",
            "active_sessions": active_sessions,
            "verification_analytics": verification_analytics,
            "services": {
                "risk_agent": "active",
                "token_manager": "active", 
                "merchant_communicator": "active",
                "verification_agent": "active",
                "orchestrator": "active"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Analytics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )

@app.post("/tokentrust/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """
    Clean up old sessions to prevent memory leaks
    """
    try:
        initial_count = len(orchestrator.active_sessions)
        orchestrator.cleanup_old_sessions(max_age_hours)
        final_count = len(orchestrator.active_sessions)
        
        cleaned_count = initial_count - final_count
        
        return {
            "success": True,
            "sessions_cleaned": cleaned_count,
            "active_sessions_remaining": final_count,
            "max_age_hours": max_age_hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Session cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup sessions: {str(e)}"
        )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TokenTrust Agentic AI Risk Service",
        "version": "2.0.0",
        "services": {
            "mongodb": "connected" if mongo_enabled else "optional (not connected)",
            "redis": "connected" if redis_enabled else "optional (not connected)",
            "groq_ai": "ready",
            "agentic_orchestrator": "active",
            "token_manager": "active",
            "merchant_communicator": "active",
            "verification_agent": "active"
        },
        "risk_levels": {
            "LOW": "0-29 (Approve)",
            "MEDIUM": "30-69 (Freeze & Verify)",
            "HIGH": "70-100 (Revoke)"
        },
        "workflow_capabilities": [
            "Risk Assessment",
            "Token Freezing/Unfreezing/Revoking",
            "Merchant 2FA Communication",
            "Automated Verification",
            "Decision Making",
            "Learning & Analytics"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

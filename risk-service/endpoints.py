"""
TokenTrust Robust API Endpoints
Proper HTTP status codes, error handling, and workflow management
"""

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from helpers import (
    storage, write_audit_entry, create_event, freeze_token, unfreeze_token, revoke_token,
    get_token_status, get_event_summary, classify_risk_score, get_decision_for_risk_level,
    parse_llm_response, validate_llm_recommendation
)
from config import (
    EVENT_STATUS_APPROVED, EVENT_STATUS_WAITING_VERIFICATION,
    EVENT_STATUS_VERIFIED_SUCCESS, EVENT_STATUS_VERIFIED_FAILURE,
    AUDIT_ACTION_ANALYZE, AUDIT_ACTION_VERIFY, AUDIT_ACTION_TRIAGE,
    TOKEN_STATUS_ACTIVE, TOKEN_STATUS_FROZEN, TOKEN_STATUS_REVOKED
)

router = APIRouter()

# Request Models
class AnalyzeRequest(BaseModel):
    token_id: str = Field(..., description="Token identifier")
    merchant_id: str = Field(..., description="Merchant identifier")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class MerchantResponse(BaseModel):
    event_id: str = Field(..., description="Event identifier")
    user_response: str = Field(..., description="User response to verification")
    verification_method: str = Field(..., description="Method used for verification")
    evidence: Optional[Dict[str, Any]] = Field(default=None, description="Verification evidence")

class TriageRequest(BaseModel):
    event_id: str = Field(..., description="Event identifier")
    agent_decision: str = Field(..., description="Agent's decision")
    reasoning: Optional[str] = Field(default=None, description="Agent's reasoning")

    @validator('agent_decision')
    def validate_agent_decision(cls, v):
        valid_decisions = ['approve', 'challenge', 'challenge_high', 'revoke']
        if v.lower() not in valid_decisions:
            raise ValueError(f'agent_decision must be one of: {valid_decisions}')
        return v.lower()

# Response Models
class AnalyzeResponse(BaseModel):
    event_id: str
    decision: str
    status: str
    token_status: str
    risk_level: str
    auto_revoke_candidate: bool
    message: str

class MerchantResponseResult(BaseModel):
    event_id: str
    final_status: str
    token_status: str
    verification_successful: bool
    message: str

class TriageResponse(BaseModel):
    event_id: str
    action_taken: str
    token_status: str
    message: str

# 1. Analyze/Ingest Endpoint
@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_transaction(request: AnalyzeRequest):
    """
    Analyze transaction risk and manage token state
    
    - Accepts event payload with risk_score
    - Classifies risk into LOW/MEDIUM/HIGH buckets
    - Persists events with proper status
    - Manages token state (freeze for MEDIUM/HIGH risk)
    - Returns decision with proper HTTP status
    """
    try:
        # Validate current token state
        current_token_status = get_token_status(request.token_id)
        if current_token_status == TOKEN_STATUS_REVOKED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token {request.token_id} is revoked and cannot be used"
            )
        
        # Create event with risk classification
        event = create_event(
            token_id=request.token_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            risk_score=request.risk_score
        )
        
        risk_level = classify_risk_score(request.risk_score)
        
        # Audit the analysis
        write_audit_entry(
            action=AUDIT_ACTION_ANALYZE,
            actor="system",
            target=event.event_id,
            reason=f"Transaction analysis - Risk Level: {risk_level}",
            details={
                "token_id": request.token_id,
                "merchant_id": request.merchant_id,
                "amount": request.amount,
                "risk_score": request.risk_score,
                "risk_level": risk_level,
                "metadata": request.metadata
            }
        )
        
        # Handle token state based on risk level
        if risk_level in ["MEDIUM", "HIGH"]:
            # Freeze token for further verification
            freeze_result = freeze_token(
                token_id=request.token_id,
                reason=f"Risk level {risk_level} detected",
                actor="system",
                auto_revoke_candidate=(risk_level == "HIGH")
            )
            
            if not freeze_result["success"]:
                # Token couldn't be frozen (might be revoked)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot freeze token: {freeze_result.get('error', 'Unknown error')}"
                )
        
        # Get final token status
        final_token_status = get_token_status(request.token_id)
        
        # Prepare response message
        if risk_level == "LOW":
            message = "Transaction approved - low risk"
        elif risk_level == "MEDIUM":
            message = "Transaction requires verification - medium risk, token frozen"
        else:  # HIGH
            message = "Transaction requires verification - high risk, token frozen, auto-revoke candidate"
        
        return AnalyzeResponse(
            event_id=event.event_id,
            decision=event.decision,
            status=event.status,
            token_status=final_token_status,
            risk_level=risk_level,
            auto_revoke_candidate=event.auto_revoke_candidate,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        write_audit_entry(
            action=AUDIT_ACTION_ANALYZE,
            actor="system",
            target=request.token_id,
            reason=f"Analysis failed: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during transaction analysis: {str(e)}"
        )

# 2. Merchant Response Endpoint
@router.post("/merchant-response", response_model=MerchantResponseResult, status_code=status.HTTP_200_OK)
async def handle_merchant_response(response: MerchantResponse):
    """
    Process merchant's verification response
    
    - Updates event status based on verification outcome
    - Manages token state (unfreeze on success, revoke on failure/suspicious)
    - Returns final status with proper HTTP codes
    """
    try:
        # Get the event
        event = storage.get_event(response.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {response.event_id} not found"
            )
        
        # Validate event can be updated
        if event.status not in [EVENT_STATUS_WAITING_VERIFICATION]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Event {response.event_id} is not waiting for verification (current status: {event.status})"
            )
        
        # Parse user response (simulate LLM analysis here)
        # In real implementation, this would call the VerificationAgent
        user_response_lower = response.user_response.lower().strip()
        
        verification_successful = False
        final_event_status = EVENT_STATUS_VERIFIED_FAILURE
        
        # Simple verification logic (enhance with actual LLM analysis)
        success_indicators = ["yes", "approve", "authorized", "legitimate", "valid", "correct"]
        failure_indicators = ["no", "deny", "fraud", "suspicious", "unauthorized", "invalid", "wrong"]
        
        if any(indicator in user_response_lower for indicator in success_indicators):
            verification_successful = True
            final_event_status = EVENT_STATUS_VERIFIED_SUCCESS
        elif any(indicator in user_response_lower for indicator in failure_indicators):
            verification_successful = False
            final_event_status = EVENT_STATUS_VERIFIED_FAILURE
        else:
            # Ambiguous response - default to failure for security
            verification_successful = False
            final_event_status = EVENT_STATUS_VERIFIED_FAILURE
        
        # Update event
        event.status = final_event_status
        event.verified_by = f"{response.verification_method}:merchant_response"
        event.verification_evidence = {
            "user_response": response.user_response,
            "verification_method": response.verification_method,
            "evidence": response.evidence,
            "processed_at": datetime.utcnow().isoformat()
        }
        storage.save_event(event)
        
        # Audit the verification
        write_audit_entry(
            action=AUDIT_ACTION_VERIFY,
            actor="merchant_user",
            target=response.event_id,
            reason=f"Merchant verification: {'Success' if verification_successful else 'Failure'}",
            details={
                "token_id": event.token_id,
                "verification_method": response.verification_method,
                "verification_successful": verification_successful,
                "user_response": response.user_response
            }
        )
        
        # Handle token state based on verification outcome
        if verification_successful:
            # Unfreeze token on successful verification
            unfreeze_result = unfreeze_token(
                token_id=event.token_id,
                actor="verification_system",
                reason="Merchant verification successful"
            )
            
            if not unfreeze_result["success"]:
                # Log warning but don't fail the response
                write_audit_entry(
                    action=AUDIT_ACTION_VERIFY,
                    actor="system",
                    target=event.token_id,
                    reason=f"Warning: Could not unfreeze token after successful verification: {unfreeze_result.get('error')}"
                )
        else:
            # Revoke token on failed verification or if it was auto-revoke candidate
            revoke_result = revoke_token(
                token_id=event.token_id,
                actor="verification_system",
                reason="Merchant verification failed"
            )
            
            if not revoke_result["success"]:
                # This shouldn't happen, but log it
                write_audit_entry(
                    action=AUDIT_ACTION_VERIFY,
                    actor="system",
                    target=event.token_id,
                    reason=f"Warning: Could not revoke token after failed verification: {revoke_result.get('error')}"
                )
        
        # Get final token status
        final_token_status = get_token_status(event.token_id)
        
        # Prepare response message
        if verification_successful:
            message = "Verification successful - token unfrozen, transaction can proceed"
        else:
            message = "Verification failed - token revoked for security"
        
        return MerchantResponseResult(
            event_id=response.event_id,
            final_status=final_event_status,
            token_status=final_token_status,
            verification_successful=verification_successful,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        write_audit_entry(
            action=AUDIT_ACTION_VERIFY,
            actor="system",
            target=response.event_id if hasattr(response, 'event_id') else "unknown",
            reason=f"Merchant response processing failed: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing merchant response: {str(e)}"
        )

# 3. Agent Triage Endpoint
@router.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def agent_triage(request: TriageRequest):
    """
    Agent triage for complex decisions
    
    - Handles agent decisions for ambiguous cases
    - Can override standard workflow based on agent analysis
    - Manages token lifecycle based on agent recommendations
    """
    try:
        # Get the event
        event = storage.get_event(request.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {request.event_id} not found"
            )
        
        # Validate agent decision
        agent_decision = validate_llm_recommendation(request.agent_decision)
        
        # Audit the triage
        write_audit_entry(
            action=AUDIT_ACTION_TRIAGE,
            actor="ai_agent",
            target=request.event_id,
            reason=f"Agent triage decision: {agent_decision}",
            details={
                "token_id": event.token_id,
                "agent_decision": agent_decision,
                "reasoning": request.reasoning,
                "original_decision": event.decision
            }
        )
        
        action_taken = "none"
        message = ""
        
        # Handle agent decision
        if agent_decision == "approve":
            # Agent approves - unfreeze token if frozen
            if get_token_status(event.token_id) == TOKEN_STATUS_FROZEN:
                unfreeze_result = unfreeze_token(
                    token_id=event.token_id,
                    actor="ai_agent",
                    reason=f"Agent approval: {request.reasoning or 'AI agent determined transaction is safe'}"
                )
                action_taken = "approved_unfrozen"
                message = "Agent approved transaction - token unfrozen"
            else:
                action_taken = "approved_no_action"
                message = "Agent approved transaction - no token action needed"
            
            # Update event status to approved
            event.status = EVENT_STATUS_APPROVED
            storage.save_event(event)
            
        elif agent_decision == "challenge":
            # Agent wants more verification - ensure token is frozen
            if get_token_status(event.token_id) == TOKEN_STATUS_ACTIVE:
                freeze_result = freeze_token(
                    token_id=event.token_id,
                    reason=f"Agent requested additional verification: {request.reasoning or 'AI agent requires more verification'}",
                    actor="ai_agent",
                    auto_revoke_candidate=False
                )
                action_taken = "challenge_frozen"
                message = "Agent requires additional verification - token frozen"
            else:
                action_taken = "challenge_already_frozen"
                message = "Agent requires additional verification - token remains frozen"
            
            # Keep event in waiting verification state
            event.status = EVENT_STATUS_WAITING_VERIFICATION
            storage.save_event(event)
            
        elif agent_decision == "challenge_high":
            # Agent sees high risk - freeze and mark for auto-revoke
            freeze_result = freeze_token(
                token_id=event.token_id,
                reason=f"Agent identified high risk: {request.reasoning or 'AI agent detected high risk indicators'}",
                actor="ai_agent",
                auto_revoke_candidate=True
            )
            action_taken = "high_risk_frozen"
            message = "Agent identified high risk - token frozen as revoke candidate"
            
            # Update event for high risk
            event.status = EVENT_STATUS_WAITING_VERIFICATION
            event.auto_revoke_candidate = True
            storage.save_event(event)
            
        elif agent_decision == "revoke":
            # Agent recommends immediate revocation
            revoke_result = revoke_token(
                token_id=event.token_id,
                actor="ai_agent",
                reason=f"Agent recommended revocation: {request.reasoning or 'AI agent determined token should be revoked'}"
            )
            action_taken = "revoked"
            message = "Agent recommended revocation - token revoked"
            
            # Update event to verified failure
            event.status = EVENT_STATUS_VERIFIED_FAILURE
            storage.save_event(event)
        
        # Get final token status
        final_token_status = get_token_status(event.token_id)
        
        return TriageResponse(
            event_id=request.event_id,
            action_taken=action_taken,
            token_status=final_token_status,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        write_audit_entry(
            action=AUDIT_ACTION_TRIAGE,
            actor="system",
            target=request.event_id if hasattr(request, 'event_id') else "unknown",
            reason=f"Agent triage failed: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during agent triage: {str(e)}"
        )

# 4. Status Check Endpoints
@router.get("/event/{event_id}", status_code=status.HTTP_200_OK)
async def get_event_status(event_id: str):
    """Get current event status"""
    event_summary = get_event_summary(event_id)
    if not event_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    return event_summary

@router.get("/token/{token_id}/status", status_code=status.HTTP_200_OK)
async def get_token_status_endpoint(token_id: str):
    """Get current token status"""
    token_state = storage.get_token(token_id)
    if not token_state:
        return {
            "token_id": token_id,
            "status": TOKEN_STATUS_ACTIVE,
            "message": "Token not found in system - default status"
        }
    
    return {
        "token_id": token_id,
        "status": token_state.status,
        "created_at": token_state.created_at.isoformat() if token_state.created_at else None,
        "frozen_at": token_state.frozen_at.isoformat() if token_state.frozen_at else None,
        "revoked_at": token_state.revoked_at.isoformat() if token_state.revoked_at else None,
        "reason": token_state.reason,
        "auto_revoke_candidate": token_state.auto_revoke_candidate
    }

# 5. Admin/Debug Endpoints
@router.get("/audit/{target}", status_code=status.HTTP_200_OK)
async def get_audit_log(target: str, limit: int = 50):
    """Get audit log entries for a specific target"""
    matching_entries = [
        {
            "audit_id": entry.audit_id,
            "action": entry.action,
            "actor": entry.actor,
            "target": entry.target,
            "reason": entry.reason,
            "timestamp": entry.timestamp.isoformat(),
            "details": entry.details
        }
        for entry in storage.audit_log
        if entry.target == target
    ][-limit:]  # Get most recent entries
    
    return {
        "target": target,
        "entries": matching_entries,
        "total_entries": len(matching_entries)
    }

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "storage_stats": {
            "tokens": len(storage.tokens),
            "events": len(storage.events),
            "audit_entries": len(storage.audit_log)
        }
    }
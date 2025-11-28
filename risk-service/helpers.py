"""
TokenTrust Core Helpers
Risk classification, token lifecycle, audit logging, and data models
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from config import (
    APPROVE_MAX, MEDIUM_MIN, MEDIUM_MAX, HIGH_MIN,
    TOKEN_STATUS_ACTIVE, TOKEN_STATUS_FROZEN, TOKEN_STATUS_REVOKED,
    EVENT_STATUS_APPROVED, EVENT_STATUS_WAITING_VERIFICATION,
    EVENT_STATUS_VERIFIED_SUCCESS, EVENT_STATUS_VERIFIED_FAILURE,
    DECISION_APPROVE, DECISION_CHALLENGE, DECISION_CHALLENGE_HIGH,
    VALID_LLM_RECOMMENDATIONS,
    AUDIT_ACTION_FREEZE, AUDIT_ACTION_UNFREEZE, AUDIT_ACTION_REVOKE,
    AUDIT_ACTION_ANALYZE, AUDIT_ACTION_VERIFY, AUDIT_ACTION_TRIAGE
)

# Data Models
@dataclass
class TokenState:
    token_id: str
    status: str = TOKEN_STATUS_ACTIVE
    frozen_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    reason: Optional[str] = None
    auto_revoke_candidate: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class Event:
    event_id: str
    token_id: str
    merchant_id: str
    amount: float
    risk_score: int
    status: str
    decision: str
    auto_revoke_candidate: bool = False
    verified_by: Optional[str] = None
    verification_evidence: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

@dataclass
class AuditEntry:
    audit_id: str
    action: str
    actor: str
    target: str
    reason: Optional[str]
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.audit_id:
            self.audit_id = str(uuid.uuid4())

# In-memory storage (replace with DB in production)
class Storage:
    def __init__(self):
        self.tokens: Dict[str, TokenState] = {}
        self.events: Dict[str, Event] = {}
        self.audit_log: List[AuditEntry] = []
    
    def get_token(self, token_id: str) -> Optional[TokenState]:
        return self.tokens.get(token_id)
    
    def save_token(self, token_state: TokenState):
        self.tokens[token_state.token_id] = token_state
    
    def get_event(self, event_id: str) -> Optional[Event]:
        return self.events.get(event_id)
    
    def save_event(self, event: Event):
        event.updated_at = datetime.utcnow()
        self.events[event.event_id] = event
    
    def add_audit_entry(self, entry: AuditEntry):
        self.audit_log.append(entry)

# Global storage instance
storage = Storage()

# 1. Risk Classification Helper
def classify_risk_score(risk_score: int) -> str:
    """
    Classify a numeric risk_score into LOW/MEDIUM/HIGH buckets
    
    Args:
        risk_score: Integer score 0-100
        
    Returns:
        str: "LOW", "MEDIUM", or "HIGH"
    """
    if risk_score <= APPROVE_MAX:
        return "LOW"
    elif MEDIUM_MIN <= risk_score <= MEDIUM_MAX:
        return "MEDIUM"
    elif risk_score >= HIGH_MIN:
        return "HIGH"
    else:
        # Edge case handling
        return "MEDIUM"

def get_decision_for_risk_level(risk_level: str) -> str:
    """
    Get the decision string for a risk level
    
    Args:
        risk_level: "LOW", "MEDIUM", or "HIGH"
        
    Returns:
        str: Decision constant
    """
    if risk_level == "LOW":
        return DECISION_APPROVE
    elif risk_level == "MEDIUM":
        return DECISION_CHALLENGE
    elif risk_level == "HIGH":
        return DECISION_CHALLENGE_HIGH
    else:
        return DECISION_CHALLENGE

# 2. Audit Logging Helper
def write_audit_entry(action: str, actor: str, target: str, reason: Optional[str] = None, 
                     details: Optional[Dict[str, Any]] = None):
    """
    Write an audit entry for all lifecycle operations
    
    Args:
        action: Action being performed (use AUDIT_ACTION_* constants)
        actor: Who is performing the action (system, user_id, etc.)
        target: What is being acted upon (token_id, event_id, etc.)
        reason: Optional reason for the action
        details: Optional additional details
    """
    entry = AuditEntry(
        audit_id=str(uuid.uuid4()),
        action=action,
        actor=actor,
        target=target,
        reason=reason,
        timestamp=datetime.utcnow(),
        details=details
    )
    storage.add_audit_entry(entry)
    print(f"AUDIT: {action} by {actor} on {target} - {reason}")

# 3. Token Lifecycle Helpers (Idempotent)
def freeze_token(token_id: str, reason: str, actor: str = "system", 
                auto_revoke_candidate: bool = False) -> Dict[str, Any]:
    """
    Idempotent token freeze operation
    
    Args:
        token_id: Token to freeze
        reason: Reason for freezing
        actor: Who is freezing the token
        auto_revoke_candidate: Whether this is a candidate for auto-revocation
        
    Returns:
        dict: Result with success status and current state
    """
    token_state = storage.get_token(token_id)
    
    if not token_state:
        # Create new token in frozen state
        token_state = TokenState(
            token_id=token_id,
            status=TOKEN_STATUS_FROZEN,
            frozen_at=datetime.utcnow(),
            reason=reason,
            auto_revoke_candidate=auto_revoke_candidate
        )
        storage.save_token(token_state)
        write_audit_entry(AUDIT_ACTION_FREEZE, actor, token_id, reason, 
                         {"auto_revoke_candidate": auto_revoke_candidate})
        return {"success": True, "action": "frozen", "was_active": False}
    
    if token_state.status == TOKEN_STATUS_ACTIVE:
        # Freeze active token
        token_state.status = TOKEN_STATUS_FROZEN
        token_state.frozen_at = datetime.utcnow()
        token_state.reason = reason
        token_state.auto_revoke_candidate = auto_revoke_candidate
        storage.save_token(token_state)
        write_audit_entry(AUDIT_ACTION_FREEZE, actor, token_id, reason,
                         {"auto_revoke_candidate": auto_revoke_candidate})
        return {"success": True, "action": "frozen", "was_active": True}
    
    elif token_state.status == TOKEN_STATUS_FROZEN:
        # Already frozen - idempotent
        return {"success": True, "action": "already_frozen", "was_active": False}
    
    elif token_state.status == TOKEN_STATUS_REVOKED:
        # Cannot freeze revoked token
        return {"success": False, "error": "cannot_freeze_revoked_token", "current_status": "revoked"}

def unfreeze_token(token_id: str, actor: str, reason: str = "verification_success") -> Dict[str, Any]:
    """
    Idempotent token unfreeze operation
    
    Args:
        token_id: Token to unfreeze
        actor: Who is unfreezing the token
        reason: Reason for unfreezing
        
    Returns:
        dict: Result with success status and current state
    """
    token_state = storage.get_token(token_id)
    
    if not token_state:
        return {"success": False, "error": "token_not_found"}
    
    if token_state.status == TOKEN_STATUS_FROZEN:
        # Unfreeze frozen token
        token_state.status = TOKEN_STATUS_ACTIVE
        token_state.frozen_at = None
        token_state.reason = None
        token_state.auto_revoke_candidate = False
        storage.save_token(token_state)
        write_audit_entry(AUDIT_ACTION_UNFREEZE, actor, token_id, reason)
        return {"success": True, "action": "unfrozen"}
    
    elif token_state.status == TOKEN_STATUS_ACTIVE:
        # Already active - idempotent
        return {"success": True, "action": "already_active"}
    
    elif token_state.status == TOKEN_STATUS_REVOKED:
        # Cannot unfreeze revoked token
        return {"success": False, "error": "cannot_unfreeze_revoked_token", "current_status": "revoked"}

def revoke_token(token_id: str, actor: str, reason: str) -> Dict[str, Any]:
    """
    Atomically revoke a token (idempotent)
    
    Args:
        token_id: Token to revoke
        actor: Who is revoking the token
        reason: Reason for revocation
        
    Returns:
        dict: Result with success status
    """
    token_state = storage.get_token(token_id)
    
    if not token_state:
        # Create token in revoked state
        token_state = TokenState(
            token_id=token_id,
            status=TOKEN_STATUS_REVOKED,
            revoked_at=datetime.utcnow(),
            reason=reason
        )
        storage.save_token(token_state)
        write_audit_entry(AUDIT_ACTION_REVOKE, actor, token_id, reason)
        return {"success": True, "action": "revoked", "was_existing": False}
    
    if token_state.status != TOKEN_STATUS_REVOKED:
        # Revoke token atomically
        previous_status = token_state.status
        token_state.status = TOKEN_STATUS_REVOKED
        token_state.revoked_at = datetime.utcnow()
        token_state.reason = reason
        storage.save_token(token_state)
        write_audit_entry(AUDIT_ACTION_REVOKE, actor, token_id, reason, 
                         {"previous_status": previous_status})
        return {"success": True, "action": "revoked", "previous_status": previous_status}
    
    else:
        # Already revoked - idempotent
        return {"success": True, "action": "already_revoked"}

# 4. Validation Helpers
def validate_llm_recommendation(recommendation: str) -> str:
    """
    Validate and normalize LLM recommendation
    
    Args:
        recommendation: Raw recommendation from LLM
        
    Returns:
        str: Validated recommendation, defaults to "challenge" if invalid
    """
    if isinstance(recommendation, str):
        normalized = recommendation.lower().strip()
        if normalized in VALID_LLM_RECOMMENDATIONS:
            return normalized
    
    # Invalid recommendation - default to challenge
    return "challenge"

def parse_llm_response(llm_output: str) -> Dict[str, Any]:
    """
    Parse structured LLM response (two-line format)
    
    Args:
        llm_output: Raw LLM output
        
    Returns:
        dict: Parsed response with summary, recommendation, and metadata
    """
    try:
        lines = llm_output.strip().split('\n')
        
        if len(lines) >= 2:
            summary = lines[0].strip()
            recommendation = validate_llm_recommendation(lines[1].strip())
            
            return {
                "summary": summary,
                "recommendation": recommendation,
                "parsing_success": True,
                "raw_output": llm_output
            }
        else:
            # Fallback for single line or malformed output
            recommendation = validate_llm_recommendation(llm_output)
            return {
                "summary": "LLM output parsing failed",
                "recommendation": recommendation,
                "parsing_success": False,
                "parsing_fallback": True,
                "raw_output": llm_output
            }
    
    except Exception:
        # Complete parsing failure
        return {
            "summary": "LLM output parsing failed",
            "recommendation": "challenge",
            "parsing_success": False,
            "parsing_fallback": True,
            "raw_output": llm_output
        }

# 5. Event Management Helpers
def create_event(token_id: str, merchant_id: str, amount: float, risk_score: int) -> Event:
    """
    Create a new event with proper classification
    
    Args:
        token_id: Token being used
        merchant_id: Merchant processing transaction
        amount: Transaction amount
        risk_score: Risk score from external system
        
    Returns:
        Event: Created event object
    """
    risk_level = classify_risk_score(risk_score)
    decision = get_decision_for_risk_level(risk_level)
    
    if risk_level == "LOW":
        status = EVENT_STATUS_APPROVED
        auto_revoke_candidate = False
    else:
        status = EVENT_STATUS_WAITING_VERIFICATION
        auto_revoke_candidate = (risk_level == "HIGH")
    
    event = Event(
        event_id=str(uuid.uuid4()),
        token_id=token_id,
        merchant_id=merchant_id,
        amount=amount,
        risk_score=risk_score,
        status=status,
        decision=decision,
        auto_revoke_candidate=auto_revoke_candidate
    )
    
    storage.save_event(event)
    return event

# 6. Helper for getting current system state
def get_token_status(token_id: str) -> str:
    """Get current token status"""
    token_state = storage.get_token(token_id)
    return token_state.status if token_state else TOKEN_STATUS_ACTIVE

def get_event_summary(event_id: str) -> Optional[Dict[str, Any]]:
    """Get event summary for API responses"""
    event = storage.get_event(event_id)
    if not event:
        return None
    
    return {
        "event_id": event.event_id,
        "token_id": event.token_id,
        "merchant_id": event.merchant_id,
        "amount": event.amount,
        "risk_score": event.risk_score,
        "status": event.status,
        "decision": event.decision,
        "auto_revoke_candidate": event.auto_revoke_candidate,
        "verified_by": event.verified_by,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat()
    }
"""
TokenTrust Configuration
Canonical thresholds and configuration constants
"""

# Risk Score Thresholds (0-100)
APPROVE_MAX = 49
MEDIUM_MIN = 50
MEDIUM_MAX = 79
HIGH_MIN = 80

# Token Status Constants
TOKEN_STATUS_ACTIVE = "active"
TOKEN_STATUS_FROZEN = "frozen"
TOKEN_STATUS_REVOKED = "revoked"

# Event Status Constants
EVENT_STATUS_APPROVED = "approved"
EVENT_STATUS_WAITING_VERIFICATION = "waiting_verification"
EVENT_STATUS_VERIFIED_SUCCESS = "verified_success"
EVENT_STATUS_VERIFIED_FAILURE = "verified_failure"

# Decision Constants
DECISION_APPROVE = "approve"
DECISION_CHALLENGE = "challenge"
DECISION_CHALLENGE_HIGH = "challenge_high"

# Valid LLM Recommendations
VALID_LLM_RECOMMENDATIONS = ["approve", "challenge", "revoke"]

# Audit Action Constants
AUDIT_ACTION_FREEZE = "freeze_token"
AUDIT_ACTION_UNFREEZE = "unfreeze_token"
AUDIT_ACTION_REVOKE = "revoke_token"
AUDIT_ACTION_ANALYZE = "analyze_event"
AUDIT_ACTION_VERIFY = "verify_event"
AUDIT_ACTION_TRIAGE = "triage_event"
# TokenTrust Robust API v2.0

A production-ready backend for TokenTrust with canonical thresholds, idempotent operations, proper HTTP status codes, and comprehensive audit logging.

## 🚀 Quick Start

### Start the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="your_groq_api_key_here"

# Start the server
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Run the Demo

```bash
# Interactive demo showing all workflows
python demo_robust_api.py

# Run comprehensive test suite
python -m pytest test_robust_api.py -v
```

## 📋 API Overview

### Base URL
- **Production API v2:** `http://localhost:8000/v2`
- **Legacy API v1:** `http://localhost:8000` (deprecated)

### Authentication
Set `GROQ_API_KEY` environment variable for AI agent functionality.

## 🔄 Core Workflows

### 1. Transaction Analysis (`POST /v2/analyze`)

Analyzes transaction risk and manages token state based on canonical thresholds.

**Request:**
```json
{
  "token_id": "token_123",
  "merchant_id": "merchant_456", 
  "amount": 150.00,
  "risk_score": 65,
  "metadata": {"source": "mobile_app"}
}
```

**Response:**
```json
{
  "event_id": "evt_789",
  "decision": "challenge",
  "status": "waiting_verification",
  "token_status": "frozen",
  "risk_level": "MEDIUM",
  "auto_revoke_candidate": false,
  "message": "Transaction requires verification - medium risk, token frozen"
}
```

**Risk Classification:**
- **LOW (0-49):** Auto-approved, token remains active
- **MEDIUM (50-79):** Requires verification, token frozen  
- **HIGH (80-100):** Requires verification, token frozen as revoke candidate

### 2. Merchant Verification (`POST /v2/merchant-response`)

Processes merchant/user verification responses for frozen transactions.

**Request:**
```json
{
  "event_id": "evt_789",
  "user_response": "Yes, I authorized this transaction",
  "verification_method": "sms_2fa",
  "evidence": {"phone_verified": true}
}
```

**Response:**
```json
{
  "event_id": "evt_789",
  "final_status": "verified_success", 
  "token_status": "active",
  "verification_successful": true,
  "message": "Verification successful - token unfrozen, transaction can proceed"
}
```

### 3. AI Agent Triage (`POST /v2/triage`)

Allows AI agents to override standard workflow based on advanced analysis.

**Request:**
```json
{
  "event_id": "evt_789",
  "agent_decision": "approve",
  "reasoning": "AI detected legitimate user pattern despite risk score"
}
```

**Response:**
```json
{
  "event_id": "evt_789",
  "action_taken": "approved_unfrozen",
  "token_status": "active", 
  "message": "Agent approved transaction - token unfrozen"
}
```

**Agent Decisions:**
- `approve`: Approve transaction, unfreeze token
- `challenge`: Require additional verification
- `challenge_high`: High risk verification, mark for potential revocation
- `revoke`: Immediately revoke token

## 📊 Status & Monitoring

### Event Status (`GET /v2/event/{event_id}`)
Get complete event information including verification history.

### Token Status (`GET /v2/token/{token_id}/status`)  
Get current token state and history.

### Audit Trail (`GET /v2/audit/{target}`)
Get audit log entries for tokens or events.

### Health Check (`GET /v2/health`)
System health and storage statistics.

## 🔒 Token Lifecycle

### Token States
- **`active`**: Normal state, can process transactions
- **`frozen`**: Temporarily suspended, requires verification
- **`revoked`**: Permanently disabled, cannot be reactivated

### Idempotent Operations
All token lifecycle operations are idempotent:

```python
# Multiple freeze calls are safe
freeze_token("token_123", "suspicious_activity", "system")
freeze_token("token_123", "suspicious_activity", "system")  # No-op

# Unfreeze after successful verification  
unfreeze_token("token_123", "verification_system", "user_confirmed")

# Revoke for security (permanent)
revoke_token("token_123", "fraud_detection", "confirmed_fraud")
```

## ⚠️ Error Handling

### HTTP Status Codes
- **200 OK**: Successful operation
- **403 Forbidden**: Revoked token cannot be used
- **404 Not Found**: Event or token not found
- **409 Conflict**: Invalid state transition 
- **422 Unprocessable**: Validation error
- **500 Internal Error**: System error

### Example Error Response
```json
{
  "detail": "Token token_123 is revoked and cannot be used"
}
```

## 🔍 Audit Logging

Every operation is automatically logged with:
- **Action**: What was performed
- **Actor**: Who performed it (system, user, agent)
- **Target**: What was acted upon
- **Timestamp**: When it occurred
- **Reason**: Why it was performed
- **Details**: Additional context

### Audit Actions
- `analyze`: Transaction risk analysis
- `freeze`: Token frozen for verification
- `unfreeze`: Token restored after successful verification
- `revoke`: Token permanently disabled
- `verify`: Merchant/user verification processed
- `triage`: AI agent decision override

## 📋 Configuration

### Canonical Thresholds (`config.py`)
```python
# Risk Score Thresholds
APPROVE_MAX = 49        # Auto-approve up to this score
MEDIUM_MIN = 50         # Medium risk starts here
MEDIUM_MAX = 79         # Medium risk ends here  
HIGH_MIN = 80           # High risk starts here

# Token States
TOKEN_STATUS_ACTIVE = "active"
TOKEN_STATUS_FROZEN = "frozen"
TOKEN_STATUS_REVOKED = "revoked"

# Event States  
EVENT_STATUS_APPROVED = "approved"
EVENT_STATUS_WAITING_VERIFICATION = "waiting_verification"
EVENT_STATUS_VERIFIED_SUCCESS = "verified_success"
EVENT_STATUS_VERIFIED_FAILURE = "verified_failure"
```

## 🧪 Testing

### Run Full Test Suite
```bash
python -m pytest test_robust_api.py -v --tb=short
```

### Test Coverage
- Risk classification helpers
- Idempotent token lifecycle operations
- Complete workflow scenarios (LOW/MEDIUM/HIGH risk)
- Agent triage functionality
- Error handling and HTTP status codes
- Audit logging verification
- End-to-end integration testing

### Test Scenarios
1. **Low Risk Transaction**: Auto-approval workflow
2. **Medium Risk Success**: Freeze → Verify → Unfreeze
3. **High Risk Failure**: Freeze → Failed Verify → Revoke
4. **Agent Triage**: AI override of standard workflow
5. **Error Cases**: Revoked tokens, invalid states, validation errors

## 🚀 Production Deployment

### Environment Variables
```bash
export GROQ_API_KEY="your_groq_api_key"
export MONGO_URI="mongodb://localhost:27017"  # Optional
export REDIS_URL="redis://localhost:6379"    # Optional
```

### Performance Considerations
- In-memory storage for development (replace with database for production)
- Token operations are O(1) with hash table lookups
- Audit logging is append-only for performance
- Event processing is stateless and horizontally scalable

### Security Features
- All operations are audited with actor attribution
- Revoked tokens cannot be reactivated (security invariant)
- Idempotent operations prevent state corruption
- Proper error messages without sensitive data leakage

## 🔄 Migration from Legacy API

### Endpoint Mapping
- `POST /analyze` → `POST /v2/analyze` (enhanced)
- `POST /tokentrust/process` → `POST /v2/analyze` + `POST /v2/merchant-response`
- `POST /tokentrust/merchant-response` → `POST /v2/merchant-response`
- New: `POST /v2/triage` for AI agent decisions

### Breaking Changes
- Response format standardized with proper HTTP codes
- Event IDs replace session IDs for tracking
- Token states are explicit (`active`/`frozen`/`revoked`)
- Audit logging is mandatory and comprehensive

### Backward Compatibility
Legacy v1 endpoints remain available but are deprecated. Migrate to v2 for production use.

## 📞 Support

For issues or questions:
1. Check the audit trail: `GET /v2/audit/{target}`
2. Verify system health: `GET /v2/health`  
3. Run test suite: `pytest test_robust_api.py`
4. Review demo script: `python demo_robust_api.py`
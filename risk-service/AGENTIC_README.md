# TokenTrust Agentic AI System 🤖🔒

## Overview

TokenTrust is an advanced agentic AI system that provides comprehensive transaction security through intelligent risk assessment, automated decision making, and merchant verification workflows. The system uses LangChain and Groq API to create a multi-agent architecture that handles the complete token trust lifecycle.

## 🎯 Key Features

### 1. **Agentic AI Architecture**
- **TokenTrustOrchestrator**: Main coordinator managing the entire workflow
- **RiskAgent**: AI-powered risk assessment using LLM
- **TokenManager**: Intelligent token lifecycle management (freeze/unfreeze/revoke)
- **MerchantCommunicator**: Automated merchant communication for 2FA
- **VerificationAgent**: Smart verification process management

### 2. **Complete Workflow Automation**
```
Transaction → Risk Assessment → Decision Making → Action Execution → Verification → Final Decision
```

### 3. **Risk-Based Actions**
- **Low Risk (0-30)**: ✅ Auto-approve transactions
- **Medium Risk (31-70)**: 🧊 Freeze token + Request merchant 2FA
- **High Risk (71-100)**: 🚫 Immediately revoke token

### 4. **Intelligent Merchant Communication**
- Multi-channel notification (email, SMS, app)
- AI-generated personalized messages
- Automated 2FA workflow management
- Real-time verification tracking

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

**Required Environment Variables:**
```bash
GROQ_API_KEY=your_groq_api_key_here
MONGO_URI=mongodb://localhost:27017  # Optional
REDIS_URL=redis://localhost:6379     # Optional
PORT=8000
```

### 2. Start the Service

```bash
# Start the FastAPI server
python app.py

# The service will be available at http://localhost:8000
```

### 3. Test the System

```bash
# Run the comprehensive test suite
python test_agentic_system.py
```

## 📡 API Endpoints

### Core Agentic Endpoints

#### 1. **Complete Transaction Processing**
```http
POST /tokentrust/process
```

Process a transaction through the complete agentic workflow.

**Request:**
```json
{
  "token": "tkn_123456789",
  "merchant_id": "merchant_001",
  "amount": 5000.0,
  "security_context": {
    "token_age_minutes": 45,
    "device_trust_score": 65,
    "usual_location": "Mumbai, India",
    "current_location": "Delhi, India",
    "new_device": true,
    "vpn_detected": false,
    "unusual_time": false,
    "rushed_transaction": true
  },
  "user_info": {
    "user_id": "user_001",
    "account_age_days": 90
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-session-id",
  "final_status": "verified_and_approved",
  "token_status": "active",
  "risk_assessment": {
    "risk_score": 45,
    "decision": "CHALLENGE",
    "explanation": "Medium risk detected due to location change and new device"
  },
  "decision_reasoning": "Token frozen for merchant verification due to moderate risk factors",
  "message": "User verified by merchant - token unfrozen and transaction approved"
}
```

#### 2. **Merchant Verification Response**
```http
POST /tokentrust/merchant-response
```

Submit merchant 2FA verification results.

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "verified": true,
  "verified_by": "store_manager_john",
  "method": "phone_verification",
  "notes": "Customer showed valid ID"
}
```

#### 3. **Session Status Tracking**
```http
GET /tokentrust/session/{session_id}
```

Get real-time status of a processing session.

#### 4. **Merchant Dashboard**
```http
GET /tokentrust/merchant/{merchant_id}/verifications
```

Get pending verifications for a merchant.

#### 5. **System Analytics**
```http
GET /tokentrust/analytics
```

Get system performance metrics and analytics.

### Traditional Endpoint (Backwards Compatible)

#### **Traditional Risk Check**
```http
POST /risk-check
```

Traditional risk assessment (backwards compatible).

## 🧠 AI Agent Architecture

### TokenTrustOrchestrator
- **Role**: Main coordinator and workflow manager
- **Capabilities**: 
  - Session management
  - Workflow orchestration
  - Decision coordination
  - Error handling and fallbacks

### RiskAgent
- **Role**: Intelligent risk assessment
- **Capabilities**:
  - LLM-powered risk analysis
  - Historical pattern learning
  - Anomaly detection
  - Contextual decision making

### TokenManager
- **Role**: Token lifecycle management
- **Capabilities**:
  - Intelligent freeze/unfreeze decisions
  - AI-powered revocation analysis
  - Token state tracking
  - Security policy enforcement

### MerchantCommunicator
- **Role**: Automated merchant communication
- **Capabilities**:
  - Multi-channel notifications
  - AI-generated personalized messages
  - Response tracking and validation
  - Communication strategy optimization

### VerificationAgent
- **Role**: Verification process intelligence
- **Capabilities**:
  - Response authenticity validation
  - Fraud pattern detection
  - Merchant reliability scoring
  - Learning from verification outcomes

## 🔄 Workflow Examples

### Scenario 1: Low Risk Transaction (Auto-Approve)
```
Transaction Request → Risk Assessment (Score: 15) → Auto-Approve → Token Active
```

### Scenario 2: Medium Risk Transaction (Freeze & Verify)
```
Transaction Request → Risk Assessment (Score: 45) → Freeze Token → 
Notify Merchant → Merchant Verifies → Unfreeze Token → Transaction Approved
```

### Scenario 3: High Risk Transaction (Immediate Revoke)
```
Transaction Request → Risk Assessment (Score: 85) → Revoke Token → 
Notify All Parties → Transaction Blocked
```

### Scenario 4: Verification Failed
```
Transaction Request → Risk Assessment (Score: 50) → Freeze Token → 
Notify Merchant → Merchant Cannot Verify → Revoke Token → Transaction Blocked
```

## 🛡️ Security Features

### 1. **Multi-Layer Risk Assessment**
- Token age and freshness validation
- Device trust scoring
- Location and behavior analysis
- Transaction pattern detection
- Historical anomaly detection

### 2. **Intelligent Decision Making**
- AI-powered risk thresholds
- Context-aware decisions
- Learning from outcomes
- Adaptive risk scoring

### 3. **Secure Communication**
- Encrypted merchant notifications
- Authenticated response validation
- Session-based security
- Time-limited verifications

### 4. **Fraud Prevention**
- Real-time pattern detection
- Merchant collusion detection
- Response authenticity validation
- Behavioral analysis

## 📊 Monitoring & Analytics

### System Metrics
- Active sessions tracking
- Verification success rates
- Merchant reliability scores
- Risk score distributions
- Processing performance

### Analytics Dashboard
```http
GET /tokentrust/analytics
```

Provides:
- Total verifications processed
- Success/failure rates
- Merchant performance metrics
- System health indicators

## 🧪 Testing

### Comprehensive Test Suite
Run the complete test suite to validate all workflows:

```bash
python test_agentic_system.py
```

**Test Scenarios:**
1. ✅ Low risk auto-approval
2. 🧊 Medium risk freeze & verify (success)
3. 🚫 High risk immediate revoke
4. ❌ Medium risk verification failure
5. 📊 System analytics validation
6. 🧹 Session cleanup

### Manual Testing
Use the provided Postman collection or curl commands to test individual endpoints.

## 🔧 Configuration

### AI Model Configuration
- **Primary Model**: `llama-3.3-70b-versatile` (Groq)
- **Temperature**: 0.1-0.3 (for consistent, logical decisions)
- **Fallback**: Built-in rule-based decisions if AI fails

### Risk Thresholds
```python
LOW_RISK_THRESHOLD = 30      # Auto-approve
MEDIUM_RISK_THRESHOLD = 70   # Freeze & verify
HIGH_RISK_THRESHOLD = 100    # Immediate revoke
```

### Timeouts
```python
VERIFICATION_TIMEOUT = 600   # 10 minutes for merchant response
TOKEN_FREEZE_DURATION = 15   # Default freeze time
SESSION_CLEANUP_HOURS = 24   # Clean old sessions
```

## 🚀 Production Deployment

### 1. **Environment Setup**
```bash
# Production environment variables
GROQ_API_KEY=prod_key
MONGO_URI=mongodb://prod-mongo:27017/tokentrust
REDIS_URL=redis://prod-redis:6379
PORT=8000
LOG_LEVEL=INFO
```

### 2. **Docker Deployment**
```bash
# Build and run
docker-compose up -d
```

### 3. **Scaling Considerations**
- Use Redis for session storage in production
- MongoDB for persistent logging and analytics
- Load balancing for high availability
- Monitoring with health check endpoints

## 🤝 Integration Guide

### Frontend Integration
```javascript
// Process transaction with agentic AI
const response = await fetch('/tokentrust/process', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(transactionData)
});

const result = await response.json();
// Handle different outcomes based on result.final_status
```

### Merchant Integration
```javascript
// Submit verification response
const verification = await fetch('/tokentrust/merchant-response', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        session_id: sessionId,
        verified: customerVerified,
        verified_by: staffMember,
        method: 'in_person_verification'
    })
});
```

## 📈 Performance Metrics

### Expected Performance
- **Risk Assessment**: < 2 seconds
- **Token Management**: < 1 second  
- **Merchant Notification**: < 3 seconds
- **Complete Workflow**: < 30 seconds (including merchant response)

### Scalability
- **Concurrent Sessions**: 1000+ (with Redis)
- **Requests per Second**: 100+ (per instance)
- **Response Time**: 95th percentile < 5 seconds

## 🛠️ Development

### Adding New Agents
1. Create agent class inheriting base functionality
2. Implement required methods and AI prompts
3. Register with TokenTrustOrchestrator
4. Add configuration and tests

### Extending Workflows
1. Update orchestrator workflow logic
2. Add new API endpoints if needed
3. Update test suite
4. Document new capabilities

## 📚 API Documentation

Full interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Common Issues

1. **Groq API Key Error**
   ```bash
   Error: Invalid Groq API key
   Solution: Check GROQ_API_KEY in .env file
   ```

2. **MongoDB Connection Failed**
   ```bash
   Warning: MongoDB not connected - running without logging
   Solution: Optional service, system works without it
   ```

3. **Redis Connection Failed**
   ```bash
   Warning: Redis not connected - running without device history  
   Solution: Optional service, system works without it
   ```

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python app.py
```

## 🔄 Updates & Migration

### Version 2.0.0 Features
- ✅ Complete agentic AI architecture
- ✅ Multi-agent workflow orchestration
- ✅ Intelligent merchant communication
- ✅ Advanced verification management
- ✅ Real-time analytics and monitoring
- ✅ Comprehensive test suite

### Backwards Compatibility
- All v1.0 endpoints remain functional
- Existing integrations continue to work
- Gradual migration path available

## 🤖 AI Capabilities

### LangChain Integration
- **Framework**: LangChain for agent orchestration
- **Model**: Groq's LLaMA 3.3 70B for reasoning
- **Memory**: Conversation buffer for context
- **Tools**: Custom tools for token management

### Intelligent Features
- **Contextual Decision Making**: AI considers full transaction context
- **Pattern Learning**: System learns from historical outcomes  
- **Adaptive Thresholds**: Risk thresholds adapt based on performance
- **Natural Language**: AI generates human-readable explanations

## 📞 Support

For technical support or questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the test suite for examples
- Consult the API documentation

---

**TokenTrust Agentic AI System - Securing transactions with intelligent automation** 🚀🔒
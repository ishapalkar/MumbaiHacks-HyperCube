# Risk Checker Service - Simple Score Evaluator

## What It Does
Analyzes transactions and returns a **risk level** (LOW/MEDIUM/HIGH) based on AI analysis.

## Risk Levels
- **LOW** (0-29): ✅ Safe transaction - proceed normally
- **MEDIUM** (30-69): ⚠️ Requires verification - ask for 2FA or additional checks
- **HIGH** (70-100): 🚨 Suspicious activity - block transaction

## API Endpoint

### POST /risk-check

**Basic Request:**
```json
{
  "device_id": "device-123",
  "ip_address": "192.168.1.1",
  "amount": 100.0,
  "currency": "USD",
  "merchant": "Amazon",
  "user_id": "user-456",
  "geo_location": "New York, USA"
}
```

**Enhanced Request (with all fraud detection fields):**
```json
{
  "device_id": "device-123",
  "ip_address": "192.168.1.1",
  "amount": 100.0,
  "currency": "USD",
  "merchant": "Amazon",
  "user_id": "user-456",
  "geo_location": "New York, USA",
  "device_type": "mobile",
  "browser": "Chrome",
  "user_agent": "Mozilla/5.0...",
  "merchant_category": "retail",
  "account_age_days": 365,
  "is_vpn": false,
  "transaction_hour": 14,
  "previous_declined": 0,
  "email_verified": true,
  "phone_verified": true
}
```

**Response:**
```json
{
  "status": "success",
  "risk_score": 15,
  "risk_level": "LOW",
  "explanation": "Low risk: Verified account (365 days old), normal retail transaction, trusted device, no VPN, daytime transaction, no previous declines.",
  "timestamp": "2025-11-29T10:30:00"
}
```

## How to Run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add your Groq API key to `.env`:
```
GROQ_API_KEY=your_key_here
```

3. Start the service:
```bash
python app.py
```

4. Test it:
```bash
python test_api.py
```

## What AI Analyzes (15+ Fraud Signals)

**Device Analysis:**
- New vs known device fingerprint
- Device type consistency (mobile/desktop)
- Multiple accounts from same device

**Location & Network:**
- IP address reputation
- VPN/Proxy/Tor detection
- Geographic location changes
- Impossible travel patterns
- Country risk level

**Transaction Patterns:**
- Amount vs user's average
- Round number patterns
- Transaction velocity (frequency)
- Time of day (unusual hours like 2-5 AM)
- Rapid successive transactions

**Merchant Risk:**
- High-risk categories (crypto, gambling)
- New or unknown merchants
- Merchant location mismatch

**User Behavior:**
- Account age
- Email/phone verification status
- Previous declined transactions
- Recent failed attempts
- Behavior pattern changes

**Technical Signals:**
- Browser/User-Agent consistency
- Bot-like behavior
- Session manipulation

## Integration Example
```python
import requests

result = requests.post("http://localhost:8000/risk-check", json={
    "device_id": "device-123",
    "ip_address": "192.168.1.1",
    "amount": 500.0,
    "merchant": "Store Name"
})

risk_level = result.json()["risk_level"]

if risk_level == "LOW":
    print("✅ Transaction approved")
elif risk_level == "MEDIUM":
    print("⚠️ Request 2FA verification")
else:  # HIGH
    print("🚨 Block transaction")
```

## No Database Required
- Works perfectly without MongoDB or Redis
- Optional: MongoDB for logging, Redis for device history
- AI works with just the Groq API key

## Port
Service runs on: `http://localhost:8000`

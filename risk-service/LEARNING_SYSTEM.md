# 🧠 AI Learning System - How It Works

## Overview
The Risk Checker now **learns from each user's transaction history** to detect anomalies. It's not just rule-based - it builds a behavioral profile for each user.

## How It Works

### 1️⃣ First Transaction (New User)
```
User: tok_new_user_001
Transaction: ₹2,500 on Amazon from Mumbai

AI Analysis:
- Detects this is the FIRST transaction
- Automatically assigns LOW RISK (score: 10-25)
- Decision: APPROVE
- Stores: amount=2500, merchant=amazon, location=Mumbai, device_trust=70

Result: ✅ APPROVED - "First transaction, establishing baseline"
```

### 2️⃣ Second Transaction (Normal Pattern)
```
User: tok_new_user_001 (same user)
Transaction: ₹2,800 on Amazon from Mumbai

AI Analysis:
- Has history: avg_amount=2500, typical_merchants=[amazon]
- Current amount (2800) is close to average (2500) ✓
- Same merchant (amazon) ✓
- Same location (Mumbai) ✓
- Pattern matches → LOW RISK

Result: ✅ APPROVED - "Normal behavior pattern"
```

### 3️⃣ Third Transaction (ANOMALY!)
```
User: tok_new_user_001 (same user)
Transaction: ₹15,000 on crypto_exchange from Delhi using VPN

AI Analysis:
- Historical avg: ₹2,650
- Current: ₹15,000 (5.6x higher!) 🚨
- New merchant: crypto_exchange (not in history) 🚨
- New location: Delhi (usually Mumbai) 🚨
- VPN detected (never used before) 🚨
- New device + Lower device trust 🚨

Anomaly Score Calculation:
+ 25 points (amount 5x higher)
+ 15 points (new merchant)
+ 20 points (new location)
+ 25 points (new VPN usage)
+ 20 points (device trust drop)
+ 10 points (new device)
= 115 points → Capped at 95

Result: 🚨 FREEZE - "Multiple anomalies detected"
```

## What Gets Stored Per User

```json
{
  "is_first_transaction": false,
  "total_transactions": 3,
  "avg_amount": 6766,
  "min_amount": 2500,
  "max_amount": 15000,
  "typical_merchants": ["amazon", "amazon", "crypto_exchange"],
  "typical_locations": ["Mumbai", "Mumbai", "Delhi"],
  "avg_device_trust": 61,
  "vpn_usage_history": true,
  "high_risk_count": 1,
  "recent_risk_scores": [95, 18, 12]
}
```

## Anomaly Detection Rules

### Amount Anomalies
- **5x user's average** → +25 points
- **3x user's average** → +15 points
- **2x historical max** → +20 points

### Merchant Anomalies
- **New merchant (never seen)** → +15 points
- **Not in typical merchants** → +10 points

### Location Anomalies
- **New location** → +20 points
- **Never seen before** → +25 points

### Behavioral Changes
- **First time using VPN** → +25 points
- **Device trust drop > 30** → +20 points
- **Multiple high-risk history** → +15 points

## Example Scenarios

### Scenario 1: Legitimate User Growth
```
Transaction 1: ₹1,000 → LOW (first time)
Transaction 2: ₹1,200 → LOW (similar pattern)
Transaction 3: ₹1,500 → LOW (gradual increase)
Transaction 4: ₹2,000 → LOW (within 2x range)
Transaction 5: ₹3,500 → MEDIUM (approaching 2x, flagged for review)
```

### Scenario 2: Account Takeover
```
Transaction 1-5: ₹2,000-3,000 on Amazon, Mumbai → LOW
Transaction 6: ₹50,000 on crypto, Singapore, VPN → HIGH 🚨
(Detected: Amount spike + new merchant + location + VPN)
```

### Scenario 3: Slow Fraud (Harder to Detect)
```
Transaction 1-3: Normal pattern
Transaction 4: Slightly higher amount → MEDIUM
Transaction 5: Different merchant → MEDIUM
Transaction 6: Combine both → HIGH
(AI learns the gradual escalation pattern)
```

## Benefits

✅ **No false positives on first transaction** - New users get approved
✅ **Learns legitimate behavior** - Regular users have smooth experience
✅ **Detects account takeover** - Sudden pattern changes trigger alerts
✅ **Catches gradual fraud** - Tracks escalating suspicious behavior
✅ **Personalized risk assessment** - Each user has unique baseline

## Testing

Run the test to see learning in action:
```bash
python test_api.py
```

You'll see:
1. First transaction → LOW (building profile)
2. Similar transaction → LOW (matches pattern)
3. Anomaly transaction → HIGH (deviation detected)

## MongoDB Required

⚠️ **Important**: This learning system requires MongoDB to store transaction history.

Without MongoDB:
- Every transaction treated as "first transaction"
- No learning or anomaly detection
- Falls back to basic rule-based scoring

To enable:
1. Ensure MongoDB is running
2. Set MONGO_URI in .env
3. Service will automatically start building profiles

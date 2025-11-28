# Token Assigner Agent & Merchant Dashboard

This project consists of two main components:
1. **Backend**: FastAPI-based Token Assigner Agent with MongoDB and Socket.IO
2. **Frontend**: React-based Merchant Dashboard with real-time updates

## 🏗️ Project Structure

```
MumbaiHacks-HyperCube/
├── backend/
│   ├── token_assigner.py      # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
└── frontend/
    ├── src/
    │   ├── main.jsx           # React entry point
    │   ├── App.jsx            # Main application component
    │   ├── socket.js          # Socket.IO client service
    │   ├── SimulatePayment.jsx # Payment simulation form
    │   ├── TokensTable.jsx    # Tokens display table
    │   ├── TokenDetail.jsx    # Token details panel
    │   └── styles.css         # Application styles
    ├── package.json           # Node.js dependencies
    ├── vite.config.js         # Vite configuration
    └── index.html             # HTML entry point
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- MongoDB (local installation or MongoDB Atlas)

### 1. Backend Setup (Token Assigner Agent)

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env file with your MongoDB connection details
# MONGO_URL=mongodb://localhost:27017  # or your MongoDB Atlas URL
# MONGO_DB=token_system
# MERCHANT_AUTH_KEY=demo_key_123

# Run the FastAPI server
uvicorn token_assigner:asgi_app --reload --port 8000
```

**Backend will be available at:** http://localhost:8000
**Socket.IO endpoint:** http://localhost:8000/socket.io/
**API Documentation:** http://localhost:8000/docs

### 2. Frontend Setup (Merchant Dashboard)

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

**Frontend will be available at:** http://localhost:5173

## 📡 API Endpoints

### Authentication
All API endpoints require the `Authorization` header:
```
Authorization: Bearer demo_key_123
```

### Token Management Endpoints

#### POST `/assign-token`
Creates a new token for a merchant payment notification.

**Request Body:**
```json
{
  "customer_id": "cust_12345",
  "payment_reference": "PAY_2024_001",
  "amount": 99.99,
  "currency": "USD",
  "merchant_id": "merchant_demo",
  "idempotency_key": "idem_unique_key_123"
}
```

**Response:**
```json
{
  "token_id": "tok_abcd1234567890efgh",
  "expires_at": "2024-11-29T15:30:00Z",
  "status": "active"
}
```

#### GET `/tokens?merchant_id=<id>`
Retrieves recent tokens for a specific merchant.

#### GET `/token/<token_id>`
Retrieves full details for a specific token.

#### POST `/freeze-token`
Freezes a token (used by Risk Agent).

**Request Body:**
```json
{
  "token_id": "tok_abcd1234567890efgh"
}
```

#### POST `/revoke-token`
Revokes a token permanently.

**Request Body:**
```json
{
  "token_id": "tok_abcd1234567890efgh"
}
```

## 🔌 Socket.IO Events

### Namespace: `/merchant`

#### Client Events (Frontend → Backend)
- `join`: Join a merchant room
  ```json
  {
    "merchant_id": "merchant_demo"
  }
  ```

#### Server Events (Backend → Frontend)
- `token.assigned`: New token created
- `token.frozen`: Token frozen by Risk Agent
- `token.revoked`: Token revoked

**Event Data Format:**
```json
{
  "token_id": "tok_abcd1234567890efgh",
  "customer_id": "cust_12345",
  "amount": 99.99,
  "currency": "USD",
  "status": "active",
  "issued_at": "2024-11-29T14:30:00Z",
  "expires_at": "2024-11-29T15:30:00Z"
}
```

## 📊 Database Schema (MongoDB)

### Tokens Collection
```json
{
  "_id": ObjectId("..."),
  "token_id": "tok_abcd1234567890efgh",
  "customer_id": "cust_12345",
  "merchant_id": "merchant_demo",
  "payment_reference": "PAY_2024_001",
  "amount": 99.99,
  "currency": "USD",
  "idempotency_key": "idem_unique_key_123",
  "issued_at": ISODate("2024-11-29T14:30:00Z"),
  "expires_at": ISODate("2024-11-29T15:30:00Z"),
  "status": "active"  // active, frozen, revoked
}
```

**Indexes:**
- `expires_at` (TTL index for automatic cleanup)
- `merchant_id` (for efficient merchant queries)
- `token_id` (unique index)

## 🎯 Features

### Backend Features
- ✅ Real-time token issuance with UUID generation
- ✅ MongoDB integration with TTL and indexing
- ✅ Socket.IO real-time notifications
- ✅ Idempotency key support
- ✅ Token status management (active/frozen/revoked)
- ✅ CORS support for frontend
- ✅ API key authentication
- ✅ Automatic token expiration (1 hour TTL)

### Frontend Features
- ✅ Real-time Socket.IO connection with status indicator
- ✅ Payment simulation form with auto-generated idempotency keys
- ✅ Live tokens table with status badges
- ✅ Detailed token inspection panel
- ✅ Responsive design for mobile/desktop
- ✅ Real-time updates for token status changes
- ✅ Error handling and user feedback

## 🔧 Configuration

### Backend Environment Variables
```env
MONGO_URL=mongodb://localhost:27017
MONGO_DB=token_system
MERCHANT_AUTH_KEY=demo_key_123
```

### Frontend Configuration
The frontend is configured to connect to:
- Backend API: `http://localhost:8000`
- Socket.IO: `http://localhost:8000/merchant`
- Merchant ID: `merchant_demo` (hardcoded for demo)

## 🧪 Testing the Integration

### 1. Start Both Services
```bash
# Terminal 1: Backend
cd backend && uvicorn token_assigner:asgi_app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 2. Test Payment Flow
1. Open http://localhost:5173 in your browser
2. Fill out the "Simulate Payment Notification" form
3. Click "Generate Token"
4. Watch the token appear in real-time in the table below
5. Click on a token to view its full details

### 3. Test Real-time Updates
Use curl or Postman to freeze/revoke tokens:

```bash
# Freeze a token
curl -X POST http://localhost:8000/freeze-token \
  -H "Authorization: Bearer demo_key_123" \
  -H "Content-Type: application/json" \
  -d '{"token_id": "tok_your_token_id_here"}'

# Revoke a token
curl -X POST http://localhost:8000/revoke-token \
  -H "Authorization: Bearer demo_key_123" \
  -H "Content-Type: application/json" \
  -d '{"token_id": "tok_your_token_id_here"}'
```

Watch the frontend update automatically with the new token status!

## 🔗 Integration with LangChain Risk Agent

This Token Assigner is designed to work seamlessly with a separate LangChain-based Risk Agent:

1. **Risk Agent Integration Points:**
   - `POST /freeze-token` - Called when suspicious activity is detected
   - `POST /revoke-token` - Called when fraud is confirmed
   - Real-time Socket.IO notifications keep merchants informed

2. **Risk Agent Implementation Pattern:**
```python
# Example Risk Agent integration
import requests

def freeze_suspicious_token(token_id, reason):
    response = requests.post(
        "http://localhost:8000/freeze-token",
        headers={"Authorization": "Bearer demo_key_123"},
        json={"token_id": token_id}
    )
    # Risk Agent can then notify merchant via email/SMS
```

## 🛟 Troubleshooting

### Common Issues

**Backend not starting:**
- Check MongoDB connection in `.env`
- Ensure port 8000 is available
- Verify Python dependencies are installed

**Frontend not connecting to Socket.IO:**
- Ensure backend is running on port 8000
- Check browser console for connection errors
- Verify CORS settings in backend

**MongoDB connection issues:**
- For local MongoDB: Ensure MongoDB service is running
- For MongoDB Atlas: Check connection string and network access
- Verify database credentials

**Real-time updates not working:**
- Check Socket.IO connection status in frontend header
- Verify merchant room joining in browser console
- Ensure backend Socket.IO events are being emitted

## 📈 Performance & Scaling

### Database Optimization
- TTL indexes automatically clean up expired tokens
- Compound indexes optimize merchant queries
- Connection pooling via Motor async driver

### Real-time Performance
- Socket.IO rooms isolate merchant notifications
- Event-driven architecture minimizes database queries
- Async/await pattern throughout for optimal performance

This implementation provides a solid foundation for real-time token management with seamless integration capabilities for AI-powered risk assessment systems.
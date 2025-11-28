import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import socketio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "token_system")
MERCHANT_AUTH_KEY = os.getenv("MERCHANT_AUTH_KEY", "demo_key_123")

# MongoDB client
mongo_client = None
database = None

# Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins=["http://localhost:5173", "http://localhost:3000"],
    async_mode='asgi'
)

# FastAPI app
app = FastAPI(title="Token Assigner Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TokenAssignRequest(BaseModel):
    customer_id: str
    payment_reference: str
    amount: float
    currency: str = "USD"
    merchant_id: str
    idempotency_key: str

class TokenResponse(BaseModel):
    token_id: str
    expires_at: datetime
    status: str

class TokenFreezeRequest(BaseModel):
    token_id: str

class TokenRevokeRequest(BaseModel):
    token_id: str

class Token(BaseModel):
    token_id: str
    customer_id: str
    merchant_id: str
    payment_reference: str
    amount: float
    currency: str
    idempotency_key: str
    issued_at: datetime
    expires_at: datetime
    status: str

# Database connection
async def connect_to_mongo():
    global mongo_client, database
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    database = mongo_client[MONGO_DB]
    
    # Create TTL index on expires_at field
    await database.tokens.create_index("expires_at", expireAfterSeconds=0)
    
    # Create index on merchant_id for faster queries
    await database.tokens.create_index("merchant_id")
    await database.tokens.create_index("token_id", unique=True)

async def close_mongo_connection():
    if mongo_client:
        mongo_client.close()

# Auth dependency
async def verify_merchant_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split("Bearer ")[1]
    if token != MERCHANT_AUTH_KEY:
        raise HTTPException(status_code=401, detail="Invalid merchant API key")
    
    return token

# Socket.IO events
@sio.event(namespace="/merchant")
async def connect(sid, environ, auth=None):
    print(f"Client {sid} connected to merchant namespace")

@sio.event(namespace="/merchant")
async def disconnect(sid):
    print(f"Client {sid} disconnected from merchant namespace")

@sio.event(namespace="/merchant")
async def join(sid, data):
    merchant_id = data.get("merchant_id")
    if merchant_id:
        room_name = f"merchant:{merchant_id}"
        await sio.enter_room(sid, room_name, namespace="/merchant")
        print(f"Client {sid} joined room {room_name}")
        await sio.emit("joined", {"room": room_name}, to=sid, namespace="/merchant")

# API endpoints
@app.post("/assign-token", response_model=TokenResponse)
async def assign_token(
    request: TokenAssignRequest,
    auth_token: str = Depends(verify_merchant_auth)
):
    try:
        # Generate token ID
        token_id = f"tok_{uuid.uuid4().hex}"
        
        # Calculate expiration (1 hour from now)
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(hours=1)
        
        # Check for duplicate idempotency key
        existing_token = await database.tokens.find_one({
            "merchant_id": request.merchant_id,
            "idempotency_key": request.idempotency_key
        })
        
        if existing_token:
            return TokenResponse(
                token_id=existing_token["token_id"],
                expires_at=existing_token["expires_at"],
                status=existing_token["status"]
            )
        
        # Create token document
        token_doc = {
            "token_id": token_id,
            "customer_id": request.customer_id,
            "merchant_id": request.merchant_id,
            "payment_reference": request.payment_reference,
            "amount": request.amount,
            "currency": request.currency,
            "idempotency_key": request.idempotency_key,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "status": "active"
        }
        
        # Insert into MongoDB
        await database.tokens.insert_one(token_doc)
        
        # Emit socket event to merchant room
        room_name = f"merchant:{request.merchant_id}"
        await sio.emit(
            "token.assigned",
            {
                "token_id": token_id,
                "customer_id": request.customer_id,
                "amount": request.amount,
                "currency": request.currency,
                "status": "active",
                "issued_at": issued_at.isoformat(),
                "expires_at": expires_at.isoformat()
            },
            room=room_name,
            namespace="/merchant"
        )
        
        return TokenResponse(
            token_id=token_id,
            expires_at=expires_at,
            status="active"
        )
        
    except Exception as e:
        print(f"Error assigning token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tokens")
async def get_tokens(
    merchant_id: str,
    auth_token: str = Depends(verify_merchant_auth)
):
    try:
        # Get recent tokens for merchant (last 24 hours)
        since = datetime.utcnow() - timedelta(hours=24)
        
        cursor = database.tokens.find({
            "merchant_id": merchant_id,
            "issued_at": {"$gte": since}
        }).sort("issued_at", -1).limit(100)
        
        tokens = []
        async for token in cursor:
            token["_id"] = str(token["_id"])  # Convert ObjectId to string
            tokens.append(token)
        
        return {"tokens": tokens}
        
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/token/{token_id}")
async def get_token(
    token_id: str,
    auth_token: str = Depends(verify_merchant_auth)
):
    try:
        token = await database.tokens.find_one({"token_id": token_id})
        
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        token["_id"] = str(token["_id"])  # Convert ObjectId to string
        return {"token": token}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/freeze-token")
async def freeze_token(
    request: TokenFreezeRequest,
    auth_token: str = Depends(verify_merchant_auth)
):
    try:
        # Find and update token
        result = await database.tokens.find_one_and_update(
            {"token_id": request.token_id, "status": {"$in": ["active", "frozen"]}},
            {"$set": {"status": "frozen"}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Token not found or already revoked")
        
        # Emit socket event to merchant room
        room_name = f"merchant:{result['merchant_id']}"
        await sio.emit(
            "token.frozen",
            {
                "token_id": request.token_id,
                "status": "frozen",
                "customer_id": result["customer_id"],
                "amount": result["amount"]
            },
            room=room_name,
            namespace="/merchant"
        )
        
        return {"message": "Token frozen successfully", "token_id": request.token_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error freezing token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/revoke-token")
async def revoke_token(
    request: TokenRevokeRequest,
    auth_token: str = Depends(verify_merchant_auth)
):
    try:
        # Find and update token
        result = await database.tokens.find_one_and_update(
            {"token_id": request.token_id, "status": {"$in": ["active", "frozen"]}},
            {"$set": {"status": "revoked"}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Token not found or already revoked")
        
        # Emit socket event to merchant room
        room_name = f"merchant:{result['merchant_id']}"
        await sio.emit(
            "token.revoked",
            {
                "token_id": request.token_id,
                "status": "revoked",
                "customer_id": result["customer_id"],
                "amount": result["amount"]
            },
            room=room_name,
            namespace="/merchant"
        )
        
        return {"message": "Token revoked successfully", "token_id": request.token_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error revoking token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    print("Connected to MongoDB")
    print(f"Server starting on http://localhost:8000")
    print(f"Socket.IO available at http://localhost:8000/socket.io/")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    print("Disconnected from MongoDB")

# Create ASGI app with Socket.IO
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='/socket.io')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("token_assigner:asgi_app", host="0.0.0.0", port=8000, reload=True)
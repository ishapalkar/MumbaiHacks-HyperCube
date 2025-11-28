
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="TokenTrust Minimal Test", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TokenTrust Agentic AI System - Minimal Test", "status": "running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TokenTrust Minimal Test",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Server starting on http://localhost:{port}")
    print("📋 Available endpoints:")
    print(f"   - http://localhost:{port}/")
    print(f"   - http://localhost:{port}/health")
    print("🔍 Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=port)

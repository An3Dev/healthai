import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import json
from typing import Dict, Any, List, Optional
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(
    title="Health AI Agent API",
    description="API for Health AI Agent using PinAI SDK",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health data path
HEALTH_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_health_data.json")

# Load health data
def load_health_data() -> Dict[str, Any]:
    try:
        with open(HEALTH_DATA_PATH, "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading health data: {e}")
        raise HTTPException(status_code=500, detail="Failed to load health data")

# Routes
@app.get("/")
async def root():
    return {"message": "Health AI Agent API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/user/profile")
async def get_user_profile():
    health_data = load_health_data()
    return health_data["user"]

@app.get("/api/health/blood-tests")
async def get_blood_tests():
    health_data = load_health_data()
    return health_data["bloodTests"]

@app.get("/api/health/vitals")
async def get_vitals():
    health_data = load_health_data()
    return health_data["vitals"]

@app.get("/api/health/medical-history")
async def get_medical_history():
    health_data = load_health_data()
    return health_data["medicalHistory"]

@app.get("/api/health/metrics")
async def get_health_metrics():
    health_data = load_health_data()
    return health_data["healthMetrics"]

# Import the PinAI agent implementation
from app.agent.health_agent import HealthAIAgent

# Initialize the Health AI Agent
health_agent = HealthAIAgent()

@app.post("/api/chat")
async def chat(request: Dict[str, Any]):
    try:
        message = request.get("message", "")
        session_id = request.get("session_id", "default_session")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get health data to provide context to the agent
        health_data = load_health_data()
        
        # Process the message using the Health AI Agent
        response = health_agent.process_message(message, health_data, session_id)
        
        return {
            "response": response,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
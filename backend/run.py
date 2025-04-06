import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment variables
port = int(os.getenv("PORT", 8000))
host = os.getenv("HOST", "0.0.0.0")
debug = os.getenv("DEBUG", "true").lower() == "true"

if __name__ == "__main__":
    print(f"Starting Health AI Agent API on http://{host}:{port}")
    print("Documentation available at http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug
    ) 
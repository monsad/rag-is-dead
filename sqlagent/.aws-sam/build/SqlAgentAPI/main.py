"""
Production-ready FastAPI entry point for deployment
"""
import os
from api import app

# Configure for production
if __name__ != "__main__":
    # This runs when deployed (not in development)
    pass

# Export app for deployment platforms
application = app  # For some platforms that expect 'application'
handler = app      # For serverless platforms

# Environment-based configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
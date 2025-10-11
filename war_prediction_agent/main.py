from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import redis.asyncio as redis
from typing import Optional
import json
from datetime import datetime
from pathlib import Path

from agent import WarPredictionAgent
from models import PredictionRequest, PredictionResponse
from config import settings

# Redis client for caching
redis_client: Optional[redis.Redis] = None
agent: Optional[WarPredictionAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global redis_client, agent
    
    # Startup
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    agent = WarPredictionAgent()
    print("✅ Application started")
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    print("👋 Application shutdown")

app = FastAPI(
    title="War Prediction Agent API",
    description="AI-powered war outbreak prediction system using multi-source intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI"""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return static_path.read_text()
    return """
    <html>
        <body>
            <h1>War Prediction Agent API</h1>
            <p>API is running. UI not found.</p>
            <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
    </html>
    """

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "service": "War Prediction Agent",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "ui": "/",
            "predict": "/predict",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = False
    try:
        await redis_client.ping()
        redis_healthy = True
    except Exception as e:
        print(f"Redis health check failed: {e}")
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_war_outbreak(
    request: PredictionRequest,
    background_tasks: BackgroundTasks
):
    """
    Main prediction endpoint
    
    Analyzes multiple data sources to predict war outbreak risk:
    - News agencies
    - Military intelligence sources
    - Social media
    
    Returns risk assessment by region and globally.
    """
    try:
        # Check cache
        cache_key = f"prediction:{request.lookback_hours}:{','.join(request.regions or [])}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            print("📦 Returning cached prediction")
            return PredictionResponse.parse_raw(cached)
        
        # Run prediction
        print(f"🚀 Starting new prediction (lookback: {request.lookback_hours}h)")
        prediction = await agent.predict(hours_back=request.lookback_hours)
        
        # Cache result for 30 minutes
        await redis_client.setex(
            cache_key,
            1800,
            prediction.model_dump_json()
        )
        
        # Log to background task
        background_tasks.add_task(log_prediction, prediction)
        
        return prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        # Get cached predictions count
        keys = await redis_client.keys("prediction:*")
        
        return {
            "cached_predictions": len(keys),
            "cache_hit_rate": "N/A",
            "uptime": "N/A",
            "total_predictions": "N/A"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache")
async def clear_cache():
    """Clear all cached predictions"""
    try:
        keys = await redis_client.keys("prediction:*")
        if keys:
            await redis_client.delete(*keys)
        
        return {
            "status": "success",
            "cleared": len(keys)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def log_prediction(prediction: PredictionResponse):
    """Background task to log predictions"""
    log_entry = {
        "timestamp": prediction.timestamp.isoformat(),
        "risk_level": prediction.global_risk_level.value,
        "risk_score": prediction.global_risk_score,
        "sources": prediction.sources_analyzed
    }
    
    # Store in Redis list (keep last 100)
    await redis_client.lpush("prediction_history", json.dumps(log_entry))
    await redis_client.ltrim("prediction_history", 0, 99)

@app.get("/history")
async def get_prediction_history(limit: int = 20):
    """Get recent prediction history"""
    try:
        history = await redis_client.lrange("prediction_history", 0, limit - 1)
        return {
            "predictions": [json.loads(h) for h in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

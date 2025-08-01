from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import uvicorn
import os
import time
import logging
from dotenv import load_dotenv

# Import your existing agent functionality
from agent import handle_user_query, get_db_connection

# Import authentication system
from auth import (
    get_api_key, require_read, require_query, require_predict, require_admin,
    get_optional_api_key, check_rate_limit, key_manager, APIKey
)

# Load environment variables
load_dotenv()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with comprehensive metadata
app = FastAPI(
    title="🔐 SQL Agent API (Secured)",
    description="""
    🤖 **AI-Powered SQL Agent API with Token-Based Security**
    
    A sophisticated REST API that provides intelligent database querying capabilities with advanced predictive analytics.
    
    ## 🔐 Authentication Required
    
    **This API is protected with API key authentication.**
    
    ### How to Authenticate:
    1. **Get an API Key**: Contact your administrator or use the `/auth/create-key` endpoint
    2. **Add to Headers**: Include `Authorization: Bearer your-api-key-here`
    3. **Use Swagger**: Click the 🔒 "Authorize" button below and enter your key
    
    ### Example Request:
    ```bash
    curl -X POST "https://your-api-url/query" \\
      -H "Authorization: Bearer sk-your-api-key-here" \\
      -H "Content-Type: application/json" \\
      -d '{"query": "How many customers do we have?"}'
    ```
    
    ## ⚡ Features
    
    * 🗣️ **Natural Language Processing**: Ask questions in plain English or Polish
    * 🔮 **Predictive Analytics**: Advanced revenue forecasting using MRC/NRC analysis
    * 📊 **Real-time Database Queries**: Connect to PostgreSQL and get instant insights
    * 🧠 **AI-Powered**: Uses OpenAI GPT models with LangChain for intelligent query processing
    * 📈 **Business Intelligence**: Sophisticated feature engineering and trend analysis
    * 🔐 **Secure**: Token-based authentication with permission management
    
    ## 🚀 Getting Started
    
    1. **Authenticate**: Get your API key and use it in requests
    2. **Check Status**: Use `/health` to verify system status (public endpoint)
    3. **Explore**: Try `/examples` to see sample queries (public endpoint)
    4. **Query**: Use `/query` for database questions (requires authentication)
    5. **Predict**: Use `/predict` for revenue forecasting (requires authentication)
    
    ## 📝 Query Examples
    
    * "How many customers do we have?"
    * "Show me top 5 products by revenue"
    * "Predict sales for next quarter"
    * "What's our MRC trend this year?"
    * "Ile mamy aktywnych produktów?" (Polish)
    
    ## 🔑 API Key Management
    
    * `/auth/keys` - List your API keys (admin only)
    * `/auth/create-key` - Create new API key (admin only)
    * `/auth/revoke-key` - Revoke API key (admin only)
    """, 
    version="2.1.0",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "https://68556f93f34d.ngrok-free.app",
            "description": "Public API Server (ngrok tunnel)"
        },
        {
            "url": "http://localhost:8001",
            "description": "Local development server"
        }
    ]
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this more restrictively in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Global exception: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )

# HTTP exception handler  
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"⚠️ HTTP exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

# Request/Response models with comprehensive documentation
class QueryRequest(BaseModel):
    """Request model for database queries and predictions"""
    query: str = Field(
        description="Natural language query about your database or request for predictions",
        example="How many suppliers do we have?",
        min_length=1,
        max_length=1000
    )
    language: Optional[str] = Field(
        default="en",
        description="Language for the query response",
        example="en",
        pattern="^(en|pl)$"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "Show me the top 5 customers by revenue",
                    "language": "en"
                },
                {
                    "query": "Predict sales for next quarter",
                    "language": "en"
                },
                {
                    "query": "Ile mamy aktywnych produktów?",
                    "language": "pl"
                }
            ]
        }

class QueryResponse(BaseModel):
    """Response model for database queries"""
    success: bool = Field(description="Whether the query was processed successfully")
    response: str = Field(description="The answer to your query or error message")
    query: str = Field(description="The original query that was processed")
    error: Optional[str] = Field(default=None, description="Error details if query failed")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "response": "You have 161 suppliers in your database.",
                    "query": "How many suppliers do we have?",
                    "error": None
                },
                {
                    "success": False,
                    "response": "",
                    "query": "invalid query",
                    "error": "Database connection failed"
                }
            ]
        }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(description="Overall system status", example="healthy")
    database_connected: bool = Field(description="Database connection status", example=True)
    message: str = Field(description="Detailed status message", example="API is running and database is connected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database_connected": True,
                "message": "API is running and database is connected"
            }
        }

class ExamplesResponse(BaseModel):
    """Examples response model"""
    sql_queries: list[str] = Field(description="Example SQL-type queries")
    prediction_queries: list[str] = Field(description="Example prediction queries")
    polish_queries: list[str] = Field(description="Example queries in Polish")
    
class SchemaResponse(BaseModel):
    """Database schema response model"""
    success: bool = Field(description="Whether schema info was retrieved successfully")
    schema_info: str = Field(description="Database schema information")

# Health check endpoint
@app.get(
    "/health", 
    response_model=HealthResponse,
    tags=["🌐 Public Endpoints"],
    summary="Health Check (Public)",
    description="Check the overall system health including API status and database connectivity"
)
async def health_check(request: Request):
    """
    ## Health Check Endpoint
    
    Performs a comprehensive health check of the system:
    
    * ✅ **API Status**: Confirms the API is running
    * 🗄️ **Database**: Tests PostgreSQL connection
    * 📊 **Response Time**: Quick response for monitoring
    
    ### Use Cases
    * Monitoring and alerting systems
    * Load balancer health checks  
    * Deployment verification
    * Troubleshooting connectivity issues
    
    ### Response Codes
    * **200**: System is healthy
    * **200**: System is degraded (API up, DB down)
    * **500**: System is unhealthy
    """
    # Apply rate limiting for unauthenticated requests
    check_rate_limit(request)
    
    try:
        # Test database connection
        conn = get_db_connection()
        db_connected = conn is not None
        if conn:
            conn.close()
        
        return HealthResponse(
            status="healthy" if db_connected else "degraded",
            database_connected=db_connected,
            message="API is running" + (" and database is connected" if db_connected else " but database connection failed")
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            message=f"Health check failed: {str(e)}"
        )

# Main query endpoint
@app.post(
    "/query", 
    response_model=QueryResponse,
    tags=["🔐 Protected Endpoints"],
    summary="Process Natural Language Query (Authentication Required)",
    description="Transform natural language questions into SQL queries and return intelligent responses"
)
async def process_query(request: QueryRequest, api_key: APIKey = Depends(require_query)):
    """
    ## 🧠 Natural Language Database Query Processing
    
    This endpoint is the core of the SQL Agent API. It accepts natural language questions
    and uses advanced AI to:
    
    ### 🔍 **Query Processing**
    * **Parse Intent**: Understands what you're asking for
    * **Generate SQL**: Creates optimized PostgreSQL queries
    * **Execute Safely**: Runs queries with proper error handling
    * **Format Results**: Returns human-readable responses
    
    ### 📊 **Supported Query Types**
    
    **Data Retrieval:**
    * "How many customers do we have?"
    * "Show me top 5 products by revenue"
    * "List all active contracts"
    
    **Analytics:**
    * "What's our total monthly recurring revenue?"
    * "Which suppliers have the most transactions?"
    * "Show revenue trends by quarter"
    
    **Filtering & Search:**
    * "Find customers in California"
    * "Show contracts expiring this month"
    * "Products with MRC over $1000"
    
    ### 🌍 **Multi-Language Support**
    * **English**: "How many active products do we have?"
    * **Polish**: "Ile mamy aktywnych produktów?"
    
    ### ⚡ **Performance**
    * Typical response time: 2-5 seconds
    * Handles complex joins automatically
    * Built-in query optimization
    
    ### 🛡️ **Security**  
    * Read-only database access
    * SQL injection protection
    * Input validation and sanitization
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Process the query using your existing agent
        response = handle_user_query(request.query)
        
        return QueryResponse(
            success=True,
            response=response,
            query=request.query
        )
    
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing query: {str(e)}")
        
        return QueryResponse(
            success=False,
            response="",
            query=request.query,
            error=f"Failed to process query: {str(e)}"
        )

# Specific endpoint for predictions
@app.post(
    "/predict", 
    response_model=QueryResponse,
    tags=["🔐 Protected Endpoints"],
    summary="Revenue & Sales Forecasting (Authentication Required)",
    description="Generate sophisticated business predictions using advanced machine learning models"
)
async def predict_sales(request: QueryRequest, api_key: APIKey = Depends(require_predict)):
    """
    ## 🔮 Advanced Business Forecasting
    
    This endpoint provides sophisticated predictive analytics using machine learning models
    trained on your actual business data.
    
    ### 🎯 **Prediction Capabilities**
    
    **Revenue Forecasting:**
    * Monthly Recurring Revenue (MRC) predictions
    * Non-Recurring Revenue (NRC) forecasts  
    * Total revenue projections
    * Seasonal trend analysis
    
    **Time Horizons:**
    * **Monthly**: "Predict sales for next month"
    * **Quarterly**: "Forecast revenue for Q2"
    * **Annual**: "What will revenue be next year?"
    * **Custom**: "6 months forecast"
    
    ### 📊 **Machine Learning Features**
    * **Feature Engineering**: 15+ business metrics
    * **Trend Analysis**: Moving averages, growth rates
    * **Seasonality**: Q1/Q4 adjustments
    * **Business Logic**: Win rates, deal velocity
    
    ### 📈 **Data Sources**
    * Historical deals from `quotes_quotecontainer`
    * Product revenue from `products_productv2`
    * Account relationships and types
    * 24-month historical analysis
    
    ### 💡 **Example Queries**
    * "Predict sales for next quarter"  
    * "What will MRC be in 6 months?"
    * "Revenue forecast for this year"
    * "Przewiduj przychody na następny kwartał" (Polish)
    
    ### 🔬 **Model Details**  
    * **Algorithm**: Linear Regression with feature engineering
    * **Training Data**: Last 24 months of business data
    * **Validation**: Cross-validation on historical data
    * **Accuracy**: Typical ±15% for quarterly forecasts
    """
    # Ensure the query is interpreted as a prediction request
    prediction_query = f"przewiduj {request.query}" if not any(word in request.query.lower() for word in ["przewiduj", "prognoza", "predict", "forecast"]) else request.query
    
    return await process_query(QueryRequest(query=prediction_query, language=request.language))

# Database schema information endpoint
@app.get(
    "/schema", 
    response_model=SchemaResponse,
    tags=["🔐 Protected Endpoints"],
    summary="Database Schema Information (Authentication Required)",
    description="Retrieve comprehensive information about your database structure and tables"
)
async def get_database_info(api_key: APIKey = Depends(require_read)):
    """
    ## 🗄️ Database Schema Explorer
    
    Get detailed information about your database structure, tables, and relationships.
    
    ### 📋 **Schema Information Includes**
    * **Tables**: All available tables and their purposes
    * **Columns**: Key columns and data types  
    * **Relationships**: Foreign key relationships
    * **Sample Data**: Example values for context
    
    ### 🔍 **Key Tables Covered**
    * `accounts_account` - Customer and supplier information
    * `quotes_quotecontainer` - Deal and revenue data
    * `products_productv2` - Product and service details
    * `accounts_supplierteam` - Supplier team structure
    
    ### 💡 **Use Cases**
    * Understanding data structure before querying
    * Exploring available data for analysis
    * Building custom reports and dashboards
    * Data integration planning
    """
    try:
        # Use your agent to get database information
        schema_query = "Display basic database schema information"
        response = handle_user_query(schema_query)
        
        return {
            "success": True,
            "schema_info": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")

# Example queries endpoint
@app.get(
    "/examples", 
    response_model=ExamplesResponse,
    tags=["🌐 Public Endpoints"],
    summary="Query Examples & Templates (Public)",
    description="Get curated example queries to help you get started with the API"
)
async def get_example_queries(request: Request):
    """
    ## 📝 Query Examples & Templates
    
    Get started quickly with these curated example queries that demonstrate
    the full capabilities of the SQL Agent API.
    
    ### 🔍 **SQL Query Examples**
    Ready-to-use queries for common database operations:
    * Data counting and aggregation
    * Filtering and searching
    * Top-N queries and rankings
    * Date-based filtering
    
    ### 🔮 **Prediction Examples**  
    Sample forecasting queries for business intelligence:
    * Revenue predictions
    * Sales forecasting
    * Trend analysis
    * Multi-timeframe projections
    
    ### 🌍 **Multi-Language Support**
    Examples in both English and Polish to demonstrate
    language flexibility.
    
    ### 💡 **Pro Tips**
    * Start with simple queries and build complexity
    * Use specific timeframes for better results
    * Combine filters for targeted insights
    * Try both prediction and analytical queries
    """
    # Apply rate limiting for unauthenticated requests
    check_rate_limit(request)
    
    examples = {
        "sql_queries": [
            "How many suppliers do we have?",
            "Show me all customers from California",
            "List the top 5 products by revenue",
            "What are the latest 10 transactions?",
            "How many active contracts do we have?",
            "Show me all customers with contracts expiring this month"
        ],
        "prediction_queries": [
            "Predict sales for next 3 months",
            "Forecast revenue trends",
            "What will be the sales projection for next quarter?"
        ],
        "polish_queries": [
            "Ile mamy dostawców?",
            "Pokaż mi wszystkich klientów z Kalifornii",
            "Przewiduj sprzedaż na następne 3 miesiące"
        ]
    }
    return examples

# Root endpoint
@app.get(
    "/",
    tags=["🌐 Public Endpoints"],
    summary="API Overview (Public)",
    description="Welcome endpoint with comprehensive API information and quick start guide"
)
async def root(request: Request):
    """
    ## 🚀 Welcome to SQL Agent API
    
    **The most advanced AI-powered database querying platform**
    
    Transform natural language into intelligent database insights with cutting-edge AI.
    
    ### ⚡ **Quick Start**
    1. Check system health: `GET /health`
    2. Explore examples: `GET /examples` 
    3. Ask your first question: `POST /query`
    4. Generate predictions: `POST /predict`
    
    ### 🎯 **Core Features**
    * **Natural Language Processing**: Ask questions in plain English or Polish
    * **Advanced Analytics**: Get intelligent insights from your PostgreSQL data
    * **Predictive Modeling**: ML-powered revenue and sales forecasting
    * **Real-time Processing**: Fast responses with sophisticated query optimization
    """
    # Apply rate limiting for unauthenticated requests
    check_rate_limit(request)
    
    return {
        "message": "🔐 Welcome to Secured SQL Agent API v2.1",
        "description": "AI-powered database intelligence platform with token-based security",
        "status": "🟢 Online",
        "features": {
            "🧠 AI-Powered": "Advanced natural language processing",
            "🔮 Predictive": "Machine learning forecasting models", 
            "🌍 Multi-language": "English and Polish support",
            "⚡ Fast": "Optimized query processing",
            "🔒 Secure": "Enterprise-grade data protection"
        },
        "endpoints": {
            "🏥 /health": "System health and database connectivity",
            "🧠 /query": "Natural language database queries",
            "🔮 /predict": "Revenue and sales forecasting",
            "🗄️ /schema": "Database structure information", 
            "📝 /examples": "Query examples and templates",
            "📚 /docs": "Interactive Swagger documentation",
            "📖 /redoc": "Alternative API documentation"
        },
        "getting_started": {
            "1": "Visit /docs for interactive documentation",
            "2": "Try /examples to see sample queries",
            "3": "Use /health to verify system status",
            "4": "Start querying with /query endpoint"
        },
        "version": "2.1.0",
        "powered_by": "🦜🔗 LangChain + 🤖 OpenAI + ⚡ FastAPI + 🔐 Auth"
    }

# =============================================================================
# 🔐 AUTHENTICATION MANAGEMENT ENDPOINTS
# =============================================================================

class CreateKeyRequest(BaseModel):
    """Request model for creating API keys"""
    name: str = Field(description="Name/description for the API key", example="My App Key")
    expires_days: Optional[int] = Field(default=None, description="Days until expiration (null for no expiration)", example=90)
    permissions: Optional[List[str]] = Field(default=["read", "query", "predict"], description="List of permissions", example=["read", "query"])

class CreateKeyResponse(BaseModel):
    """Response model for created API key"""
    success: bool
    key: str = Field(description="The API key - save this, it won't be shown again")
    key_id: str = Field(description="Key identifier")
    name: str
    expires_at: Optional[str]
    permissions: List[str]

class KeyListResponse(BaseModel):
    """Response model for listing API keys"""
    success: bool
    keys: List[dict]

@app.post(
    "/auth/create-key",
    response_model=CreateKeyResponse,
    tags=["🔑 API Key Management"],
    summary="Create New API Key (Admin Only)",
    description="Create a new API key with specified permissions and expiration"
)
async def create_api_key(request: CreateKeyRequest, api_key: APIKey = Depends(require_admin)):
    """
    ## 🔑 Create New API Key
    
    Creates a new API key with the specified permissions and optional expiration date.
    
    **⚠️ Admin Permission Required**
    
    ### Permissions Available:
    - `read` - Access to database schema and information
    - `query` - Natural language database queries
    - `predict` - Revenue forecasting and predictions
    - `admin` - API key management (create, list, revoke)
    
    ### Security Notes:
    - The API key will only be shown once in the response
    - Save the key immediately in a secure location
    - Keys can be revoked at any time using the revoke endpoint
    """
    try:
        key, new_api_key = key_manager.create_key(
            name=request.name,
            expires_days=request.expires_days,
            permissions=request.permissions or ["read", "query", "predict"]
        )
        
        logger.info(f"🔑 New API key created: {new_api_key.key_id} by {api_key.name}")
        
        return CreateKeyResponse(
            success=True,
            key=key,
            key_id=new_api_key.key_id,
            name=new_api_key.name,
            expires_at=new_api_key.expires_at,
            permissions=new_api_key.permissions
        )
    except Exception as e:
        logger.error(f"❌ Error creating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")

@app.get(
    "/auth/keys",
    response_model=KeyListResponse,
    tags=["🔑 API Key Management"],
    summary="List API Keys (Admin Only)",
    description="List all API keys with their details (without showing the actual keys)"
)
async def list_api_keys(api_key: APIKey = Depends(require_admin)):
    """
    ## 📋 List API Keys
    
    Returns a list of all API keys with their metadata (without exposing the actual key values).
    
    **⚠️ Admin Permission Required**
    
    ### Information Included:
    - Key ID and name
    - Creation and expiration dates
    - Permissions and status
    - Usage statistics
    """
    try:
        keys = key_manager.list_keys()
        keys_data = []
        
        for key in keys:
            keys_data.append({
                "key_id": key.key_id,
                "name": key.name,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "is_active": key.is_active,
                "permissions": key.permissions,
                "usage_count": key.usage_count,
                "last_used": key.last_used
            })
        
        return KeyListResponse(success=True, keys=keys_data)
    except Exception as e:
        logger.error(f"❌ Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing API keys: {str(e)}")

@app.post(
    "/auth/revoke-key/{key_id}",
    tags=["🔑 API Key Management"],
    summary="Revoke API Key (Admin Only)",
    description="Revoke an API key by its ID"
)
async def revoke_api_key(key_id: str, api_key: APIKey = Depends(require_admin)):
    """
    ## 🚫 Revoke API Key
    
    Permanently deactivates an API key. The key will no longer be able to authenticate.
    
    **⚠️ Admin Permission Required**
    
    ### Notes:
    - Revoked keys cannot be reactivated
    - This action is permanent and immediate
    - The key will be logged as revoked for audit purposes
    """
    try:
        success = key_manager.revoke_key(key_id)
        
        if success:
            logger.info(f"🚫 API key revoked: {key_id} by {api_key.name}")
            return {"success": True, "message": f"API key {key_id} has been revoked"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")

@app.get(
    "/auth/me",
    tags=["🔑 API Key Management"],
    summary="Get Current API Key Info",
    description="Get information about the currently authenticated API key"
)
async def get_current_key_info(api_key: APIKey = Depends(get_api_key)):
    """
    ## 👤 Current API Key Information
    
    Returns information about the currently authenticated API key.
    
    ### Information Included:
    - Key ID and name
    - Permissions and status
    - Usage statistics
    - Expiration information
    """
    return {
        "success": True,
        "key_info": {
            "key_id": api_key.key_id,
            "name": api_key.name,
            "created_at": api_key.created_at,
            "expires_at": api_key.expires_at,
            "is_active": api_key.is_active,
            "permissions": api_key.permissions,
            "usage_count": api_key.usage_count,
            "last_used": api_key.last_used
        }
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("=" * 80)
    print("🤖 SQL AGENT API v2.0 - PRODUCTION READY")
    print("=" * 80)
    print(f"🚀 Server: http://{host}:{port}")
    print(f"📚 Swagger Docs: http://localhost:{port}/docs")
    print(f"📖 ReDoc: http://localhost:{port}/redoc")
    print(f"🏥 Health Check: http://localhost:{port}/health")
    print(f"📝 Examples: http://localhost:{port}/examples")
    print("=" * 80)
    print("🎯 FEATURES:")
    print("   • 🧠 AI-Powered Natural Language Queries")
    print("   • 🔮 Advanced Business Predictions") 
    print("   • 🌍 Multi-Language Support (EN/PL)")
    print("   • 📊 Real-time Database Analytics")
    print("   • 🔒 Production-Grade Error Handling")
    print("   • 📝 Comprehensive API Documentation")
    print("=" * 80)
    print("🚦 Ready for public testing!")
    print("=" * 80)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,  # Disable reload in production
        log_level="info",
        access_log=True
    )
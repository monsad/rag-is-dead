# SQL Agent API 🤖

A FastAPI-powered REST API that provides AI-driven database querying capabilities with predictive analytics. This API wraps a LangChain SQL agent that can understand natural language queries and convert them to SQL, with built-in sales prediction functionality.

## Features ✨

- 🗣️ **Natural Language Queries**: Ask questions in plain English (or Polish)
- 🔮 **Predictive Analytics**: Built-in sales forecasting capabilities  
- 🌐 **RESTful API**: Easy integration with any application
- 📊 **Database Schema Discovery**: Automatic table and column detection
- 🚀 **FastAPI**: High-performance async API with automatic documentation
- 🔒 **Error Handling**: Robust error handling and validation

## Quick Start 🚀

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key

### 2. Installation

```bash
# Clone or download the project
cd sqlagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DB_HOST=your_postgres_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Start the API

```bash
# Start the development server
python api.py

# Or using uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints 📡

### Health Check
```http
GET /health
```
Check if the API and database connection are working.

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "message": "API is running and database is connected"
}
```

### Process Query
```http
POST /query
```
Process a natural language database query.

**Request Body:**
```json
{
  "query": "How many suppliers do we have?",
  "language": "en"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on the database query, you have 3 supplier teams in the accounts_supplierteam table.",
  "query": "How many suppliers do we have?",
  "error": null
}
```

### Generate Predictions
```http
POST /predict
```
Generate sales predictions or forecasts.

**Request Body:**
```json
{
  "query": "Predict sales for next 3 months",
  "language": "en"
}
```

### Get Database Schema
```http
GET /schema
```
Retrieve basic database schema information.

### Get Example Queries
```http
GET /examples
```
Get example queries that can be used with the API.

## Usage Examples 💡

### Python Client Example

```python
import requests

# API base URL
api_url = "http://localhost:8000"

# Health check
response = requests.get(f"{api_url}/health")
print(response.json())

# Query the database
query_data = {
    "query": "Show me all customers from California",
    "language": "en"
}
response = requests.post(f"{api_url}/query", json=query_data)
result = response.json()

if result["success"]:
    print("Query Result:", result["response"])
else:
    print("Error:", result["error"])
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const apiUrl = 'http://localhost:8000';

async function queryDatabase(query) {
    try {
        const response = await axios.post(`${apiUrl}/query`, {
            query: query,
            language: 'en'
        });
        
        if (response.data.success) {
            console.log('Query Result:', response.data.response);
        } else {
            console.log('Error:', response.data.error);
        }
    } catch (error) {
        console.error('Request failed:', error.message);
    }
}

// Example usage
queryDatabase("How many active contracts do we have?");
```

### cURL Examples

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Database query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the latest 5 transactions", "language": "en"}'

# Sales prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"query": "Forecast sales for next quarter", "language": "en"}'
```

## Supported Query Types 🎯

### SQL Queries
- **Data Retrieval**: "Show me all customers", "List active contracts"
- **Aggregations**: "How many suppliers do we have?", "Total revenue this year"
- **Filtering**: "Customers from Texas", "Contracts expiring this month"
- **Joins**: "Products with their supplier information"

### Prediction Queries
- **Sales Forecasting**: "Predict sales for next 3 months"
- **Revenue Projections**: "Forecast revenue trends"
- **Trend Analysis**: "Sales projection for Q2"

### Multi-language Support
- **English**: "How many customers do we have?"
- **Polish**: "Ile mamy klientów?", "Przewiduj sprzedaż na następny miesiąc"

## Error Handling 🛡️

The API provides comprehensive error handling:

```json
{
  "success": false,
  "response": "",
  "query": "invalid query",
  "error": "Failed to process query: Database connection failed"
}
```

Common error scenarios:
- Invalid database connection
- Malformed queries
- Missing environment variables
- OpenAI API failures

## Development 🔧

### Running Tests

```bash
# Test the API client example
python api_client_example.py
```

### API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Project Structure

```
sqlagent/
├── agent.py              # Core SQL agent logic
├── api.py                # FastAPI application
├── api_client_example.py # Example client usage
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── README.md            # This documentation
└── venv/                # Virtual environment
```

## Deployment 🚀

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Security**: 
   - Use environment variables for secrets
   - Configure CORS appropriately
   - Add authentication if needed

2. **Performance**:
   - Use production ASGI server (e.g., gunicorn + uvicorn)
   - Implement connection pooling
   - Add caching for frequent queries

3. **Monitoring**:
   - Add logging
   - Implement health checks
   - Monitor database connections

## Troubleshooting 🔍

### Common Issues

1. **Database Connection Failed**
   - Check your `.env` file configuration
   - Verify database is running and accessible
   - Test connection manually

2. **OpenAI API Errors**
   - Verify your OpenAI API key
   - Check API usage limits
   - Ensure you have access to the required models

3. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Activate virtual environment: `source venv/bin/activate`

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is licensed under the MIT License.

## Support 💬

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Create an issue in the repository

---

**Happy Querying! 🎉**
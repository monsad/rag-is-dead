#!/usr/bin/env python3
"""
Example client for SQL Agent API
Demonstrates how to interact with the FastAPI endpoints
"""

import requests
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"

def make_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[Any, Any]:
    """Make a request to the API and handle errors"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            response = requests.get(url)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making request to {url}: {e}")
        return {"error": str(e)}

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing health check...")
    result = make_request("/health")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Database Connected: {result.get('database_connected', False)}")
    print(f"Message: {result.get('message', 'No message')}")
    print()

def test_query(query: str):
    """Test a database query"""
    print(f"📊 Testing query: '{query}'")
    data = {"query": query, "language": "en"}
    result = make_request("/query", "POST", data)
    
    if result.get("success"):
        print("✅ Query successful!")
        print(f"Response: {result.get('response', 'No response')}")
    else:
        print("❌ Query failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()

def test_prediction(query: str):
    """Test a prediction query"""
    print(f"🔮 Testing prediction: '{query}'")
    data = {"query": query, "language": "en"}
    result = make_request("/predict", "POST", data)
    
    if result.get("success"):
        print("✅ Prediction successful!")
        print(f"Response: {result.get('response', 'No response')}")
    else:
        print("❌ Prediction failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()

def get_examples():
    """Get example queries from the API"""
    print("📝 Getting example queries...")
    result = make_request("/examples")
    
    if "sql_queries" in result:
        print("SQL Query Examples:")
        for i, query in enumerate(result["sql_queries"][:3], 1):
            print(f"  {i}. {query}")
        print()
        
        print("Prediction Query Examples:")
        for i, query in enumerate(result["prediction_queries"][:2], 1):
            print(f"  {i}. {query}")
        print()
    else:
        print("❌ Could not retrieve examples")

def get_schema_info():
    """Get database schema information"""
    print("🗄️  Getting database schema info...")
    result = make_request("/schema")
    
    if result.get("success"):
        print("✅ Schema info retrieved!")
        schema_info = result.get("schema_info", "No schema info available")
        # Truncate long responses
        if len(schema_info) > 500:
            schema_info = schema_info[:500] + "..."
        print(f"Schema: {schema_info}")
    else:
        print("❌ Could not retrieve schema info")
    print()

def main():
    """Run example API calls"""
    print("🚀 SQL Agent API Client Example")
    print("=" * 50)
    
    # Test health check
    test_health_check()
    
    # Get examples
    get_examples()
    
    # Test some basic queries
    test_query("How many supplier teams do we have?")
    test_query("Show me information about accounts table")
    
    # Test prediction
    test_prediction("sales forecast for next quarter")
    
    # Get schema info
    get_schema_info()
    
    print("✅ API testing completed!")

if __name__ == "__main__":
    main()
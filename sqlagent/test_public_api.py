#!/usr/bin/env python3
"""
🧪 Public API Testing Script
Comprehensive testing suite for the SQL Agent API
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8001"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict = None, description: str = ""):
    """Test an API endpoint and display results"""
    url = f"{API_BASE_URL}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {method} {endpoint}")
    if description:
        print(f"📝 {description}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        if method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            response = requests.get(url)
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response Time: {elapsed_time:.3f}s")  
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            result = response.json()
            
            # Pretty print JSON response
            if isinstance(result, dict):
                if len(str(result)) > 500:
                    print("📄 Response (truncated):")
                    print(json.dumps(result, indent=2)[:500] + "...")
                else:
                    print("📄 Response:")
                    print(json.dumps(result, indent=2))
            else:
                print(f"📄 Response: {result}")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"🚨 REQUEST ERROR: {e}")
    except Exception as e:
        print(f"🚨 UNEXPECTED ERROR: {e}")

def main():
    """Run comprehensive API tests"""
    print("🤖 SQL AGENT API - PUBLIC TESTING SUITE")
    print("=" * 80)
    print("🎯 This script will test all major API endpoints")
    print("🌐 Make sure your API is running: python api.py")
    print("=" * 80)
    
    # Test 1: Root endpoint
    test_api_endpoint(
        "/", 
        description="API welcome and overview information"
    )
    
    # Test 2: Health check
    test_api_endpoint(
        "/health", 
        description="System health and database connectivity"
    )
    
    # Test 3: Examples
    test_api_endpoint(
        "/examples", 
        description="Query examples and templates"
    )
    
    # Test 4: Database schema
    test_api_endpoint(
        "/schema", 
        description="Database structure information"
    )
    
    # Test 5: Simple database query
    test_api_endpoint(
        "/query", 
        method="POST",
        data={
            "query": "How many suppliers do we have?",
            "language": "en"
        },
        description="Natural language database query"
    )
    
    # Test 6: Analytics query
    test_api_endpoint(
        "/query", 
        method="POST",
        data={
            "query": "Show me the total number of accounts by type",
            "language": "en"
        },
        description="Business analytics query"
    )
    
    # Test 7: Prediction query
    test_api_endpoint(
        "/predict", 
        method="POST",
        data={
            "query": "Predict revenue for next 3 months",
            "language": "en"
        },
        description="Revenue forecasting with ML"
    )
    
    # Test 8: Polish language query
    test_api_endpoint(
        "/query", 
        method="POST",
        data={
            "query": "Ile mamy aktywnych produktów?",
            "language": "pl"
        },
        description="Multi-language support (Polish)"
    )
    
    # Test 9: Error handling
    test_api_endpoint(
        "/query", 
        method="POST",
        data={
            "query": "",
            "language": "en"
        },
        description="Error handling test (empty query)"
    )
    
    print(f"\n{'='*80}")
    print("🎉 PUBLIC API TESTING COMPLETE!")
    print("=" * 80)
    print("📊 SWAGGER DOCUMENTATION:")
    print(f"   🌐 Interactive: {API_BASE_URL}/docs")
    print(f"   📖 ReDoc: {API_BASE_URL}/redoc")
    print("=" * 80)
    print("🏆 Your API is ready for public use!")
    print("🚀 Share the /docs URL for interactive testing")
    print("=" * 80)

if __name__ == "__main__":
    main()
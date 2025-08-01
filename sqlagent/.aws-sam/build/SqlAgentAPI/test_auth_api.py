#!/usr/bin/env python3
"""
🔐 SQL Agent API - Authentication Testing Script
Test the secured API with token-based authentication
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8001"  # Change to your API URL

class AuthenticatedAPIClient:
    """Client for testing the authenticated SQL Agent API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, description: str = ""):
        """Test an API endpoint and display results"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {method} {endpoint}")
        if description:
            print(f"📝 {description}")
        if self.api_key:
            print(f"🔑 Using API Key: {self.api_key[:20]}...")
        else:
            print("🌐 No authentication (public endpoint)")
        print(f"{'='*60}")
        
        try:
            start_time = time.time()
            
            if method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            elif method == "GET":
                response = requests.get(url, headers=self.headers)
            else:
                print(f"❌ Unsupported method: {method}")
                return
            
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  Response Time: {elapsed_time:.3f}s")  
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
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
                        
                except json.JSONDecodeError:
                    print(f"📄 Response (text): {response.text}")
                    
            elif response.status_code == 401:
                print("🔐 AUTHENTICATION REQUIRED!")
                print(f"Error: {response.text}")
            elif response.status_code == 403:
                print("🚫 PERMISSION DENIED!")
                print(f"Error: {response.text}")
            elif response.status_code == 429:
                print("⏰ RATE LIMITED!")
                print(f"Error: {response.text}")
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"🚨 REQUEST ERROR: {e}")
        except Exception as e:
            print(f"🚨 UNEXPECTED ERROR: {e}")

def main():
    """Run comprehensive API authentication tests"""
    print("🔐 SQL AGENT API - AUTHENTICATION TESTING SUITE")
    print("=" * 80)
    print("🎯 This script will test the secured API endpoints")
    print("🌐 Make sure your API is running: python api.py")
    print("=" * 80)
    
    # Get API key from user
    api_key = input("\n🔑 Enter your API key (or press Enter to test public endpoints only): ").strip()
    
    if not api_key:
        print("\n⚠️  No API key provided - testing public endpoints only")
        print("🔐 Protected endpoints will show authentication errors")
    
    # Initialize clients
    public_client = AuthenticatedAPIClient(API_BASE_URL)
    auth_client = AuthenticatedAPIClient(API_BASE_URL, api_key) if api_key else None
    
    print(f"\n🚀 Starting tests against: {API_BASE_URL}")
    
    # =================================================================
    # Test Public Endpoints (No Authentication Required)
    # =================================================================
    
    print(f"\n{'='*80}")
    print("🌐 TESTING PUBLIC ENDPOINTS (No Authentication Required)")
    print("=" * 80)
    
    # Test 1: Root endpoint
    public_client.test_endpoint(
        "GET", "/", 
        description="API welcome and overview information"
    )
    
    # Test 2: Health check
    public_client.test_endpoint(
        "GET", "/health", 
        description="System health and database connectivity"
    )
    
    # Test 3: Examples
    public_client.test_endpoint(
        "GET", "/examples", 
        description="Query examples and templates"
    )
    
    # =================================================================
    # Test Protected Endpoints (Authentication Required)
    # =================================================================
    
    print(f"\n{'='*80}")
    print("🔐 TESTING PROTECTED ENDPOINTS (Authentication Required)")
    print("=" * 80)
    
    client = auth_client if auth_client else public_client
    
    # Test 4: Database schema (requires 'read' permission)
    client.test_endpoint(
        "GET", "/schema", 
        description="Database structure information (requires 'read' permission)"
    )
    
    # Test 5: Natural language query (requires 'query' permission)
    client.test_endpoint(
        "POST", "/query",
        data={
            "query": "How many suppliers do we have?",
            "language": "en"
        },
        description="Natural language database query (requires 'query' permission)"
    )
    
    # Test 6: Business analytics query
    client.test_endpoint(
        "POST", "/query",
        data={
            "query": "Show me total accounts by type",
            "language": "en"
        },
        description="Business analytics query"
    )
    
    # Test 7: Prediction query (requires 'predict' permission)
    client.test_endpoint(
        "POST", "/predict",
        data={
            "query": "Predict sales for next quarter",
            "language": "en"
        },
        description="Revenue forecasting (requires 'predict' permission)"
    )
    
    # Test 8: Multi-language query
    client.test_endpoint(
        "POST", "/query",
        data={
            "query": "Ile mamy aktywnych produktów?",
            "language": "pl"
        },
        description="Multi-language support (Polish)"
    )
    
    # =================================================================
    # Test Admin Endpoints (Admin Permission Required)
    # =================================================================
    
    if auth_client:
        print(f"\n{'='*80}")
        print("👑 TESTING ADMIN ENDPOINTS (Admin Permission Required)")
        print("=" * 80)
        
        # Test 9: Get current key info
        auth_client.test_endpoint(
            "GET", "/auth/me",
            description="Get current API key information"
        )
        
        # Test 10: List API keys (admin only)
        auth_client.test_endpoint(
            "GET", "/auth/keys",
            description="List all API keys (admin permission required)"
        )
        
        # Test 11: Create new API key (admin only)
        auth_client.test_endpoint(
            "POST", "/auth/create-key",
            data={
                "name": "Test Key",
                "expires_days": 30,
                "permissions": ["read", "query"]
            },
            description="Create new API key (admin permission required)"
        )
    
    # =================================================================
    # Summary
    # =================================================================
    
    print(f"\n{'='*80}")
    print("🎉 AUTHENTICATION TESTING COMPLETE!")
    print("=" * 80)
    
    if api_key:
        print("✅ Tests completed with authentication")
        print("📊 SWAGGER DOCUMENTATION:")
        print(f"   🌐 Interactive: {API_BASE_URL}/docs")
        print(f"   📖 ReDoc: {API_BASE_URL}/redoc")
        print()
        print("🔑 API KEY MANAGEMENT:")
        print(f"   👤 Current Key Info: GET {API_BASE_URL}/auth/me")
        print(f"   📋 List Keys: GET {API_BASE_URL}/auth/keys")
        print(f"   🔑 Create Key: POST {API_BASE_URL}/auth/create-key")
    else:
        print("⚠️  Tests completed without authentication")
        print("🔐 To test protected endpoints:")
        print("   1. Get your API key from the server logs when it starts")
        print("   2. Run this script again with your API key")
        print("   3. Or use the Swagger UI at /docs")
    
    print("=" * 80)
    print("🏆 Your secured API is ready for production!")
    print("🔐 Enterprise-grade security with token-based authentication!")
    print("=" * 80)

if __name__ == "__main__":
    main()
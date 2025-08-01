"""
🔐 SQL Agent API - Authentication System
Secure API key-based authentication
"""

import os
import hashlib
import secrets
import time
from typing import Optional, Dict, List
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
from datetime import datetime, timedelta

# Security scheme
security = HTTPBearer()

class APIKey(BaseModel):
    """API Key model"""
    key_id: str
    name: str
    key_hash: str
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True
    permissions: List[str] = ["read", "query", "predict"]
    usage_count: int = 0
    last_used: Optional[str] = None

class APIKeyManager:
    """Manages API keys for the application"""
    
    def __init__(self, keys_file: str = "api_keys.json"):
        self.keys_file = keys_file
        self.keys: Dict[str, APIKey] = {}
        self.load_keys()
        
        # Create master key if none exist
        if not self.keys:
            self.create_master_key()
    
    def load_keys(self):
        """Load API keys from file"""
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                    self.keys = {k: APIKey(**v) for k, v in data.items()}
        except Exception as e:
            print(f"⚠️ Error loading API keys: {e}")
            self.keys = {}
    
    def save_keys(self):
        """Save API keys to file"""
        try:
            data = {k: v.dict() for k, v in self.keys.items()}
            with open(self.keys_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving API keys: {e}")
    
    def hash_key(self, key: str) -> str:
        """Hash an API key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_key(self) -> str:
        """Generate a new API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def create_key(self, name: str, expires_days: Optional[int] = None, permissions: List[str] = None) -> tuple[str, APIKey]:
        """Create a new API key"""
        key = self.generate_key()
        key_id = secrets.token_hex(8)
        
        if permissions is None:
            permissions = ["read", "query", "predict"]
        
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        api_key = APIKey(
            key_id=key_id,
            name=name,
            key_hash=self.hash_key(key),
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            permissions=permissions
        )
        
        self.keys[key_id] = api_key
        self.save_keys()
        
        return key, api_key
    
    def create_master_key(self) -> tuple[str, APIKey]:
        """Create the master API key"""
        key, api_key = self.create_key(
            name="Master Key", 
            permissions=["read", "query", "predict", "admin"]
        )
        
        print("🔑 MASTER API KEY CREATED!")
        print("=" * 50)
        print(f"API Key: {key}")
        print(f"Key ID: {api_key.key_id}")
        print("=" * 50)
        print("⚠️  SAVE THIS KEY - IT WON'T BE SHOWN AGAIN!")
        print("💡 Use this key in Authorization header: Bearer {key}")
        print("=" * 50)
        
        return key, api_key
    
    def validate_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key"""
        key_hash = self.hash_key(key)
        
        for api_key in self.keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if api_key.expires_at:
                    expires = datetime.fromisoformat(api_key.expires_at)
                    if datetime.now() > expires:
                        continue
                
                # Update usage
                api_key.usage_count += 1
                api_key.last_used = datetime.now().isoformat()
                self.save_keys()
                
                return api_key
        
        return None
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            self.save_keys()
            return True
        return False
    
    def list_keys(self) -> List[APIKey]:
        """List all API keys (without sensitive data)"""
        return list(self.keys.values())

# Global key manager
key_manager = APIKeyManager()

def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> APIKey:
    """FastAPI dependency to validate API key"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = key_manager.validate_key(credentials.credentials)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(api_key: APIKey = Depends(get_api_key)) -> APIKey:
        if permission not in api_key.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return api_key
    return permission_checker

# Common permission dependencies
require_read = require_permission("read")
require_query = require_permission("query") 
require_predict = require_permission("predict")
require_admin = require_permission("admin")

def get_optional_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)) -> Optional[APIKey]:
    """Optional API key for public endpoints with rate limiting"""
    if not credentials:
        return None
    
    try:
        return key_manager.validate_key(credentials.credentials)
    except:
        return None

# Rate limiting for public endpoints
class RateLimiter:
    """Simple rate limiter for public endpoints"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str, max_requests: int = 10, window_minutes: int = 1) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > window_start
        ]
        
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter()

def check_rate_limit(request):
    """Check rate limit for requests"""
    # Use API key if available, otherwise use IP
    credentials = None
    try:
        if hasattr(request, 'headers') and 'authorization' in request.headers:
            api_key_obj = get_optional_api_key()
            if api_key_obj:
                return  # Authenticated users bypass rate limiting
    except:
        pass
    
    # Rate limit by IP for unauthenticated requests
    client_ip = getattr(request.client, 'host', 'unknown')
    if not rate_limiter.is_allowed(client_ip, max_requests=20, window_minutes=1):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please authenticate with an API key for higher limits."
        )
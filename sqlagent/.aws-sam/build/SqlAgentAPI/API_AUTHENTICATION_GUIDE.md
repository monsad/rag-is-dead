# 🔐 **SQL Agent API - Authentication Guide**

## 🎉 **Your API is Now Secured with Token-Based Authentication!**

Your SQL Agent API now includes robust token-based security to protect your valuable database and AI resources.

---

## 🔑 **Getting Your API Key**

### **🎬 First Time Setup:**

When you start your secured API for the first time, it will automatically create a **Master API Key**:

```bash
# Start your API server
python api.py

# You'll see output like this:
🔑 MASTER API KEY CREATED!
==================================================
API Key: sk-abc123def456...your-key-here
Key ID: a1b2c3d4
==================================================
⚠️  SAVE THIS KEY - IT WON'T BE SHOWN AGAIN!
💡 Use this key in Authorization header: Bearer sk-abc123...
==================================================
```

**⚠️ IMPORTANT**: Save this master key immediately! It won't be shown again.

---

## 🚀 **How to Use Your API Key**

### **📋 Option 1: Using Swagger UI (Easiest)**

1. **Go to your API docs**: `https://your-api-url/docs`
2. **Click the 🔒 "Authorize" button** (top right)
3. **Enter your API key**: `sk-your-api-key-here`
4. **Click "Authorize"**
5. **Try any endpoint** - authentication is automatic!

### **📋 Option 2: Using curl**

```bash
# Add Authorization header to all requests
curl -X POST "https://your-api-url/query" \
  -H "Authorization: Bearer sk-your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many customers do we have?"}'
```

### **📋 Option 3: Using Python requests**

```python
import requests

headers = {
    "Authorization": "Bearer sk-your-api-key-here",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://your-api-url/query",
    headers=headers,
    json={"query": "How many suppliers do we have?"}
)

print(response.json())
```

### **📋 Option 4: Using JavaScript/Fetch**

```javascript
const response = await fetch('https://your-api-url/query', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-your-api-key-here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'How many active products do we have?'
  })
});

const data = await response.json();
console.log(data);
```

---

## 🔐 **API Endpoints Security**

### **🌐 Public Endpoints (No Authentication Required)**
- `GET /` - API overview and welcome
- `GET /health` - System health check  
- `GET /examples` - Query examples and templates

*Note: Public endpoints have rate limiting (20 requests/minute per IP)*

### **🔒 Protected Endpoints (Authentication Required)**
- `POST /query` - Natural language database queries
- `POST /predict` - Revenue forecasting and predictions
- `GET /schema` - Database schema information

### **👑 Admin Endpoints (Admin Permission Required)**
- `POST /auth/create-key` - Create new API keys
- `GET /auth/keys` - List all API keys
- `POST /auth/revoke-key/{key_id}` - Revoke API keys
- `GET /auth/me` - Get current key information

---

## 🔑 **API Key Management**

### **🎯 Creating Additional API Keys**

Use your master key to create additional keys:

```bash
curl -X POST "https://your-api-url/auth/create-key" \
  -H "Authorization: Bearer sk-your-master-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App Key",
    "expires_days": 90,
    "permissions": ["read", "query"]
  }'
```

### **📋 Listing Your API Keys**

```bash
curl -X GET "https://your-api-url/auth/keys" \
  -H "Authorization: Bearer sk-your-master-key"
```

### **🚫 Revoking API Keys**

```bash
curl -X POST "https://your-api-url/auth/revoke-key/key_id_here" \
  -H "Authorization: Bearer sk-your-master-key"
```

---

## 🎭 **Permission System**

### **📊 Available Permissions:**

| Permission | Description | Endpoints |
|------------|-------------|-----------|
| `read` | Database schema access | `/schema` |
| `query` | Natural language queries | `/query` |
| `predict` | Revenue forecasting | `/predict` |
| `admin` | Key management | `/auth/*` |

### **👥 Common Permission Combinations:**

```json
// Read-only access
["read"]

// Standard user
["read", "query"]

// Business analyst  
["read", "query", "predict"]

// Administrator
["read", "query", "predict", "admin"]
```

---

## 🛡️ **Security Features**

### **✅ What's Protected:**
- ✅ **Token-based authentication** - Industry standard security
- ✅ **Permission-based access** - Fine-grained control
- ✅ **Key expiration** - Automatic expiry dates
- ✅ **Usage tracking** - Monitor API key usage
- ✅ **Rate limiting** - Prevent abuse on public endpoints
- ✅ **Request logging** - Full audit trail
- ✅ **Key revocation** - Instant deactivation

### **🔐 Security Best Practices:**

1. **🔑 Keep Keys Secret**: Never commit API keys to code repositories
2. **⏰ Use Expiration**: Set expiration dates for temporary access
3. **🎯 Least Privilege**: Only grant necessary permissions
4. **📝 Monitor Usage**: Regular check key usage and revoke unused keys
5. **🚫 Revoke Compromised Keys**: Immediately revoke any compromised keys

---

## 🚨 **Troubleshooting**

### **❌ "API key required" Error**
```json
{
  "detail": "API key required"
}
```
**Solution**: Add `Authorization: Bearer your-key` header to your request.

### **❌ "Invalid or expired API key" Error**
```json
{
  "detail": "Invalid or expired API key"
}
```
**Solutions**:
- Check your API key is correct
- Verify the key hasn't expired
- Ensure the key hasn't been revoked

### **❌ "Permission required" Error**
```json
{
  "detail": "Permission 'predict' required"
}
```
**Solution**: Your API key doesn't have the required permission. Create a new key with the needed permissions.

### **❌ "Rate limit exceeded" Error**
```json
{
  "detail": "Rate limit exceeded. Please authenticate with an API key for higher limits."
}
```
**Solution**: You're hitting the rate limit on public endpoints. Use an API key for unlimited access.

---

## 📱 **Integration Examples**

### **🐍 Python Client Class**

```python
import requests
from typing import Optional, Dict, Any

class SQLAgentClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def query(self, question: str, language: str = "en") -> Dict[str, Any]:
        """Ask a natural language question"""
        response = requests.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json={"query": question, "language": language}
        )
        return response.json()
    
    def predict(self, question: str, language: str = "en") -> Dict[str, Any]:
        """Get revenue predictions"""
        response = requests.post(
            f"{self.base_url}/predict", 
            headers=self.headers,
            json={"query": question, "language": language}
        )
        return response.json()
    
    def health(self) -> Dict[str, Any]:
        """Check API health (no auth required)"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = SQLAgentClient("https://your-api-url", "sk-your-key")
result = client.query("How many suppliers do we have?")
print(result["response"])
```

### **🌐 JavaScript/Node.js Client**

```javascript
class SQLAgentClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async query(question, language = 'en') {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ query: question, language })
        });
        return await response.json();
    }

    async predict(question, language = 'en') {
        const response = await fetch(`${this.baseUrl}/predict`, {
            method: 'POST', 
            headers: this.headers,
            body: JSON.stringify({ query: question, language })
        });
        return await response.json();
    }
}

// Usage
const client = new SQLAgentClient('https://your-api-url', 'sk-your-key');
const result = await client.query('How many customers do we have?');
console.log(result.response);
```

---

## 🎉 **Ready to Use!**

Your API is now **production-ready** with enterprise-grade security:

✅ **Secure Authentication** - Token-based security  
✅ **Permission Control** - Fine-grained access management  
✅ **Rate Limiting** - Abuse prevention  
✅ **Usage Monitoring** - Complete audit trail  
✅ **Easy Integration** - Works with any HTTP client  
✅ **Swagger Documentation** - Interactive testing with auth  

**🚀 Your AI-powered SQL Agent is now ready for secure public deployment!**

---

## 📞 **Need Help?**

- **📚 API Documentation**: Visit `/docs` on your API URL
- **🔍 Test Endpoints**: Use the interactive Swagger UI
- **📊 Monitor Usage**: Check `/auth/keys` for usage statistics
- **🚨 Security Issues**: Revoke compromised keys immediately

**Your secure, AI-powered database API is ready for the world!** 🌟
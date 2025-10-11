# War Prediction Agent 🌍⚔️

AI system for predicting war outbreak risk based on multi-source intelligence analysis using LangGraph, FastAPI and **OpenSearch**.

## 🎯 Features

- **Multi-source Intelligence**: Collecting data from news services, military sources, and social media
- **AI-Powered Analysis**: Utilizing LLM (GPT-4) for analysis and prediction
- **Real-time Risk Assessment**: Real-time risk assessment for different regions
- **OpenSearch Analytics**: Full-text search, aggregations and data analysis
- **RESTful API**: Easy integration with other systems
- **Caching**: Redis for performance optimization
- **Alerting System**: Automatic alert creation for high risk situations
- **Sentiment Analysis**: Sentiment analysis of information sources
- **OpenSearch Dashboards**: Real-time data visualization
- **Mesh Agent Architecture**: Using LangGraph to build mesh agent

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI       │
│   (REST API)    │
└────────┬────────┘
         │
┌────────▼────────┐
│  LangGraph      │
│  Mesh Agent     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐  ┌──────┐
│ News │  │ Mil  │  │Social│
│Source│  │Intel │  │Media │
└───┬──┘  └──┬───┘  └───┬──┘
    │        │          │
    └────────┼──────────┘
             │
      ┌──────▼──────┐
      │  OpenSearch │
      │   + Redis   │
      └─────────────┘
```

## 📦 Tech Stack

- **LangGraph**: AI agent orchestration
- **FastAPI**: API Framework
- **OpenSearch**: Search engine and analytics
- **Redis**: Cache and message broker
- **OpenAI GPT-4**: Language model
- **Python 3.11+**: Programming language
- **Docker**: Containerization

## 🚀 Installation

### 1. Clone repository

```bash
git clone <repo-url>
cd war-prediction-agent
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY` - required
- `NEWS_API_KEY` - optional (not currently used)
- `TWITTER_BEARER_TOKEN` - optional (for social media monitoring)

### 3. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

Services:
- **API**: http://localhost:8000
- **OpenSearch**: https://localhost:9200 (admin/Admin123!)
- **OpenSearch Dashboards**: http://localhost:5601
- **Redis**: localhost:6379

### 4. Local deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run OpenSearch
docker run -d -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Admin123!" \
  opensearchproject/opensearch:2.11.0

# Run Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run API
uvicorn main:app --reload
```

## 📡 API Endpoints

### Core Endpoints

#### `POST /predict`
Main endpoint for war risk prediction.

**Request:**
```json
{
  "regions": ["Europe", "Middle East"],
  "include_social_media": true,
  "lookback_hours": 24
}
```

**Response:**
```json
{
  "timestamp": "2025-10-11T10:30:00",
  "global_risk_score": 0.45,
  "global_risk_level": "medium",
  "regional_analyses": [...],
  "key_events": [...],
  "confidence": 0.78,
  "reasoning": "Based on analysis...",
  "sources_analyzed": 250
}
```

#### `GET /health`
System health check (Redis + OpenSearch).

#### `GET /stats`
System statistics with information about OpenSearch indices.

### OpenSearch Analytics Endpoints

#### `GET /opensearch/search/data-points`
Full-text search of data points.

**Parameters:**
- `query`: Query string (e.g. "military mobilization")
- `source_type`: Source type filter (news/military/social_media)
- `hours_back`: How many hours back
- `min_relevance`: Minimum relevance score
- `size`: Number of results

**Example:**
```bash
curl "http://localhost:8000/opensearch/search/data-points?query=war&hours_back=48&min_relevance=0.5"
```

#### `GET /opensearch/search/keywords`
Search by specific keywords.

**Example:**
```bash
curl "http://localhost:8000/opensearch/search/keywords?keywords=war&keywords=invasion"
```

#### `GET /opensearch/predictions/history`
Prediction history with filters.

**Parameters:**
- `days_back`: Days back
- `min_risk_score`: Minimum risk score
- `size`: Number of results

#### `GET /opensearch/analytics/risk-by-region`
Risk aggregation by regions.

**Example:**
```bash
curl "http://localhost:8000/opensearch/analytics/risk-by-region?days=7"
```

**Response:**
```json
{
  "period_days": 7,
  "regions": {
    "Europe": {
      "avg_risk": 0.35,
      "max_risk": 0.62,
      "count": 42
    },
    "Middle East": {
      "avg_risk": 0.58,
      "max_risk": 0.85,
      "count": 38
    }
  }
}
```

#### `GET /opensearch/analytics/trending-keywords`
Trending conflict keywords.

#### `GET /opensearch/analytics/sentiment`
Sentiment analysis of collected data.

**Response:**
```json
{
  "period_hours": 24,
  "sentiment_distribution": {
    "very_negative": 45,
    "negative": 120,
    "neutral": 80,
    "positive": 30,
    "very_positive": 5
  },
  "average_sentiment": -0.23
}
```

#### `GET /opensearch/alerts`
Get system alerts.

#### `POST /opensearch/alerts/create`
Create manual alert.

**Request:**
```json
{
  "alert_type": "high_risk",
  "severity": "critical",
  "region": "Middle East",
  "message": "Escalating tensions detected",
  "risk_score": 0.85,
  "triggered_by": "analyst"
}
```

#### `GET /opensearch/analytics/dashboard`
Comprehensive dashboard data (combines all analytics).

## 🔧 Configuration

Key settings in `config.py`:

```python
# OpenSearch
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASSWORD = "Admin123!"

# Risk thresholds
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.6
HIGH_RISK_THRESHOLD = 0.8

# Data sources
NEWS_SOURCES = [...]
CONFLICT_KEYWORDS = [...]
```

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Test OpenSearch examples
python opensearch_examples.py
```

## 📊 LangGraph Workflow

The agent uses the following workflow:

1. **collect_data**: Collect data from all sources
2. **analyze_relevance**: Analyze relevance and sentiment of data
3. **extract_indicators**: Extract conflict indicators
4. **calculate_risk**: Calculate risk scores
5. **generate_prediction**: Generate final prediction with reasoning

After each prediction:
- Data is indexed in OpenSearch
- Cache is created in Redis
- Alerts are automatically generated for high risk

## 🔍 OpenSearch Features

### Indices

The system creates three main indices:

1. **war-prediction-data-points**: Raw data from all sources
2. **war-prediction-predictions**: Prediction history
3. **war-prediction-alerts**: Alert system

### Search capabilities

- **Full-text search**: Search in titles and contents
- **Keyword filtering**: Filter by keywords
- **Time-range queries**: Queries within time ranges
- **Aggregations**: Aggregations by regions, sentiment, etc.
- **Relevance scoring**: Result relevance scoring

### Analytics

- **Risk trends**: Risk trends over time
- **Regional analysis**: Analysis by regions
- **Sentiment tracking**: Sentiment tracking
- **Keyword trending**: Trending topics
- **Alert management**: Alert management

## 📈 OpenSearch Dashboards

Access: http://localhost:5601

Default login:
- Username: `admin`
- Password: `Admin123!`

### Suggested visualizations:

1. **Risk Timeline**: Line chart of global risk over time
2. **Regional Heatmap**: Heat map of risk by regions
3. **Sentiment Gauge**: Current sentiment indicator
4. **Keyword Cloud**: Keyword cloud
5. **Alert Dashboard**: Dashboard with active alerts
6. **Source Distribution**: Distribution of information sources

## 🛡️ Automatic Alerts

The system automatically creates alerts when:

- Global risk >= 0.7 (HIGH/CRITICAL)
- Regional risk >= 0.65 (MEDIUM/HIGH)
- Detection of specific high-risk keywords

Alerts are stored in OpenSearch and can be retrieved via API.

## 📊 Usage Examples

### Python Client

```python
import httpx
import asyncio

async def analyze_current_risk():
    async with httpx.AsyncClient() as client:
        # Prediction
        response = await client.post(
            "http://localhost:8000/predict",
            json={"lookback_hours": 24}
        )
        prediction = response.json()
        
        # OpenSearch search
        search_response = await client.get(
            "http://localhost:8000/opensearch/search/data-points",
            params={"query": "military", "hours_back": 24}
        )
        
        # Dashboard
        dashboard = await client.get(
            "http://localhost:8000/opensearch/analytics/dashboard",
            params={"hours": 24, "days": 7}
        )
        
        return prediction, search_response.json(), dashboard.json()

asyncio.run(analyze_current_risk())
```

### cURL Examples

```bash
# Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"lookback_hours": 24}'

# Search
curl "http://localhost:8000/opensearch/search/data-points?query=conflict&hours_back=48"

# Risk trends
curl "http://localhost:8000/opensearch/analytics/risk-by-region?days=7"

# Dashboard
curl "http://localhost:8000/opensearch/analytics/dashboard?hours=24&days=7"
```

## 🔄 Data Flow

```
1. News/Military/Social → Data Collectors
2. Data Collectors → LangGraph Agent
3. LangGraph Agent → Analysis & Prediction
4. Prediction → OpenSearch (indexing)
5. Prediction → Redis (caching)
6. High Risk → Alert Creation
7. User Query → OpenSearch → Results
```

## 🐛 Debugging

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f opensearch

# OpenSearch status
curl -k -u admin:Admin123! https://localhost:9200/_cluster/health

# Check indices
curl -k -u admin:Admin123! https://localhost:9200/_cat/indices?v

# Test OpenSearch query
curl -k -u admin:Admin123! -X GET \
  "https://localhost:9200/war-prediction-data-points/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match_all": {}}}'
```

## 🚀 Performance Tips

1. **Indexing**: Bulk indexing for better performance
2. **Caching**: 30-minute cache in Redis for predictions
3. **Search**: Use filters instead of query when possible
4. **Aggregations**: Limit time range for large aggregations
5. **Sharding**: Consider multiple shards for production

## 📝 TODO

- [x] OpenSearch integration
- [x] Full-text search
- [x] Sentiment analysis
- [x] Automated alerting
- [x] Dashboard analytics
- [ ] Web UI Dashboard (React)
- [ ] Email/SMS notifications
- [ ] Machine Learning predictions (sklearn)
- [ ] Telegram bot integration
- [ ] Advanced anomaly detection
- [ ] Multi-language support

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT License

## ⚠️ Disclaimer

This system is an analytical tool and should not be used as the sole source of information for decision-making. Predictions are based on available data and may not reflect the actual geopolitical situation.

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ using LangGraph, FastAPI, OpenSearch and OpenAI**

---

# War Prediction Agent (Legacy/Simplified Version) 🌍⚔️

AI system for predicting war outbreak risk based on multi-source intelligence analysis using LangGraph and FastAPI.

## 🎯 Features

- **Multi-source Intelligence**: Collecting data from news services, military sources, and social media
- **AI-Powered Analysis**: Utilizing LLM (GPT-4) for analysis and prediction
- **Real-time Risk Assessment**: Real-time risk assessment for different regions
- **RESTful API**: Easy integration with other systems
- **Caching**: Redis for performance optimization
- **Mesh Agent Architecture**: Using LangGraph to build mesh agent

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI       │
│   (REST API)    │
└────────┬────────┘
         │
┌────────▼────────┐
│  LangGraph      │
│  Mesh Agent     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐  ┌──────┐
│ News │  │ Mil  │  │Social│
│Source│  │Intel │  │Media │
└──────┘  └──────┘  └──────┘
```

## 📦 Tech Stack

- **LangGraph**: AI agent orchestration
- **FastAPI**: API Framework
- **Redis**: Cache and message broker
- **OpenAI GPT-4**: Language model
- **Python 3.11+**: Programming language
- **Docker**: Containerization

## 🚀 Installation

### 1. Clone repository

```bash
git clone <repo-url>
cd war-prediction-agent
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY` - required
- `NEWS_API_KEY` - optional (not currently used)
- `TWITTER_BEARER_TOKEN` - optional (for social media monitoring)

### 3. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

### 4. Local deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run API
uvicorn main:app --reload
```

## 📡 API Endpoints

### `POST /predict`

Main endpoint for war risk prediction.

**Request:**
```json
{
  "regions": ["Europe", "Middle East"],
  "include_social_media": true,
  "lookback_hours": 24
}
```

**Response:**
```json
{
  "timestamp": "2025-10-11T10:30:00",
  "global_risk_score": 0.45,
  "global_risk_level": "medium",
  "regional_analyses": [
    {
      "region": "Europe",
      "risk_score": 0.35,
      "risk_level": "low",
      "indicators": [...],
      "active_conflicts": [],
      "data_points_analyzed": 150
    }
  ],
  "key_events": [...],
  "confidence": 0.78,
  "reasoning": "Based on analysis...",
  "sources_analyzed": 250
}
```

### `GET /health`

System health check.

### `GET /stats`

System statistics.

### `GET /history`

Prediction history.

### `DELETE /cache`

Clear cache.

## 🔧 Configuration

Key settings in `config.py`:

```python
# Risk thresholds
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.6
HIGH_RISK_THRESHOLD = 0.8

# Data sources
NEWS_SOURCES = [
    "https://www.defense.gov/News/Releases/",
    "https://www.nato.int/cps/en/natohq/news.htm",
    # ...
]

# Conflict keywords
CONFLICT_KEYWORDS = [
    "war", "conflict", "military mobilization",
    "troops deployment", "missile strike",
    # ...
]
```

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## 📊 LangGraph Workflow

The agent uses the following workflow:

1. **collect_data**: Collect data from all sources
2. **analyze_relevance**: Analyze relevance and sentiment of data
3. **extract_indicators**: Extract conflict indicators
4. **calculate_risk**: Calculate risk scores
5. **generate_prediction**: Generate final prediction with reasoning

## 🔍 Data Sources

### News Sources
- Defense.gov
- NATO News
- UN Press Releases
- New York Times World
- BBC World News

### Military Intelligence
- Jane's Defence
- Defense One

### Social Media
- Twitter/X (monitoring military hashtags)

## ⚙️ Mesh Agent

The system uses LangGraph to create a mesh agent that:
- Dynamically analyzes data from multiple sources
- Performs iterative analysis and refinement
- Uses LLM to extract insights
- Aggregates results into coherent prediction

## 🛡️ Security

- API keys stored in environment variables
- Rate limiting for external APIs
- Input data validation with Pydantic
- CORS configured for production

## 📈 Scaling

The system supports:
- Horizontal scaling with Load Balancer
- Redis as shared cache
- Async processing for long tasks
- Background tasks for logging

## 🐛 Debugging

```bash
# Docker logs
docker-compose logs -f api

# Redis logs
docker-compose logs -f redis

# Test single collector
python -c "
import asyncio
from data_collectors import NewsCollector
async def test():
    collector = NewsCollector()
    data = await collector.collect()
    print(f'Collected {len(data)} items')
asyncio.run(test())
"
```

## 📝 TODO

- [ ] Add more military sources
- [ ] Implement ML model for classification
- [ ] Dashboard web UI
- [ ] Alerting system (email/SMS)
- [ ] Historical data analysis
- [ ] Telegram bot integration

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT License

## ⚠️ Disclaimer

This system is an analytical tool and should not be used as the sole source of information for decision-making. Predictions are based on available data and may not reflect the actual geopolitical situation.

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ using LangGraph, FastAPI and OpenAI**
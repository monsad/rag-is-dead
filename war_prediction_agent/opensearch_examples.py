
"""
OpenSearch API Endpoints Usage Examples
"""

import asyncio
import httpx
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def example_search_data_points():
    """Search data points"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/search/data-points",
            params={
                "query": "military mobilization",
                "hours_back": 48,
                "min_relevance": 0.5,
                "size": 20
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Found {data['results_count']} results for: {data['query']}\n")
            
            for i, result in enumerate(data['results'][:5], 1):
                print(f"{i}. {result['title']}")
                print(f"   Source: {result['source']} | Relevance: {result['relevance_score']:.2f}")
                print(f"   Date: {result['timestamp']}\n")

async def example_search_by_keywords():
    """Search by keywords"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/search/keywords",
            params={
                "keywords": ["war", "conflict", "invasion"],
                "hours_back": 24,
                "size": 30
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🏷️  Found {data['results_count']} articles with keywords: {', '.join(data['keywords'])}\n")
            
            for result in data['results'][:5]:
                print(f"- {result['title']}")
                print(f"  Keywords: {', '.join(result.get('keywords', []))}\n")

async def example_predictions_history():
    """Predictions history"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/predictions/history",
            params={
                "days_back": 7,
                "min_risk_score": 0.4,
                "size": 20
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Prediction history (last {data['period']['days']} days):")
            print(f"Found {data['predictions_count']} predictions\n")
            
            for pred in data['predictions'][:10]:
                print(f"⏰ {pred['timestamp']}")
                print(f"   Level: {pred['global_risk_level']} ({pred['global_risk_score']:.2f})")
                print(f"   Confidence: {pred['confidence']:.2%}")
                print(f"   Sources: {pred['sources_analyzed']}\n")

async def example_risk_by_region():
    """Risk aggregation by regions"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/analytics/risk-by-region",
            params={"days": 7}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🌍 Risk by regions (last {data['period_days']} days):\n")
            
            # Sort by average risk
            regions = sorted(
                data['regions'].items(),
                key=lambda x: x[1]['avg_risk'],
                reverse=True
            )
            
            for region, stats in regions:
                print(f"📍 {region}:")
                print(f"   Average risk: {stats['avg_risk']:.2f}")
                print(f"   Max risk: {stats['max_risk']:.2f}")
                print(f"   Measurements count: {stats['count']}\n")

async def example_trending_keywords():
    """Trending keywords"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/analytics/trending-keywords",
            params={
                "hours": 24,
                "size": 15
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔥 Trending keywords (last {data['period_hours']}h):\n")
            
            for i, kw in enumerate(data['trending_keywords'], 1):
                bar = "█" * (kw['count'] // 5)
                print(f"{i:2d}. {kw['keyword']:25s} {bar} ({kw['count']})")

async def example_sentiment_analysis():
    """Sentiment analysis"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/analytics/sentiment",
            params={"hours": 24}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"😊😐😢 Sentiment analysis (last {data['period_hours']}h):\n")
            print(f"Average sentiment: {data['average_sentiment']:.2f}\n")
            print("Distribution:")
            
            dist = data['sentiment_distribution']
            for sentiment, count in dist.items():
                emoji = {
                    'very_negative': '😡',
                    'negative': '😟',
                    'neutral': '😐',
                    'positive': '🙂',
                    'very_positive': '😊'
                }.get(sentiment, '❓')
                
                bar = "█" * (count // 2)
                print(f"{emoji} {sentiment:15s} {bar} ({count})")

async def example_get_alerts():
    """Get alerts"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/alerts",
            params={
                "hours": 24,
                "size": 20
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🚨 Alerts (last {data['period_hours']}h):")
            print(f"Found {data['alerts_count']} alerts\n")
            
            for alert in data['alerts']:
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert['severity'], '⚪')
                
                print(f"{severity_emoji} [{alert['severity'].upper()}] {alert['region']}")
                print(f"   {alert['message']}")
                print(f"   Risk: {alert['risk_score']:.2f} | {alert['timestamp']}\n")

async def example_create_alert():
    """Create manual alert"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/opensearch/alerts/create",
            params={
                "alert_type": "manual_review",
                "severity": "medium",
                "region": "Europe",
                "message": "Increased military exercises near border detected",
                "risk_score": 0.55,
                "triggered_by": "analyst_john"
            }
        )
        
        if response.status_code == 200:
            print("✅ Alert created successfully")
        else:
            print(f"❌ Error: {response.status_code}")

async def example_dashboard_data():
    """Complete dashboard data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/analytics/dashboard",
            params={
                "hours": 24,
                "days": 7
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("="*60)
            print("📊 DASHBOARD WAR PREDICTION AGENT")
            print("="*60)
            print(f"Timestamp: {data['timestamp']}")
            print(f"Okres: {data['periods']['recent_hours']}h / {data['periods']['historical_days']} dni\n")
            
            # Statistics
            stats = data['statistics']
            print("📈 Statystyki:")
            print(f"   Total predictions: {stats['total_predictions']}")
            print(f"   Total alerts: {stats['total_alerts']}")
            print(f"   High-risk regions: {', '.join(stats['high_risk_regions']) if stats['high_risk_regions'] else 'None'}\n")
            
            # Trending Keywords
            print("🔥 Top 5 Trending Keywords:")
            for i, kw in enumerate(data['trending_keywords'][:5], 1):
                print(f"   {i}. {kw['keyword']} ({kw['count']})")
            
            # Sentiment
            print(f"\n😊 Average Sentiment: {data['sentiment_analysis']['average']:.2f}")
            
            # Regional Risk
            print("\n🌍 Top Risk Regions:")
            top_regions = sorted(
                data['regional_risk'].items(),
                key=lambda x: x[1]['avg_risk'],
                reverse=True
            )[:5]
            
            for region, risk_data in top_regions:
                print(f"   {region}: {risk_data['avg_risk']:.2f}")
            
            # Recent Alerts
            print(f"\n🚨 Recent Alerts: {len(data['recent_alerts'])}")
            for alert in data['recent_alerts'][:3]:
                print(f"   [{alert['severity']}] {alert['region']}: {alert['message'][:50]}...")
            
            print("\n" + "="*60)

async def example_full_text_search():
    """Advanced full-text search"""
    queries = [
        "nuclear weapons",
        "cyber attack",
        "border conflict",
        "military drills"
    ]
    
    print("🔍 Advanced search\n")
    
    async with httpx.AsyncClient() as client:
        for query in queries:
            response = await client.get(
                f"{API_BASE_URL}/opensearch/search/data-points",
                params={
                    "query": query,
                    "hours_back": 72,
                    "min_relevance": 0.6,
                    "size": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Query: '{query}' → {data['results_count']} results")
            
            await asyncio.sleep(0.5)

async def example_time_series_analysis():
    """Time series analysis of predictions"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/opensearch/predictions/history",
            params={
                "days_back": 30,
                "size": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            predictions = data['predictions']
            
            print(f"📈 Trend analysis (last 30 days)\n")
            
            # Count predictions by risk levels
            risk_levels = {}
            for pred in predictions:
                level = pred['global_risk_level']
                risk_levels[level] = risk_levels.get(level, 0) + 1
            
            print("Risk level distribution:")
            for level, count in sorted(risk_levels.items()):
                bar = "█" * (count * 2)
                print(f"{level:10s} {bar} ({count})")
            
            # Average risk
            avg_risk = sum(p['global_risk_score'] for p in predictions) / len(predictions)
            print(f"\nAverage risk: {avg_risk:.2f}")

# Main menu
async def main():
    """OpenSearch examples main menu"""
    print("=" * 60)
    print("War Prediction Agent - OpenSearch Examples")
    print("=" * 60)
    
    while True:
        print("\nChoose an example:")
        print("1.  Search data points")
        print("2.  Search by keywords")
        print("3.  Predictions history")
        print("4.  Risk by regions")
        print("5.  Trending keywords")
        print("6.  Sentiment analysis")
        print("7.  Get alerts")
        print("8.  Create alert")
        print("9.  Dashboard (comprehensive)")
        print("10. Advanced search")
        print("11. Time series analysis")
        print("0.  Exit")
        
        choice = input("\nChoice: ")
        
        try:
            if choice == "1":
                await example_search_data_points()
            elif choice == "2":
                await example_search_by_keywords()
            elif choice == "3":
                await example_predictions_history()
            elif choice == "4":
                await example_risk_by_region()
            elif choice == "5":
                await example_trending_keywords()
            elif choice == "6":
                await example_sentiment_analysis()
            elif choice == "7":
                await example_get_alerts()
            elif choice == "8":
                await example_create_alert()
            elif choice == "9":
                await example_dashboard_data()
            elif choice == "10":
                await example_full_text_search()
            elif choice == "11":
                await example_time_series_analysis()
            elif choice == "0":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        if choice != "0":
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())
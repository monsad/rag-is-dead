"""
War Prediction Agent API Usage Examples
"""

import asyncio
import httpx
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def example_basic_prediction():
    """Basic prediction"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/predict",
            json={
                "regions": None,  # All regions
                "include_social_media": True,
                "lookback_hours": 24
            },
            timeout=120.0  # 2 minute timeout for analysis
        )
        
        if response.status_code == 200:
            data = response.json()
            print("🎯 Global Prediction:")
            print(f"  Risk: {data['global_risk_level'].upper()}")
            print(f"  Score: {data['global_risk_score']:.2f}")
            print(f"  Confidence: {data['confidence']:.2%}")
            print(f"  Sources: {data['sources_analyzed']}")
            print(f"\n📊 Regional Analysis:")
            for region in data['regional_analyses']:
                print(f"  {region['region']}: {region['risk_level']} ({region['risk_score']:.2f})")
            print(f"\n💡 Reasoning:\n{data['reasoning'][:500]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

async def example_regional_prediction():
    """Prediction for specific regions"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/predict",
            json={
                "regions": ["Europe", "Middle East", "East Asia"],
                "include_social_media": True,
                "lookback_hours": 48  # 2 days back
            },
            timeout=120.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print("🌍 Regional Prediction:")
            for region in data['regional_analyses']:
                print(f"\n📍 {region['region']}:")
                print(f"   Level: {region['risk_level']}")
                print(f"   Score: {region['risk_score']:.2f}")
                print(f"   Data points: {region['data_points_analyzed']}")

async def example_check_health():
    """Check system health"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print("💚 System Status:")
            print(f"  Status: {data['status']}")
            print(f"  Redis: {data['redis']}")
            print(f"  Timestamp: {data['timestamp']}")
        else:
            print("❌ System unavailable")

async def example_get_history():
    """Get prediction history"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/history?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            print("📜 Prediction History:")
            for i, pred in enumerate(data['predictions'], 1):
                print(f"\n  {i}. {pred['timestamp']}")
                print(f"     Level: {pred['risk_level']}")
                print(f"     Score: {pred['risk_score']:.2f}")
                print(f"     Sources: {pred['sources']}")

async def example_get_stats():
    """Get statistics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/stats")
        
        if response.status_code == 200:
            data = response.json()
            print("📊 System Statistics:")
            for key, value in data.items():
                print(f"  {key}: {value}")

async def example_clear_cache():
    """Clear cache"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE_URL}/cache")
        
        if response.status_code == 200:
            data = response.json()
            print(f"🗑️  Cache cleared: {data['cleared']} entries")

async def example_continuous_monitoring():
    """Continuous monitoring (every hour)"""
    print("🔄 Starting continuous monitoring...")
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/predict",
                    json={
                        "regions": None,
                        "include_social_media": True,
                        "lookback_hours": 24
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"\n⏰ [{timestamp}] Update:")
                    print(f"  Risk: {data['global_risk_level'].upper()} ({data['global_risk_score']:.2f})")
                    
                    # Alert for high risk
                    if data['global_risk_score'] > 0.7:
                        print("  ⚠️  WARNING: High risk detected!")
                        print(f"  Details: {data['reasoning'][:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait one hour
        await asyncio.sleep(3600)

async def example_compare_timeframes():
    """Compare predictions for different timeframes"""
    timeframes = [6, 12, 24, 48, 72]
    
    print("🕐 Analysis of different timeframes:\n")
    
    async with httpx.AsyncClient() as client:
        for hours in timeframes:
            response = await client.post(
                f"{API_BASE_URL}/predict",
                json={
                    "regions": None,
                    "include_social_media": True,
                    "lookback_hours": hours
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  {hours}h: {data['global_risk_level']} ({data['global_risk_score']:.2f})")
            
            # Short pause between requests
            await asyncio.sleep(2)

# Main menu
async def main():
    """Main menu of examples"""
    print("=" * 60)
    print("War Prediction Agent - Usage Examples")
    print("=" * 60)
    
    while True:
        print("\nChoose an example:")
        print("1. Basic prediction")
        print("2. Regional prediction")
        print("3. Check system health")
        print("4. Get history")
        print("5. Get statistics")
        print("6. Clear cache")
        print("7. Compare different timeframes")
        print("8. Continuous monitoring (CTRL+C to stop)")
        print("0. Exit")
        
        choice = input("\nChoice: ")
        
        try:
            if choice == "1":
                await example_basic_prediction()
            elif choice == "2":
                await example_regional_prediction()
            elif choice == "3":
                await example_check_health()
            elif choice == "4":
                await example_get_history()
            elif choice == "5":
                await example_get_stats()
            elif choice == "6":
                await example_clear_cache()
            elif choice == "7":
                await example_compare_timeframes()
            elif choice == "8":
                await example_continuous_monitoring()
            elif choice == "0":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
        
        except KeyboardInterrupt:
            print("\n⏸️  Stopped")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        if choice != "8":
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())
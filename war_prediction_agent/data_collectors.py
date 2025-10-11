import httpx
import feedparser
import tweepy
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timedelta
from models import DataPoint, SourceType
from config import settings
import asyncio
import hashlib

class NewsCollector:
    """Collector for news sources"""
    
    async def collect(self, hours_back: int = 24) -> List[DataPoint]:
        data_points = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for source_url in settings.NEWS_SOURCES:
                try:
                    if source_url.endswith('.xml') or 'rss' in source_url:
                        data_points.extend(await self._parse_rss(source_url, cutoff_time))
                    else:
                        data_points.extend(await self._scrape_website(client, source_url, cutoff_time))
                except Exception as e:
                    print(f"Error collecting from {source_url}: {e}")
        
        return data_points
    
    async def _parse_rss(self, url: str, cutoff_time: datetime) -> List[DataPoint]:
        feed = feedparser.parse(url)
        data_points = []
        
        for entry in feed.entries:
            pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
            
            if pub_date >= cutoff_time:
                content = entry.get('summary', '') or entry.get('description', '')
                title = entry.get('title', '')
                
                if self._is_relevant(title + " " + content):
                    data_points.append(DataPoint(
                        id=hashlib.md5(entry.link.encode()).hexdigest(),
                        source=feed.feed.get('title', url),
                        source_type=SourceType.NEWS,
                        title=title,
                        content=content,
                        url=entry.link,
                        timestamp=pub_date,
                        keywords=self._extract_keywords(title + " " + content)
                    ))
        
        return data_points
    
    async def _scrape_website(self, client: httpx.AsyncClient, url: str, cutoff_time: datetime) -> List[DataPoint]:
        try:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x or 'news' in x))
            data_points = []
            
            for article in articles[:20]:
                title_elem = article.find(['h1', 'h2', 'h3', 'a'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                content = article.get_text(strip=True)[:500]
                
                if self._is_relevant(title + " " + content):
                    data_points.append(DataPoint(
                        id=hashlib.md5((url + title).encode()).hexdigest(),
                        source=url,
                        source_type=SourceType.NEWS,
                        title=title,
                        content=content,
                        url=url,
                        timestamp=datetime.now(),
                        keywords=self._extract_keywords(title + " " + content)
                    ))
            
            return data_points
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []
    
    def _is_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in settings.CONFLICT_KEYWORDS)
    
    def _extract_keywords(self, text: str) -> List[str]:
        return [kw for kw in settings.CONFLICT_KEYWORDS if kw.lower() in text.lower()]


class MilitaryIntelCollector:
    """Collector for military intelligence sources"""
    
    async def collect(self, hours_back: int = 24) -> List[DataPoint]:
        data_points = []
        
        for source_url in settings.MILITARY_SOURCES:
            try:
                feed = feedparser.parse(source_url)
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                for entry in feed.entries:
                    pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    if pub_date >= cutoff_time:
                        data_points.append(DataPoint(
                            id=hashlib.md5(entry.link.encode()).hexdigest(),
                            source=feed.feed.get('title', source_url),
                            source_type=SourceType.MILITARY,
                            title=entry.title,
                            content=entry.get('summary', ''),
                            url=entry.link,
                            timestamp=pub_date
                        ))
            except Exception as e:
                print(f"Error collecting from {source_url}: {e}")
        
        return data_points


class SocialMediaCollector:
    """Collector for social media (Twitter/X)"""
    
    def __init__(self):
        if settings.TWITTER_BEARER_TOKEN:
            self.client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
        else:
            self.client = None
    
    async def collect(self, hours_back: int = 24) -> List[DataPoint]:
        if not self.client:
            return []
        
        data_points = []
        search_terms = ["military conflict", "war breaking", "troops deployed", "missile strike"]
        
        try:
            for term in search_terms:
                tweets = self.client.search_recent_tweets(
                    query=f"{term} -is:retweet lang:en",
                    max_results=100,
                    tweet_fields=['created_at', 'public_metrics']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        data_points.append(DataPoint(
                            id=str(tweet.id),
                            source="Twitter",
                            source_type=SourceType.SOCIAL_MEDIA,
                            title=tweet.text[:100],
                            content=tweet.text,
                            timestamp=tweet.created_at,
                            keywords=self._extract_keywords(tweet.text)
                        ))
        except Exception as e:
            print(f"Error collecting from Twitter: {e}")
        
        return data_points
    
    def _extract_keywords(self, text: str) -> List[str]:
        return [kw for kw in settings.CONFLICT_KEYWORDS if kw.lower() in text.lower()]
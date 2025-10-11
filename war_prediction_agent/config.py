from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    NEWS_API_KEY: str = ""  # Optional - not currently used
    TWITTER_BEARER_TOKEN: str = ""  # Optional - for social media monitoring
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # OpenSearch Configuration
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = "admin"
    OPENSEARCH_USE_SSL: bool = True
    OPENSEARCH_VERIFY_CERTS: bool = False
    
    # News Sources
    NEWS_SOURCES: List[str] = [
        "https://www.defense.gov/News/Releases/",
        "https://www.nato.int/cps/en/natohq/news.htm",
        "https://www.un.org/press/en",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml"
    ]
    
    # Military Intelligence Sources
    MILITARY_SOURCES: List[str] = [
        "https://www.janes.com/feeds",
        "https://www.defenseone.com/rss/"
    ]
    
    # Conflict Keywords
    CONFLICT_KEYWORDS: List[str] = [
        "war", "conflict", "military mobilization", "troops deployment",
        "missile strike", "invasion", "border tension", "military exercise",
        "airspace violation", "naval confrontation", "ceasefire violation"
    ]
    
    # Risk Thresholds
    LOW_RISK_THRESHOLD: float = 0.3
    MEDIUM_RISK_THRESHOLD: float = 0.6
    HIGH_RISK_THRESHOLD: float = 0.8
    
    # Agent Configuration
    MAX_ITERATIONS: int = 5
    TEMPERATURE: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
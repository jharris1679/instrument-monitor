#!/usr/bin/env python3
"""Test datetime serialization fix"""
import json
import sys
from datetime import datetime
sys.path.insert(0, '/Users/studio/answerlayer/asset-monitor')

from app.market_data_fetcher import MarketDataFetcher
from app.rss_processor import load_feeds

def test_json_serialization():
    """Test that market data and news can be JSON serialized"""
    print("Testing JSON serialization of market data and news...")

    # Test market data serialization
    fetcher = MarketDataFetcher()
    market_data = fetcher.fetch_all()

    print(f"✓ Fetched {len(market_data)} assets")

    try:
        market_json = json.dumps(market_data, indent=2)
        print(f"✓ Market data serialized successfully ({len(market_json)} bytes)")

        # Test RSS news serialization
        news = load_feeds()
        print(f"✓ Loaded {len(news)} RSS feeds")

        # Get recent articles from first few feeds
        recent_articles = []
        for feed in news[:3]:  # Test with 3 feeds
            recent_articles.extend(feed.entries[:5])
            print(f"  - Feed '{feed.title}': {len(feed.entries)} articles")

        news_json = json.dumps(recent_articles[:10], indent=2)
        print(f"✓ News articles serialized successfully ({len(news_json)} bytes)")

        return True
    except TypeError as e:
        print(f"✗ JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_json_serialization()
    sys.exit(0 if success else 1)
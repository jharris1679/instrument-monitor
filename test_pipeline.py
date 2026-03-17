#!/usr/bin/env python3
"""
End-to-end test for instrument monitor pipeline
Tests: RSS feeds → Market data → Briefing generation
"""
import os
import sys
from datetime import datetime

# Add asset-monitor to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rss_processor import RSSFeedProcessor
from app.market_data_fetcher import MarketDataFetcher
from app.insight_generator import InsightGenerator


def test_pipeline():
    """Run complete pipeline test"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 60}")
    print(f"Running Pipeline Test at {timestamp}")
    print(f"{'=' * 60}\n")

    # Step 1: Fetch RSS feeds
    print("Step 1: Fetching RSS feeds...")
    rss_processor = RSSFeedProcessor()
    news_items = rss_processor.fetch_news()
    print(f"✓ Fetched {len(news_items)} news articles")

    # Filter valid news items (pubdate is required for sorting)
    valid_news = [n for n in news_items if n.get('published')]
    print(f"✓ Valid news items with dates: {len(valid_news)}\n")

    # Step 2: Fetch market data (equity ETFs only)
    print("Step 2: Fetching market data...")
    fetcher = MarketDataFetcher()
    market_data = fetcher.fetch_all()

    print(f"✓ Fetched {len(market_data)} asset prices")

    # Display market data
    print("\n--- Market Data ---")
    for asset in market_data:
        price = asset.get('price', 'N/A')
        change = asset.get('change_percent', 'N/A')
        print(f"  {asset['symbol']}: ${price} ({change}%)")

    # Step 3: Generate insights
    print("\nStep 3: Generating insights...")
    insights_generator = InsightGenerator()
    insights = []

    # Use basic insight generation method (fallback if GLM is not available)
    # Filter to only successful market data items (those with valid price data)
    successful = [m for m in market_data if m.get('price') and m.get('price') != 'N/A']
    
    try:
        result = insights_generator.generate_briefing(
            market_data=successful,
            news=valid_news,
        )
        briefing = result.get('briefing', '')
        sources = result.get('sources', [])
        tracked = result.get('tracked_instruments', [])
        print(f"✓ Generated briefing ({len(briefing)} chars, {len(sources)} sources)")

        if tracked:
            print(f"  New instruments discovered: {', '.join(tracked)}")

        if briefing:
            print("\n--- Briefing Preview ---")
            # Show first 500 chars
            preview = briefing[:500]
            if len(briefing) > 500:
                preview += "..."
            print(preview)

    except Exception as e:
        print(f"✗ Error generating briefing: {e}")
        briefing = ''

    print(f"\n{'=' * 60}")
    print(f"Pipeline Test Complete")
    print(f"{'=' * 60}\n")

    return {"status": "success", "rss_count": len(valid_news), "market_count": len(successful), "briefing_length": len(briefing)}


if __name__ == "__main__":
    test_pipeline()
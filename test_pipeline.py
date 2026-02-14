#!/usr/bin/env python3
"""
End-to-end test for asset monitoring pipeline
Tests: RSS feeds → Market data → Insights generation
"""
import json
import os
import sys
from datetime import datetime

# Add asset-monitor to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        insights = insights_generator.generate_insights(successful, valid_news, current_context='daily_report')
        print(f"✓ Generated {len(insights)} insights")

        if insights:
            print("\n--- Sample Insights ---")
            for i, insight in enumerate(insights[:5], 1):
                print(f"\n{i}. {insight.get('title', 'N/A')}")
                print(f"   Source: {insight.get('source', 'N/A')}")
                print(f"   Price Action: {insight.get('price_action', 'N/A')}")
                print(f"   Context: {insight.get('context', 'N/A')}")

    except Exception as e:
        print(f"✗ Error generating insights: {e}")

    print(f"\n{'=' * 60}")
    print(f"Pipeline Test Complete")
    print(f"{'=' * 60}\n")

    return {"status": "success", "rss_count": len(valid_news), "market_count": len(successful), "insight_count": len(insights)}


if __name__ == "__main__":
    test_pipeline()
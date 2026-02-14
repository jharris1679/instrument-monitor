#!/usr/bin/env python3
"""Test script to trigger a single market report"""

from datetime import datetime
from app.market_data_fetcher import MarketDataFetcher
from app.rss_processor import RSSFeedProcessor
from app.slack_notifier import SlackNotifier
from app.insight_generator import InsightGenerator

def test_run_report():
    """Generate and display a market report"""

    print(f"\n{'='*50}")
    print(f"Generating Report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Fetch market data
    print("Fetching market data...")
    market_data_fetcher = MarketDataFetcher()
    market_data = market_data_fetcher.fetch_all()
    print(f"✓ Fetched {len(market_data)} asset prices")

    # Display market data
    print("\n--- Market Data ---")
    for item in market_data:
        symbol = item.get('symbol', '')
        price = item.get('price')
        change = item.get('change_percent')
        print(f"  {symbol}: ${price if price else 'N/A'} ({change}%)")

    # Fetch RSS news
    print("\nFetching news...")
    rss_processor = RSSFeedProcessor()
    news = rss_processor.fetch_news()
    trending_news = news[:3]
    print(f"✓ Fetched {len(news)} news articles")

    # Display news
    print("\n--- News ---")
    for article in news[:5]:
        print(f"  [{article.get('source', 'Unknown')}] {article.get('title', 'No title')}")

    # Generate insights
    print("\nGenerating insights...")
    insight_generator = InsightGenerator()
    insights = insight_generator.generate_insights(
        market_data=market_data,
        news=news,
        current_context="test"
    )

    print(f"✓ Generated {len(insights)} insights")

    # Display insights
    print("\n--- Insights ---")
    for insight in insights:
        priority = insight.get('priority', 'medium')
        symbol = insight.get('symbol', 'Market')
        description = insight.get('description', '')
        category = insight.get('category', 'General')
        print(f"  [{priority.upper()}] {symbol} - {description[:60]}... ({category})")

    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    test_run_report()
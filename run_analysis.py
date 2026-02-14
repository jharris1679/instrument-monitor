#!/usr/bin/env python3
"""
Quick analysis script for instrument-monitor
Fetches market data and generates AI insights
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.market_data_fetcher import MarketDataFetcher
from app.rss_processor import RSSFeedProcessor
from app.insight_generator import InsightGenerator

def main():
    print("\n" + "="*70)
    print("📊 Instrument Monitor - Quick Analysis")
    print("="*70 + "\n")
    
    # Initialize components
    print("Initializing components...")
    fetcher = MarketDataFetcher()
    rss_processor = RSSFeedProcessor()
    insight_generator = InsightGenerator()
    
    print("✓ Components initialized\n")
    
    # Fetch market data
    print("Fetching market data...")
    market_data = fetcher.fetch_all()
    print(f"✓ Fetched {len(market_data)} asset prices\n")
    
    # Fetch news
    print("Fetching news...")
    news = rss_processor.fetch_news()
    print(f"✓ Fetched {len(news)} news articles\n")
    
    # Generate insights
    print("Generating AI insights...")
    insights = insight_generator.generate_insights(
        market_data=market_data,
        news=news,
        current_context="quick_analysis"
    )
    
    if not insights:
        print("⚠ No insights generated")
        return
    
    print(f"✓ Generated {len(insights)} insights\n")
    
    print("REPORT SUMMARY")
    print("-" * 70)
    
    # Categorize by priority
    high_priority = [i for i in insights if i.get('priority') == 'high']
    medium_priority = [i for i in insights if i.get('priority') == 'medium']
    low_priority = [i for i in insights if i.get('priority') == 'low']
    
    print(f"\nHIGH PRIORITY ({len(high_priority)}):")
    print("-" * 70)
    for insight in high_priority:
        print(f"\n🔥 {insight.get('title', 'Urgent Alert')}")
        print(f"   Asset: {insight.get('asset_symbol', 'N/A')}")
        print(f"   Confidence: {insight.get('confidence', 'N/A')}")
        print(f"   Insight: {insight.get('insight', 'No details')}")
    
    print(f"\n\nMEDIUM PRIORITY ({len(medium_priority)}):")
    print("-" * 70)
    for insight in medium_priority:
        print(f"\n⚡ {insight.get('title', 'Update')}")
        print(f"   Asset: {insight.get('asset_symbol', 'N/A')}")
        print(f"   Insight: {insight.get('insight', 'No details')}")
    
    print(f"\n\nLOW PRIORITY ({len(low_priority)}):")
    print("-" * 70)
    for insight in low_priority[:5]:  # Show top 5
        print(f"\n📌 {insight.get('title', 'Summary')}")
        print(f"   Asset: {insight.get('asset_symbol', 'N/A')}")
        print(f"   Confidence: {insight.get('confidence', 'N/A')}")
    
    print(f"\n\n📊 Processed {len(market_data)} assets")
    print(f"📰 Retrieved {len(news)} news articles")
    print(f"🧠 Generated {len(insights)} AI insights (High: {len(high_priority)}, Medium: {len(medium_priority)}, Low: {len(low_priority)})")
    
    print("\n" + "="*70)
    print("✅ Analysis complete!")
    print("\nWould you like:")
    print("  - Send insights to Slack? Run: python send_to_slack.py")
    print("  - Run scheduled report? Run: python app/scheduler.py")
    print("  - Start API server? Run: python app/main.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Daily macro briefing — fetches market data + news, generates prose analysis.
"""
import sys
import os
import textwrap

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.market_data_fetcher import MarketDataFetcher
from app.rss_processor import RSSFeedProcessor
from app.insight_generator import InsightGenerator

COLS = 80

def main():
    fetcher = MarketDataFetcher()
    rss_processor = RSSFeedProcessor()
    insight_generator = InsightGenerator()

    print("Fetching data...")
    market_data = fetcher.fetch_all()
    news = rss_processor.fetch_news()
    print(f"  {len(market_data)} assets, {len(news)} articles\n")

    # Price table
    print(f"{'Symbol':<6} {'Price':>10} {'Chg%':>7} {'SMA50':>10} {'SMA200':>10}")
    print("-" * 47)
    for item in market_data:
        print(f"{item['symbol']:<6} {item['price']:>10.2f} {(item.get('change_percent') or 0):>+6.2f}% "
              f"{(item.get('sma_50') or 0):>10.2f} {(item.get('sma_200') or 0):>10.2f}")

    # Generate briefing
    print(f"\n{'=' * COLS}")
    print("MACRO BRIEFING")
    print(f"{'=' * COLS}\n")

    result = insight_generator.generate_briefing(market_data=market_data, news=news)

    # Print briefing prose, wrapped to terminal width
    for paragraph in result['briefing'].split('\n'):
        paragraph = paragraph.strip()
        if paragraph:
            print(textwrap.fill(paragraph, width=COLS))
            print()

    # Sources
    sources = result.get('sources', [])
    if sources:
        print(f"{'-' * COLS}")
        print("Sources:")
        for src in sources:
            title = src.get('title', '')
            link = src.get('link', '')
            if title:
                print(f"  - {title}")
                if link:
                    print(f"    {link}")

if __name__ == "__main__":
    main()

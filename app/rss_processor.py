import feedparser
from datetime import datetime
from typing import List, Dict

class RSSFeedProcessor:
    def __init__(self):
        self.feeds = []
        self.load_feeds()

    def load_feeds(self):
        """Load RSS feeds from config file"""
        feeds = []
        try:
            import os
            this_dir = os.path.dirname(os.path.abspath(__file__))
            feeds_file = os.path.join(this_dir, '..', 'rss_sources', 'financial.feeds')

            with open(feeds_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    # Skip comments (lines starting with #)
                    # Also skip lines with leading dashes that shouldn't be part of URLs
                    if not line.startswith('#') and not line.startswith('-') and line:
                        feeds.append(line)
        except Exception as e:
            print(f"Error loading feeds: {e}")
        self.feeds = feeds

    def fetch_news(self) -> List[Dict]:
        """Fetch and parse all RSS feeds"""
        news_items = []

        for feed_url in self.feeds:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:10]:  # Limit to 10 items per feed
                    news_items.append({
                        "title": entry.get('title'),
                        "link": entry.get('link'),
                        "summary": entry.get('summary'),
                        "published": entry.get('published'),
                        "source": parsed.feed.get('title'),
                        "category": self._categorize_news(entry)
                    })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")

        # Sort by published date (newest first)
        news_items.sort(key=lambda x: x['published'], reverse=True)
        return news_items

    def _categorize_news(self, entry) -> str:
        """Simple categorization based on keywords"""
        categories = []

        # Market and financial terms
        if any(term in entry.get('title', '').lower() for term in ['stock', 'market', 'economy', 'fed', 'cpi', 'nfp']):
            categories.append('Market')
        if any(term in entry.get('title', '').lower() for term in ['crypto', 'bitcoin', 'ethereum', 'coin', 'defi']):
            categories.append('Crypto')
        if any(term in entry.get('title', '').lower() for term in ['decline', 'rise', 'movement', 'shift', 'trend']):
            categories.append('Price Action')
        if any(term in entry.get('title', '').lower() for term in ['earnings', '财报', 'profit', 'revenue']):
            categories.append('Corporate Data')
        if any(term in entry.get('title', '').lower() for term in ['challenge', 'opportunity', 'strategic', 'policy']):
            categories.append('Strategic')

        return categories[0] if categories else 'General'
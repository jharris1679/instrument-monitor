import schedule
import time
import json
from typing import Dict, List
from datetime import datetime

from app.market_data_fetcher import MarketDataFetcher
from app.rss_processor import RSSFeedProcessor
from app.slack_notifier import SlackNotifier
from app.insight_generator import InsightGenerator

class MarketMonitor:
    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.rss_processor = RSSFeedProcessor()
        self.insight_generator = InsightGenerator()
        self.slack_notifier = SlackNotifier()

    def run_report(self):
        """Generate and send a market report"""
        print(f"\n{'='*50}")
        print(f"Generating Report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        # Fetch market data
        print("Fetching market data...")
        market_data = self.market_data.fetch_all()
        print(f"✓ Fetched {len(market_data)} asset prices")

        # Fetch RSS news
        print("\nFetching news...")
        news = self.rss_processor.fetch_news()
        trending_news = self._get_trending_news(news)
        print(f"✓ Fetched {len(news)} news articles")

        # Generate insights
        print("\nGenerating insights...")
        insights = self.insight_generator.generate_insights(
            market_data=market_data,
            news=news,
            current_context="daily"
        )

        # Prioritize insights
        high_priority = [i for i in insights if i.get('priority') == 'high']
        medium_priority = [i for i in insights if i.get('priority') == 'medium']
        low_priority = [i for i in insights if i.get('priority') == 'low']

        # Send notifications
        print("\nSending notifications...")

        # High priority - broadcast
        if high_priority:
            print(f"  Sending {len(high_priority)} high priority alerts...")
            self.slack_notifier.send_alert({
                "title": "🚨 CRITICAL INSIGHTS",
                "insights": high_priority,
                "report_type": "critical"
            })

        # Medium priority - channel
        if medium_priority:
            print(f"  Sending {len(medium_priority)} medium priority updates...")
            self.slack_notifier.send_update({
                "title": "📈 Market Updates",
                "insights": medium_priority,
                "report_type": "update"
            })

        # Low priority - detailed report
        if low_priority:
            print(f"  Sending {len(low_priority)} summary insights...")
            self.slack_notifier.send_detailed_report({
                "title": "📊 Daily Market Summary",
                "insights": low_priority,
                "trending_news": trending_news,
                "report_type": "summary"
            })

        print(f"\n✓ Report generation complete. {len(insights)} insights generated.")
        print(f"  - High priority: {len(high_priority)}")
        print(f"  - Medium priority: {len(medium_priority)}")
        print(f"  - Low priority: {len(low_priority)}\n")

    def _get_trending_news(self, news: List[Dict]) -> List[Dict]:
        """Get top 3 most trending news items"""
        return news[:3]

    def start_scheduled_reports(self):
        """Start the scheduled reporting system"""
        print("Starting Market Monitor scheduler...")
        print("Reporting hours: 9am, 12pm, 3pm, 9pm daily")

        # Schedule reports at specified times
        schedule.every().day.at("09:00").do(self.run_report)
        schedule.every().day.at("12:00").do(self.run_report)
        schedule.every().day.at("15:00").do(self.run_report)
        schedule.every().day.at("21:00").do(self.run_report)

        # Run immediately on startup
        self.run_report()

        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)
import schedule
import time
import json
from typing import Dict, List
from datetime import datetime, date

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

    def run_report(self, include_intraday: bool = False, session_context: str = ""):
        """Generate and send a market report"""
        print(f"\n{'='*50}")
        print(f"Generating Report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Session context: {session_context or 'none'}")
        print(f"{'='*50}\n")

        # Fetch market data
        print("Fetching market data...")
        market_data = self.market_data.fetch_all()
        print(f"✓ Fetched {len(market_data)} asset prices")

        # Fetch intraday data for midday runs
        intraday = None
        if include_intraday:
            print("\nFetching intraday bars...")
            intraday = self.market_data.fetch_intraday()
            print(f"✓ Fetched {len(intraday)} intraday bars")

        # Fetch RSS news
        print("\nFetching news...")
        news = self.rss_processor.fetch_news()
        trending_news = self._get_trending_news(news)
        print(f"✓ Fetched {len(news)} news articles")

        # Generate briefing
        print("\nGenerating macro briefing...")
        result = self.insight_generator.generate_briefing(
            market_data=market_data,
            news=news,
            intraday=intraday,
            session_context=session_context,
        )

        briefing = result.get('briefing', '')
        sources = result.get('sources', [])
        tracked = result.get('tracked_instruments', [])

        # Send briefing to Slack
        print("\nSending briefing...")
        self.slack_notifier.send_update({
            "title": "📊 Macro Briefing",
            "briefing": briefing,
            "sources": sources,
            "tracked_instruments": tracked,
            "trending_news": trending_news,
            "report_type": "briefing"
        })

        if tracked:
            print(f"  New instruments tracked: {', '.join(tracked)}")

        print(f"\n✓ Briefing sent ({len(briefing)} chars, {len(sources)} sources).")

    def _get_trending_news(self, news: List[Dict]) -> List[Dict]:
        """Get top 3 most trending news items"""
        return news[:3]

    def update_historical_data(self):
        """Update OHLCV CSVs with any new trading days"""
        print(f"Updating historical OHLCV data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        updated = self.market_data.update_historical()
        total_new = sum(updated.values())
        if total_new:
            print(f"✓ Added {total_new} new rows across {sum(1 for v in updated.values() if v)} symbols")
        else:
            print("✓ Historical data already up to date")

    def _is_weekend(self):
        return date.today().weekday() >= 5  # 5=Saturday, 6=Sunday

    def _run_weekday_report(self, include_intraday: bool = False, session_context: str = ""):
        if not self._is_weekend():
            self.run_report(include_intraday=include_intraday, session_context=session_context)

    def _run_weekend_report(self):
        if self._is_weekend():
            self.run_report(session_context="WEEKEND. Markets closed. Prices are Friday's close. Focus on newsflow and positioning for Monday.")

    def start_scheduled_reports(self):
        """Start the scheduled reporting system"""
        print("Starting Market Monitor scheduler...")
        print("Weekday reports: 9am, 12pm, 3pm, 9pm")
        print("Weekend reports: 9am")
        print("Historical OHLCV update: 8am daily")

        # Update historical data once daily before markets open
        schedule.every().day.at("08:00").do(self.update_historical_data)

        # Weekday reports (Mon-Fri): 9am, 12pm (intraday), 3pm (intraday), 9pm
        schedule.every().day.at("09:00").do(
            self._run_weekday_report,
            session_context="PRE-MARKET (9am). US equity markets open at 9:30am. Prices are yesterday's close.",
        )
        schedule.every().day.at("12:00").do(
            self._run_weekday_report,
            include_intraday=True,
            session_context="INTRADAY (12pm). Markets are open. Prices are live.",
        )
        schedule.every().day.at("15:00").do(
            self._run_weekday_report,
            include_intraday=True,
            session_context="INTRADAY (3pm). Markets close at 4pm. Prices are live.",
        )
        schedule.every().day.at("21:00").do(
            self._run_weekday_report,
            session_context="POST-MARKET (9pm). Markets closed at 4pm. Prices are today's close.",
        )

        # Weekend reports (Sat-Sun): 9am only
        schedule.every().day.at("09:00").do(self._run_weekend_report)

        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)
from slack_sdk import WebClient
from typing import Dict, List
import os
from datetime import datetime

class SlackNotifier:
    def __init__(self):
        self.token = os.getenv('SLACK_TOKEN')
        self.channel = os.getenv('SLACK_CHANNEL', '#market-monitor')
        if not self.token:
            print("Warning: SLACK_TOKEN not set - Slack notifications will be disabled")

    def send_alert(self, data: Dict):
        """Send critical priority alerts"""
        if not self.token or not self.channel:
            print("Skipping Slack alert: token not configured")
            return

        try:
            client = slack_sdk.WebClient(token=self.token)

            # Format alert message
            insights_text = "\n".join([
                f"🔴 <{i.get('link', '#')}|{i.get('title', 'No title')}> - {i.get('symbol', 'Unknown')}\n"
                f"   ⚠️ {i.get('description', 'No description')}"
                for i in data.get('insights', [])
            ])

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": data.get('title', '🚨 ALERT')
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": insights_text
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Report Type:* {data.get('report_type', 'alert')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]

            client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=data.get('title', '🚨 ALERT')
            )
            print("✓ High priority alert sent to Slack")

        except Exception as e:
            print(f"Error sending Slack alert: {e}")

    def send_update(self, data: Dict):
        """Send medium priority updates"""
        if not self.token or not self.channel:
            print("Skipping Slack update: token not configured")
            return

        try:
            client = slack_sdk.WebClient(token=self.token)

            insights_text = "\n".join([
                f"📈 <{i.get('link', '#')}|{i.get('title', 'No title')}> - {i.get('description', '')}\n"
                f"   Previous Price: ${i.get('previous_price', 'N/A')}"
                for i in data.get('insights', [])[:10]
            ])

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": data.get('title', '📈 UPDATE')
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Insights Count:*\n{len(data.get('insights', []))}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Report Type:*\n{data.get('report_type', 'update')}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{insights_text[:2000]}"
                    }
                }
            ]

            client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=data.get('title', '📈 UPDATE')
            )
            print("✓ Medium priority update sent to Slack")

        except Exception as e:
            print(f"Error sending Slack update: {e}")

    def send_detailed_report(self, data: Dict):
        """Send comprehensive daily summary"""
        if not self.token or not self.channel:
            print("Skipping Slack detailed report: token not configured")
            return

        try:
            client = slack_sdk.WebClient(token=self.token)

            # Format insights
            insights_text = "\n".join([
                f"- <{i.get('symbol', '#')}|{i.get('symbol')}*: ${i.get('current_price') or i.get('last_price')}*\n"
                f"  Description: {i.get('description', 'No description')}"
                for i in data.get('insights', [])[:15]
            ])

            # Format trending news
            news_text = "\n".join([
                f"📰 <{n.get('link', '#')}|{n.get('title', 'No title')}> ({n.get('source', 'Unknown')})"
                for n in data.get('trending_news', [])[:5]
            ])

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": data.get('title', '📊 DAILY SUMMARY')
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{datetime.now().strftime('%Y-%m-%d')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Day of Week:*\n{datetime.now().strftime('%A')}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"## Market Insights\n{insights_text[:2000]}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"## Trending News\n{news_text[:2000]}"
                    }
                }
            ]

            client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=data.get('title', '📊 DAILY SUMMARY')
            )
            print("✓ Detailed report sent to Slack")

        except Exception as e:
            print(f"Error sending Slack detailed report: {e}")
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
            client = WebClient(token=self.token)

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
        """Send a macro briefing to Slack."""
        if not self.token or not self.channel:
            print("Skipping Slack update: token not configured")
            return

        try:
            client = WebClient(token=self.token)

            briefing = data.get('briefing', '')
            sources = data.get('sources', [])

            # Build blocks: header, briefing paragraphs, sources
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Macro Briefing — {datetime.now().strftime('%b %d, %H:%M')}"
                    }
                },
            ]

            # Split briefing into sections to stay under Slack's 3000-char block limit
            paragraphs = [p.strip() for p in briefing.split('\n') if p.strip()]
            chunk = ""
            for para in paragraphs:
                if len(chunk) + len(para) + 2 > 2900:
                    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": chunk}})
                    chunk = para
                else:
                    chunk = f"{chunk}\n\n{para}" if chunk else para
            if chunk:
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": chunk}})

            # Sources
            if sources:
                blocks.append({"type": "divider"})
                source_lines = "\n".join(
                    f"• <{s.get('link', '#')}|{s.get('title', 'Source')}>"
                    for s in sources[:8]
                )
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": source_lines[:3000]}]
                })

            # Newly discovered instruments
            tracked = data.get('tracked_instruments', [])
            if tracked:
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f"🔍 *New instruments discovered:* {', '.join(tracked)} — added to supplementary tracking"
                    }]
                })

            client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=briefing[:500],  # fallback for notifications
            )
            print("✓ Briefing sent to Slack")

        except Exception as e:
            print(f"Error sending Slack update: {e}")

    def send_detailed_report(self, data: Dict):
        """Send comprehensive daily summary"""
        if not self.token or not self.channel:
            print("Skipping Slack detailed report: token not configured")
            return

        try:
            client = WebClient(token=self.token)

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
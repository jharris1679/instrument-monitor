from typing import List, Dict
from datetime import datetime
import numpy as np
import json
import os
import requests
import time
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("/Users/studio/answerlayer/asset-monitor/.env")

@dataclass
class MarketItem:
    symbol: str
    change_percent: float = 0.0
    price: Optional[float] = None
    volume: Optional[float] = None

class LocalGLMAgent:
    """Local GLM 4.7 Flash client for on-device inference"""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize local GLM model agent

        Args:
            model_path: Path to GLM model (defaults to os.getenv("GLM_MODEL_PATH"))
        """
        if model_path and os.path.exists(model_path):
            self.model_path = model_path
        else:
            self.model_path = os.getenv("GLM_MODEL_PATH")

    def call(self, prompt: str, max_retries: int = 3, timeout: int = 120) -> str:
        """
        Call the local GLM model with the given prompt via HTTP

        Args:
            prompt: Input prompt for the model
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Returns:
            Model response as string
        """
        url = "http://localhost:8082/v1/chat/completions"

        for attempt in range(max_retries):
            data = None
            try:
                # Use chat completion format with messages
                payload = {
                    "model": self.model_path,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "stream": False
                }

                response = requests.post(
                    url,
                    json=payload,
                    timeout=timeout
                )

                data = response.json()
                # Chat completion format uses message.content instead of text
                return data["choices"][0]["message"]["content"].strip()

            except requests.Timeout as e:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue

            except requests.HTTPError as e:
                print(f"HTTP error on attempt {attempt + 1}: {e.response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue

            except requests.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue

            except (KeyError, IndexError) as e:
                print(f"Response parsing error on attempt {attempt + 1}: {e}")
                try:
                    print(f"Response data: {data}")
                except:
                    print("Could not access response data")
                break

            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                import traceback
                traceback.print_exc()
                break

        return "Error: Could not generate insight with local GLM model"

    def synthesize_insights(self, market_data: List[Dict], news: List[Dict]) -> Dict:
        """
        Synthesize market data and news into actionable insights

        Args:
            market_data: List of market data dictionaries
            news: List of news article dictionaries

        Returns:
            Dictionary containing synthesized insights
        """
        # Format market data for the agent
        market_summary = json.dumps(market_data, indent=2)[:1000]

        # Format news for the agent
        news_summary = json.dumps(news[:20], indent=2)[:1500]

        prompt = f"""You are a financial market analysis agent with extensive knowledge of equities, commodities, currencies, and market sentiment.

TASK: Analyze the following market data and news, then synthesize actionable insights.

MARKET DATA:
{market_summary}

RECENT NEWS:
{news_summary}

CONTEXT:
Current analysis needs to consider global market conditions and provide strategic recommendations.

YOUR RESPONSIBILITIES:
1. Identify significant price movements across assets
2. Correlate news events with market movements
3. Extract key themes and opportunities
4. Prioritize insights by impact and urgency
5. Provide specific, actionable recommendations

OUTPUT FORMAT (JSON):
{{
    "summary": "Brief executive summary of market conditions (1-2 sentences)",
    "market_sentiment": "OVERALL sentiment (BULLISH/BEARISH/NEUTRAL)",
    "key_findings": [
        {{
            "category": "price_action|market_sentiment|sector_rotation|macro|cross_market",
            "symbol": "Asset symbol or 'Market-Wide'",
            "description": "Clear, concise insight (2-3 sentences)",
            "confidence": 0-100,
            "priority": "high|medium|low",
            "action": "Specific recommendation or observation",
            "secondary_data": "Additional context if relevant"
        }}
    ],
    "opportunities": [
        {{
            "asset": "Asset symbol",
            "opportunity": "Description of opportunity",
            "risk": "Primary risk factor",
            "confidence": 0-100
        }}
    ],
    "risks": [
        {{
            "asset": "Asset symbol or 'Market'",
            "risk": "Description of emerging risk",
            "likelihood": "low|medium|high"
        }}
    ],
    "market_breadth": "Description of market participation and breadth indicators"
}}

Provide your analysis in JSON format only."""

        response = self.call(prompt, timeout=180)

        try:
            # Parse the JSON response
            insights_data = json.loads(response)
            return insights_data
        except json.JSONDecodeError as e:
            print(f"Failed to parse agent response as JSON: {e}")
            print(f"Got response: {response[:500] if len(response) > 500 else response}")
            return {
                "summary": "Analysis completed",
                "market_sentiment": "NEUTRAL",
                "key_findings": [],
                "opportunities": [],
                "risks": [],
                "market_breadth": "Incomplete analysis"
            }

class InsightGenerator:
    def __init__(self):
        self.sentiment_keywords = {
            'bullish': ['surge', 'jump', 'rise', 'gain', 'soar', 'climb', 'record', 'beat', 'strong', 'positive', 'win'],
            'bearish': ['drop', 'decline', 'fall', 'loss', 'plummet', 'crash', 'weak', 'negative', 'sell', 'risk'],
            'neutral': [['stalled', 'flat', 'paused', 'holding'], ['trending', 'moving', 'fluctuating'], ['slight', 'moderate']]
        }
        self.glm_agent = LocalGLMAgent(model_path=os.getenv("GLM_MODEL_PATH"))

    def generate_insights(self, market_data: List[Dict], news: List[Dict], current_context: str) -> List[Dict]:
        """Generate actionable insights from market data and news using agent-based synthesis"""
        try:
            insights_data = self.glm_agent.synthesize_insights(market_data, news)

            insights = []

            # Add key findings
            for finding in insights_data.get('key_findings', []):
                insights.append({
                    'id': f'insight-{int(datetime.now().timestamp())}-{hash(finding.get("description", ""))}',
                    'symbol': finding.get('symbol', 'Market-Wide'),
                    'description': finding.get('description', ''),
                    'category': finding.get('category', 'General'),
                    'priority': finding.get('priority', 'medium'),
                    'impact_score': round(finding.get('confidence', 50) / 10, 1),
                    'current_price': None,
                    'news_count': 0,
                    'news_summary': finding.get('action', ''),
                    'secondary_data': finding.get('secondary_data', ''),
                    'context': current_context
                })

            # Add opportunities
            for opportunity in insights_data.get('opportunities', []):
                insight = {
                    'id': f'opportunity-{int(datetime.now().timestamp())}-{hash(opportunity.get("opportunity", ""))}',
                    'symbol': opportunity.get('asset', 'Market'),
                    'description': opportunity.get('opportunity', ''),
                    'action_item': opportunity.get('opportunity', ''),
                    'category': 'Opportunity',
                    'priority': 'medium',
                    'impact_score': round(opportunity.get('confidence', 50) / 10, 1),
                    'current_price': None,
                    'news_count': 0,
                    'news_summary': opportunity.get('opportunity', ''),
                    'secondary_data': opportunity.get('risk', ''),
                    'context': current_context
                }
                insights.append(insight)

            # Add risks
            for risk in insights_data.get('risks', []):
                insight = {
                    'id': f'risk-{int(datetime.now().timestamp())}-{hash(risk.get("risk", ""))}',
                    'symbol': risk.get('asset', 'Market'),
                    'description': f"RISK: {risk.get('risk', '')}",
                    'category': 'Risk',
                    'priority': 'high' if risk.get('likelihood') == 'high' else 'medium',
                    'impact_score': round(100 - risk.get('likelihood', 'medium') + 30, 1),
                    'current_price': None,
                    'news_count': 0,
                    'news_summary': risk.get('risk', ''),
                    'secondary_data': f"Likelihood: {risk.get('likelihood').upper()}",
                    'context': current_context
                }
                insights.append(insight)

            return insights

        except Exception as e:
            print(f"Error in agent-based insight generation: {e}")
            # Fallback to basic method if agent fails
            return self._generate_basic_insights(market_data, news, current_context)

    def _generate_market_insights(self, market_data: List[Dict]) -> List[Dict]:
        """Generate insights from market price movements"""
        insights = []

        for item in market_data:
            symbol = item.get('symbol', '').upper()
            change_percent = item.get('change_percent') or 0

            # Identify significant movements
            if abs(change_percent) >= 2.0:
                sentiment = 'bullish' if change_percent > 0 else 'bearish'
                trend = 'strong' if abs(change_percent) >= 5.0 else 'moderate'

                insights.append({
                    'id': f'mkt-{symbol}-{int(datetime.now().timestamp())}',
                    'symbol': symbol,
                    'description': f"<http://finance.yahoo.com/quote/{symbol}|{symbol}> is experiencing a {trend} {sentiment} move of {abs(change_percent):.2f}%",
                    'category': 'Price Action',
                    'priority': 'high' if abs(change_percent) >= 5.0 else 'medium',
                    'impact_score': self._calculate_impact_score(abs(change_percent), item.get('volume', 0)),
                    'current_price': item.get('price'),
                    'news_count': 0,
                    'context': 'daily'
                })

            # Market breadth indicators
            if symbol == 'VIX':
                vix = change_percent
                trend = 'strong' if abs(change_percent) >= 5.0 else 'moderate'
                sentiment = 'bullish' if change_percent > 0 else 'bearish'
                insights.append({
                    'id': f'vix-{int(datetime.now().timestamp())}',
                    'symbol': 'VIX',
                    'description': f"<http://finance.yahoo.com/quote/VIX|VIX> {trend.lower()} {sentiment} at {abs(vix):.2f}% - {self._interpret_vix(vix)}",
                    'category': 'Market Sentiment',
                    'priority': 'high' if abs(vix) >= 15 else 'medium',
                    'impact_score': self._calculate_impact_score(abs(vix), item.get('volume', 0)),
                    'current_price': item.get('price'),
                    'news_count': 0,
                    'context': 'daily'
                })

            # Sector rotation insights
            if symbol in ['GLD', 'TLT', 'GDX']:
                safe_haven_buying = symbol == 'GLD'
                insights.append({
                    'id': f'sector-{int(datetime.now().timestamp())}',
                    'symbol': symbol,
                    'description': f"<http://finance.yahoo.com/quote/{symbol}|{symbol}> movement indicates {"safe-haven buying" if safe_haven_buying else "interest rate opportunities"}",
                    'category': 'Portfolio Rotation',
                    'priority': 'medium',
                    'impact_score': 4,
                    'current_price': item.get('price'),
                    'news_count': 0,
                    'context': 'daily'
                })

        return insights

    def _generate_news_insights(self, market_data: List[Dict], news: List[Dict], current_context: str) -> List[Dict]:
        """Generate insights from news articles"""
        insights = []

        # Look for correlations between news and market movements
        for news_item in news[:15]:  # Limit news items
            title = news_item.get('title', '').lower()
            summary = news_item.get('summary', '').lower()

            # Identify key financial themes in news
            if any(word for word in self._get_stock_price_keywords(summary)):
                insights.append({
                    'id': f'news-{int(datetime.now().timestamp())}',
                    'symbol': 'Market-Wide',
                    'description': f"<{news_item.get('link', '#')}|*{news_item.get('title', 'Market Update')}*>",
                    'category': news_item.get('category', 'General'),
                    'priority': 'medium',
                    'impact_score': self._calculate_news_impact(news_item),
                    'current_price': None,
                    'news_count': 1,
                    'news_summary': news_item.get('title'),
                    'context': current_context
                })

            # Currency and commodity news
            if any(word in title for word in ['euro', 'dollar', 'pound', 'yen', 'crypto', 'bitcoin', 'gold', 'oil']):
                insights.append({
                    'id': f'news-currency-{int(datetime.now().timestamp())}',
                    'symbol': 'Currency-Alt',
                    'description': f"<{news_item.get('link', '#')}|*Currency/Commodity Update*>: {news_item.get('title', 'Market News')}",
                    'category': 'Macro',
                    'priority': 'low',
                    'impact_score': 2,
                    'current_price': None,
                    'news_count': 1,
                    'news_summary': news_item.get('title'),
                    'context': current_context
                })

        return insights

    def _deduplicate_insights(self, insights: List[Dict]) -> List[Dict]:
        """Deduplicate insights and consolidate related ones"""
        unique_insights = {}
        seen_symbols = set()

        for insight in insights:
            symbol = insight.get('symbol', 'Market-Wide')
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            unique_insights[symbol] = insight

        return list(unique_insights.values())

    def _get_stock_price_keywords(self, text: str) -> List[str]:
        """Extract stock-related keywords from text"""
        keywords = []
        for keyword in ['stock', 'market', 'rise', 'fall', 'plunge', 'surge', 'gain', 'loss']:
            if keyword in text:
                keywords.append(keyword)
        return keywords

    def _calculate_impact_score(self, movement: float, volume: Optional[float] = None) -> float:
        """Calculate impact score for market movements"""
        base_score = movement * 0.5
        if volume is None:
            volume = 0

        if volume > 1000000:  # High volume multiplier
            base_score *= 1.5

        return min(base_score, 10)  # Cap at 10

    def _calculate_news_impact(self, news_item: Dict) -> float:
        """Calculate impact score for news items"""
        title = news_item.get('title', '').lower()
        impact_score = 3  # Base score for news

        # Boost scores for high-impact keywords
        if 'fed' in title or 'cpi' in title or 'nfp' in title:
            impact_score += 3
        if any(word in title for word in ['crisis', 'explosion', 'breakthrough', 'boycott']):
            impact_score += 2
        if any(word in title for word in ['earnings', 'revenue', 'profit']):
            impact_score += 2

        return min(impact_score, 10)

    def _interpret_vix(self, vix_change: float) -> str:
        """Interpret VIX movement"""
        if abs(vix_change) < 3:
            return "stable sentiment"
        elif vix_change > 0:
            return "increased fear/volatility"
        else:
            return "decreased fear/volatility"

    def _get_sentiment(self, text: str) -> str:
        """Determine sentiment from text"""
        sentiment_keywords = {
            'bullish': ['surge', 'jump', 'rise', 'gain', 'soar', 'climb', 'record', 'beat', 'strong', 'positive', 'win'],
            'bearish': ['drop', 'decline', 'fall', 'loss', 'plummet', 'crash', 'weak', 'negative', 'sell', 'risk'],
            'neutral': ['stalled', 'flat', 'paused', 'holding', 'trending', 'moving', 'fluctuating', 'slight', 'moderate']
        }

        text_lower = text.lower()
        bullish_count = sum(1 for wordlist in sentiment_keywords['bullish'] if wordlist in text_lower)
        bearish_count = sum(1 for wordlist in sentiment_keywords['bearish'] if wordlist in text_lower)

        if bullish_count > bearish_count:
            return 'positive'
        elif bearish_count > bullish_count:
            return 'negative'
        else:
            return 'neutral'

    def _generate_basic_insights(self, market_data: List[Dict], news: List[Dict], current_context: str) -> List[Dict]:
        """Fallback basic insight generation when agent fails"""
        insights = []

        # Generate basic market insights
        for item in market_data:
                symbol = item.get('symbol', '').upper()
                change_percent = item.get('change_percent') or 0

                if abs(change_percent) >= 2.0:
                    sentiment = 'bullish' if change_percent > 0 else 'bearish'
                    trend = 'strong' if abs(change_percent) >= 5.0 else 'moderate'

                    insights.append({
                        'id': f'mkt-{symbol}-{int(datetime.now().timestamp())}',
                        'symbol': symbol,
                        'description': f"<http://finance.yahoo.com/quote/{symbol}|{symbol}> is experiencing a {trend} {sentiment} move of {abs(change_percent):.2f}%",
                        'category': 'Price Action',
                        'priority': 'high' if abs(change_percent) >= 5.0 else 'medium',
                        'impact_score': self._calculate_impact_score(abs(change_percent), item.get('volume')),
                        'current_price': item.get('price'),
                        'news_count': 0,
                        'news_summary': '',
                        'secondary_data': '',
                        'context': 'daily'
                    })

        # Generate basic news insights
        for news_item in news[:10]:
            title = news_item.get('title', '')
            summary = news_item.get('summary', '')

            if title:
                insights.append({
                    'id': f'news-{int(datetime.now().timestamp())}',
                    'symbol': 'Market-Wide',
                    'description': f"<{news_item.get('link', '#')}|*{title}*>",
                    'category': news_item.get('category', 'General'),
                    'priority': 'medium',
                    'impact_score': self._calculate_news_impact(news_item),
                    'current_price': None,
                    'news_count': 1,
                    'news_summary': title,
                    'secondary_data': '',
                    'context': current_context
                })

        return insights[:20]  # Limit to 20 insights
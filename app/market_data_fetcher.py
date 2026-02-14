import yfinance as yf
from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MarketDataFetcher:
    def __init__(self):
        self.assets = []
        self.commodities = []
        self.load_config()

    def load_config(self):
        """Load asset configurations"""
        try:
            with open('/Users/studio/answerlayer/asset-monitor/assets.txt', 'r') as f:
                self.assets = [line.strip() for line in f if line.strip()]

            with open('/Users/studio/answerlayer/asset-monitor/commodities.txt', 'r') as f:
                self.commodities = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading config: {e}")

    def fetch_all(self) -> List[Dict]:
        """Fetch market data for all assets"""
        all_data = []
        all_assets = self.assets + self.commodities

        for symbol in all_assets:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if info and info.get('currentPrice') or info.get('regularMarketPrice'):
                    asset_type = self._determine_asset_type(symbol)
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    daily_change = info.get('regularMarketChange')
                    daily_change_pct = info.get('regularMarketChangePercent')

                    result = {
                        "symbol": symbol,
                        "asset_type": asset_type,
                        "price": current_price,
                        "change": daily_change,
                        "change_percent": daily_change_pct,
                        "high": info.get('dayHigh'),
                        "low": info.get('dayLow'),
                        "volume": info.get('volume'),
                        "market_cap": info.get('marketCap'),
                        "52_week_high": info.get('fiftyTwoWeekHigh'),
                        "52_week_low": info.get('fiftyTwoWeekLow'),
                        "last_updated": datetime.now().isoformat()
                    }

                    # Fetch and calculate historical metrics
                    if asset_type != 'commodity':
                        historical_data = self._calculate_historical_metrics(symbol, current_price, info.get('regularMarketVolume', 0))
                        result.update(historical_data)

                    all_data.append(result)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")

        return all_data

    def fetch_historical(self, symbol: str, period: str = '1mo') -> pd.DataFrame:
        """Fetch historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            return df
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def _determine_asset_type(self, symbol: str) -> str:
        """Determine asset type based on symbol"""
        if any(x in symbol for x in ['BTC', 'ETH', 'coin']):
            return 'cryptocurrency'
        elif symbol in ['GOLD', 'SILVER']:
            return 'commodity'
        elif symbol.endswith('=X'):
            return 'forex'
        elif symbol.endswith('ETFS') or symbol.endswith('ETF'):
            return 'eqty-etf'
        else:
            return 'equity'

    def get_sector_performance(self) -> Dict:
        """Get sector performance metrics"""
        sectors = {
            'Tech': self._get_sector_data('XLK'),
            'Finance': self._get_sector_data('XLF'),
            'Energy': self._get_sector_data('XLE'),
            'Health': self._get_sector_data('XLV')
        }
        return sectors

    def _get_sector_data(self, symbol: str) -> Dict:
        """Get data for a sector ETF"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "price": info.get('currentPrice', 0),
                "change": info.get('regularMarketChange', 0),
                "change_percent": info.get('regularMarketChangePercent', 0)
            }
        except:
            return {}

    def _calculate_historical_metrics(self, symbol: str, current_price: float = None, current_volume: int = 0) -> Dict:
        """Calculate historical metrics for context-aware market analysis"""
        try:
            df = self.fetch_historical(symbol, period='5d')

            if df.empty:
                return {
                    "7d_high": None,
                    "7d_low": None,
                    "7d_avg": None,
                    "30d_avg": None,
                    "7d_trend": None,
                    "7d_volume_avg": None,
                    "7d_volume变动": None
                }

            data = df.tail(7)

            current_price = current_price if current_price else data['Close'].iloc[-1]
            price_change_7d = data['Close'].iloc[-1] - data['Open'].iloc[0]
            price_change_pct_7d = (data['Close'].iloc[-1] - data['Open'].iloc[0]) / data['Open'].iloc[0] * 100

            if current_volume > 0:
                avg_volume = int(current_volume / 7)
                volume_change_pct = (current_volume - avg_volume) / avg_volume * 100
            else:
                avg_volume = current_volume
                volume_change_pct = 0

            return {
                "7d_high": float(data['High'].max()),
                "7d_low": float(data['Low'].min()),
                "7d_avg": float(data['Close'].mean()),
                "30d_avg": float(df['Close'].mean()),
                "7d_trend": float(price_change_pct_7d),
                "7d_volume_avg": int(avg_volume),
                "7d_volume变动": float(volume_change_pct)
            }
        except Exception as e:
            print(f"Error calculating historical metrics for {symbol}: {e}")
            return {
                "7d_high": None,
                "7d_low": None,
                "7d_avg": None,
                "30d_avg": None,
                "7d_trend": None,
                "7d_volume_avg": None,
                "7d_volume变动": None
            }
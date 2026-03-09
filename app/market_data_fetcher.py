import os
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
            import os as _os
            assets_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'assets.txt')
            with open(assets_path, 'r') as f:
                self.assets = [line.strip() for line in f if line.strip()]

            # commodities.txt has been removed - only equities are tracked
            self.commodities = []
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

                    # Add simple moving averages from stored OHLCV data
                    result.update(self.calculate_smas(symbol))

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
                    "7d_volume_change": None
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
                "7d_volume_change": float(volume_change_pct)
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
                "7d_volume_change": None
            }

    SMA_PERIODS = (8, 21, 50, 100, 200)

    def calculate_smas(self, symbol: str, data_dir: str = None) -> Dict:
        """Calculate simple moving averages from the stored OHLCV CSV.

        Returns dict like {"sma_8": 602.3, "sma_21": 598.1, ...}.
        Missing values (not enough data) are None.
        """
        if data_dir is None:
            data_dir = self._data_dir()
        path = os.path.join(data_dir, f"{symbol}.csv")
        result = {f"sma_{p}": None for p in self.SMA_PERIODS}
        try:
            if not os.path.exists(path):
                return result
            df = pd.read_csv(path, parse_dates=['Date'], index_col='Date')
            closes = df['Close']
            for p in self.SMA_PERIODS:
                if len(closes) >= p:
                    result[f"sma_{p}"] = round(float(closes.iloc[-p:].mean()), 4)
        except Exception as e:
            print(f"  Error calculating SMAs for {symbol}: {e}")
        return result

    def fetch_historical_ohlcv(self, symbol: str, period: str = '1y') -> pd.DataFrame:
        """Fetch daily OHLCV data for a symbol.

        Args:
            symbol: Ticker symbol
            period: yfinance period string (e.g. '1y', '2y', '5y')

        Returns:
            DataFrame with Date, Open, High, Low, Close, Volume columns
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval='1d')
            if df.empty:
                print(f"  No historical data returned for {symbol}")
                return pd.DataFrame()
            # Keep only OHLCV columns and reset the DatetimeIndex to a column
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.index = df.index.tz_localize(None)  # drop tz for clean CSV dates
            df.index.name = 'Date'
            return df
        except Exception as e:
            print(f"  Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def _data_dir(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

    def fetch_all_historical(self, period: str = '1y', data_dir: str = None) -> Dict[str, str]:
        """Download daily OHLCV for every tracked asset and save as CSV.

        Args:
            period: yfinance period string (default '1y')
            data_dir: Directory to write CSVs into (default: <project>/data/)

        Returns:
            Dict mapping symbol -> csv file path
        """
        if data_dir is None:
            data_dir = self._data_dir()
        os.makedirs(data_dir, exist_ok=True)

        results = {}
        all_assets = self.assets + self.commodities
        for symbol in all_assets:
            print(f"Fetching {period} daily OHLCV for {symbol}...")
            df = self.fetch_historical_ohlcv(symbol, period=period)
            if df.empty:
                continue
            path = os.path.join(data_dir, f"{symbol}.csv")
            df.to_csv(path)
            results[symbol] = path
            print(f"  {symbol}: {len(df)} rows -> {path}")
        return results

    def update_historical(self, data_dir: str = None) -> Dict[str, int]:
        """Append new trading days to existing OHLCV CSVs.

        Reads each CSV, finds the last date, fetches recent data from
        yfinance, and appends only rows newer than what we already have.
        If a CSV doesn't exist yet, downloads the full year.

        Returns:
            Dict mapping symbol -> number of new rows appended
        """
        if data_dir is None:
            data_dir = self._data_dir()
        os.makedirs(data_dir, exist_ok=True)

        updated = {}
        all_assets = self.assets + self.commodities
        for symbol in all_assets:
            path = os.path.join(data_dir, f"{symbol}.csv")
            try:
                if not os.path.exists(path):
                    # No file yet — do a full 1y download
                    print(f"  {symbol}: no CSV found, fetching 1y...")
                    df = self.fetch_historical_ohlcv(symbol, period='1y')
                    if not df.empty:
                        df.to_csv(path)
                        updated[symbol] = len(df)
                        print(f"  {symbol}: wrote {len(df)} rows (new file)")
                    continue

                existing = pd.read_csv(path, parse_dates=['Date'], index_col='Date')
                last_date = existing.index.max()

                # Fetch last 5 trading days — enough to cover weekends/holidays
                fresh = self.fetch_historical_ohlcv(symbol, period='5d')
                if fresh.empty:
                    updated[symbol] = 0
                    continue

                new_rows = fresh[fresh.index > last_date]
                if new_rows.empty:
                    updated[symbol] = 0
                    continue

                combined = pd.concat([existing, new_rows])
                combined.to_csv(path)
                updated[symbol] = len(new_rows)
                print(f"  {symbol}: +{len(new_rows)} rows (through {new_rows.index.max().date()})")

            except Exception as e:
                print(f"  {symbol}: error updating — {e}")
                updated[symbol] = 0

        return updated

    def fetch_intraday(self, interval: str = '5m') -> List[Dict]:
        """Fetch today's intraday bars for all tracked assets.

        Returns list of dicts with symbol, time, open, high, low, close, volume.
        """
        all_assets = self.assets + self.commodities
        rows = []
        for symbol in all_assets:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='1d', interval=interval)
                if df.empty:
                    continue
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                df.index = df.index.tz_localize(None)
                for ts, row in df.iterrows():
                    rows.append({
                        'symbol': symbol,
                        'time': ts,
                        'open': row['Open'],
                        'high': row['High'],
                        'low': row['Low'],
                        'close': row['Close'],
                        'volume': int(row['Volume']),
                    })
            except Exception as e:
                print(f"  Error fetching intraday for {symbol}: {e}")
        return rows
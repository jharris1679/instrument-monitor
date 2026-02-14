from fastapi import FastAPI
import yfinance as yf

app = FastAPI(title="Asset Monitor")

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Asset Monitor",
        "version": "1.0.0"
    }

@app.get("/market-data")
async def get_market_data():
    """Fetch current market data for all configured assets"""
    assets = []
    try:
        with open('/Users/studio/answerlayer/instrument-monitor/assets.txt', 'r') as f:
            equities = [line.strip() for line in f if line.strip()]

        # commodities.txt is removed, no longer used

        all_assets = equities

        for symbol in all_assets:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                assets.append({
                    "symbol": symbol,
                    "price": info.get('currentPrice') or info.get('regularMarketPrice'),
                    "change": info.get('regularMarketChange'),
                    "change_percent": info.get('regularMarketChangePercent'),
                    "high": info.get('dayHigh'),
                    "low": info.get('dayLow'),
                    "volume": info.get('volume'),
                    "last_updated": info.get('lastUpdate') or info.get('previousClose')
                })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")

        return {
            "status": "success",
            "data": assets,
            "count": len(assets)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
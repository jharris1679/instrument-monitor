## How to Run Instrument Monitor

### Quick Commands

**To get an instant analysis:**
```bash
cd /Users/studio/answerlayer/instrument-monitor
python3 run_analysis.py
```

**To start the API server (port 8001):**
```bash
cd /Users/studio/answerlayer/instrument-monitor
python3 app/main.py
```

Then visit: http://localhost:8001

**To install dependencies (first time):**
```bash
cd /Users/studio/answerlayer/instrument-monitor
pip3 install -r requirements.txt
```

**External Dependencies Required:**
- **MLX Server**: Must be running on `http://localhost:8082` (using GLM-4.7 Flash model)
- **Slack Webhook**: Set in `.env` file for notifications

### Current Status

**Model**: ✅ Fully operational (GLM-4.7 Flash)
**Market Data API**: ⚠️ experiencing issues (Yahoo Finance returning 404s)
**RSS Processing**: ⏸️ not tested
**Insight Generation**: ⏸️ depends on successful market data fetch

### What to Expect

The system will:
1. Fetch current market data from configured instruments
2. Fetch news from RSS feeds
3. Generate AI-powered insights using the GLM-4.7 Flash model
4. Display prioritized insights (High/Medium/Low)

### Troubleshooting

If Yahoo Finance fails with 404 errors, possible causes:
- API rate limiting
- Temporary service issues
- Market hours only (check during NYSE/NASDAQ hours)

**Suggested**: Try running during US trading hours (9:30 AM - 4:00 PM EST)
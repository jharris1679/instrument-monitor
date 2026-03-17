## How to Run Instrument Monitor

### Prerequisites

- **Python 3.11+** with dependencies: `pip3 install -r requirements.txt`
- **MLX Server** running at `http://localhost:8082` with a loaded language model (GLM-4.7 Flash or equivalent)
- **`.env` file** with `SLACK_TOKEN` and `SLACK_CHANNEL` set (optional — Slack notifications are skipped if not configured)

### Commands

**Start the scheduler (production mode — runs indefinitely):**
```bash
cd /Users/studio/answerlayer/instrument-monitor
python3 run_scheduler.py
```
Sends briefings at 09:00, 12:00, 15:00, 21:00 on weekdays and 09:00 on weekends. Updates OHLCV CSVs at 08:00 daily.

**One-shot briefing to stdout:**
```bash
python3 run_analysis.py
```
Fetches data, generates a briefing, and prints it. Does not send to Slack.

**Integration test:**
```bash
python3 test_pipeline.py
```
Runs through RSS fetch, market data fetch, and briefing generation. Prints results to stdout.

**FastAPI server (port 8001):**
```bash
python3 app/main.py
```
Exposes `/market-data` endpoint for current prices.

### Current Status

All systems operational:

- **Market data**: 14 standard assets in `assets.txt` (SPY, QQQ, GLD, TLT, IWM, MAGS, IGV, IBIT, CORN, DBA, SOYB, WEAT, UUP, USO) + supplementary assets discovered by the model
- **RSS processing**: Fetches from feeds listed in `rss_sources/financial.feeds`
- **Insight generation**: Two-phase DSPy RLM pipeline with DuckDB exploration and prose synthesis
- **Slack integration**: Sends formatted briefings with Block Kit (requires `SLACK_TOKEN` in `.env`)
- **Scheduler**: All time slots operational (pre-market, intraday x2, post-market, weekend)

### Troubleshooting

- **MLX server not running**: You'll see a connection error at startup when DSPy tries to query `/models`. Start the MLX server first.
- **yfinance failures**: Some symbols may fail intermittently. The fetcher retries twice with backoff and creates stub entries for persistent failures.
- **No Slack messages**: Check that `SLACK_TOKEN` and `SLACK_CHANNEL` are set in `.env`. The notifier silently skips if unconfigured.

See `ARCHITECTURE.md` for full system documentation.

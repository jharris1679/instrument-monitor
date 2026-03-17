# Instrument Monitor — Architecture

## Overview

Scheduled macro briefing pipeline using a two-phase DSPy RLM that explores market data via SQL, discovers new instruments on the fly, and delivers briefings to Slack. The system fetches OHLCV data from yfinance, loads it into an in-memory DuckDB, lets a ReAct-style language model explore freely via SQL tools, then synthesizes a prose briefing grounded in actual prices.

## Data Flow

```
Scheduler (schedule library)
  → MarketDataFetcher (yfinance) — current prices + SMA calculations from stored CSVs
  → RSSFeedProcessor (feedparser) — financial news from RSS feeds
  → InsightGenerator
      → MarketInsightGenerator (DSPy module):
          Phase 1: RLM explores DuckDB via query_db() + track_instrument() tools
          Phase 2: ChainOfThought synthesizes briefing from analysis + ground-truth price table
  → SlackNotifier (slack_sdk) — formatted briefing to Slack channel
```

Briefings are also persisted as JSON in `briefings/` for narrative continuity (last 3 are passed to Phase 2).

## Schedule

All times are local. Managed by `schedule` library in `run_scheduler.py`.

| Time  | Days      | Type         | Notes                                      |
|-------|-----------|--------------|---------------------------------------------|
| 08:00 | Daily     | Data update  | Update OHLCV CSVs (`update_historical`)     |
| 09:00 | Weekdays  | PRE-MARKET   | Prices are prior close                      |
| 12:00 | Weekdays  | INTRADAY     | Includes 5-min bars, prices are live        |
| 15:00 | Weekdays  | INTRADAY     | Includes 5-min bars, prices are live        |
| 21:00 | Weekdays  | POST-MARKET  | Prices are today's close                    |
| 09:00 | Weekends  | WEEKEND      | Markets closed, focus on newsflow           |

## Asset Tracking

- `assets.txt` — standard watchlist (14 symbols: SPY, QQQ, GLD, TLT, IWM, MAGS, IGV, IBIT, CORN, DBA, SOYB, WEAT, UUP, USO). Always fetched.
- `supplementary_assets.txt` — model-discovered tickers (persisted across runs, fetched on-demand via `track_instrument()` during Phase 1).

## Module Reference

### `app/dspy_modules.py`
DuckDB setup and the two-phase DSPy pipeline. Creates the in-memory database (`create_market_db`) with tables for market snapshots, OHLCV history, intraday bars, and news. Defines `query_db()` and `track_instrument()` as tools for the Phase 1 RLM. `AnalysisSignature` (Phase 1) lets the model explore data via SQL with up to 12 iterations. `BriefingSignature` (Phase 2) is a ChainOfThought that produces prose + sources + opportunity calls grounded in the price table. `MarketInsightGenerator` orchestrates both phases and rebuilds the price table from DuckDB after Phase 1 so discovered instruments appear in synthesis.

### `app/insight_generator.py`
DSPy/LM configuration (connects to local MLX server via OpenAI-compatible API). Manages prior briefing loading from `briefings/*.json` and briefing persistence. `InsightGenerator` class wraps `MarketInsightGenerator` and provides a `generate_briefing()` method with fallback to basic summary if DSPy fails.

### `app/market_data_fetcher.py`
yfinance wrapper. `fetch_all()` fetches current prices for all tracked assets with retry logic. `calculate_smas()` computes 8/21/50/100/200-day SMAs from stored CSVs. `fetch_historical_ohlcv()` and `update_historical()` manage OHLCV CSV files. `fetch_intraday()` gets today's 5-min bars.

### `app/scheduler.py`
`MarketMonitor` class wires together all components. `run_report()` is the main entry point — fetches data, generates briefing, sends to Slack. `start_scheduled_reports()` sets up the schedule and runs the event loop. Includes `update_historical_data()` for the daily 08:00 CSV refresh. Weekend vs weekday logic is handled via `_is_weekend()`.

### `app/slack_notifier.py`
`send_update()` formats and sends briefings to Slack with Block Kit (header, prose sections, sources, discovered instruments). `send_alert()` sends critical priority alerts. `send_detailed_report()` sends comprehensive daily summaries. All methods gracefully no-op if `SLACK_TOKEN` is not set.

### `app/rss_processor.py`
Loads RSS feed URLs from `rss_sources/financial.feeds`. Fetches and parses feeds via `feedparser`, categorizes articles by keywords, sorts by publication date.

### `app/main.py`
FastAPI server (port 8001). Root endpoint returns service status. `/market-data` endpoint returns current prices for all tracked assets. Standalone entry point via uvicorn.

## Data Storage

```
data/*.csv                   — Daily OHLCV per symbol (updated at 08:00)
briefings/*.json             — Generated briefings with prose, sources, tracked_instruments, timestamp
rss_sources/financial.feeds  — RSS feed URLs (one per line, # comments supported)
assets.txt                   — Standard watchlist (one ticker per line)
supplementary_assets.txt     — Model-discovered tickers (appended automatically)
```

## DuckDB Schema (in-memory, rebuilt each run)

| Table            | Columns                                                                         |
|------------------|---------------------------------------------------------------------------------|
| market_snapshot  | symbol, price, change_pct, volume, sma_8, sma_21, sma_50, sma_100, sma_200, high_52w, low_52w, trend_7d |
| ohlcv            | symbol, date, open, high, low, close, volume                                    |
| intraday         | symbol, time, open, high, low, close, volume                                    |
| news             | title, summary, link, source, published                                         |

All tables are created even if empty (schema-only) so SQL queries never fail on missing tables.

## Instrument Discovery (`track_instrument`)

During Phase 1, the RLM can call `track_instrument(ticker)` to:

1. Fetch current price from yfinance
2. Fetch 3-month OHLCV history
3. Insert into DuckDB (`market_snapshot` + `ohlcv` tables)
4. Append ticker to `supplementary_assets.txt`

The data is immediately available for SQL queries in the same session. The price table for Phase 2 is rebuilt from DuckDB after Phase 1 completes, so discovered instruments appear in the briefing synthesis with accurate prices.

## Configuration

Environment variables (`.env` file):

| Variable          | Purpose                                      | Default              |
|-------------------|----------------------------------------------|----------------------|
| SLACK_TOKEN       | Slack Bot User OAuth Token                   | (required for Slack) |
| SLACK_CHANNEL     | Slack channel for briefings                  | #market-monitor      |
| RLMKIT_BASE_URL   | MLX server OpenAI-compatible API endpoint    | http://localhost:8082/v1 |

The MLX server must be running at `RLMKIT_BASE_URL` with a loaded model. The model ID is auto-detected via the `/models` endpoint at startup.

## Running

```bash
# Start the scheduler (runs indefinitely, sends briefings on schedule)
python3 run_scheduler.py

# One-shot briefing to stdout (no Slack)
python3 run_analysis.py

# Integration test
python3 test_pipeline.py

# FastAPI server (port 8001)
python3 app/main.py
```

## Key Design Decisions

- **Two-phase RLM**: Phase 1 explores freely via SQL tools (up to 12 iterations), Phase 2 synthesizes with ground-truth price table. This separates exploration from presentation and prevents hallucinated prices.
- **session_context**: Tells Phase 2 whether prices are stale (pre/post-market) or live (intraday), so the briefing frames data appropriately.
- **Price table rebuilt from DuckDB**: After Phase 1, so any instruments the model discovered via `track_instrument()` are included in the Phase 2 synthesis.
- **Briefing history**: Last 3 briefings passed for narrative continuity — the model references evolving themes and prior calls.
- **Fallback generation**: If DSPy/RLM fails, `_generate_basic_briefing()` produces a simple movers + headlines summary.
- **Retry with backoff**: `fetch_all()` retries failed symbols twice with 5s/15s delays before creating stub entries.

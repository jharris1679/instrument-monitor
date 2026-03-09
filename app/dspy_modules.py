import json
import os
from glob import glob

import dspy
import duckdb
import pandas as pd


# ---------------------------------------------------------------------------
# DuckDB infrastructure
# ---------------------------------------------------------------------------

_db: duckdb.DuckDBPyConnection | None = None


def query_db(sql: str) -> str:
    """Execute SQL against the market database and return results as a table.

    Available tables:
      market_snapshot — symbol, price, change_pct, volume, sma_8, sma_21,
                        sma_50, sma_100, sma_200, high_52w, low_52w, trend_7d
      ohlcv          — symbol, date, open, high, low, close, volume
      news           — title, summary, link, source, published

    Args:
        sql: A SQL query string.

    Returns:
        Tab-separated result table (capped at 200 rows), or an error message.
    """
    if _db is None:
        return "ERROR: database not initialised"
    try:
        rel = _db.execute(sql)
        cols = [desc[0] for desc in rel.description]
        rows = rel.fetchmany(200)
        lines = ["\t".join(str(c) for c in cols)]
        for row in rows:
            lines.append("\t".join(str(v) for v in row))
        return "\n".join(lines)
    except Exception as e:
        return f"SQL ERROR: {e}"


def create_market_db(
    market_data: list,
    news: list,
    data_dir: str,
    intraday: list | None = None,
) -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB with market_snapshot, ohlcv, and news tables."""
    db = duckdb.connect(":memory:")

    # -- market_snapshot --
    snapshot_rows = []
    for m in market_data:
        snapshot_rows.append({
            "symbol": m.get("symbol", ""),
            "price": m.get("price"),
            "change_pct": m.get("change_percent"),
            "volume": m.get("volume"),
            "sma_8": m.get("sma_8"),
            "sma_21": m.get("sma_21"),
            "sma_50": m.get("sma_50"),
            "sma_100": m.get("sma_100"),
            "sma_200": m.get("sma_200"),
            "high_52w": m.get("52_week_high"),
            "low_52w": m.get("52_week_low"),
            "trend_7d": str(m.get("7d_trend", "")),
        })
    if snapshot_rows:
        df_snap = pd.DataFrame(snapshot_rows)
        db.execute("CREATE TABLE market_snapshot AS SELECT * FROM df_snap")
    else:
        db.execute(
            "CREATE TABLE market_snapshot ("
            "symbol VARCHAR, price DOUBLE, change_pct DOUBLE, volume BIGINT, "
            "sma_8 DOUBLE, sma_21 DOUBLE, sma_50 DOUBLE, sma_100 DOUBLE, "
            "sma_200 DOUBLE, high_52w DOUBLE, low_52w DOUBLE, trend_7d VARCHAR)"
        )

    # -- ohlcv (all CSVs combined) --
    csv_files = sorted(glob(os.path.join(data_dir, "*.csv")))
    ohlcv_frames = []
    for csv_path in csv_files:
        sym = os.path.splitext(os.path.basename(csv_path))[0].upper()
        try:
            df = pd.read_csv(csv_path, parse_dates=["Date"])
            df = df.rename(columns={
                "Date": "date", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume",
            })
            df["symbol"] = sym
            ohlcv_frames.append(df[["symbol", "date", "open", "high", "low", "close", "volume"]])
        except Exception:
            continue
    if ohlcv_frames:
        df_ohlcv = pd.concat(ohlcv_frames, ignore_index=True)
        db.execute("CREATE TABLE ohlcv AS SELECT * FROM df_ohlcv")
    else:
        db.execute(
            "CREATE TABLE ohlcv ("
            "symbol VARCHAR, date TIMESTAMP, open DOUBLE, high DOUBLE, "
            "low DOUBLE, close DOUBLE, volume BIGINT)"
        )

    # -- news --
    news_rows = []
    for n in news:
        news_rows.append({
            "title": n.get("title", ""),
            "summary": n.get("summary", ""),
            "link": n.get("link", ""),
            "source": n.get("source", ""),
            "published": n.get("published", ""),
        })
    if news_rows:
        df_news = pd.DataFrame(news_rows)
        db.execute("CREATE TABLE news AS SELECT * FROM df_news")
    else:
        db.execute(
            "CREATE TABLE news ("
            "title VARCHAR, summary VARCHAR, link VARCHAR, "
            "source VARCHAR, published VARCHAR)"
        )

    # -- intraday (5-min bars for today, if provided) --
    if intraday:
        df_intra = pd.DataFrame(intraday)
        db.execute("CREATE TABLE intraday AS SELECT * FROM df_intra")
    else:
        db.execute(
            "CREATE TABLE intraday ("
            "symbol VARCHAR, time TIMESTAMP, open DOUBLE, high DOUBLE, "
            "low DOUBLE, close DOUBLE, volume BIGINT)"
        )

    return db


# ---------------------------------------------------------------------------
# Schema description passed to the RLM (compact, ~600 chars)
# ---------------------------------------------------------------------------

DB_SCHEMA = (
    "Tables in the database (query with query_db(sql)):\n"
    "  market_snapshot: symbol, price, change_pct, volume, "
    "sma_8, sma_21, sma_50, sma_100, sma_200, high_52w, low_52w, trend_7d\n"
    "  ohlcv: symbol, date, open, high, low, close, volume  "
    "(daily OHLCV history for all tracked symbols)\n"
    "  intraday: symbol, time, open, high, low, close, volume  "
    "(today's 5-min bars — use to see how the trading day is unfolding)\n"
    "  news: title, summary, link, source, published\n"
    "\n"
    "Example queries:\n"
    "  query_db(\"SELECT symbol, price, change_pct FROM market_snapshot ORDER BY change_pct DESC\")\n"
    "  query_db(\"SELECT * FROM ohlcv WHERE symbol='SPY' ORDER BY date DESC LIMIT 10\")\n"
    "  query_db(\"SELECT symbol, time, close FROM intraday WHERE symbol='SPY' ORDER BY time\")\n"
    "  query_db(\"SELECT title, source FROM news LIMIT 5\")\n"
)


# ---------------------------------------------------------------------------
# Phase 1: RLM explores and analyzes (output is free-form text)
# ---------------------------------------------------------------------------

class AnalysisSignature(dspy.Signature):
    """Macro strategist analyzing markets via SQL. Use query_db(sql) for ALL data access.

    IMPORTANT: Keep reasoning VERY brief (1-2 sentences). Write SHORT code blocks.
    Do NOT repeat data you already retrieved. Do NOT write long explanations.

    Workflow — one query per iteration, stay concise:
    1. query_db("SELECT symbol, price, change_pct, sma_50, sma_200 FROM market_snapshot ORDER BY change_pct")
    2. query_db("SELECT title, source FROM news LIMIT 10")
    3. query_db("SELECT * FROM ohlcv WHERE symbol='SPY' ORDER BY date DESC LIMIT 5")
    4. Synthesize: cross-asset signals, geopolitics, risk appetite, Fed/policy

    Focus: SPY/QQQ/IWM (equities), TLT (bonds), GLD/GOLD (gold), CORN (commodities).
    Use actual prices, SMA levels, percentage moves. Connect headlines to price action."""

    db_schema: str = dspy.InputField(
        desc="Database schema and example SQL queries for the query_db() tool"
    )

    analysis: str = dspy.OutputField(
        desc="Thorough macro analysis connecting geopolitical events, policy signals, and cross-asset price action"
    )


# ---------------------------------------------------------------------------
# Phase 2: ChainOfThought synthesizes a prose briefing from the analysis
# ---------------------------------------------------------------------------

class BriefingSignature(dspy.Signature):
    """Write a concise daily macro briefing — 2-3 short paragraphs, ~150-250 words,
    followed by 3 opportunity calls.

    Be dense and direct. Every sentence should carry information. No filler,
    no throat-clearing, no hedging. Use actual prices and levels.

    Structure: (1) dominant theme + key movers, (2) cross-asset signals and
    any contradictions, (3) one line on what to watch. Reference news articles
    only when they directly drive the narrative.

    You receive previous briefings for narrative continuity — reference how
    themes are evolving, whether prior calls played out, and what changed.
    Do NOT repeat the same analysis; build on it.

    End with "Opportunities:" followed by exactly 3 lines:
    - 1W: [specific instrument + direction + reasoning in one sentence]
    - 1M: [specific instrument + direction + reasoning in one sentence]
    - 3M: [specific instrument + direction + reasoning in one sentence]
    Be concrete — name the ticker, give a price target or level, explain why."""

    analysis: str = dspy.InputField(
        desc="Raw macro analysis with price data and cross-asset signals"
    )
    news_data: str = dspy.InputField(
        desc="JSON array of news articles with title, link, summary, source"
    )
    prior_briefings: str = dspy.InputField(
        desc="Previous 3 briefings (most recent first) for narrative continuity. May be empty if no prior briefings exist."
    )

    briefing: str = dspy.OutputField(
        desc="2-3 short paragraphs (150-250 words) + Opportunities section with 1W/1M/3M calls. Dense, opinionated, with specific prices. No bullet points in the prose section."
    )
    sources: str = dspy.OutputField(
        desc='JSON array of referenced articles: [{"title": "...", "link": "..."}]'
    )


# ---------------------------------------------------------------------------
# Two-phase module: RLM explore -> ChainOfThought synthesize
# ---------------------------------------------------------------------------

class MarketInsightGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.explore = dspy.RLM(
            AnalysisSignature,
            tools=[query_db],
            max_iterations=12,
            max_llm_calls=10,
            max_output_chars=10000,
            verbose=True,
        )
        self.synthesize = dspy.ChainOfThought(BriefingSignature)

    def forward(
        self,
        market_data: list,
        news_data: list,
        data_dir: str,
        intraday: list | None = None,
        prior_briefings: str = "",
    ) -> dspy.Prediction:
        global _db

        # Build the DuckDB and make it available to query_db()
        _db = create_market_db(market_data, news_data, data_dir, intraday=intraday)

        try:
            # Phase 1: RLM explores data via SQL, produces macro analysis
            exploration = self.explore(db_schema=DB_SCHEMA)
            analysis_text = getattr(exploration, "analysis", "")

            # If RLM produced a trajectory but no clean analysis field,
            # concatenate the trajectory outputs as the analysis
            if not analysis_text and hasattr(exploration, "trajectory"):
                parts = []
                for entry in exploration.trajectory:
                    if isinstance(entry, dict) and entry.get("output"):
                        parts.append(str(entry["output"]))
                analysis_text = "\n".join(parts) if parts else "No analysis produced"

            # Phase 2: ChainOfThought synthesizes prose briefing
            news_json = json.dumps(news_data[:15], default=str)
            result = self.synthesize(
                analysis=analysis_text,
                news_data=news_json,
                prior_briefings=prior_briefings or "No prior briefings yet.",
            )

            # Validate sources JSON
            try:
                json.loads(result.sources)
            except (json.JSONDecodeError, TypeError):
                result.sources = "[]"

            return result
        finally:
            _db.close()
            _db = None

from typing import List, Dict
from datetime import datetime
import json
import os
from glob import glob
from pathlib import Path

import dspy
from dotenv import load_dotenv

from app.dspy_modules import MarketInsightGenerator

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

# Configure DSPy to use local MLX server
def _get_model_id(base_url: str) -> str:
    """Query an MLX server's /models endpoint to get the loaded model ID."""
    import httpx
    try:
        resp = httpx.get(f"{base_url}/models", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("data", [])
        if models:
            return models[0]["id"]
    except Exception as e:
        print(f"Warning: could not query MLX models endpoint at {base_url}: {e}")
    return "default"


_base_url = os.getenv("RLMKIT_BASE_URL", "http://localhost:8082/v1")

lm = dspy.LM(
    model=f"openai/{_get_model_id(_base_url)}",
    api_base=_base_url,
    api_key="not-needed",
    max_tokens=4096,
    temperature=0.7,
)
dspy.configure(lm=lm)

_BRIEFINGS_DIR = str(Path(__file__).resolve().parent.parent / "briefings")


class InsightGenerator:
    def __init__(self):
        self.insight_module = MarketInsightGenerator()
        os.makedirs(_BRIEFINGS_DIR, exist_ok=True)

    def _load_prior_briefings(self, count: int = 3) -> str:
        """Load the most recent briefings as a single string for context."""
        files = sorted(glob(os.path.join(_BRIEFINGS_DIR, "*.json")), reverse=True)
        parts = []
        for f in files[:count]:
            try:
                with open(f) as fh:
                    data = json.load(fh)
                ts = data.get("generated_at", "unknown time")
                text = data.get("briefing", "")
                if text:
                    parts.append(f"--- {ts} ---\n{text}")
            except Exception:
                continue
        return "\n\n".join(parts)

    def _save_briefing(self, result: Dict):
        """Save briefing to disk for future reference."""
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(_BRIEFINGS_DIR, f"{ts}.json")
        try:
            with open(path, "w") as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: could not save briefing: {e}")

    def generate_briefing(self, market_data: List[Dict], news: List[Dict],
                          intraday: List[Dict] | None = None,
                          session_context: str = "") -> Dict:
        """Generate a macro briefing from market data and news using DSPy.

        Returns dict with 'briefing' (prose text) and 'sources' (list of articles).
        """
        data_dir = str(Path(__file__).resolve().parent.parent / "data")
        prior_briefings = self._load_prior_briefings()

        try:
            result = self.insight_module(
                market_data=market_data,
                news_data=news[:15],
                data_dir=data_dir,
                intraday=intraday,
                prior_briefings=prior_briefings,
                session_context=session_context,
            )

            briefing = getattr(result, 'briefing', '')
            sources = json.loads(getattr(result, 'sources', '[]'))

            if not briefing or len(briefing) < 50:
                print("DSPy returned empty briefing, falling back to basic summary")
                return self._generate_basic_briefing(market_data, news)

            output = {
                'briefing': briefing,
                'sources': sources,
                'generated_at': datetime.now().isoformat(),
            }
            self._save_briefing(output)
            return output

        except Exception as e:
            print(f"Error in DSPy briefing generation: {e}")
            return self._generate_basic_briefing(market_data, news)

    def _generate_basic_briefing(self, market_data: List[Dict], news: List[Dict]) -> Dict:
        """Fallback briefing when DSPy module fails."""
        movers = sorted(market_data, key=lambda x: abs(x.get('change_percent') or 0), reverse=True)
        lines = []
        if movers:
            top = movers[:3]
            parts = [f"{m['symbol']} {(m.get('change_percent') or 0):+.2f}%" for m in top]
            lines.append(f"Biggest movers today: {', '.join(parts)}.")
        if news:
            lines.append(f"\nTop headlines: " + "; ".join(n.get('title', '') for n in news[:5]) + ".")
        return {
            'briefing': "\n".join(lines) if lines else "No data available for briefing.",
            'sources': [{'title': n.get('title', ''), 'link': n.get('link', '')} for n in news[:5]],
            'generated_at': datetime.now().isoformat(),
        }

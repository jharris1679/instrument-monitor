#!/usr/bin/env python3
"""Start the market monitor scheduler (runs indefinitely)."""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scheduler import MarketMonitor

if __name__ == "__main__":
    monitor = MarketMonitor()
    monitor.start_scheduled_reports()

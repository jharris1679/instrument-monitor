#!/usr/bin/env python3
"""Test to verify ticker variable conflicts"""
import yfinance as yf

def test_ticker_conflict():
    ticker = yf.Ticker("AAPL")

    print(f"Ticker is Ticker class: {type(ticker).__name__}")
    print(f"Has history method: {hasattr(ticker, 'history')}")

    # Simulate assignment that might break it
    ticker.obj = "test"

    print(f"After assignment, has 'obj': {hasattr(ticker, 'obj')}")
    print(f"After assignment, has 'history': {hasattr(ticker, 'history')}")

if __name__ == "__main__":
    test_ticker_conflict()
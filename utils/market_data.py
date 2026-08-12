"""Cached Yahoo Finance access with partial-failure tolerance."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import yfinance as yf


def _close_series(raw: pd.DataFrame, ticker: str) -> pd.Series:
    """Extract one close series regardless of yfinance's column layout."""
    if raw.empty:
        return pd.Series(dtype=float)
    if isinstance(raw.columns, pd.MultiIndex):
        for candidate in ((ticker, "Close"), ("Close", ticker)):
            if candidate in raw.columns:
                return raw[candidate].dropna()
    if "Close" in raw:
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            if ticker in close:
                return close[ticker].dropna()
            return close.iloc[:, 0].dropna()
        return close.dropna()
    return pd.Series(dtype=float)


@st.cache_data(ttl=300, show_spinner=False)
def get_quotes(tickers: tuple[str, ...]) -> tuple[pd.DataFrame, str]:
    """Fetch current price and previous close for symbols in one Yahoo request."""
    if not tickers:
        return pd.DataFrame(columns=["ticker", "current_price", "previous_close"]), datetime.now(timezone.utc).isoformat()
    try:
        raw = yf.download(list(tickers), period="5d", interval="1d", progress=False, auto_adjust=False, group_by="ticker", threads=True)
        records = []
        for ticker in tickers:
            try:
                prices = _close_series(raw, ticker)
                if len(prices):
                    records.append({"ticker": ticker, "current_price": float(prices.iloc[-1]), "previous_close": float(prices.iloc[-2] if len(prices) > 1 else prices.iloc[-1])})
            except (KeyError, IndexError, TypeError):
                continue
        return pd.DataFrame(records, columns=["ticker", "current_price", "previous_close"]), datetime.now(timezone.utc).isoformat()
    except Exception:
        return pd.DataFrame(columns=["ticker", "current_price", "previous_close"]), datetime.now(timezone.utc).isoformat()


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(tickers: tuple[str, ...], start: str, end: str | None = None) -> pd.DataFrame:
    """Return a daily close matrix; unavailable symbols are omitted."""
    if not tickers:
        return pd.DataFrame()
    try:
        raw = yf.download(list(tickers), start=start, end=end, interval="1d", progress=False, auto_adjust=True, group_by="ticker", threads=True)
        if raw.empty:
            return pd.DataFrame()
        result = {ticker: _close_series(raw, ticker) for ticker in tickers}
        return pd.DataFrame({ticker: series for ticker, series in result.items() if not series.empty}).dropna(how="all")
    except Exception:
        return pd.DataFrame()


def refresh_market_cache() -> None:
    get_quotes.clear(); get_price_history.clear()

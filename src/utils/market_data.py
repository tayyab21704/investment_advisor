"""
market_data.py — Data helpers for Investment Council API.

Data sources (in priority order):
  1. nsepython — pulls directly from NSE India (no rate limiting, no API key)
  2. Twelve Data — fallback for BSE, intraday, fundamentals (free key from twelvedata.com)

Public functions (called by server.py and agent nodes):
  calculate_sma()            → used by server.py endpoints
  calculate_rsi()            → used by server.py endpoints
  get_regime()               → used by server.py endpoints
  hist_to_chart()            → used by server.py endpoints (nsepython DataFrame)
  fetch_tickers_parallel()   → used by server.py /sectors endpoint
  fetch_market_indicators()  → used by market_node.py agent
  fetch_sectoral_breadth()   → used by market_node.py agent

High-level helpers (new — can be used by server.py or future code):
  get_stock_quote()
  get_index_quote()
  get_stock_history()
  get_top_movers()
  get_sector_performance()
  get_stock_fundamentals()
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
IST = timezone("Asia/Kolkata")


# ─── TWELVE DATA CLIENT ───────────────────────────────────────────────────────

def _get_td_client():
    """Returns a configured TDClient instance."""
    from twelvedata import TDClient
    key = os.getenv("TWELVE_DATA_API_KEY", "")
    return TDClient(apikey=key)


# ─── DATE HELPERS ─────────────────────────────────────────────────────────────

def _nse_date(days_ago: int = 0) -> str:
    """Returns date string in DD-MM-YYYY format for nsepython."""
    d = datetime.now() - timedelta(days=days_ago)
    return d.strftime("%d-%m-%Y")


def _safe_float(val, default=None):
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        f = float(val)
        return round(f, 2) if f == f else default   # NaN check
    except Exception:
        return default


def _safe_int(val, default=0):
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return int(float(val))
    except Exception:
        return default


# ─── CHART CONVERTERS ────────────────────────────────────────────────────────

def hist_to_chart(df, tz: str = "Asia/Kolkata") -> List[Dict[str, Any]]:
    """
    Converts an nsepython equity_history DataFrame to OHLCV candle dicts.

    nsepython v2.97 equity_history columns:
      HistoricalDate, OPEN, HIGH, LOW, LTP/CLOSE, VOLUME (uppercase)

    Legacy nsepython columns (older):
      CH_TIMESTAMP, CH_OPENING_PRICE, CH_TRADE_HIGH_PRICE, CH_TRADE_LOW_PRICE,
      CH_CLOSING_PRICE, CH_TOT_TRADED_VAL

    Also accepts yfinance-style DataFrames (Open/High/Low/Close/Volume).
    """
    if df is None or (hasattr(df, 'empty') and df.empty):
        return []

    cols = set(df.columns)
    result = []

    # nsepython v2.97 equity_history format (uppercase columns)
    if "OPEN" in cols and "HIGH" in cols and "LOW" in cols:
        date_col = next((c for c in ("HistoricalDate", "TIMESTAMP", "Date") if c in cols), None)
        close_col = next((c for c in ("CLOSE", "LTP", "LAST_PRICE") if c in cols), None)
        # For index history, columns include 'SharesTraded' for volume
        vol_col   = next((c for c in ("TOTAL_TRADED_QUANTITY", "VOLUME", "VOL", "SharesTraded") if c in cols), None)
        for _, row in df.iterrows():
            try:
                result.append({
                    "timestamp": str(row[date_col]) if date_col else "",
                    "open":   _safe_float(row.get("OPEN",   0)),
                    "high":   _safe_float(row.get("HIGH",   0)),
                    "low":    _safe_float(row.get("LOW",    0)),
                    "close":  _safe_float(row[close_col])  if close_col else 0,
                    "volume": _safe_int(row[vol_col])      if vol_col   else 0,
                })
            except Exception:
                continue
        return sorted(result, key=lambda c: c["timestamp"])

    # Legacy nsepython format (CH_ prefix columns)
    nse_cols = {"CH_TIMESTAMP", "CH_CLOSING_PRICE", "CH_OPENING_PRICE"}
    if nse_cols.issubset(cols):
        for _, row in df.iterrows():
            try:
                result.append({
                    "timestamp": str(row.get("CH_TIMESTAMP", "")),
                    "open":   _safe_float(row.get("CH_OPENING_PRICE",   0)),
                    "high":   _safe_float(row.get("CH_TRADE_HIGH_PRICE", 0)),
                    "low":    _safe_float(row.get("CH_TRADE_LOW_PRICE",  0)),
                    "close":  _safe_float(row.get("CH_CLOSING_PRICE",   0)),
                    "volume": _safe_float(row.get("CH_TOT_TRADED_VAL",  0)),
                })
            except Exception:
                continue
        return result

    # Fallback: yfinance-style / DatetimeIndex DataFrame (Open/High/Low/Close/Volume)
    for idx, row in df.iterrows():
        try:
            ts = idx
            if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
                ts = ts.tz_convert(tz)
            elif hasattr(ts, "tz_localize"):
                ts = ts.tz_localize("UTC").tz_convert(tz)
            result.append({
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                "open":   _safe_float(row.get("Open")),
                "high":   _safe_float(row.get("High")),
                "low":    _safe_float(row.get("Low")),
                "close":  _safe_float(row.get("Close")),
                "volume": _safe_int(row.get("Volume")),
            })
        except Exception:
            continue
    return result


def td_to_chart(td_data: list) -> List[Dict[str, Any]]:
    """Converts Twelve Data time_series response to OHLCV list."""
    result = []
    for candle in (td_data or []):
        try:
            result.append({
                "timestamp": candle.get("datetime", ""),
                "open":   _safe_float(candle.get("open", 0)),
                "high":   _safe_float(candle.get("high", 0)),
                "low":    _safe_float(candle.get("low", 0)),
                "close":  _safe_float(candle.get("close", 0)),
                "volume": _safe_float(candle.get("volume", 0)),
            })
        except Exception:
            continue
    return result


def _df_from_td(td_candles: list) -> pd.DataFrame:
    """Convert Twelve Data candles to a pandas DataFrame with Open/High/Low/Close/Volume columns."""
    rows = []
    for c in (td_candles or []):
        try:
            rows.append({
                "Date":   c.get("datetime", ""),
                "Open":   float(c.get("open", 0)),
                "High":   float(c.get("high", 0)),
                "Low":    float(c.get("low", 0)),
                "Close":  float(c.get("close", 0)),
                "Volume": float(c.get("volume", 0)),
            })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    return df


# ─── INDICATOR CALCULATIONS ───────────────────────────────────────────────────

def calculate_sma(series, period: int) -> Optional[float]:
    """
    Returns the most recent SMA value.
    Accepts pd.Series or plain Python list.
    """
    if not hasattr(series, "__len__"):
        series = list(series)
    if len(series) < period:
        return None
    s = pd.Series(series) if not isinstance(series, pd.Series) else series
    val = s.rolling(window=period).mean().iloc[-1]
    return round(float(val), 2) if pd.notna(val) else None


def calculate_rsi(series, period: int = 14) -> Optional[float]:
    """
    Standard Wilder RSI calculation (0–100).
    Accepts pd.Series or plain list.
    """
    if not hasattr(series, "__len__"):
        series = list(series)
    if len(series) < period + 1:
        return None
    s = pd.Series(series) if not isinstance(series, pd.Series) else series
    delta    = s.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss.replace(0, float("inf"))
    rsi      = 100 - (100 / (1 + rs))
    val      = rsi.iloc[-1]
    return round(float(val), 2) if pd.notna(val) else None


def get_regime(price: float, sma_50: Optional[float]) -> tuple:
    """
    Returns (regime_string, confidence_0_to_1).
    regime: 'BULLISH' | 'NEUTRAL' | 'BEARISH'
    confidence: capped at 5% distance from SMA50.
    """
    if sma_50 is None or sma_50 == 0:
        return "NEUTRAL", 0.5
    pct_distance = ((price - sma_50) / sma_50) * 100
    if abs(pct_distance) < 0.5:
        regime = "NEUTRAL"
    elif pct_distance > 0:
        regime = "BULLISH"
    else:
        regime = "BEARISH"
    confidence = round(min(abs(pct_distance) / 5.0, 1.0), 3)
    return regime, confidence


# ─── CORE DATA FUNCTIONS ─────────────────────────────────────────────────────

def get_stock_quote(symbol: str) -> Optional[dict]:
    """
    Live quote for a single NSE stock.
    Primary: nsepython → fallback: Twelve Data.
    """
    # 1. nsepython
    try:
        from nsepython import nse_eq
        data = nse_eq(symbol)
        price_info = data.get("priceInfo", {})
        intraday   = price_info.get("intraDayHighLow", {})
        week       = price_info.get("weekHighLow", {})
        return {
            "symbol":        symbol,
            "current_price": _safe_float(price_info.get("lastPrice"), 0),
            "change":        _safe_float(price_info.get("change"), 0),
            "change_pct":    _safe_float(price_info.get("pChange"), 0),
            "day_high":      _safe_float(intraday.get("max"), 0),
            "day_low":       _safe_float(intraday.get("min"), 0),
            "year_high":     _safe_float(week.get("max"), 0),
            "year_low":      _safe_float(week.get("min"), 0),
            "prev_close":    _safe_float(price_info.get("previousClose"), 0),
            "open":          _safe_float(price_info.get("open"), 0),
            "volume":        _safe_float(data.get("preOpenMarket", {}).get("totalTradedVolume"), 0),
        }
    except Exception as e:
        logger.debug(f"[nsepython] get_stock_quote({symbol}) failed: {e}")

    # 2. Twelve Data fallback
    try:
        td = _get_td_client()
        result = td.quote(symbol=symbol, exchange="NSE").as_json()
        return {
            "symbol":        symbol,
            "current_price": _safe_float(result.get("close"), 0),
            "change":        _safe_float(result.get("change"), 0),
            "change_pct":    _safe_float(result.get("percent_change"), 0),
            "day_high":      _safe_float(result.get("high"), 0),
            "day_low":       _safe_float(result.get("low"), 0),
            "year_high":     _safe_float(result.get("fifty_two_week", {}).get("high"), 0),
            "year_low":      _safe_float(result.get("fifty_two_week", {}).get("low"), 0),
            "prev_close":    _safe_float(result.get("previous_close"), 0),
            "open":          _safe_float(result.get("open"), 0),
            "volume":        _safe_float(result.get("volume"), 0),
        }
    except Exception as e:
        logger.warning(f"[TwelveData] get_stock_quote({symbol}) failed: {e}")
        return None


def _nse_index_df():
    """
    Returns the full nsepython index DataFrame (cached lazily per call).
    nsepython v2.97: nse_index() takes 0 args, returns DataFrame with columns:
      indexName, last, change, percChange, high, low, previousClose, yearHigh, yearLow, open
    """
    from nsepython import nse_index
    return nse_index()


def _get_nse_index_row(index_name: str):
    """Fetch a single index row by its indexName from nsepython."""
    df = _nse_index_df()
    # Column name mappings across different nsepython versions
    name_col = next((c for c in df.columns if c.lower() in ("indexname", "key", "name")), None)
    if name_col is None:
        return None
    rows = df[df[name_col].str.strip() == index_name.strip()]
    if rows.empty:
        return None
    return rows.iloc[0]


def get_index_quote(index_name: str) -> Optional[dict]:
    """
    Live quote for an NSE/BSE index.
    'SENSEX' → Twelve Data (BSE); otherwise nsepython first.
    """
    # SENSEX lookup
    if "SENSEX" in index_name.upper():
        try:
            # Try nsepython index list first (rare for BSE but some versions had it)
            row = _get_nse_index_row("SENSEX")
            if row is not None:
                current = _safe_float(row.get("last", 0))
                change  = _safe_float(row.get("change", 0))
                pct     = _safe_float(row.get("percChange", row.get("pChange", 0)))
                return {
                    "symbol": "SENSEX", "name": "SENSEX",
                    "current_price": current, "change": change, "change_pct": pct,
                    "day_high": _safe_float(row.get("high"), 0),
                    "day_low": _safe_float(row.get("low"), 0),
                }
            # Fallback to Twelve Data
            td = _get_td_client()
            result = td.quote(symbol="SENSEX", exchange="BSE").as_json()
            return {
                "symbol":        "SENSEX",
                "name":          "SENSEX",
                "current_price": _safe_float(result.get("close"), 0),
                "change":        _safe_float(result.get("change"), 0),
                "change_pct":    _safe_float(result.get("percent_change"), 0),
                "day_high":      _safe_float(result.get("high"), 0),
                "day_low":       _safe_float(result.get("low"), 0),
            }
        except Exception as e:
            logger.warning(f"SENSEX lookup failed: {e}")
            return None

    # NSE indices → nsepython v2.97 (nse_index() returns all indices as DataFrame)
    try:
        row = _get_nse_index_row(index_name)
        if row is not None:
            # Column names in v2.97 DataFrame
            def _col(row, *names):
                for n in names:
                    if n in row.index:
                        return row[n]
                return 0

            current    = _safe_float(_col(row, "last"), 0)
            change_col = _safe_float(_col(row, "variation", "change"), 0)
            pct        = _safe_float(_col(row, "percChange", "pChange"), 0)
            high       = _safe_float(_col(row, "high"), 0)
            low        = _safe_float(_col(row, "low"), 0)
            prev       = _safe_float(_col(row, "previousClose", "prevClose"), 0)
            yr_high    = _safe_float(_col(row, "yearHigh", "52wHigh"), 0)
            yr_low     = _safe_float(_col(row, "yearLow", "52wLow"), 0)

            # Fix: If change is 0 but price moved from previous close, recalculate
            if change_col == 0 and prev > 0 and current > 0:
                change_col = round(current - prev, 2)

            return {
                "symbol":        index_name.replace(" ", "_"),
                "name":          index_name,
                "current_price": current,
                "change":        change_col,
                "change_pct":    pct,
                "day_high":      high,
                "day_low":       low,
                "prev_close":    prev,
                "year_high":     yr_high,
                "year_low":      yr_low,
            }
    except Exception as e:
        logger.debug(f"[nsepython] get_index_quote({index_name}) failed: {e}")

    # Twelve Data fallback for NSE indices
    try:
        td_symbol = "NIFTY" if "50" in index_name else "BANKNIFTY"
        td = _get_td_client()
        result = td.quote(symbol=td_symbol, exchange="NSE").as_json()
        return {
            "symbol":        td_symbol,
            "name":          index_name,
            "current_price": _safe_float(result.get("close"), 0),
            "change":        _safe_float(result.get("change"), 0),
            "change_pct":    _safe_float(result.get("percent_change"), 0),
            "day_high":      _safe_float(result.get("high"), 0),
            "day_low":       _safe_float(result.get("low"), 0),
        }
    except Exception as e:
        logger.warning(f"[TwelveData] get_index_quote({index_name}) failed: {e}")
        return None



def get_stock_history(symbol: str, period: str, interval: str) -> List[dict]:
    """
    Historical OHLCV for an NSE symbol or index.
    period: '1d'|'5d'|'1mo'|'1y'|'5y'
    interval: '5m'|'15m'|'1d'|'1wk'
    Returns list of ChartCandle dicts.
    """
    period_days = {"1d": 1, "5d": 5, "1mo": 30, "1y": 365, "5y": 1825}
    days = period_days.get(period, 30)

    # Detect if it's an NSE index
    # Note: index_history needs exact name like 'NIFTY 50'
    indices_list = {"NIFTY 50", "NIFTY BANK", "NIFTY IT", "SENSEX", "NIFTY NEXT 50", "NIFTY 100"}
    is_nse_index = symbol in indices_list or symbol.startswith("NIFTY")

    # nsepython history for daily data
    if interval in ("1d", "1wk"):
        try:
            from nsepython import equity_history, index_history
            all_candles = []
            chunk = 90
            remaining = days
            end_dt = datetime.now()
            
            while remaining > 0:
                fetch_days = min(remaining, chunk)
                start_dt   = end_dt - timedelta(days=fetch_days)
                
                # Different date formats for equity vs index history
                if is_nse_index:
                    end_str   = end_dt.strftime("%d-%b-%Y")
                    start_str = start_dt.strftime("%d-%b-%Y")
                else:
                    end_str   = end_dt.strftime("%d-%m-%Y")
                    start_str = start_dt.strftime("%d-%m-%Y")

                try:
                    if is_nse_index:
                        # nsepython v2.97 index_history(name, start, end)
                        df = index_history(symbol, start_str, end_str)
                    else:
                        df = equity_history(symbol, "EQ", start_str, end_str)
                        
                    if df is not None and not df.empty:
                        all_candles.extend(hist_to_chart(df))
                except Exception as chunk_err:
                    logger.debug(f"[nsepython] history chunk failed ({start_str}→{end_str}): {chunk_err}")
                
                end_dt    = start_dt - timedelta(days=1)
                remaining -= fetch_days
            
            if all_candles:
                seen = set()
                unique = []
                for c in sorted(all_candles, key=lambda x: x["timestamp"]):
                    if c["timestamp"] not in seen:
                        seen.add(c["timestamp"])
                        unique.append(c)
                return unique
        except Exception as e:
            logger.debug(f"[nsepython] get_stock_history({symbol}) failed: {e}")

    # Twelve Data fallback (also used for intraday 5m/15m)
    try:
        td = _get_td_client()
        td_interval_map = {
            "5m": "5min", "15m": "15min",
            "1d": "1day", "1wk": "1week",
        }
        td_interval = td_interval_map.get(interval, "1day")
        outputsize  = min(days * 8, 500)
        ts = td.time_series(
            symbol=symbol,
            exchange="NSE",
            interval=td_interval,
            outputsize=outputsize,
        ).as_json()
        return td_to_chart(ts)
    except Exception as e:
        logger.warning(f"[TwelveData] time_series({symbol}) failed: {e}")
        return []



def get_top_movers() -> dict:
    """
    Returns {'gainers': [...], 'losers': [...]}.
    nsepython v2.97: nse_get_top_gainers() / nse_get_top_losers() return DataFrames.
    """
    def _normalize_df_row(row) -> dict:
        """Normalise a DataFrame row from nse_get_top_gainers/nse_get_top_losers."""
        sym     = str(row.get("symbol", "") or "")
        price   = _safe_float(row.get("lastPrice") or row.get("last"), 0)
        chg     = _safe_float(row.get("netPrice")  or row.get("change"), 0)
        pct     = _safe_float(row.get("pChange")   or row.get("percChange"), 0)
        vol     = _safe_float(row.get("totalTradedVolume") or row.get("tradedQuantity"), 0)
        return {
            "symbol":        sym,
            "name":          sym,
            "current_price": price,
            "change":        chg,
            "change_pct":    pct,
            "volume":        vol,
            "avg_volume":    vol,
            "volume_surge":  False,
            "sector":        "",
            "sparkline":     [],
        }

    try:
        from nsepython import nse_get_top_gainers, nse_get_top_losers
        gainers_df = nse_get_top_gainers()
        losers_df  = nse_get_top_losers()

        gainers = [_normalize_df_row(r) for _, r in gainers_df.head(5).iterrows()] if gainers_df is not None and not gainers_df.empty else []
        losers  = [_normalize_df_row(r) for _, r in losers_df.head(5).iterrows()]  if losers_df  is not None and not losers_df.empty  else []
        return {"gainers": gainers, "losers": losers}
    except Exception as e:
        logger.warning(f"[nsepython] get_top_movers failed: {e}")
        return {"gainers": [], "losers": []}


def get_sector_1w_change(index_name: str) -> float:
    """Gets 1-week percentage change for a sector index."""
    try:
        from nsepython import index_history
        end = datetime.now().strftime("%d-%b-%Y")
        start = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        df = index_history(index_name, start, end)
        if df is not None and not df.empty and len(df) >= 2:
            first_close = _safe_float(df.iloc[-1].get("CLOSE", 0))
            last_close = _safe_float(df.iloc[0].get("CLOSE", 0))
            if first_close and first_close > 0:
                return round(((last_close - first_close) / first_close) * 100, 2)
    except Exception:
        pass
    return 0.0


def get_sector_1m_change(index_name: str) -> float:
    """Gets 1-month percentage change for a sector index."""
    try:
        from nsepython import index_history
        end = datetime.now().strftime("%d-%b-%Y")
        start = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        df = index_history(index_name, start, end)
        if df is not None and not df.empty and len(df) >= 2:
            first_close = _safe_float(df.iloc[-1].get("CLOSE", 0))
            last_close = _safe_float(df.iloc[0].get("CLOSE", 0))
            if first_close and first_close > 0:
                return round(((last_close - first_close) / first_close) * 100, 2)
    except Exception:
        pass
    return 0.0


def get_sector_top_bottom(sector_name: str) -> tuple[str, str]:
    """Returns (top_performer_symbol, worst_performer_symbol) for a sector."""
    from src.utils.stock_universe import SECTOR_CONSTITUENTS
    from nsepython import nse_eq

    tickers = SECTOR_CONSTITUENTS.get(sector_name, [])
    if not tickers:
        return "", ""

    changes = {}

    def fetch_change(ticker):
        try:
            data = nse_eq(ticker)
            # nse_eq returns a dict with priceInfo
            return ticker, _safe_float(data.get("priceInfo", {}).get("pChange", 0))
        except Exception:
            return ticker, None

    # Use thread pool to speed up multiple nse_eq calls
    with ThreadPoolExecutor(max_workers=min(len(tickers), 10)) as executor:
        futures = [executor.submit(fetch_change, t) for t in tickers]
        for f in as_completed(futures):
            t, pct = f.result()
            if pct is not None:
                changes[t] = pct

    if not changes:
        return "—", "—"

    best = max(changes, key=changes.get)
    worst = min(changes, key=changes.get)
    return best, worst


def get_sector_performance() -> List[dict]:
    """
    Performance for 8 NSE sectoral indices.
    nsepython v2.97: reads from the bulk nse_index() DataFrame via _get_nse_index_row.
    """
    sector_index_map = {
        "IT":      "NIFTY IT",
        "Banking": "NIFTY BANK",
        "Auto":    "NIFTY AUTO",
        "Pharma":  "NIFTY PHARMA",
        "Energy":  "NIFTY ENERGY",
        "FMCG":    "NIFTY FMCG",
        "Metals":  "NIFTY METAL",
        "Realty":  "NIFTY REALTY",
    }

    # Pre-fetch the full index DataFrame once
    index_df = None
    try:
        index_df = _nse_index_df()
    except Exception as e:
        logger.warning(f"[nsepython] nse_index() for sectors failed: {e}")

    results = []
    # Using ThreadPool for history calls to avoid sequential blocking (8 indices * 2 calls each)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(get_sector_1w_change, index_name): (sector_name, index_name, "1w")
            for sector_name, index_name in sector_index_map.items()
        }
        future_map.update({
            executor.submit(get_sector_1m_change, index_name): (sector_name, index_name, "1m")
            for sector_name, index_name in sector_index_map.items()
        })

        # Base results from live index_df
        temp_data = {}
        for sector_name, index_name in sector_index_map.items():
            change_pct = 0.0
            if index_df is not None:
                try:
                    name_col = next((c for c in index_df.columns if c.lower() in ("indexname", "key", "name")), None)
                    if name_col:
                        rows = index_df[index_df[name_col].str.strip() == index_name.strip()]
                        if not rows.empty:
                            row = rows.iloc[0]
                            change_pct = _safe_float(
                                row.get("percChange") if "percChange" in row.index
                                else row.get("pChange", 0), 0.0
                            ) or 0.0
                except Exception:
                    pass
            temp_data[sector_name] = {"change_pct": change_pct, "1w": 0.0, "1m": 0.0}

        for future in as_completed(future_map):
            sector_name, index_name, period = future_map[future]
            try:
                val = future.result()
                temp_data[sector_name][period] = val
            except Exception:
                pass

    for sector_name in sector_index_map:
        d = temp_data[sector_name]
        top, worst = get_sector_top_bottom(sector_name)
        results.append({
            "sector_name":    sector_name,
            "change_pct":     d["change_pct"],
            "performance_1w": d["1w"],
            "performance_1m": d["1m"],
            "top_performer":  top,
            "worst_performer": worst,
            "market_cap_cr":  0.0,
        })
    return results


def get_stock_fundamentals(symbol: str) -> dict:
    """Fundamentals via Twelve Data statistics endpoint."""
    defaults = {
        "market_cap_cr": 0.0, "pe_ratio": 0.0, "pb_ratio": 0.0,
        "dividend_yield": 0.0, "eps": 0.0, "roe": 0.0,
        "debt_to_equity": 0.0, "revenue_cr": 0.0, "profit_cr": 0.0,
    }
    try:
        td = _get_td_client()
        stats      = td.statistics(symbol=symbol, exchange="NSE").as_json()
        valuation  = stats.get("valuations_metrics", {})
        financials = stats.get("financials", {})
        income     = financials.get("income_statement", {})
        balance    = financials.get("balance_sheet", {})

        USD_TO_INR = 83.0
        CR         = 1e7  # 1 crore = 10^7

        mktcap_usd  = _safe_float(valuation.get("market_capitalization"), 0) or 0.0
        revenue_usd = _safe_float(income.get("revenue", {}).get("annual"), 0) or 0.0
        profit_usd  = _safe_float(income.get("net_income", {}).get("annual"), 0) or 0.0

        return {
            "market_cap_cr":  round((mktcap_usd  * USD_TO_INR) / CR, 2),
            "pe_ratio":       _safe_float(valuation.get("pe_ratio"), 0.0),
            "pb_ratio":       _safe_float(valuation.get("price_to_book_mrq"), 0.0),
            "dividend_yield": _safe_float(valuation.get("dividend_yield"), 0.0),
            "eps":            _safe_float(valuation.get("diluted_eps_ttm"), 0.0),
            "roe":            _safe_float(financials.get("statistics", {}).get("return_on_equity_ttm"), 0.0),
            "debt_to_equity": _safe_float(balance.get("total_debt_to_equity_mrq"), 0.0),
            "revenue_cr":     round((revenue_usd * USD_TO_INR) / CR, 2),
            "profit_cr":      round((profit_usd  * USD_TO_INR) / CR, 2),
        }
    except Exception as e:
        logger.warning(f"[TwelveData] get_stock_fundamentals({symbol}) failed: {e}")
        return defaults


# ─── SERVER.PY COMPATIBILITY LAYER ───────────────────────────────────────────
#
# server.py calls fetch_tickers_parallel() which previously returned
# (yf.Ticker, pd.DataFrame) pairs. We provide a duck-typed shim so that
# server.py code continues to work without modification.
#
# The shim object (NSETicker) exposes:
#   .info          → dict with dayHigh, dayLow, marketCap, etc.
#   .history(period, interval, auto_adjust) → pd.DataFrame with Open/High/Low/Close/Volume

class NSETicker:
    """
    Duck-typed replacement for yf.Ticker. Backed by nsepython/Twelve Data.
    Implements only the fields/methods that server.py actually uses.
    """

    def __init__(self, symbol: str):
        # Strip .NS suffix — nsepython needs bare symbol
        self.symbol   = symbol.replace(".NS", "").upper()
        self._quote   = None    # lazy-loaded
        self._info_cache = None

    def _load_quote(self):
        if self._quote is None:
            self._quote = get_stock_quote(self.symbol) or {}
        return self._quote

    @property
    def info(self) -> dict:
        """
        Returns dict mimicking yfinance .info with fields used by server.py:
        dayHigh, dayLow, marketCap, previousClose, open, sector, longName
        """
        if self._info_cache is not None:
            return self._info_cache
        q = self._load_quote()
        # marketCap from fundamentals (expensive — only fetch if needed)
        try:
            fund = get_stock_fundamentals(self.symbol)
            mktcap_inr = (fund.get("market_cap_cr") or 0) * 1e7  # back to absolute INR
            mktcap_usd = mktcap_inr / 83.0
        except Exception:
            mktcap_usd = 0

        self._info_cache = {
            "longName":       q.get("symbol", self.symbol),
            "sector":         "",
            "dayHigh":        q.get("day_high"),
            "dayLow":         q.get("day_low"),
            "regularMarketDayHigh": q.get("day_high"),
            "regularMarketDayLow":  q.get("day_low"),
            "previousClose":  q.get("prev_close"),
            "open":           q.get("open"),
            "volume":         q.get("volume"),
            "marketCap":      mktcap_usd if mktcap_usd else None,
            "currentPrice":   q.get("current_price"),
            "52WeekHigh":     q.get("year_high"),
            "52WeekLow":      q.get("year_low"),
            "trailingPE":     None,
            "priceToBook":    None,
            "dividendYield":  None,
        }
        return self._info_cache

    def history(
        self,
        period: str = "1d",
        interval: str = "1d",
        auto_adjust: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """Returns a pd.DataFrame with Open/High/Low/Close/Volume columns."""
        # Use nsepython for daily data (includes 1y)
        days_map    = {"1d": 1, "5d": 5, "1mo": 30, "1y": 365, "5y": 1825, "3mo": 90}
        intvl_map   = {"1d": "1d", "1wk": "1wk", "5m": "5m", "15m": "15m"}
        period_norm  = period
        interval_norm = intvl_map.get(interval, "1d")

        candles = get_stock_history(self.symbol, period_norm, interval_norm)
        if not candles:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        rows = []
        for c in candles:
            rows.append({
                "Open":   c.get("open") or 0.0,
                "High":   c.get("high") or 0.0,
                "Low":    c.get("low")  or 0.0,
                "Close":  c.get("close") or 0.0,
                "Volume": c.get("volume") or 0,
            })

        try:
            timestamps = []
            for c in candles:
                ts_str = c.get("timestamp", "")
                try:
                    ts = pd.to_datetime(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.tz_localize("Asia/Kolkata")
                    timestamps.append(ts)
                except Exception:
                    timestamps.append(pd.Timestamp.now(tz="Asia/Kolkata"))
        except Exception:
            timestamps = pd.date_range(
                end=datetime.now(), periods=len(rows), freq="D", tz="Asia/Kolkata"
            )

        df = pd.DataFrame(rows, index=timestamps)
        df = df.sort_index()
        return df


def _fetch_single_nse(symbol_ns: str, period: str, interval: str) -> tuple:
    """Worker for fetch_tickers_parallel. Returns (symbol_ns, (NSETicker, DataFrame))."""
    try:
        ticker = NSETicker(symbol_ns)
        hist   = ticker.history(period=period, interval=interval, auto_adjust=True)
        return symbol_ns, (ticker, hist)
    except Exception as e:
        logger.warning(f"[NSETicker] fetch failed for {symbol_ns}: {e}")
        return symbol_ns, None


def fetch_tickers_parallel(
    tickers_ns: List[str],
    period: str   = "1d",
    interval: str = "1d",
    max_workers: int = 8,
) -> Dict[str, Any]:
    """
    Fetches multiple tickers in parallel using NSETicker shims.
    Returns dict: ticker_ns → (NSETicker, pd.DataFrame) or None.
    API-compatible with the old yfinance-based implementation.
    """
    results: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_single_nse, t, period, interval): t
            for t in tickers_ns
        }
        for future in as_completed(futures):
            sym, data = future.result()
            results[sym] = data
    return results


# ─── AGENT-FACING FUNCTIONS (used by market_node.py) ─────────────────────────

def fetch_market_indicators() -> Dict[str, Any]:
    """
    Fetches India VIX approximation and NIFTY 50 data.
    Used by market_node.py agent — do not change signature.
    """
    try:
        # NIFTY 50 quote
        nifty = get_index_quote("NIFTY 50")
        if not nifty:
            raise ValueError("NIFTY 50 quote unavailable")

        current_price = nifty.get("current_price", 0)

        # Get 3-month history for SMA-50
        candles = get_stock_history("NIFTY", "1y", "1d")

        vix = 18.0  # nsepython doesn't return India VIX in a simple call — use default
        if not candles:
            return {
                "vix": vix,
                "nifty_price": round(current_price, 2),
                "nifty_sma_50": None,
                "nifty_trend": "NEUTRAL",
            }

        closes = pd.Series([c["close"] for c in candles if c.get("close")])
        sma_50 = calculate_sma(closes, 50)

        trend = "NEUTRAL"
        if sma_50:
            trend = "BULLISH" if current_price > sma_50 else "BEARISH"

        return {
            "vix": round(vix, 2),
            "nifty_price":  round(current_price, 2),
            "nifty_sma_50": sma_50,
            "nifty_trend":  trend,
        }
    except Exception as e:
        logger.error(f"fetch_market_indicators failed: {e}")
        return {"error": str(e), "vix": 18.0, "nifty_trend": "NEUTRAL"}


def fetch_sectoral_breadth() -> Dict[str, str]:
    """
    Checks trend across Indian sectors using NSE sectoral indices.
    Used by market_node.py agent — do not change signature.
    Returns dict: sector_name → 'BULLISH' | 'BEARISH' | 'UNKNOWN'
    """
    sector_map = {
        "BANKING": "NIFTY BANK",
        "IT":      "NIFTY IT",
        "AUTO":    "NIFTY AUTO",
        "METAL":   "NIFTY METAL",
        "PHARMA":  "NIFTY PHARMA",
    }

    breadth = {}
    for name, index_name in sector_map.items():
        try:
            # Get 1-month history for SMA20
            symbol = "NIFTY" if "50" in index_name else index_name.replace("NIFTY ", "NIFTY")
            # nsepython equity_history doesn't support index symbols directly;
            # use Twelve Data for index history
            td = _get_td_client()
            td_symbol = {
                "NIFTY BANK":   "BANKNIFTY",
                "NIFTY IT":     "CNXIT",
                "NIFTY AUTO":   "CNXAUTO",
                "NIFTY METAL":  "CNXMETAL",
                "NIFTY PHARMA": "CNXPHARMA",
            }.get(index_name, "NIFTY")

            ts = td.time_series(
                symbol=td_symbol,
                exchange="NSE",
                interval="1day",
                outputsize=30,
            ).as_json()

            closes = pd.Series([float(c["close"]) for c in (ts or []) if c.get("close")])
            if len(closes) < 3:
                breadth[name] = "UNKNOWN"
                continue

            current = closes.iloc[-1]
            sma20   = calculate_sma(closes, min(20, len(closes)))
            breadth[name] = "BULLISH" if sma20 and current > sma20 else "BEARISH"

        except Exception as e:
            logger.debug(f"fetch_sectoral_breadth {name} failed: {e}")
            breadth[name] = "UNKNOWN"

    return breadth
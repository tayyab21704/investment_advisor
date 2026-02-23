"""
Investment Council — FastAPI Bridge
Connects Next.js frontend to frozen Python agents.
DO NOT import from agents directly except council_app.
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from urllib.parse import unquote
import pandas as pd
import time
import asyncio
import logging
import csv
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# The ONE import from agents we're allowed:
from src.orchestrator.graph import council_app

# Utility helpers
from src.utils.market_data import (
    calculate_sma, calculate_rsi, get_regime,
    hist_to_chart, fetch_tickers_parallel,
    get_stock_quote, get_index_quote, get_stock_history,
    get_top_movers, get_sector_performance, get_stock_fundamentals,
)
from src.utils.stock_universe import STOCK_UNIVERSE, SECTOR_CONSTITUENTS, search_universe

app = FastAPI(title="Investment Council API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

IST = ZoneInfo("Asia/Kolkata")

# CORS — update with your Vercel domain after deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── IN-MEMORY CACHE ────────────────────────────────────────────────────────
_cache: dict = {}

def get_cached(key: str, ttl: int, fetch_fn) -> tuple[Any, bool]:
    """
    Returns (data, cache_hit: bool).
    cache_hit=True means data came from cache, False means freshly fetched.
    """
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < ttl:
            return data, True
    data = fetch_fn()
    _cache[key] = (data, time.time())
    return data, False


def _make_response(data: Any, cache_hit: bool, response: Response) -> Any:
    """Attach X-Cache header and return data."""
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return data


# ─── SYMBOL MASTER LIST (kept for legacy /api/search fallback) ──────────────
_symbols: list = []

def load_symbols():
    global _symbols
    path = os.path.join(os.path.dirname(__file__), "../../data/nse_symbols.csv")
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            _symbols = list(reader)
    logger.info(f"Loaded {len(_symbols)} symbols from CSV")

@app.on_event("startup")
async def startup():
    load_symbols()


# ─── HELPERS ────────────────────────────────────────────────────────────────

INDEX_META = {
    "^NSEI":    "NIFTY 50",
    "^BSESN":   "SENSEX",
    "^NSEBANK": "BANK NIFTY",
}

USD_TO_INR = 83.0   # approximate conversion rate

def _safe_float(val, default=None):
    try:
        f = float(val)
        return round(f, 2) if f == f else default   # NaN check
    except Exception:
        return default

def _safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

def _market_cap_cr(info: dict) -> Optional[float]:
    """Convert market cap from USD to INR crores."""
    mc = info.get("marketCap")
    if mc:
        return round(mc * USD_TO_INR / 1e7, 2)   # 1 crore = 10^7
    return None


# ─── HEALTH ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check(response: Response):
    """Returns server status and current IST timestamp."""
    now_ist = datetime.now(IST).isoformat()
    response.headers["X-Cache"] = "MISS"
    return {"status": "ok", "timestamp": now_ist}


# ─── MARKET STATUS ───────────────────────────────────────────────────────────

@app.get("/api/market-status")
def market_status(response: Response):
    """NSE session info — no cache."""
    now = datetime.now(IST)
    weekday = now.weekday()          # 0=Mon … 4=Fri, 5=Sat, 6=Sun

    market_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    is_weekday = weekday < 5

    if not is_weekday:
        session = "closed"
        is_open = False
    elif now < market_open:
        session = "pre_market"
        is_open = False
    elif now <= market_close:
        session = "open"
        is_open = True
    else:
        session = "post_market"
        is_open = False

    # Next open: next Monday if weekend, else tomorrow (or today if not yet open)
    if is_open or (is_weekday and now < market_open):
        # Today is/was a trading day
        next_open_date = now.date() if (is_weekday and now < market_open) else None
        if next_open_date is None:
            # After market close or weekend — next business day
            days_ahead = 1
            trial = now.date() + timedelta(days=days_ahead)
            while trial.weekday() >= 5:
                days_ahead += 1
                trial = now.date() + timedelta(days=days_ahead)
            next_open_date = trial
    else:
        # Weekend or post-market
        days_ahead = 1
        trial = now.date() + timedelta(days=days_ahead)
        while trial.weekday() >= 5:
            days_ahead += 1
            trial = now.date() + timedelta(days=days_ahead)
        next_open_date = trial

    if is_weekday and now < market_open:
        next_open_dt = market_open
    else:
        next_open_dt = datetime(
            next_open_date.year, next_open_date.month, next_open_date.day,
            9, 15, 0, tzinfo=IST
        )

    response.headers["X-Cache"] = "MISS"
    return {
        "is_open": is_open,
        "current_time_ist": now.isoformat(),
        "session": session,
        "next_open": next_open_dt.isoformat(),
    }


# ─── MARKET INDICES (enriched) ───────────────────────────────────────────────

@app.get("/api/market-indices")
def market_indices(response: Response):
    """NIFTY 50, SENSEX, BANK NIFTY — enriched via nsepython, cached 5 min."""

    # Map from legacy ticker key → nsepython index name
    INDEX_NSE_MAP = {
        "^NSEI":    "NIFTY 50",
        "^BSESN":   "SENSEX",
        "^NSEBANK": "NIFTY BANK",
        "^CNXIT":   "NIFTY IT",
    }

    def fetch():
        result = {}
        for ticker, index_name in INDEX_NSE_MAP.items():
            try:
                quote = get_index_quote(index_name)
                if not quote:
                    result[ticker] = {"value": 0, "change": 0, "change_pct": 0,
                                      "symbol": ticker, "name": INDEX_META.get(ticker, index_name)}
                    continue

                current    = quote.get("current_price", 0) or 0
                change     = quote.get("change", 0) or 0
                change_pct = quote.get("change_pct", 0) or 0
                prev_close = quote.get("prev_close") or (current - change)

                # 1-year daily history for SMA-50 + year high/low + sparkline
                # Map index to a symbol nsepython history supports
                hist_symbol = {"NIFTY 50": "NIFTY", "NIFTY BANK": "BANKNIFTY"}.get(index_name)
                close_list = []
                if hist_symbol:
                    candles_1y = get_stock_history(hist_symbol, "1y", "1d")
                    close_list = [c["close"] for c in candles_1y if c.get("close")]

                close_series = pd.Series(close_list) if close_list else pd.Series([current])
                sma_50 = calculate_sma(close_series, 50) if len(close_series) >= 50 else None
                regime, confidence = get_regime(current, sma_50)

                year_high = _safe_float(close_series.max()) if len(close_series) > 1 else quote.get("day_high")
                year_low  = _safe_float(close_series.min()) if len(close_series) > 1 else quote.get("day_low")
                sparkline = [round(float(v), 2) for v in close_series.tail(30).values]

                result[ticker] = {
                    "value":             round(current, 2),
                    "change":            round(change, 2),
                    "change_pct":        round(change_pct, 2),
                    "symbol":            ticker,
                    "name":              INDEX_META.get(ticker, index_name),
                    "current_price":     round(current, 2),
                    "day_high":          quote.get("day_high"),
                    "day_low":           quote.get("day_low"),
                    "year_high":         year_high,
                    "year_low":          year_low,
                    "sparkline":         sparkline,
                    "market_regime":     regime,
                    "regime_confidence": confidence,
                }
            except Exception as e:
                logger.error(f"Error fetching index {index_name}: {e}")
                result[ticker] = {"value": 0, "change": 0, "change_pct": 0,
                                  "symbol": ticker, "name": INDEX_META.get(ticker, index_name)}
        return result

    data, hit = get_cached("market_indices", 300, fetch)
    return _make_response(data, hit, response)


# ─── TOP MOVERS (enriched) ───────────────────────────────────────────────────

@app.get("/api/top-movers")
def top_movers(response: Response):
    """Top 5 gainers and losers via nsepython NIFTY 100 — cached 3 min."""
    def fetch():
        raw = get_top_movers()
        # Enrich with name/sector from STOCK_UNIVERSE
        def enrich(item: dict) -> dict:
            sym  = item.get("symbol", "")
            meta = STOCK_UNIVERSE.get(sym, {})
            price = item.get("current_price", 0) or 0
            return {
                "symbol":        sym,
                "name":          meta.get("name", sym) or sym,
                "price":         price,
                "current_price": price,
                "change":        item.get("change", 0),
                "change_pct":    item.get("change_pct", 0),
                "volume":        item.get("volume", 0),
                "avg_volume":    item.get("avg_volume", 0),
                "volume_surge":  item.get("volume_surge", False),
                "sector":        meta.get("sector"),
                "sparkline":     [],   # sparkline via separate call if needed
            }
        return {
            "gainers": [enrich(g) for g in raw.get("gainers", [])],
            "losers":  [enrich(l) for l in raw.get("losers",  [])],
        }

    data, hit = get_cached("top_movers", 180, fetch)
    return _make_response(data, hit, response)


# ─── SECTORS (new) ───────────────────────────────────────────────────────────

@app.get("/api/sectors")
def sectors(response: Response):
    """Sector heatmap — 8 NSE sectoral indices via nsepython, cached 15 min."""
    def fetch():
        return get_sector_performance()

    data, hit = get_cached("sectors", 900, fetch)
    return _make_response(data, hit, response)


# ─── SEARCH (upgraded) ───────────────────────────────────────────────────────

@app.get("/api/search")
def search(q: str, response: Response):
    """Instant symbol/name search from STOCK_UNIVERSE — live prices via nsepython."""
    if len(q.strip()) < 1:
        response.headers["X-Cache"] = "MISS"
        return {"results": [], "query": q, "total": 0}

    matches = search_universe(q, max_results=8)
    results = []
    for m in matches:
        sym = m["symbol"]
        try:
            quote = get_stock_quote(sym)
            current_price = quote.get("current_price") if quote else None
            change_pct    = quote.get("change_pct")    if quote else None
            market_cap_cr = None   # fundamentals call is expensive for search
        except Exception:
            current_price = None
            change_pct    = None
            market_cap_cr = None

        results.append({
            "symbol":        sym,
            "name":          m.get("name", sym),
            "sector":        m.get("sector"),
            "industry":      m.get("industry"),
            "current_price": current_price,
            "change_pct":    change_pct,
            "market_cap_cr": market_cap_cr,
        })

    response.headers["X-Cache"] = "MISS"
    return {"results": results, "query": q, "total": len(results)}


# ─── STOCK DETAIL (enriched) ────────────────────────────────────────────────

@app.get("/api/stock/{symbol}")
def stock_detail(symbol: str, response: Response):
    """Comprehensive stock detail — nsepython/Twelve Data, cached 2 min."""
    symbol    = unquote(symbol).upper().strip()
    clean_sym = symbol.replace(".NS", "")

    # Unify Index and Stock handling
    is_index = clean_sym.startswith("^")
    index_name = {
        "^NSEI":    "NIFTY 50",
        "^BSESN":   "SENSEX",
        "^NSEBANK": "NIFTY BANK",
        "^CNXIT":   "NIFTY IT",
    }.get(clean_sym)

    def fetch():
        # ── Quote (live price) ──────────────────────────────────────────
        if is_index:
            if not index_name:
                raise HTTPException(status_code=404, detail={"error": "Index not supported", "symbol": clean_sym})
            quote = get_index_quote(index_name)
        else:
            quote = get_stock_quote(clean_sym)

        if not quote:
            raise HTTPException(status_code=404, detail={"error": "Symbol not found or data unavailable", "symbol": clean_sym})

        current_price = quote.get("current_price") or 0.0
        prev_close    = quote.get("prev_close") or current_price
        change        = quote.get("change") or (current_price - prev_close)
        change_pct    = quote.get("change_pct") or 0.0

        # ── Historical candles (all 5 timeframes) ───────────────────────
        # Use full index name for indices so market_data.py can route to index_history
        hist_symbol = index_name if is_index else clean_sym

        candles_1d = get_stock_history(hist_symbol, "1d",  "5m")
        candles_1w = get_stock_history(hist_symbol, "5d",  "15m")
        candles_1m = get_stock_history(hist_symbol, "1mo", "1d")
        candles_1y = get_stock_history(hist_symbol, "1y",  "1d")
        candles_5y = get_stock_history(hist_symbol, "5y",  "1wk")

        # Best available close series for technicals
        base_candles = candles_1y or candles_1m
        close_list   = [c["close"] for c in base_candles if c.get("close")]
        close_series = pd.Series(close_list) if close_list else pd.Series([current_price])

        # ── Technicals ──────────────────────────────────────────────────
        # For indices, SMA is calculated from history if available
        if is_index and candles_1y:
            closes = [c["close"] for c in candles_1y if c.get("close")]
            close_series = pd.Series(closes) if closes else pd.Series([current_price])
            sma_20  = calculate_sma(close_series, 20)
            sma_50  = calculate_sma(close_series, 50)
            sma_200 = calculate_sma(close_series, 200)
            rsi_14  = calculate_rsi(close_series, 14)
            regime, regime_conf = get_regime(current_price, sma_50)
        else:
            sma_20  = calculate_sma(close_series, 20)
            sma_50  = calculate_sma(close_series, 50)
            sma_200 = calculate_sma(close_series, 200)
            rsi_14  = calculate_rsi(close_series, 14)
            regime, regime_conf = get_regime(current_price, sma_50)

        year_high = _safe_float(quote.get("year_high") or (close_series.max() if len(close_series) > 1 else None))
        year_low  = _safe_float(quote.get("year_low")  or (close_series.min() if len(close_series) > 1 else None))

        # ── Fundamentals (Twelve Data — can be 0 if no key set) ─────────
        fund = get_stock_fundamentals(clean_sym)

        # ── Legacy chart (v1 compat) ─────────────────────────────────────
        legacy_chart = []
        for c in (candles_1y or []):
            ts = c.get("timestamp", "")
            # If it's a date like 17-Feb-2026, leave it; if it's ISO, slice to 10
            time_str = ts[:10] if "-" in ts and len(ts) > 10 else ts
            legacy_chart.append({
                "time":   time_str,
                "open":   c.get("open"),
                "high":   c.get("high"),
                "low":    c.get("low"),
                "close":  c.get("close"),
                "volume": int(c.get("volume") or 0)
            })

        # ── Meta from universe ───────────────────────────────────────────
        meta = STOCK_UNIVERSE.get(clean_sym, {})

        return {
            # Identity
            "symbol":   clean_sym,
            "name":     meta.get("name", clean_sym),
            "sector":   meta.get("sector"),
            "industry": meta.get("industry"),
            "description": "",

            # Price
            "price":         round(current_price, 2),
            "current_price": round(current_price, 2),
            "change":        round(float(change), 2),
            "change_pct":    round(float(change_pct), 2),
            "open":          quote.get("open"),
            "high":          quote.get("day_high"),
            "low":           quote.get("day_low"),
            "prev_close":    round(prev_close, 2),
            "day_high":      quote.get("day_high"),
            "day_low":       quote.get("day_low"),
            "year_high":     year_high,
            "year_low":      year_low,
            "week_52_high":  year_high,
            "week_52_low":   year_low,
            "volume":        _safe_int(quote.get("volume")),
            "avg_volume":    0,
            "market_cap":    None,
            "debt_equity":   fund.get("debt_to_equity"),

            # Fundamentals
            "market_cap_cr":  fund.get("market_cap_cr"),
            "pe_ratio":       fund.get("pe_ratio"),
            "pb_ratio":       fund.get("pb_ratio"),
            "dividend_yield": fund.get("dividend_yield"),
            "eps":            fund.get("eps"),
            "roe":            fund.get("roe"),
            "debt_to_equity": fund.get("debt_to_equity"),
            "revenue_cr":     fund.get("revenue_cr"),
            "profit_cr":      fund.get("profit_cr"),

            # Multi-timeframe charts
            "chart_1d": candles_1d,
            "chart_1w": candles_1w,
            "chart_1m": candles_1m,
            "chart_1y": candles_1y,
            "chart_5y": candles_5y,
            "chart":    legacy_chart,

            # Technicals
            "sma_20":        sma_20,
            "sma_50":        sma_50,
            "sma_200":       sma_200,
            "rsi_14":        rsi_14,
            "above_sma_50":  (current_price > sma_50)  if sma_50  else None,
            "above_sma_200": (current_price > sma_200) if sma_200 else None,

            # Sentiment
            "regime":            regime,
            "regime_confidence": regime_conf,
        }

    data, hit = get_cached(f"stock_{clean_sym}", 120, fetch)
    return _make_response(data, hit, response)


@app.get("/api/chart/{symbol}")
def get_chart(symbol: str, response: Response, timeframe: str = "1M"):
    """
    Lightweight endpoint — returns ONLY chart data for a symbol.
    Much faster than /api/stock/{symbol} which fetches everything.
    """
    symbol = unquote(symbol).upper().strip()

    # Map timeframe to period/interval
    tf_map = {
        "1D": ("1d", "5m"),
        "1W": ("5d", "15m"),
        "1M": ("1mo", "1d"),
        "1Y": ("1y", "1d"),
        "5Y": ("5y", "1wk"),
    }
    period, interval = tf_map.get(timeframe, ("1mo", "1d"))

    cache_key = f"chart_{symbol}_{period}_{interval}"

    def fetch():
        # Handle index symbol (^) mapping
        hist_symbol = symbol
        if symbol.startswith("^"):
            index_name = {
                "^NSEI":    "NIFTY 50",
                "^BSESN":   "SENSEX",
                "^NSEBANK": "NIFTY BANK",
                "^CNXIT":   "NIFTY IT",
            }.get(symbol)
            if index_name:
                hist_symbol = index_name

        candles = get_stock_history(hist_symbol, period, interval)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": candles
        }

    data, hit = get_cached(cache_key, 300, fetch)
    return _make_response(data, hit, response)


# ─── AI COUNCIL ──────────────────────────────────────────────────────────────

class UserProfileInput(BaseModel):
    risk_appetite: str              # "Conservative" | "Moderate" | "Aggressive"
    actual_risk_capacity: int       # 1-10
    monthly_surplus: float          # in ₹
    monthly_income: Optional[float] = None
    monthly_debt: Optional[float] = None

@app.post("/api/council/analyze")
async def council_analyze(profile: UserProfileInput):
    """Run the full agent graph. Takes 10-30 seconds. Returns full report."""
    initial_state = {
        "user_id": "web_user_" + str(int(time.time())),
        "behavioral_answers": [],
        "user_profile": {
            "risk_appetite":        profile.risk_appetite,
            "actual_risk_capacity": profile.actual_risk_capacity,
            "monthly_surplus":      profile.monthly_surplus,
            "monthly_income":       profile.monthly_income or 0,
            "monthly_debt":         profile.monthly_debt or 0,
            "monthly_expenses": (profile.monthly_income or 0) - profile.monthly_surplus,
            "existing_debt": profile.monthly_debt or 0,
            "liquidity_required_pct": 20.0,
            "max_single_asset_pct": 20.0,
            "investment_horizon_years": 10,
            "debt_to_income_ratio": (profile.monthly_debt / profile.monthly_income)
                if profile.monthly_income and profile.monthly_income > 0 else 0
        },
        "market_context":        {},
        "scout_recommendations": [],
        "risk_assessment":       {},
        "final_portfolio":       [],
        "agent_outputs":         {},
        "iteration":             0,
        "decision":              "PENDING",
        "error":                 None,
        "feedback_for_scout":    None,
        "orchestrator_decision": {},
    }
    try:
        result = await council_app.ainvoke(initial_state)

        portfolio = result.get("final_portfolio", [])
        risk = result.get("risk_assessment", {})

        return {
            "regime":            result.get("market_context", {}).get("regime", "NEUTRAL"),
            "regime_confidence": result.get("market_context", {}).get("confidence", 0.5),
            "decision":          result.get("decision", "REJECT"),
            "reasoning":         result.get("orchestrator_decision", {}).get("reasoning", ""),
            "portfolio":         portfolio,
            "risk_metrics": {
                "portfolio_beta":  risk.get("metrics", {}).get("portfolio_beta"),
                "volatility":      risk.get("metrics", {}).get("volatility"),
                "var_95":          risk.get("metrics", {}).get("var_95"),
                "avg_correlation": risk.get("metrics", {}).get("avg_correlation"),
            },
            "debate_rounds":         result.get("iteration", 0),
            "safe_harbor_activated": result.get("safe_harbor", False),
        }
    except Exception as e:
        logger.exception("Council analysis failed")
        raise HTTPException(status_code=500, detail=f"Council failed: {str(e)}")

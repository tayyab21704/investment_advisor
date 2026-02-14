import yfinance as yf
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("MarketUtils")

def fetch_nifty_data() -> Dict:
    """Fetches key Nifty 50 benchmarks."""
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1mo")
        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[0]
        change_pct = ((current - prev) / prev) * 100
        
        return {
            "index": "Nifty 50",
            "price": round(current, 2),
            "change_1mo_pct": round(change_pct, 2),
            "trend": "BULLISH" if change_pct > 2 else "BEARISH" if change_pct < -2 else "NEUTRAL"
        }
    except Exception as e:
        logger.error(f"Error fetching Nifty: {e}")
        return {"trend": "NEUTRAL", "price": 22000}

def fetch_vix() -> float:
    """Fetches India VIX or global VIX as fallback."""
    try:
        vix = yf.Ticker("^INDIAVIX") # India VIX
        hist = vix.history(period="1d")
        if hist.empty:
            vix = yf.Ticker("^VIX") # Global VIX fallback
            hist = vix.history(period="1d")
        return round(hist["Close"].iloc[-1], 2)
    except:
        return 15.0

def fetch_stock_info(ticker: str) -> Dict:
    """Fetches key metrics for a specific ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "symbol": ticker,
            "price": info.get("currentPrice", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "market_cap": info.get("marketCap", 0),
            "beta": info.get("beta", 1.0)
        }
    except:
        return {"symbol": ticker, "beta": 1.0}

def screen_nifty_50(criteria: Dict) -> List[Dict]:
    """
    Mock screening of Nifty 50 stocks based on criteria.
    In production, this would iterate through yfinance for Nifty components.
    """
    # Sample universe for demo/scouting
    universe = [
        {"ticker": "RELIANCE.NS", "sector": "Energy", "quality_score": 9},
        {"ticker": "TCS.NS", "sector": "IT", "quality_score": 9},
        {"ticker": "HDFCBANK.NS", "sector": "Banking", "quality_score": 8},
        {"ticker": "INFY.NS", "sector": "IT", "quality_score": 8},
        {"ticker": "ICICIBANK.NS", "sector": "Banking", "quality_score": 8},
        {"ticker": "HINDUNILVR.NS", "sector": "FMCG", "quality_score": 9},
        {"ticker": "BTC-USD", "sector": "Crypto", "quality_score": 7}
    ]
    
    # Filter by risk/quality
    min_quality = criteria.get("min_quality_score", 7)
    results = [s for s in universe if s["quality_score"] >= min_quality]
    
    return results

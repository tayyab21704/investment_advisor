import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def fetch_market_indicators() -> Dict[str, Any]:
    """
    Fetches core Indian market indicators: VIX and Nifty 50.
    """
    try:
        # 1. Fetch India VIX (Expectation of Volatility)
        vix = yf.Ticker("^INDIAVIX").history(period="1d")['Close'].iloc[-1]

        # 2. Fetch Nifty 50 & 50-day SMA (Price Momentum)
        nifty_ticker = yf.Ticker("^NSEI")
        nifty_hist = nifty_ticker.history(period="3mo")
        nifty_current = nifty_hist['Close'].iloc[-1]
        sma_50 = nifty_hist['Close'].rolling(window=50).mean().iloc[-1]

        return {
            "vix": round(vix, 2),
            "nifty_price": round(nifty_current, 2),
            "nifty_sma_50": round(sma_50, 2),
            "nifty_trend": "BULLISH" if nifty_current > sma_50 else "BEARISH"
        }
    except Exception as e:
        logger.error(f"Core market data fetch failed: {e}")
        return {"error": str(e), "vix": 18.0, "nifty_trend": "NEUTRAL"}

def fetch_sectoral_breadth() -> Dict[str, str]:
    """
    Elite feature: Checks if the rally is broad-based across Indian sectors.
    Inspired by your Colab sectoral screening logic.
    """
    sectors = {
        "BANKING": "^NSEBANK",
        "IT": "NIFTY_IT.NS",
        "AUTO": "NIFTY_AUTO.NS",
        "METAL": "NIFTY_METAL.NS",
        "PHARMA": "NIFTY_PHARMA.NS"
    }
    
    breadth = {}
    for name, ticker in sectors.items():
        try:
            data = yf.Ticker(ticker).history(period="1mo")
            if not data.empty:
                current = data['Close'].iloc[-1]
                sma20 = data['Close'].rolling(20).mean().iloc[-1]
                breadth[name] = "BULLISH" if current > sma20 else "BEARISH"
        except Exception:
            breadth[name] = "UNKNOWN"
            
    return breadth
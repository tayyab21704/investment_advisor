import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def flatten_yf_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to handle yfinance MultiIndex columns and empty results."""
    if df.empty:
        return df
    # If columns are MultiIndex (e.g., ['Close', '^NSEI']), drop the ticker level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def fetch_market_indicators() -> Dict[str, Any]:
    """Fetches India VIX and Nifty 50 with defensive MultiIndex handling."""
    try:
        # 1. Fetch India VIX
        vix_data = yf.download("^INDIAVIX", period="1d", progress=False)
        vix_data = flatten_yf_dataframe(vix_data)
        
        if vix_data.empty or 'Close' not in vix_data.columns:
            vix = 18.0 # Fallback
        else:
            vix = vix_data['Close'].iloc[-1]

        # 2. Fetch Nifty 50
        nifty_data = yf.download("^NSEI", period="3mo", progress=False)
        nifty_data = flatten_yf_dataframe(nifty_data)
        
        if nifty_data.empty or 'Close' not in nifty_data.columns:
            return {"vix": round(float(vix), 2), "nifty_trend": "NEUTRAL", "error": "Nifty data empty"}

        nifty_current = nifty_data['Close'].iloc[-1]
        sma_50 = nifty_data['Close'].rolling(window=50).mean().iloc[-1]

        return {
            "vix": round(float(vix), 2),
            "nifty_price": round(float(nifty_current), 2),
            "nifty_sma_50": round(float(sma_50), 2),
            "nifty_trend": "BULLISH" if nifty_current > sma_50 else "BEARISH"
        }
    except Exception as e:
        logger.error(f"Core market data fetch failed: {e}")
        return {"error": str(e), "vix": 18.0, "nifty_trend": "NEUTRAL"}

def fetch_sectoral_breadth() -> Dict[str, str]:
    """Checks breadth across Indian sectors with MultiIndex safety."""
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
            data = yf.download(ticker, period="1mo", progress=False)
            data = flatten_yf_dataframe(data)
            if not data.empty and 'Close' in data.columns:
                current = data['Close'].iloc[-1]
                sma20 = data['Close'].rolling(20).mean().iloc[-1]
                breadth[name] = "BULLISH" if current > sma20 else "BEARISH"
            else:
                breadth[name] = "UNKNOWN"
        except Exception:
            breadth[name] = "UNKNOWN"
            
    return breadth
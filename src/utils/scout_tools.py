import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def flatten_yf_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to handle yfinance MultiIndex headers (Critical for stability)."""
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_universe_by_regime(regime: str) -> List[str]:
    """
    Returns a curated list of tickers based on the market regime.
    """
    universes = {
        "RISK_ON": [
            "TCS.NS", "INFY.NS", "RELIANCE.NS", "BAJFINANCE.NS", "TITAN.NS",
            "TATAMOTORS.NS", "ICICIBANK.NS", "DLF.NS", "ZOMATO.NS"
        ],
        "RISK_OFF": [
            "HINDUNILVR.NS", "ITC.NS", "BRITANNIA.NS", "NESTLEIND.NS",
            "SUNPHARMA.NS", "CIPLA.NS", "MARICO.NS", "DABUR.NS"
        ],
        "NEUTRAL": [
            "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "LT.NS",
            "ULTRACEMCO.NS", "MARUTI.NS", "ASIANPAINT.NS"
        ]
    }
    return universes.get(regime, universes["NEUTRAL"])

def get_real_time_fundamentals(tickers: List[str]) -> List[Dict]:
    """
    NEW: Fetches Price, Volatility, and Beta for a list of tickers.
    This allows the Scout to 'Self-Correct' on risk before recommending.
    """
    valid_data = []
    if not tickers: return []

    try:
        # Download 1 year of data for stocks + Benchmark (Nifty 50) in one go
        all_symbols = tickers + ["^NSEI"]
        data = yf.download(all_symbols, period="1y", progress=False)
        data = flatten_yf_dataframe(data)
        
        if 'Close' not in data.columns or data['Close'].empty:
            return []

        # Calculate Daily Returns
        returns = data['Close'].pct_change().dropna()
        
        if "^NSEI" not in returns.columns:
            logger.warning("Benchmark (^NSEI) missing. Skipping Beta calc.")
            return []

        market_variance = returns["^NSEI"].var()

        for ticker in tickers:
            if ticker not in returns.columns: continue
                
            # Calculate Beta: Covariance(Stock, Market) / Variance(Market)
            covariance = returns[[ticker, "^NSEI"]].cov().iloc[0, 1]
            beta = covariance / market_variance if market_variance != 0 else 1.0
            
            # Calculate Volatility (Annualized)
            volatility = returns[ticker].std() * np.sqrt(252) * 100
            
            current_price = data['Close'][ticker].iloc[-1]

            valid_data.append({
                "ticker": ticker,
                "current_price": round(float(current_price), 2),
                "beta": round(float(beta), 2),
                "volatility": round(float(volatility), 2),
                "status": "Active"
            })
            
    except Exception as e:
        logger.error(f"Fundamental analysis failed: {e}")
        
    return valid_data

def find_safe_fallback_assets() -> List[Dict]:
    """
    NEW: Returns 'Safety Portfolio' (ETFs) to ensure we never return 'REJECTED'.
    """
    return [
        {"ticker": "NIFTYBEES.NS", "name": "Nippon India ETF Nifty BeES", "reason": "Benchmark Safety", "type": "ETF"},
        {"ticker": "GOLDBEES.NS", "name": "Nippon India ETF Gold BeES", "reason": "Volatility Hedge", "type": "ETF"},
        {"ticker": "LIQUIDBEES.NS", "name": "Nippon India ETF Liquid BeES", "reason": "Cash Management", "type": "ETF"}
    ]

# --- Keep existing helper functions for legacy support if needed ---

def calculate_composite_score(info: Dict[str, Any]) -> float:
    """Calculates Quality Score (0-100) using fundamental factors."""
    try:
        roe = info.get('returnOnEquity', 0) * 100
        roe_score = min(roe * 2, 40)
        
        growth = info.get('earningsGrowth', 0) * 100
        if growth is None: growth = 0
        growth_score = min(max(growth * 0.5, 0), 30)
        
        debt_ratio = info.get('debtToEquity', 100)
        if debt_ratio is None: debt_score = 15
        elif debt_ratio < 50: debt_score = 30
        elif debt_ratio < 100: debt_score = 20
        elif debt_ratio < 200: debt_score = 10
        else: debt_score = 0
        
        return round(roe_score + growth_score + debt_score, 2)
    except Exception:
        return 0.0

def analyze_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """Legacy single-ticker analysis (Slow, use get_real_time_fundamentals for batching)."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        score = calculate_composite_score(info)
        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "quality_score": score,
            "type": info.get("quoteType", "EQUITY")
        }
    except Exception:
        return None
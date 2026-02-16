import yfinance as yf
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_universe_by_regime(regime: str) -> List[str]:
    """
    Returns a curated list of tickers based on the market regime.
    RISK_ON = Growth/Tech/Crypto
    RISK_OFF = Defensive/Gold/FMCG
    """
    universes = {
        "RISK_ON": [
            "TCS.NS", "INFY.NS", "RELIANCE.NS", "BAJFINANCE.NS", "TITAN.NS",
            "TATAMOTORS.NS", "ICICIBANK.NS", "BTC-USD", "ETH-USD", "SOL-USD"
        ],
        "RISK_OFF": [
            "HINDUNILVR.NS", "ITC.NS", "BRITANNIA.NS", "NESTLEIND.NS",
            "SUNPHARMA.NS", "CIPLA.NS", "GC=F", "SI=F" # Gold/Silver
        ],
        "NEUTRAL": [
            "HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "LT.NS",
            "ULTRACEMCO.NS", "MARUTI.NS", "RELIANCE.NS", "ITC.NS"
        ]
    }
    # Default to NEUTRAL if regime is unknown
    return universes.get(regime, universes["NEUTRAL"])

def calculate_composite_score(info: Dict[str, Any]) -> float:
    """
    Calculates a Quality Score (0-100) using fundamental factors.
    Prevents picking high-ROE stocks that have dangerous debt.
    """
    try:
        # 1. ROE Factor (40 points max)
        roe = info.get('returnOnEquity', 0) * 100
        roe_score = min(roe * 2, 40)
        
        # 2. Profit Growth Factor (30 points max)
        growth = info.get('earningsGrowth', 0) * 100
        # If growth is None, assume 0
        if growth is None: growth = 0
        growth_score = min(max(growth * 0.5, 0), 30)
        
        # 3. Debt-to-Equity Penalty (30 points max)
        debt_ratio = info.get('debtToEquity', 100)
        # Ideally debt < 100 (1:1 ratio). Over 200 is risky.
        if debt_ratio is None: 
            debt_score = 15 # Neutral assumption if missing
        elif debt_ratio < 50: debt_score = 30
        elif debt_ratio < 100: debt_score = 20
        elif debt_ratio < 200: debt_score = 10
        else: debt_score = 0
        
        total_score = roe_score + growth_score + debt_score
        return round(total_score, 2)
    except Exception as e:
        logger.warning(f"Error calculating score: {e}")
        return 0.0

def analyze_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetches live data and computes the composite score for a single ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        score = calculate_composite_score(info)
        
        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "price": info.get("currentPrice"),
            "pe": info.get("trailingPE"),
            "roe": round(info.get("returnOnEquity", 0) * 100, 2),
            "quality_score": score,
            "type": info.get("quoteType", "EQUITY")
        }
    except Exception as e:
        logger.error(f"Failed to analyze {ticker}: {e}")
        return None

def get_vibe_check(ticker: str) -> str:
    """
    Simplified Sentiment Analysis. Fetches top 3 news headlines.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:3] if stock.news else []
        if not news:
            return "No recent news found."
        headlines = [n.get('title', '') for n in news]
        return "; ".join(headlines)
    except Exception:
        return "Sentiment data unavailable."
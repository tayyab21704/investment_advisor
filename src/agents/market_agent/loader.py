
# [Paste your loader code here]
"""
loader.py - Unified Data Loader for All Investment Tools

Single file that handles ALL data fetching for Tools 1-9:
- Tool 1: Market Regime (VIX, Nifty, rates, inflation, yield curve)
- Tool 2: Asset Class (uses Tool 1 data)
- Tool 3: Sector Rotation (NSE sector indices)
- Tool 4-9: (Add as needed)

Features:
- Live data fetching (yfinance)
- Data normalization (raw → signals)
- Built-in caching (avoid redundant API calls)
- Error handling (graceful degradation)
- Smart mocks (for data sources not yet available)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

class DataConfig:
    """Centralized data configuration"""

    # Market indices
    NIFTY50_TICKER = "^NSEI"
    INDIA_VIX_TICKER = "^INDIAVIX"
    US_VIX_TICKER = "^VIX"  # Fallback

    # NSE Sector indices
    NSE_SECTORS = {
        "Financial Services": "NIFTY_FIN_SERVICE.NS",
        "Banking": "^NSEBANK",
        "IT": "^CNXIT",
        "Pharma": "^CNXPHARMA",
        "FMCG": "^CNXFMCG",
        "Energy": "^CNXENERGY",
        "Auto": "^CNXAUTO",
        "Metals": "^CNXMETAL",
        "Realty": "^CNXREALTY",
        "Media": "^CNXMEDIA",
        "Infrastructure": "^CNXINFRA",
        "PSU Banks": "^CNXPSUBANK",
    }

    # Cache settings
    CACHE_TTL_SECONDS = 3600  # 1 hour


# ============================================================================
# SIMPLE CACHE (In-Memory)
# ============================================================================

class SimpleCache:
    """Time-based cache to avoid redundant API calls"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[any]:
        """Get cached value if not expired"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self._ttl:
                return value
        return None

    def set(self, key: str, value: any):
        """Cache a value with timestamp"""
        self._cache[key] = (value, datetime.now())

    def clear(self):
        """Clear all cache"""
        self._cache = {}
        print("🗑️  Cache cleared")


# Global cache instance
_cache = SimpleCache(ttl_seconds=DataConfig.CACHE_TTL_SECONDS)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_close_prices(df: pd.DataFrame) -> Optional[pd.Series]:
    """Extract close prices from yfinance DataFrame (handles multi-index)"""
    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0):
            close = df['Close']
            return close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close
        elif 'Adj Close' in df.columns.get_level_values(0):
            adj_close = df['Adj Close']
            return adj_close.iloc[:, 0] if isinstance(adj_close, pd.DataFrame) else adj_close
    else:
        if 'Close' in df.columns:
            return df['Close']
        elif 'Adj Close' in df.columns:
            return df['Adj Close']

    return None


def calculate_return(prices: pd.Series, periods: int) -> Optional[float]:
    """Calculate percentage return over N periods"""
    if prices is None or len(prices) < periods:
        return None

    try:
        start_price = prices.iloc[-periods]
        end_price = prices.iloc[-1]

        if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
            return None

        return ((end_price - start_price) / start_price) * 100
    except:
        return None


def calculate_volatility(prices: pd.Series) -> float:
    """Calculate annualized volatility"""
    if prices is None or len(prices) < 2:
        return 0.0

    daily_returns = prices.pct_change().dropna()
    if len(daily_returns) < 2:
        return 0.0

    return daily_returns.std() * (252 ** 0.5)


# ============================================================================
# TOOL 1: MARKET REGIME DATA LOADERS
# ============================================================================

def fetch_vix(use_india_vix: bool = True) -> Optional[float]:
    """
    Fetch current VIX (volatility index)

    Returns: Current VIX value or None
    """
    cache_key = "vix_current"
    cached = _cache.get(cache_key)
    if cached is not None:
        print(f"📦 Using cached VIX: {cached:.2f}")
        return cached

    try:
        ticker = DataConfig.INDIA_VIX_TICKER if use_india_vix else DataConfig.US_VIX_TICKER
        df = yf.download(ticker, period="5d", progress=False, auto_adjust=True)

        if df.empty:
            print(f"⚠️  India VIX unavailable, trying US VIX...")
            if use_india_vix:  # Try US VIX as fallback
                return fetch_vix(use_india_vix=False)
            return None

        prices = extract_close_prices(df)
        if prices is None or prices.empty:
            return None

        vix_value = float(prices.iloc[-1])
        _cache.set(cache_key, vix_value)
        return vix_value

    except Exception as e:
        print(f"❌ VIX fetch error: {e}")
        return None


def fetch_nifty_trend(days: int = 90) -> Optional[pd.DataFrame]:
    """
    Fetch Nifty 50 historical data for trend analysis

    Returns: DataFrame with price data
    """
    cache_key = f"nifty_trend_{days}"
    cached = _cache.get(cache_key)
    if cached is not None:
        print(f"📦 Using cached Nifty data ({len(cached)} days)")
        return cached

    try:
        # Fetch extra days to account for weekends/holidays
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 60)  # Increased buffer

        df = yf.download(
            DataConfig.NIFTY50_TICKER,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            print("⚠️  Nifty 50 data unavailable")
            return None

        # Accept data even if slightly less than 90 days (due to holidays)
        if len(df) < 60:
            print(f"⚠️  Nifty 50 insufficient data (got {len(df)} days, need at least 60)")
            return None

        _cache.set(cache_key, df)
        print(f"✅ Fetched Nifty 50 data: {len(df)} days")
        return df

    except Exception as e:
        print(f"❌ Nifty fetch error: {e}")
        return None


def normalize_vix_to_volatility_level(vix: Optional[float]) -> float:
    """
    Normalize VIX to 0-1 scale for Tool 1

    Typical ranges:
    - VIX < 15: Low volatility (0.0 - 0.3)
    - VIX 15-25: Moderate (0.3 - 0.6)
    - VIX 25-40: High (0.6 - 0.9)
    - VIX > 40: Extreme (0.9 - 1.0)
    """
    if vix is None:
        print("⚠️  VIX unavailable, defaulting to moderate (0.5)")
        return 0.5

    if vix < 15:
        return 0.0 + (vix / 15) * 0.3
    elif vix < 25:
        return 0.3 + ((vix - 15) / 10) * 0.3
    elif vix < 40:
        return 0.6 + ((vix - 25) / 15) * 0.3
    else:
        return min(1.0, 0.9 + (vix - 40) / 20 * 0.1)


def calculate_equity_trend_score(df: Optional[pd.DataFrame]) -> float:
    """
    Calculate equity trend score (-1 to +1) from Nifty data

    Logic:
    - Compare current price vs 20-day, 50-day moving averages
    - Positive trend = price above MAs
    - Negative trend = price below MAs
    - Adapts to available data (if less than 90 days)
    """
    if df is None or df.empty:
        print("⚠️  Nifty data unavailable, defaulting to neutral (0.0)")
        return 0.0

    prices = extract_close_prices(df)
    if prices is None or len(prices) < 20:
        print("⚠️  Insufficient Nifty data, defaulting to neutral (0.0)")
        return 0.0

    current_price = prices.iloc[-1]

    # Calculate moving averages based on available data
    score = 0.0

    # 20-day MA (always available if we have 20+ days)
    if len(prices) >= 20:
        ma_20 = prices.iloc[-20:].mean()
        if current_price > ma_20:
            score += 0.5
        else:
            score -= 0.5

    # 50-day MA (if available)
    if len(prices) >= 50:
        ma_50 = prices.iloc[-50:].mean()
        if current_price > ma_50:
            score += 0.3
        else:
            score -= 0.3

    # 90-day MA (if available)
    if len(prices) >= 90:
        ma_90 = prices.iloc[-90:].mean()
        if current_price > ma_90:
            score += 0.2
        else:
            score -= 0.2

    return max(-1.0, min(1.0, score))


def mock_rate_direction() -> int:
    """
    Mock interest rate direction

    TODO: Replace with real RBI repo rate API
    Returns: -1 (cutting), 0 (neutral), 1 (hiking)
    """
    return 0


def mock_inflation_level() -> float:
    """
    Mock inflation level

    TODO: Replace with real CPI data
    Returns: 0-1 scale (0 = low, 1 = high)
    """
    return 0.5


def mock_yield_curve_slope() -> float:
    """
    Mock yield curve slope

    TODO: Replace with real 10Y-2Y treasury spread
    Returns: Positive = normal, Negative = inverted
    """
    return 0.5


def load_market_regime_inputs() -> Dict:
    """
    Load ALL data needed for Tool 1 (Market Regime)

    Returns: Dict with normalized signals ready for Tool 1
    """
    print("\n" + "="*70)
    print("📊 LOADING MARKET REGIME DATA")
    print("="*70)

    # Fetch live data
    vix = fetch_vix()
    nifty_data = fetch_nifty_trend()

    # Normalize to signals
    volatility_level = normalize_vix_to_volatility_level(vix)
    equity_trend_score = calculate_equity_trend_score(nifty_data)

    # Mock data (TODO: replace with real APIs)
    rate_direction = mock_rate_direction()
    inflation_level = mock_inflation_level()
    yield_curve_slope = mock_yield_curve_slope()

    vix_display = f"{vix:.2f}" if vix is not None else "N/A"
    print(f"\n✅ VIX: {vix_display} → Volatility Level: {volatility_level:.2f}")
    print(f"✅ Equity Trend Score: {equity_trend_score:+.2f}")
    print(f"⚠️  Rate Direction: {rate_direction} (mocked)")
    print(f"⚠️  Inflation Level: {inflation_level:.2f} (mocked)")
    print(f"⚠️  Yield Curve: {yield_curve_slope:+.2f} (mocked)")
    print("="*70 + "\n")

    return {
        "equity_trend_score": equity_trend_score,
        "volatility_level": volatility_level,
        "rate_direction": rate_direction,
        "inflation_level": inflation_level,
        "yield_curve_slope": yield_curve_slope,
    }


# ============================================================================
# TOOL 3: SECTOR ROTATION DATA LOADERS
# ============================================================================

def fetch_sector_data(sector: str, days: int = 100) -> Optional[pd.DataFrame]:
    """
    Fetch price data for a specific sector

    Returns: DataFrame with OHLCV data
    """
    cache_key = f"sector_{sector}_{days}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    ticker = DataConfig.NSE_SECTORS.get(sector)
    if not ticker:
        print(f"❌ Unknown sector: {sector}")
        return None

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )

        if df.empty or len(df) < 5:
            return None

        _cache.set(cache_key, df)
        return df

    except Exception as e:
        return None


def fetch_all_sector_data(days: int = 100) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for all NSE sectors

    Returns: Dict of {sector_name: DataFrame}
    """
    print(f"📊 Fetching {len(DataConfig.NSE_SECTORS)} sectors...")

    sector_data = {}
    for sector in DataConfig.NSE_SECTORS.keys():
        df = fetch_sector_data(sector, days)
        if df is not None:
            sector_data[sector] = df

    return sector_data


def calculate_sector_performance(
    sector_data: Dict[str, pd.DataFrame],
    benchmark_data: Optional[pd.DataFrame] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics for all sectors

    Returns: Dict of {sector: {return_1w, return_1m, return_3m, volatility, relative_strength}}
    """
    if benchmark_data is None:
        benchmark_data = fetch_nifty_trend(100)

    # Calculate benchmark returns
    benchmark_prices = extract_close_prices(benchmark_data)
    benchmark_returns = {
        "1w": calculate_return(benchmark_prices, 5) or 0,
        "1m": calculate_return(benchmark_prices, 21) or 0,
        "3m": calculate_return(benchmark_prices, 63) or 0,
    }

    sector_performance = {}

    for sector, df in sector_data.items():
        prices = extract_close_prices(df)

        if prices is None:
            continue

        return_1w = calculate_return(prices, 5) or 0
        return_1m = calculate_return(prices, 21) or 0
        return_3m = calculate_return(prices, 63) or 0
        volatility = calculate_volatility(prices)
        relative_strength = return_1m - benchmark_returns["1m"]

        sector_performance[sector] = {
            "return_1w": return_1w,
            "return_1m": return_1m,
            "return_3m": return_3m,
            "volatility": volatility,
            "relative_strength": relative_strength,
        }

        print(f"✅ {sector}: 1W={return_1w:+.2f}% | 1M={return_1m:+.2f}% | 3M={return_3m:+.2f}%")

    return sector_performance


def load_sector_rotation_data() -> Dict[str, Dict[str, float]]:
    """
    Load ALL data needed for Tool 3 (Sector Rotation)

    Returns: Dict with sector performance metrics
    """
    print("\n" + "="*70)
    print("📊 LOADING SECTOR ROTATION DATA")
    print("="*70 + "\n")

    # Fetch all sector data
    sector_data = fetch_all_sector_data(days=100)

    if not sector_data:
        raise ValueError("❌ Failed to fetch any sector data")

    print(f"\n📈 Calculating performance for {len(sector_data)} sectors...\n")

    # Calculate performance metrics
    performance = calculate_sector_performance(sector_data)

    print("\n" + "="*70)
    print(f"✅ Sector data loaded: {len(performance)} sectors")
    print("="*70 + "\n")

    return performance


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_cache():
    """Clear all cached data (useful for forcing fresh fetches)"""
    _cache.clear()


def get_cache_info() -> Dict:
    """Get cache statistics"""
    return {
        "cached_items": len(_cache._cache),
        "ttl_seconds": _cache._ttl,
    }

#==============================================================================
#  TOOL 4 : fundamentals sanity check
#==============================================================================
def fetch_fundamental_metrics(ticker: str) -> Dict[str, float]:
    """
    Fetches key fundamental ratios for Sanity Check.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # We extract the 'raw' values to calculate or use directly
        metrics = {
            "debt_to_equity": info.get('debtToEquity', 0) / 100, # Convert to decimal
            "current_ratio": info.get('currentRatio', 0),
            "roe": info.get('returnOnEquity', 0),
            "operating_margin": info.get('operatingMargins', 0),
            "free_cash_flow": info.get('freeCashflow', 0),
            "market_cap": info.get('marketCap', 0)
        }
        return metrics
    except Exception as e:
        print(f"⚠️ Could not fetch fundamentals for {ticker}: {e}")
        return {}
#==============================================================================
#  TOOL 5 : valuation sanity check
#==============================================================================

def fetch_valuation_metrics(ticker: str) -> Dict[str, float]:
    """
    Fetches valuation specific data from yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "current_pe": info.get('forwardPE', info.get('trailingPE', 0)),
            "five_year_avg_pe": info.get('trailingPegRatio', 0), # yfinance PEG is sometimes used as a proxy
            "price_to_book": info.get('priceToBook', 0),
            "peg_ratio": info.get('pegRatio', 0),
            "dividend_yield": info.get('dividendYield', 0)
        }
    except:
        return {}
#==============================================================================
#  TOOL 6 : oppertunity cost

#=============================================================================

def fetch_performance_metrics(ticker: str) -> float:
    """
    Fetches the 1-year trailing return of an instrument.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return 0.0

        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        return ((end_price - start_price) / start_price) * 100
    except:
        return 0.0

#==============================================================================
#  TOOL 8
#=============================================================================
def fetch_forward_estimates(ticker: str) -> Dict[str, float]:
    """
    Fetches forward-looking analyst estimates.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "forward_eps": info.get('forwardEps', 0),
            "trailing_eps": info.get('trailingEps', 0),
            "growth_rate": info.get('earningsQuarterlyGrowth', 0),
            "target_price": info.get('targetMeanPrice', 0)
        }
    except:
        return {}

#bloat code need a resolve if it runs
# ADD THIS TO THE BOTTOM OF YOUR CURRENT LOADER.PY
def fetch_sector_performance() -> Dict[str, Dict[str, float]]:
    """
    Alias function to connect the existing logic
    to the name expected by workflow.py
    """
    return load_sector_rotation_data()

# --- WORKFLOW BRIDGE ---
def fetch_sector_performance() -> Dict[str, Dict[str, float]]:
    """
    Bridge function to connect your existing logic
    to the name expected by workflow.py
    """
    return load_sector_rotation_data()

def fetch_sector_performance():
    """Workflow Bridge for Tool 3"""
    return load_sector_rotation_data()
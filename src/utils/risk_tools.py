import numpy as np
import pandas as pd
import yfinance as yf
import logging
from typing import List, Dict, Any, Union

logger = logging.getLogger(__name__)

def get_comprehensive_risk_metrics(tickers: List[str], benchmark: str = "^NSEI") -> Dict[str, Union[float, str]]:
    """
    Calculates institutional-grade risk metrics:
    - Volatility (Annualized)
    - Max Drawdown
    - Beta (vs Nifty 50)
    - Value at Risk (95% Confidence)
    """
    try:
        if not tickers:
            return {"error": "No tickers provided"}

        # 1. Fetch Data (Portfolio + Benchmark)
        # We fetch 1 year of data to get a statistical sample
        data = yf.download(tickers + [benchmark], period="1y", progress=False)['Close']
        
        # Handle cases where data might be missing
        if data.empty:
            return {"error": "Failed to fetch market data"}

        # 2. Calculate Daily Returns
        returns = data.pct_change().dropna()
        
        # Separate Portfolio and Benchmark
        # handle single ticker case by checking if it's a Series or DataFrame
        if len(tickers) == 1:
            port_returns = returns[tickers[0]]
        else:
            # Assume Equal Weights (1/N) for the audit
            port_returns = returns[tickers].mean(axis=1)
            
        bench_returns = returns[benchmark]
        
        # 3. Calculate Metrics
        
        # A. Volatility (Annualized Standard Deviation)
        vol = port_returns.std() * np.sqrt(252) * 100
        
        # B. Beta (Sensitivity to Market)
        # Covariance(Port, Market) / Variance(Market)
        covariance = np.cov(port_returns, bench_returns)[0][1]
        market_variance = np.var(bench_returns)
        beta = covariance / market_variance
        
        # C. Value at Risk (VaR 95%)
        # The 5th percentile of daily returns (worst 5% of days)
        var_95 = np.percentile(port_returns, 5) * 100 
        
        # D. Max Drawdown
        cum_returns = (1 + port_returns).cumprod()
        peak = cum_returns.cummax()
        drawdown = (cum_returns - peak) / peak
        max_dd = drawdown.min() * 100

        return {
            "volatility": round(vol, 2),
            "beta": round(beta, 2),
            "var_95": round(var_95, 2),
            "max_drawdown": round(max_dd, 2)
        }
    except Exception as e:
        logger.error(f"Risk calc failed: {e}")
        return {"error": str(e)}

def analyze_diversification(tickers: List[str]) -> Dict[str, Any]:
    """
    Checks for 'Hidden Concentration' risk by calculating the average correlation.
    If stocks move together (Correlation > 0.7), diversification is fake.
    """
    try:
        if len(tickers) < 2:
            return {"status": "Concentrated", "avg_correlation": 1.0, "message": "Single asset portfolio."}

        data = yf.download(tickers, period="6mo", progress=False)['Close']
        returns = data.pct_change().dropna()
        
        # Correlation Matrix
        corr_matrix = returns.corr()
        
        # Calculate Average Correlation (excluding the diagonal 1.0s)
        # Sum of matrix minus diagonal (len(tickers)), divided by N*(N-1)
        sum_corr = corr_matrix.sum().sum() - len(tickers)
        count = (len(tickers)**2) - len(tickers)
        avg_corr = sum_corr / count
        
        # Interpret the Score
        if avg_corr > 0.7:
            status = "High Risk (Highly Correlated)"
        elif avg_corr > 0.4:
            status = "Moderate Correlation"
        else:
            status = "Well Diversified"
            
        return {
            "avg_correlation": round(avg_corr, 2),
            "diversification_status": status
        }
    except Exception as e:
        return {"error": str(e)}

def run_stress_test(tickers: List[str], scenario: str = "market_crash") -> Dict[str, float]:
    """
    Simulates a 'What If' scenario based on Beta.
    Scenarios:
    - 'market_crash': Nifty drops 20%
    - 'correction': Nifty drops 10%
    """
    try:
        metrics = get_comprehensive_risk_metrics(tickers)
        if "error" in metrics: return metrics
        
        beta = metrics.get("beta", 1.0)
        
        # Define scenarios
        scenarios = {
            "market_crash": -20.0, # 2008 style
            "correction": -10.0,   # Standard correction
            "bear_market": -30.0   # Deep recession
        }
        
        market_drop = scenarios.get(scenario, -20.0)
        
        # Expected Loss = Beta * Market Drop
        expected_loss = beta * market_drop
        
        return {
            "scenario": scenario,
            "market_drop": market_drop,
            "portfolio_beta": beta,
            "expected_portfolio_loss": round(expected_loss, 2)
        }
    except Exception:
        return {"expected_portfolio_loss": 0.0}
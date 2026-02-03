

from loader import (
    fetch_fundamental_metrics,
    fetch_performance_metrics,
    fetch_forward_estimates,
    fetch_valuation_metrics
)

from contracts import (
    MarketRegime, LiquidityState, RiskState, MarketRegimeInput, MarketRegimeOutput,
    AssetRating, AssetSuitabilityOutput, SectorSignal, SectorRotationOutput,
    ScannedInstrument, InstrumentScreenerOutput, SECTOR_MAP, SanityCheckResult,
    ValuationResult, OppCostResult, ForwardAudit, SentimentAudit
)


#========================================================
# TOOL1
#========================================================


# -----------------------------
# 3. CORE LOGIC
# -----------------------------
def market_regime_tool(input_data: MarketRegimeInput) -> MarketRegimeOutput:
    """
    Classifies the current macro environment.
    Strategy: Uses weighted factor analysis of trend, vol, rates, and curve.
    """
    drivers = []

    # --- A. Liquidity State Logic ---
    liquidity_map = {1: LiquidityState.TIGHTENING, -1: LiquidityState.EASING, 0: LiquidityState.NEUTRAL}
    liquidity_state = liquidity_map[input_data.rate_direction]

    if input_data.rate_direction == 1:
        drivers.append("Tightening liquidity (Rising Rates)")
    elif input_data.rate_direction == -1:
        drivers.append("Easing liquidity (Rate Cuts)")

    # --- B. Risk Score Calculation ---
    # We use a base sensitivity model
    risk_score = (input_data.equity_trend_score * 1.5) - \
                 (input_data.volatility_level * 2.0) - \
                 (input_data.inflation_level * 1.0)

    if input_data.yield_curve_slope < 0:
        risk_score -= 1.0
        drivers.append("Yield curve inversion (Recession signal)")

    # Qualitative Driver Tracking
    if input_data.equity_trend_score > 0.4: drivers.append("Bullish momentum")
    elif input_data.equity_trend_score < -0.4: drivers.append("Bearish momentum")
    if input_data.volatility_level > 0.6: drivers.append("High volatility stress")
    if input_data.inflation_level > 0.7: drivers.append("High inflationary pressure")

    # --- C. Regime Classification Engine ---
    if input_data.yield_curve_slope < 0 and input_data.rate_direction == 1:
        regime = MarketRegime.LATE_CYCLE
    elif risk_score >= 0.7 and input_data.volatility_level < 0.4:
        regime = MarketRegime.RISK_ON
    elif risk_score <= -1.0:
        regime = MarketRegime.RISK_OFF
    elif liquidity_state == LiquidityState.EASING and input_data.equity_trend_score > -0.2:
        regime = MarketRegime.RECOVERY
    else:
        regime = MarketRegime.TRANSITION

    # --- D. Risk State Determination ---
    if risk_score >= 0.6: risk_state = RiskState.LOW
    elif risk_score <= -0.8: risk_state = RiskState.HIGH
    else: risk_state = RiskState.MODERATE

    # --- E. Confidence Heuristic ---
    # High confidence if signals agree; lower if they conflict
    signal_agreement = 1.0 - abs(input_data.equity_trend_score + (-input_data.volatility_level)) / 2
    raw_conf = ( (1.0 - input_data.volatility_level) + signal_agreement ) / 2
    confidence = round(max(0.3, min(1.0, raw_conf)), 2)

    return MarketRegimeOutput(
        market_regime=regime,
        risk_state=risk_state,
        liquidity_state=liquidity_state,
        confidence=confidence,
        drivers=list(set(drivers)),
        raw_scores={"composite_risk_score": round(risk_score, 2)}
    )

#========================================================
# TOOL2
#========================================================
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# -----------------------------
# 2. CORE TOOL LOGIC
# -----------------------------

def asset_suitability_tool(regime_output: MarketRegimeOutput, volatility_index: float) -> AssetSuitabilityOutput:
    # 1. Sensitivity Matrix (0 = Defensive, 1 = Very Aggressive)
    # This 'risk_type' helps us decide if the asset should fall or rise during Risk-Off
    ASSET_SENSITIVITY = {
        "Savings_FD":   {"aggression": 0.0, "liquidity_need": 0.1, "inflation_hedge": 0.2},
        "Debt_Funds":   {"aggression": 0.2, "liquidity_need": 0.4, "inflation_hedge": 0.3},
        "Gold":         {"aggression": -0.5, "liquidity_need": 0.2, "inflation_hedge": 0.9}, # Negative aggression = Safe Haven
        "Equity":       {"aggression": 0.8, "liquidity_need": 0.7, "inflation_hedge": 0.5},
        "Real_Estate":  {"aggression": 0.4, "liquidity_need": 0.9, "inflation_hedge": 0.8},
        "Crypto":       {"aggression": 1.0, "liquidity_need": 1.0, "inflation_hedge": 0.1},
    }

    # 2. Score Mappings
    # In Risk-Off (-1.0), an asset with -0.5 aggression (Gold) becomes (-1.0 * -0.5) = +0.5 (Preferred!)
    REGIME_BASE = {
        MarketRegime.RISK_ON: 0.8,
        MarketRegime.RECOVERY: 0.5,
        MarketRegime.TRANSITION: 0.0,
        MarketRegime.LATE_CYCLE: -0.2,
        MarketRegime.RISK_OFF: -0.8
    }

    results = {}
    base_val = REGIME_BASE[regime_output.market_regime]

    # Volatility penalty only applies to high-aggression assets
    vol_impact = 0.5 if volatility_index > 25 else 0.0

    for asset, weights in ASSET_SENSITIVITY.items():
        # CORE LOGIC:
        # For Equities: (-0.8 base) + (0.8 aggression * -0.8) = Deep Red
        # For Gold: (-0.8 base) + (-0.5 aggression * -0.8) = -0.8 + 0.4 = -0.4 (Better than Equity)

        # We also add a 'Floor' for Savings/Gold so they never get 'Rejected' in a crisis
        aggression_score = weights["aggression"] * base_val

        # Safe Havens get a boost when base is negative
        if weights["aggression"] <= 0 and base_val < 0:
            score = abs(base_val) * 0.7 # Boost safe havens in a crash
        else:
            score = base_val + aggression_score - (vol_impact * weights["aggression"])

        # Map to Rating (Refined Thresholds)
        if score >= 0.4: rating = "Preferred"
        elif score >= -0.2: rating = "Neutral"
        elif score >= -0.7: rating = "Avoid"
        else: rating = "Reject"

        results[asset] = AssetRating(
            rating=rating,
            confidence=regime_output.confidence,
            score=round(score, 2),
            reason=f"Defensive profile check during {regime_output.market_regime.value}."
        )

    return AssetSuitabilityOutput(
        regime=regime_output.market_regime.value,
        risk_state=regime_output.risk_state.value,
        asset_class_ratings=results
    )

#========================================================
# TOOL3
#========================================================
from typing import Dict, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime



# -----------------------------
# 2. CORE TOOL LOGIC
# -----------------------------

def sector_rotation_tool(
    regime_output: MarketRegimeOutput,
    sector_performance: Dict[str, Dict[str, float]]
) -> SectorRotationOutput:
    """
    Pure Logic Tool: Ranks sectors by combining Loader Momentum + Regime Fit.
    """

    # --- A. Regime-Sector Alignment Matrix ---
    # 1.0 = Strong Fit, 0.5 = Neutral, 0.0 = Poor Fit
    REGIME_FIT = {
        MarketRegime.RISK_ON: {
            "IT": 0.9, "Banking": 0.8, "Auto": 0.8, "Realty": 0.7, "Metals": 0.6, "FMCG": 0.4, "Pharma": 0.3
        },
        MarketRegime.RISK_OFF: {
            "Pharma": 0.9, "FMCG": 0.9, "IT": 0.7, "Banking": 0.4, "Metals": 0.3, "Auto": 0.3, "Realty": 0.2
        },
        MarketRegime.RECOVERY: {
            "Banking": 0.9, "Auto": 0.8, "Realty": 0.8, "Metals": 0.7, "IT": 0.6, "Pharma": 0.3
        },
        MarketRegime.LATE_CYCLE: {
            "Energy": 0.9, "Metals": 0.8, "FMCG": 0.6, "Banking": 0.5, "IT": 0.4
        }
    }

    results = {}
    current_regime = regime_output.market_regime
    regime_map = REGIME_FIT.get(current_regime, REGIME_FIT[MarketRegime.RISK_ON])

    for sector, metrics in sector_performance.items():
        # 1. Momentum Calculation (40% weight in final)
        # Using the standardized returns from loader.py
        m_raw = (metrics.get("return_1w", 0) * 0.2) + \
                (metrics.get("return_1m", 0) * 0.5) + \
                (metrics.get("return_3m", 0) * 0.3)

        # Normalize momentum to a 0-1 scale for combination
        m_score = max(0, min(1, (m_raw + 10) / 20))

        # 2. Macro Score (60% weight in final)
        # Check if sector keyword exists in our regime map
        macro_score = 0.5 # Default
        for key in regime_map:
            if key in sector:
                macro_score = regime_map[key]

        # 3. Composite Score
        composite = (macro_score * 0.6) + (m_score * 0.4)

        # 4. Recommendation Mapping
        if composite >= 0.65: rec = "Overweight"
        elif composite <= 0.40: rec = "Underweight"
        else: rec = "Neutral"

        results[sector] = SectorSignal(
            sector_name=sector,
            recommendation=rec,
            momentum_score=round(m_raw, 2),
            macro_score=round(macro_score, 2),
            composite_score=round(composite, 2),
            reasoning=f"Alignment with {current_regime.value} and momentum of {m_raw:.1f}%"
        )

    # 5. Sorting and Highlights
    sorted_sectors = sorted(results.items(), key=lambda x: x[1].composite_score, reverse=True)
    top_3 = [s[0] for s in sorted_sectors[:3]]
    avoid_3 = [s[0] for s in sorted_sectors[-3:]]

    return SectorRotationOutput(
        timestamp=datetime.now(),
        sector_signals=results,
        rotation_narrative=f"System identifies {current_regime.value} regime. Top picks: {', '.join(top_3)}",
        top_sectors=top_3,
        avoid_sectors=avoid_3,
        confidence_score=regime_output.confidence
    )

#========================================================
# TOOL 4
#========================================================
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field


# -----------------------------
# 3. CORE TOOL LOGIC
# -----------------------------

def instrument_screener_tool(
    regime_output: MarketRegimeOutput,
    target_sectors: List[str],
    universe_tickers: List[str]
) -> InstrumentScreenerOutput:
    """
    Screens a list of tickers with a 3-layer filter:
    1. Sector Alignment (Contextual)
    2. Fundamental Health (Safety)
    3. Technical Trend (Momentum)
    """
    screened_results = []

    print(f"🔍 Starting scan of {len(universe_tickers)} instruments...")
    print(f"🎯 Target Strategy: {target_sectors}")

    for ticker in universe_tickers:
        try:
            # A. Fetch Live Data
            stock = yf.Ticker(ticker)
            info = stock.info

            # B. SECTOR VALIDATION GATE
            raw_sector = info.get('sector', 'Unknown')
            is_aligned = False

            for target in target_sectors:
                # Check for direct match or use the mapping
                possible_names = SECTOR_MAP.get(target, [target])
                if any(name.lower() in raw_sector.lower() for name in possible_names):
                    is_aligned = True
                    break

            if not is_aligned:
                continue # Skip stocks that don't match our strategy

            # C. FUNDAMENTAL HEALTH (40% of Score)
            roe = info.get('returnOnEquity', 0)
            de_ratio = info.get('debtToEquity', 100) / 100

            f_score = 0.5 # Baseline
            if roe > 0.15: f_score += 0.2
            if de_ratio < 1.0: f_score += 0.3

            # D. TECHNICAL TREND (60% of Score)
            # Fetch last 250 days to calculate 200-day Moving Average
            hist = stock.history(period="250d")
            if len(hist) < 200: continue

            sma_200 = hist['Close'].iloc[-200:].mean()
            current_price = hist['Close'].iloc[-1]

            # Bonus points for being in an uptrend
            t_score = 1.0 if current_price > sma_200 else 0.3

            # E. FINAL SCORING
            composite = (t_score * 0.6) + (f_score * 0.4)

            screened_results.append({
                "ticker": ticker,
                "name": info.get('shortName', ticker),
                "sector": raw_sector,
                "score": round(composite, 2),
                "reason": f"Strategic fit in {raw_sector}. Price is {'above' if current_price > sma_200 else 'below'} 200-MA."
            })

        except Exception as e:
            # Silently skip errors to keep the pipeline moving
            continue

    # F. RANK AND CAP AT TOP 10
    sorted_list = sorted(screened_results, key=lambda x: x['score'], reverse=True)

    top_10_picks = []
    for i, item in enumerate(sorted_list[:10]):
        top_10_picks.append(ScannedInstrument(
            ticker=item['ticker'],
            name=item['name'],
            sector=item['sector'],
            composite_score=item['score'],
            rank=i + 1,
            recommendation_reason=item['reason']
        ))

    return InstrumentScreenerOutput(
        timestamp=datetime.now(),
        regime=regime_output.market_regime.value,
        top_picks=top_10_picks
    )

print("✅ Tool 4: Instrument Screener ready.")

#========================================================
# TOOL5
#========================================================
from pydantic import BaseModel
from typing import List, Dict



def fundamental_sanity_check_tool(
    candidates: List[ScannedInstrument],
    regime_output: MarketRegimeOutput
) -> Dict[str, SanityCheckResult]:
    """
    Performs a deep-dive audit.
    Handles missing data and sector-specific debt rules.
    """
    audit_results = {}

    is_risk_off = regime_output.market_regime == MarketRegime.RISK_OFF

    for stock in candidates:
        # 1. Fetch live metrics
        m = fetch_fundamental_metrics(stock.ticker)

        # --- NULL SAFETY: Provide defaults if data is missing ---
        # We use .get(key, default) to prevent 'NoneType' errors
        de = m.get("debt_to_equity") if m.get("debt_to_equity") is not None else 0.0
        roe = m.get("roe") if m.get("roe") is not None else 0.10
        cr = m.get("current_ratio") if m.get("current_ratio") is not None else 1.5

        red_flags = []
        score = 100

        # --- TEST 1: Sector-Aware Debt Check ---
        # Banks/Financials naturally have high D/E. We ignore it for them.
        is_financial = any(x in stock.sector for x in ["Financial", "Banking", "Banks"])

        max_de = 0.5 if is_risk_off else 1.5
        if not is_financial and de > max_de:
            red_flags.append(f"High Leverage: {de:.2f}")
            score -= 40

        # --- TEST 2: Liquidity (Current Ratio) ---
        if cr < 1.1:
            red_flags.append(f"Low Liquidity: {cr:.2f}")
            score -= 30

        # --- TEST 3: Profitability (ROE) ---
        target_roe = 0.15 if is_risk_off else 0.10
        if roe < target_roe:
            red_flags.append(f"Weak ROE: {roe*100:.1f}%")
            score -= 30

        # Decision Logic
        is_safe = score >= 60 and len(red_flags) < 2

        audit_results[stock.ticker] = SanityCheckResult(
            ticker=stock.ticker,
            pass_status=is_safe,
            health_score=score,
            red_flags=red_flags,
            audit_remark="PASSED" if is_safe else "FAILED"
        )

    return audit_results

#========================================================
# TOOL 6
#========================================================
import yfinance as yf
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime



# -----------------------------
# 2. CORE TOOL LOGIC
# -----------------------------

def valuation_sanity_check_tool(candidates: List[ScannedInstrument]) -> Dict[str, ValuationResult]:
    """
    Analyzes stock price justification. Handles missing yfinance data gracefully.
    """
    valuation_reports = {}

    for stock in candidates:
        try:
            # 1. Fetch live data
            ticker_obj = yf.Ticker(stock.ticker)
            info = ticker_obj.info

            # --- NULL SAFETY: Extract values with defaults ---
            t_pe = info.get('trailingPE')
            f_pe = info.get('forwardPE')
            peg = info.get('pegRatio')
            pb = info.get('priceToBook')

            # Default scoring starts at 100
            score = 100
            red_flags = []

            # 2. TEST: The PEG Ratio (Growth vs. Price)
            # If PEG is missing, we don't penalize, we just move on
            if peg is not None:
                if peg > 2.5:
                    score -= 30
                    red_flags.append(f"High PEG ({peg:.2f})")
                elif peg > 4.0:
                    score -= 50
                    red_flags.append("Extreme Valuation Bubble")

            # 3. TEST: P/E Expansion
            if f_pe and t_pe and f_pe > t_pe:
                score -= 15
                red_flags.append("Earnings expected to contract")

            # 4. TEST: Absolute P/E Gate (Indian Market Context)
            if t_pe and t_pe > 80:
                score -= 30
                red_flags.append(f"High P/E Multiplier ({t_pe:.1f})")

            # Determine Status
            if score >= 80: status = "Fair Value"
            elif score >= 60: status = "Premium"
            elif score >= 40: status = "Expensive"
            else: status = "Overheated"

            # Final Decision: Must score at least 50
            is_safe = score >= 50

            valuation_reports[stock.ticker] = ValuationResult(
                ticker=stock.ticker,
                valuation_status=status,
                valuation_score=score,
                is_safe_to_buy=is_safe,
                metrics={
                    "trailing_pe": t_pe if t_pe else 0.0,
                    "peg_ratio": peg if peg else 0.0,
                    "pb_ratio": pb if pb else 0.0
                },
                remark=f"Valuation: {status}. " + (f"Flags: {', '.join(red_flags)}" if red_flags else "No major price concerns.")
            )

        except Exception as e:
            # If a major error occurs, we create a 'Neutral' fallback so the dashboard doesn't break
            print(f"⚠️ Warning: Could not fully audit {stock.ticker}: {e}")
            valuation_reports[stock.ticker] = ValuationResult(
                ticker=stock.ticker,
                valuation_status="Data Unavailable",
                valuation_score=50,
                is_safe_to_buy=True,
                metrics={},
                remark="Audit skipped due to missing API data."
            )

    return valuation_reports

#========================================================
# TOOL 7
#========================================================
from pydantic import BaseModel
from typing import List, Dict



def opportunity_cost_tool(
    candidates: List[ScannedInstrument],
    risk_free_rate: float = 7.1  # Current 10Y Indian Bond Yield %
) -> Dict[str, OppCostResult]:
    """
    Calculates if the stock is likely to beat a Risk-Free Bond.
    Logic: Net Alpha = Stock Return - (Risk Free Rate + Risk Premium)
    """
    # We add a 3% 'Risk Premium' because stocks are riskier than bonds
    required_hurdle = risk_free_rate + 3.0
    opp_reports = {}

    for stock in candidates:
        actual_return = fetch_performance_metrics(stock.ticker)
        net_alpha = actual_return - required_hurdle

        is_efficient = net_alpha > 0

        opp_reports[stock.ticker] = OppCostResult(
            ticker=stock.ticker,
            stock_expected_return=round(actual_return, 2),
            hurdle_rate=round(required_hurdle, 2),
            opportunity_gain_loss=round(net_alpha, 2),
            verdict="🚀 Alpha Generator" if is_efficient else "⚠️ Capital Waster"
        )

    return opp_reports

print("✅ Tool 7: Opportunity Cost Computer ready.")

#========================================================
# TOOL 8
#========================================================



# -----------------------------
# 2. CORE TOOL LOGIC
# -----------------------------
def forward_risk_opportunity_tool(candidates: List[ScannedInstrument]) -> Dict[str, ForwardAudit]:
    """
    Analyzes analyst price targets and EPS growth to determine future viability.
    """
    forward_reports = {}

    for stock in candidates:
        try:
            # 1. Fetch live forward data (Ensure these exist in loader.py)
            # In your setup, this likely calls a helper function you built earlier
            est = fetch_forward_estimates(stock.ticker)
            ticker_obj = yf.Ticker(stock.ticker)

            # --- NULL SAFETY: Handles missing analyst data ---
            f_eps = est.get("forward_eps") or 0.0
            t_eps = est.get("trailing_eps") or 0.0
            target = est.get("target_price") or 0.0

            # Fetch current price for upside math
            hist = ticker_obj.history(period="1d")
            if hist.empty:
                continue
            curr_price = hist['Close'].iloc[-1]

            # 2. Logic: Upside Calculation
            # Prevents division by zero or crashing on missing targets
            upside = ((target - curr_price) / curr_price) * 100 if target > 0 else 0.0

            # 3. Logic: Growth Outlook
            outlook = "Positive" if f_eps > t_eps and f_eps != 0 else "Neutral/Negative"

            # 4. Logic: Forward Risk Score (0-100)
            risk_score = 30 # Base risk
            if outlook == "Neutral/Negative":
                risk_score += 30
            if upside <= 0:
                risk_score += 20

            # Verdict Logic: High Conviction requires growth AND manageable risk
            verdict = "🚀 HIGH CONVICTION" if (outlook == "Positive" and risk_score < 60) else "⚠️ UNCERTAIN"

            forward_reports[stock.ticker] = ForwardAudit(
                ticker=stock.ticker,
                growth_outlook=outlook,
                forward_risk_score=float(risk_score),
                upside_potential=round(float(upside), 2),
                verdict=verdict
            )
        except Exception as e:
            print(f"⚠️ Risk analysis error for {stock.ticker}: {e}")
            # Fallback to prevent breaking the workflow loop
            continue

    return forward_reports

#========================================================
# TOOL 9
#========================================================
from pydantic import BaseModel
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yfinance as yf
from typing import List, Dict


def reddit_sentiment_tool(candidates: List[ScannedInstrument]) -> Dict[str, SentimentAudit]:
    """
    Safely scans news sentiment. If 'title' or news is missing,
    it returns a fallback to prevent workflow KeyErrors.
    """
    try:
        sia = SentimentIntensityAnalyzer()
    except:
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        sia = SentimentIntensityAnalyzer()

    sentiment_reports = {}

    for stock in candidates:
        try:
            ticker_obj = yf.Ticker(stock.ticker)
            news = ticker_obj.news

            # SAFE EXTRACTION: Use .get() to prevent KeyError: 'title'
            if news and isinstance(news, list):
                headlines = [item.get('title', 'Market Update') for item in news[:10]]
            else:
                headlines = [f"No news available for {stock.ticker}"]

            # Sentiment Math
            scores = [sia.polarity_scores(h)['compound'] for h in headlines]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            status = "Neutral"
            if avg_score > 0.15: status = "Bullish"
            elif avg_score < -0.15: status = "Bearish"

            sentiment_reports[stock.ticker] = SentimentAudit(
                ticker=stock.ticker,
                sentiment_score=round(avg_score, 3),
                crowd_status=status,
                is_overhyped=avg_score > 0.85,
                verdict="✅ CROWD ALIGNED" if status != "Neutral" else "⚠️ CROWD SKEPTICAL"
            )

        except Exception as e:
            # FALLBACK: Prevents the entire workflow from crashing
            print(f"⚠️ Sentiment fallback triggered for {stock.ticker}: {e}")
            sentiment_reports[stock.ticker] = SentimentAudit(
                ticker=stock.ticker,
                sentiment_score=0.0,
                crowd_status="Neutral",
                is_overhyped=False,
                verdict="⚠️ DATA UNAVAILABLE"
            )

    return sentiment_reports

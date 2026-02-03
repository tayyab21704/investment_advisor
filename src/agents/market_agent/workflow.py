# workflow.py
import os
from dotenv import load_dotenv
from google import genai

# 1. Load the variables from the .env file into the environment
load_dotenv() 

# 2. Access the key using standard os.environ
os.environ["GEMINI_API_KEY"] = os.getenv('GEMINI_API_KEY')

# 3. Initialize the client (it now finds the key in the environment)
client = genai.Client()
import os
from google import genai
from typing import List, Dict
from contracts import MarketRegimeInput
from tools import (
    market_regime_tool, sector_rotation_tool, instrument_screener_tool,
    fundamental_sanity_check_tool, valuation_sanity_check_tool,
    opportunity_cost_tool, forward_risk_opportunity_tool, reddit_sentiment_tool
)
from loader import load_market_regime_inputs, load_sector_rotation_data

client = genai.Client()

def get_gemini_verdict(full_context: dict) -> str:
    prompt = f"Act as a Senior Investment Council. Based on this technical data: {full_context}..."
    response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
    return response.text

def run_invest_ai_workflow(universe_tickers: List[str]):
    print("🚀 Running Invest-AI Pipeline...")

    # Phase 1 & 2
    macro_input = load_market_regime_inputs()
    regime_out = market_regime_tool(MarketRegimeInput(**macro_input))
    sector_data = load_sector_rotation_data()
    rotation_out = sector_rotation_tool(regime_out, sector_data)
    screener_out = instrument_screener_tool(regime_out, rotation_out.top_sectors, universe_tickers)
    top_picks = screener_out.top_picks

    # Phase 3: Triple-Audit (With KeyError Protection)
    audit_data = []
    for stock in top_picks:
        ticker = stock.ticker

        # Use .get() fallbacks to ensure one failing tool doesn't kill the loop
        health = fundamental_sanity_check_tool([stock], regime_out).get(ticker)
        valuation = valuation_sanity_check_tool([stock]).get(ticker)
        opp_cost = opportunity_cost_tool([stock]).get(ticker)
        forward = forward_risk_opportunity_tool([stock]).get(ticker)
        sentiment = reddit_sentiment_tool([stock]).get(ticker)

        audit_data.append({
            "ticker": ticker,
            "name": stock.name,
            "health": health.model_dump() if health else {},
            "valuation": valuation.model_dump() if valuation else {},
            "opp_cost": opp_cost.model_dump() if opp_cost else {},
            "forward": forward.model_dump() if forward else {},
            "sentiment": sentiment.model_dump() if sentiment else {"verdict": "DATA_MISSING"}
        })

    # Phase 4: AI Reasoning
    final_context = {"regime": regime_out.model_dump(), "audits": audit_data}
    print("🧠 Gemini is generating your High-Conviction Report...")
    print("\n" + "="*50)
    print(get_gemini_verdict(final_context))
    print("="*50)

if __name__ == "__main__":
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
    run_invest_ai_workflow(tickers)
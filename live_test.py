import asyncio
import uuid
import logging
from src.orchestrator.graph import council_app

# Configure logging to see agent transitions in the console
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("LiveTest")

async def run_investment_council():
    """
    Triggers the full autonomous multi-agent council.
    """
    print("\n" + "="*60)
    print("🚀 INITIALIZING AUTONOMOUS INVESTMENT COUNCIL")
    print("="*60)

    # 1. Setup Thread Configuration for Persistence
    # This allows the MemorySaver to store the 'debate' history.
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # 2. Define Initial State (Simulating a User Profile)
    # In production, this would be fetched from your MongoDB.
    initial_state = {
        "user_id": "Mo_Tayyab_2026",
        "behavioral_answers": [8, 9, 7, 8, 9],  # High risk tolerance
        "raw_user_data": {
            "monthly_income": 120000,
            "monthly_expenses": 40000,
            "monthly_surplus": 80000,
            "liquidity_required_pct": 20,
            "max_single_asset_pct": 15
        },
        "user_profile": {
            "actual_risk_capacity": 8,  # Aggressive
            "monthly_surplus": 80000,
            "liquidity_required_pct": 20,
            "max_single_asset_pct": 15,
            "max_beta": 1.5
        },
        "iteration": 0,
        "agent_outputs": {},
        "scout_recommendations": [],
        "final_portfolio": []
    }

    # 3. Stream the execution to watch the "Thoughts" of each node
    try:
        print("\n🤖 Council is convening... Please wait for agent analysis.\n")
        
        # Using .astream allows us to see the output of each node as it finishes
        async for event in council_app.astream(initial_state, config=config):
            for node_name, output in event.items():
                print(f"\n📍 NODE COMPLETED: {node_name}")
                print("-" * 30)
                
                # Highlight key transitions
                if "decision" in output:
                    print(f"📢 ORCHESTRATOR VERDICT: {output['decision']}")
                
                if "final_portfolio" in output and output["final_portfolio"]:
                    print("💰 FINAL ALLOCATION GENERATED.")

        # 4. Fetch the final resulting state
        final_state = await council_app.ainvoke(initial_state, config=config)
        
        print("\n" + "="*60)
        print("🏆 FINAL INVESTMENT STRATEGY")
        print("="*60)
        print(f"Status: {final_state.get('decision')}")
        print(f"Reasoning: {final_state.get('orchestrator_decision', {}).get('reasoning')}")
        
        if final_state.get("final_portfolio"):
            print("\nALLOCATED PORTFOLIO:")
            for asset in final_state["final_portfolio"]:
                print(f"✅ {asset['ticker']} | ₹{asset['monthly_investment']} ({asset['allocation_pct']}%)")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"❌ Council Session Crashed: {e}")

if __name__ == "__main__":
    asyncio.run(run_investment_council())
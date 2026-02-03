import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# --- DATA MODELS FOR STORAGE ---

class SignalSnapshot(BaseModel):
    timestamp: str
    equity_trend_score: float
    volatility_level: float
    rate_direction: int
    inflation_level: float
    yield_curve_slope: float
    sector_performance: Dict[str, Any]
    metadata: Dict[str, Any]

class ToolResult(BaseModel):
    timestamp: str
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]

# --- STORAGE ENGINE ---

class DataStorage:
    def __init__(self, base_dir: str = "data_storage"):
        self.base_dir = base_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create storage folders if they don't exist"""
        for subfolder in ["signals", "results"]:
            path = os.path.join(self.base_dir, subfolder)
            if not os.path.exists(path):
                os.makedirs(path)

    def save_signals(self, signals: Dict[str, Any]):
        """Saves a snapshot of raw signals from loader.py"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"signals_{timestamp}.json"
        filepath = os.path.join(self.base_dir, "signals", filename)

        data = {
            "timestamp": datetime.now().isoformat(),
            **signals
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ Signals saved to {filepath}")

    def save_tool_output(self, tool_name: str, outputs: Dict[str, Any]):
        """Saves the final recommendation from a tool"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{tool_name}_{timestamp}.json"
        filepath = os.path.join(self.base_dir, "results", filename)

        data = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "outputs": outputs
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ {tool_name} results saved to {filepath}")

    def get_latest_signals(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent signal file"""
        path = os.path.join(self.base_dir, "signals")
        files = sorted([f for f in os.listdir(path) if f.endswith('.json')])
        if not files:
            return None

        with open(os.path.join(path, files[-1]), 'r') as f:
            return json.load(f)
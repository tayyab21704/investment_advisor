# agent.py
from pydantic import BaseModel
from .state import AnalystState
from .contracts import ToolInput, ToolOutput
from .workflow import run_workflow

class AnalystAgent:
    """
    Public interface for the Analyst Agent.
    Orchestrator calls this class to run the agent.
    """

    def __init__(self):
        pass

    def run(self, input_data: ToolInput) -> dict:
        """
        Run the Analyst Agent workflow with the given input data.
        Returns a dictionary with all tool outputs and summary.
        """
        # Initialize state
        state = AnalystState(input_data=input_data)

        # Run workflow
        final_state = run_workflow(state)

        # Prepare final output dictionary
        output = {
            "tool_outputs": {k: v.dict() for k, v in final_state.tool_outputs.items()},
            "candidate_assets": final_state.candidate_assets,
            "confidence_summary": final_state.confidence_summary,
        }

        return output

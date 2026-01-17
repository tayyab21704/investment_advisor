"""Deprecated: risk_qualification_agent moved to risk_analysis_agent.

This module is retained as a lightweight shim for compatibility. Use
`src.agents.risk_analysis_agent` instead.
"""

from ..risk_analysis_agent.agent import RiskAnalysisAgent  # noqa: E402,F401

# Keep a deprecated alias for backward compatibility
class RiskQualificationAgent(RiskAnalysisAgent):
    pass

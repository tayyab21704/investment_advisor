"""
Main orchestrator control flow.

The orchestrator:
1. Loads data from external sources (MongoDB, etc.)
2. Calls agents with ONLY their required inputs
3. Uses AI engine to evaluate agent reasoning and decide next steps
4. Decides: iterate or terminate

AI-Powered Decision Making:
- Each agent returns detailed reasoning in their logic box
- AI engine analyzes all agent reasoning together
- AI decides REITERATE (continue debate) or TERMINATE (proceed)
- Falls back to rules-based if no AI engine available
"""

import logging
from typing import Callable, Optional, Dict, Any
from src.orchestrator.state import CouncilState, AgentOutput, EvaluationResult, UserProfile, AssetCandidate, MarketContext, Position
from src.orchestrator.termination_rules import evaluate_council, should_terminate, evaluate_with_ai_engine
from src.orchestrator.data_provider import DataProvider, get_data_provider
from src.orchestrator.ai_integration import load_ai_engine_from_env
from src.config.llm_config import AIEngineFactory

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Council debate orchestrator.
    
    Manages:
    - Data loading from external sources
    - Agent execution with required inputs only
    - State lifecycle across iterations
    - Decision making (iterate vs terminate)
    - Iteration control
    """
    
    def __init__(
        self,
        max_iterations: int = 5,
        ai_engine: Optional[Any] = None,
        data_provider: Optional[DataProvider] = None,
        use_ai_decisions: bool = True
    ):
        """
        Initialize the orchestrator.
        
        Args:
            max_iterations: Maximum debate rounds before forced termination
            ai_engine: Optional AI engine for intelligent reasoning over agent outputs
                      If None, will attempt to load from environment
            data_provider: Data provider for loading user_profile, asset, market context
                          Defaults to mock provider if not specified
            use_ai_decisions: If True, use AI engine for decisions; if False use rules-based
        """
        self.max_iterations = max_iterations
        self.use_ai_decisions = use_ai_decisions
        self.data_provider = data_provider or get_data_provider("mock")
        self.agents: Dict[str, Callable] = {}
        self.logger = logger
        
        # Load or use provided AI engine
        if ai_engine:
            self.ai_engine = ai_engine
        elif use_ai_decisions:
            try:
                self.ai_engine = load_ai_engine_from_env()
                if self.ai_engine:
                    self.logger.info("AI Engine loaded for decision-making")
                else:
                    self.logger.info("AI Engine not configured, using rules-based decisions")
            except Exception as e:
                self.logger.warning(f"Failed to load AI engine: {e}, using rules-based decisions")
                self.ai_engine = None
        else:
            self.ai_engine = None
        
        # Define which inputs each agent needs
        self.agent_inputs = {
            "risk_qualification": ["user_profile", "asset_candidate", "market_context", "position"],
            "devils_advocate": ["asset_candidate", "market_context", "risk_qualification"],
            "personal_suitability": ["user_profile", "asset_candidate", "position"],
        }
        
    def register_agent(self, agent_name: str, agent_callable: Callable) -> None:
        """
        Register an agent for the council.
        
        Args:
            agent_name: Unique identifier for the agent
            agent_callable: Function that takes required inputs and returns AgentOutput
        """
        self.agents[agent_name] = agent_callable
        self.logger.info(f"Registered agent: {agent_name}")
    
    def initialize_state(
        self,
        user_id: str,
        asset_id: str,
        proposed_investment_amount: float,
        percentage_of_portfolio: float
    ) -> CouncilState:
        """
        Create initial council state by loading data from external sources.
        
        Args:
            user_id: User identifier (for MongoDB lookup)
            asset_id: Asset identifier (for MongoDB lookup)
            proposed_investment_amount: Amount to invest in dollars
            percentage_of_portfolio: Position as % of total portfolio
            
        Returns:
            Initialized CouncilState with data from external sources
        """
        try:
            # Load data from external source (MongoDB, etc.)
            user_profile: UserProfile = self.data_provider.get_user_profile(user_id)
            asset_candidate: AssetCandidate = self.data_provider.get_asset_candidate(asset_id)
            market_context: MarketContext = self.data_provider.get_market_context()
            
            # Create position
            position: Position = Position(
                proposed_investment_amount=proposed_investment_amount,
                percentage_of_portfolio=percentage_of_portfolio
            )
            
            # Initialize state
            state: CouncilState = CouncilState(
                user_profile=user_profile,
                asset_candidate=asset_candidate,
                market_context=market_context,
                position=position,
                risk_qualification=None,
                devils_advocate=None,
                personal_suitability=None,
                iteration=0,
                decision=None,
                max_iterations=self.max_iterations,
                debate_history=[]
            )
            
            self.logger.info(f"Council state initialized for user {user_id}, asset {asset_id}")
            return state
        
        except Exception as e:
            self.logger.error(f"Failed to initialize council state: {e}")
            raise
    
    def _prepare_agent_input(self, state: CouncilState, agent_name: str) -> dict:
        """
        Prepare input dict for an agent with ONLY the data it needs.
        
        This implements the agent-specific input requirements:
        - risk_qualification needs: user_profile, asset_candidate, market_context, position
        - devils_advocate needs: asset_candidate, market_context, risk_qualification (output)
        - personal_suitability needs: user_profile, asset_candidate, position
        
        Args:
            state: Full council state
            agent_name: Name of agent to prepare input for
            
        Returns:
            Dict with only the inputs that agent needs
        """
        required_inputs = self.agent_inputs.get(agent_name, [])
        agent_input = {}
        
        for field in required_inputs:
            if field in state:
                agent_input[field] = state[field]
            elif field == "iteration":
                agent_input[field] = state.get("iteration", 0)
            else:
                self.logger.warning(f"Agent {agent_name} requested field {field} not in state")
        
        self.logger.debug(f"Agent {agent_name} prepared with inputs: {list(agent_input.keys())}")
        return agent_input
    
    def call_agents(self, state: CouncilState) -> CouncilState:
        """
        Execute all registered agents with their specific required inputs.
        
        Rule: Agents NEVER talk to each other.
        Only the orchestrator sees all outputs.
        Each agent receives ONLY the data it needs.
        
        Args:
            state: Current council state
            
        Returns:
            Updated state with agent outputs
        """
        self.logger.info(f"Iteration {state['iteration']}: Calling {len(self.agents)} agents")
        
        for agent_name, agent_func in self.agents.items():
            try:
                # Prepare agent-specific input
                agent_input = self._prepare_agent_input(state, agent_name)
                
                # Call agent with only its required inputs
                output = agent_func(agent_input)
                
                # Validate output against AgentOutput contract
                if not self._validate_agent_output(output):
                    self.logger.warning(f"Agent {agent_name} returned invalid output")
                    continue
                
                # Store in state namespace
                self._store_agent_output(state, agent_name, output)
                self.logger.debug(f"Agent {agent_name}: {output['verdict']} (confidence: {output['confidence']})")
                
            except Exception as e:
                self.logger.error(f"Error calling agent {agent_name}: {e}")
                continue
        
        return state
    
    def _validate_agent_output(self, output: AgentOutput) -> bool:
        """
        Validate output against AgentOutput contract.
        
        Args:
            output: Agent output to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = {
            "agent_name", "verdict", "confidence", 
            "key_findings", "blocking_issues", "recommendations", "metrics"
        }
        
        if not all(key in output for key in required_keys):
            return False
        
        if output["verdict"] not in ["APPROVE", "MODIFY", "REJECT"]:
            return False
        
        if not (0.0 <= output["confidence"] <= 1.0):
            return False
        
        return True
    
    def _store_agent_output(self, state: CouncilState, agent_name: str, output: AgentOutput) -> None:
        """
        Store agent output in its namespace within state.
        
        Rule: Agents NEVER change global state.
        They only return outputs that the orchestrator stores.
        
        Args:
            state: Current state
            agent_name: Agent identifier
            output: Agent output to store
        """
        # Map agent names to state keys
        state_key_map = {
            "risk_qualification": "risk_qualification",
            "devils_advocate": "devils_advocate",
            "personal_suitability": "personal_suitability",
            "market_analysis": "market_analysis",
            "feasibility_analysis": "feasibility_analysis",
        }
        
        state_key = state_key_map.get(agent_name)
        if state_key:
            state[state_key] = output
    
    def evaluate_and_decide(self, state: CouncilState) -> CouncilState:
        """
        Evaluate council outputs and make iteration decision using AI engine.
        
        The AI engine reads all agent reasoning/logic boxes and makes intelligent
        decisions about whether to continue the debate or proceed.
        
        Falls back to rules-based evaluation if AI engine not available.
        
        Args:
            state: Current council state with all outputs
            
        Returns:
            Updated state with decision
        """
        # Use AI engine for decision if configured, otherwise use rules-based
        if self.use_ai_decisions and self.ai_engine:
            evaluation = evaluate_with_ai_engine(
                self.ai_engine,
                state,
                state.get("user_profile", {}),
                state.get("asset_candidate", {})
            )
        else:
            # Fall back to deterministic rules
            evaluation = evaluate_council(state)
        
        state["decision"] = evaluation
        self.logger.info(f"Council evaluation: {evaluation['action']} ({evaluation['reason']})")
        
        return state
    
    def apply_modifications(self, state: CouncilState) -> CouncilState:
        """
        Process MODIFY verdicts and prepare for next iteration.
        
        This is where the AI engine can be used to synthesize modifications
        based on multiple agent recommendations.
        
        Args:
            state: Current state with evaluation
            
        Returns:
            Modified state for next iteration
        """
        # Only MODIFY verdicts trigger processing
        modify_agents = []
        for key in ["risk_qualification", "devils_advocate", "personal_suitability", 
                   "market_analysis", "feasibility_analysis"]:
            output = state.get(key)
            if output and output["verdict"] == "MODIFY":
                modify_agents.append({
                    "agent": output["agent_name"],
                    "recommendations": output["recommendations"]
                })
        
        if modify_agents:
            self.logger.info(f"Processing {len(modify_agents)} MODIFY verdicts")
            
            # Use AI engine if available for complex synthesis
            if self.ai_engine:
                modifications = self._synthesize_modifications_with_ai(
                    state, modify_agents
                )
                state["modification_synthesis"] = modifications
            else:
                # Simple merge of recommendations
                state["pending_modifications"] = modify_agents
        
        return state
    
    def _synthesize_modifications_with_ai(
        self, 
        state: CouncilState, 
        modify_agents: list
    ) -> dict:
        """
        Use AI engine to synthesize modifications from multiple agents.
        
        This is the "brain" component mentioned in your requirements.
        The AI understands complex relationships between agent outputs.
        
        Args:
            state: Current state
            modify_agents: Agents requesting modifications
            
        Returns:
            AI-synthesized modifications
        """
        prompt = self._build_synthesis_prompt(state, modify_agents)
        
        try:
            synthesis = self.ai_engine.reason(prompt)
            self.logger.info("AI synthesis completed")
            return synthesis
        except Exception as e:
            self.logger.error(f"AI synthesis failed: {e}")
            return {"error": str(e)}
    
    def _build_synthesis_prompt(self, state: CouncilState, modify_agents: list) -> str:
        """Build prompt for AI synthesis of modifications."""
        recommendations = []
        for agent_info in modify_agents:
            recommendations.extend(agent_info["recommendations"])
        
        prompt = f"""
You are an investment council orchestrator's reasoning engine.
Multiple agents have suggested modifications:

{chr(10).join([f'- {rec}' for rec in recommendations])}

Asset: {state.get('asset_candidate', {}).get('name', 'Unknown')}
Investment Amount: {state.get('position', {}).get('proposed_investment_amount', 'Unknown')}

Synthesize these recommendations into a coherent set of modifications
that respect all constraints and optimize for consensus in the next iteration.
Return as a structured list of actions.
"""
        return prompt
    
    def orchestrate(
        self,
        user_profile: dict,
        asset_candidate: dict,
        market_context: dict,
        position: Optional[dict] = None
    ) -> CouncilState:
        """
        Main orchestration loop.
        
        Control flow:
        1. Initialize state
        2. LOOP:
           a. Increment iteration
           b. Call agents
           c. Evaluate outputs
           d. Add to history
           e. If TERMINATE → return state
           f. Apply modifications
           g. Check termination conditions
        
        Args:
            user_profile: User investment profile
            asset_candidate: Asset under review
            market_context: Market conditions
            position: Position sizing
            
        Returns:
            Final state with decision
        """
        state = self.initialize_state(user_profile, asset_candidate, market_context, position)
        
        while True:
            # Step 1: Increment iteration
            state["iteration"] += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ITERATION {state['iteration']} START")
            self.logger.info(f"{'='*60}")
            
            # Step 2: Call agents
            state = self.call_agents(state)
            
            # Step 3: Evaluate
            state = self.evaluate_and_decide(state)
            
            # Step 4: Add to history
            iteration_record = {
                "iteration": state["iteration"],
                "verdicts": {
                    "risk_qualification": state.get("risk_qualification", {}).get("verdict") if state.get("risk_qualification") else None,
                    "devils_advocate": state.get("devils_advocate", {}).get("verdict") if state.get("devils_advocate") else None,
                    "personal_suitability": state.get("personal_suitability", {}).get("verdict") if state.get("personal_suitability") else None,
                    "market_analysis": state.get("market_analysis", {}).get("verdict") if state.get("market_analysis") else None,
                    "feasibility_analysis": state.get("feasibility_analysis", {}).get("verdict") if state.get("feasibility_analysis") else None,
                },
                "decision": state.get("decision", {}).get("reason") if state.get("decision") else None
            }
            state["debate_history"].append(iteration_record)
            
            # Step 5: Check termination
            if should_terminate(state):
                self.logger.info(f"ORCHESTRATION COMPLETE: {state['decision']['reason']}")
                return state
            
            # Step 6: Apply modifications and prepare for next iteration
            state = self.apply_modifications(state)
            
            # Step 7: Check iteration limit
            if state["iteration"] >= state["max_iterations"]:
                self.logger.warning(f"Max iterations ({state['max_iterations']}) reached")
                state["decision"] = {
                    "action": "TERMINATE",
                    "reason": "MAX_ITERATIONS"
                }
                return state
    
    def get_final_recommendation(self, state: CouncilState) -> dict:
        """
        Extract final recommendation from state.
        
        Args:
            state: Final council state
            
        Returns:
            Structured recommendation
        """
        return {
            "recommendation": state.get("decision", {}).get("reason"),
            "consensus": state.get("decision", {}).get("action") == "TERMINATE",
            "iterations": state.get("iteration", 0),
            "agent_verdicts": {
                "risk_qualification": state.get("risk_qualification", {}).get("verdict") if state.get("risk_qualification") else None,
                "devils_advocate": state.get("devils_advocate", {}).get("verdict") if state.get("devils_advocate") else None,
                "personal_suitability": state.get("personal_suitability", {}).get("verdict") if state.get("personal_suitability") else None,
            },
            "average_confidence": self._calculate_average_confidence(state),
            "debate_history": state.get("debate_history", [])
        }
    
    def _calculate_average_confidence(self, state: CouncilState) -> float:
        """Calculate average confidence across all agents."""
        confidences = []
        for key in ["risk_qualification", "devils_advocate", "personal_suitability",
                   "market_analysis", "feasibility_analysis"]:
            output = state.get(key)
            if output:
                confidences.append(output["confidence"])
        
        return sum(confidences) / len(confidences) if confidences else 0.0


def run_orchestrator_example():
    """
    Example: Initialize and run orchestrator with mock data.
    
    This demonstrates the basic usage pattern:
    1. Create orchestrator with data provider
    2. Initialize state from external data
    3. Register agents
    4. Run orchestration debate
    """
    from src.orchestrator.mongodb_provider import MongoDBDataProviderMock
    
    # Create orchestrator with mock data provider
    data_provider = MongoDBDataProviderMock()
    orchestrator = Orchestrator(max_iterations=5, data_provider=data_provider)
    
    # Initialize state from external data
    initial_state = orchestrator.initialize_state(
        user_id="test_user",
        asset_id="test_asset",
        proposed_investment_amount=50000.0,
        percentage_of_portfolio=0.15
    )
    
    logger.info("Orchestrator initialized successfully")
    logger.info(f"User Risk Tolerance: {initial_state['user_profile']['risk_tolerance']}")
    logger.info(f"Asset Type: {initial_state['asset_candidate']['asset_type']}")
    logger.info(f"Market Trend: {initial_state['market_context']['market_trend']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_orchestrator_example()

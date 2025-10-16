"""LangGraph workflow for iterative product concept refinement."""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

from ..agents import (
    IdeatorAgent,
    PersonaGenerator,
    MarketPredictorAgent,
    CriticAgent,
)
from ..utils import (
    get_config,
    get_logger,
    ProductConcept,
    Persona,
    PersonaResponse,
    MarketFitScore,
    CriticFeedback,
)


class WorkflowState(TypedDict):
    """State for the LangGraph workflow."""
    # Input
    seed_idea: str
    
    # Configuration
    max_iterations: int
    pmf_threshold: float
    personas_count: int
    
    # Current state
    iteration: int
    current_concept: ProductConcept
    personas: Sequence[Persona]
    persona_responses: Sequence[PersonaResponse]
    market_fit: MarketFitScore
    critic_feedback: CriticFeedback
    
    # History
    history: Annotated[Sequence[dict], operator.add]
    
    # Control
    should_continue: bool


class ProductIdeationWorkflow:
    """
    LangGraph workflow for iterative product concept refinement.
    
    Workflow:
    1. Generate personas (once)
    2. Ideate concept
    3. Simulate market response
    4. Calculate PMF
    5. Analyze feedback
    6. Decide: continue or finalize
    7. If continue: refine and repeat from step 3
    """
    
    def __init__(self):
        """Initialize workflow."""
        self.config = get_config()
        self.logger = get_logger()
        
        # Initialize agents
        self.ideator = IdeatorAgent()
        self.persona_gen = PersonaGenerator()
        self.market_predictor = MarketPredictorAgent()
        self.critic = CriticAgent()
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define workflow
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("generate_personas", self._generate_personas_node)
        workflow.add_node("ideate", self._ideate_node)
        workflow.add_node("simulate_market", self._simulate_market_node)
        workflow.add_node("calculate_pmf", self._calculate_pmf_node)
        workflow.add_node("analyze_feedback", self._analyze_feedback_node)
        workflow.add_node("decide", self._decide_node)
        
        # Define edges
        workflow.set_entry_point("generate_personas")
        workflow.add_edge("generate_personas", "ideate")
        workflow.add_edge("ideate", "simulate_market")
        workflow.add_edge("simulate_market", "calculate_pmf")
        workflow.add_edge("calculate_pmf", "analyze_feedback")
        workflow.add_edge("analyze_feedback", "decide")
        
        # Conditional edge from decide
        workflow.add_conditional_edges(
            "decide",
            self._should_continue_routing,
            {
                "continue": "ideate",
                "finalize": END
            }
        )
        
        return workflow.compile()
    
    def _generate_personas_node(self, state: WorkflowState) -> dict:
        """Generate personas for market simulation."""
        personas = self.persona_gen.generate_personas(state["personas_count"])
        return {"personas": personas}
    
    def _ideate_node(self, state: WorkflowState) -> dict:
        """Generate or refine product concept."""
        if state["iteration"] == 0:
            # Initial concept generation
            concept = self.ideator.generate_concept(state["seed_idea"])
        else:
            # Refine existing concept based on critic feedback
            feedback = state["critic_feedback"].to_refinement_prompt()
            concept = self.ideator.refine_concept(
                state["current_concept"],
                feedback
            )
        
        # Increment iteration
        new_iteration = state["iteration"] + 1
        
        return {
            "current_concept": concept,
            "iteration": new_iteration
        }
    
    def _simulate_market_node(self, state: WorkflowState) -> dict:
        """Simulate market response from personas."""
        responses = self.market_predictor.simulate_market_response(
            state["current_concept"],
            state["personas"]
        )
        
        return {"persona_responses": responses}
    
    def _calculate_pmf_node(self, state: WorkflowState) -> dict:
        """Calculate Product-Market Fit score."""
        market_fit = self.market_predictor.calculate_pmf(
            state["persona_responses"],
            state["pmf_threshold"]
        )
        
        # Log iteration results
        self.logger.log_iteration(
            state["iteration"],
            market_fit.pmf_score,
            state["current_concept"].name
        )
        
        # Add to history
        history_entry = {
            "iteration": state["iteration"],
            "product_name": state["current_concept"].name,
            "pmf_score": market_fit.pmf_score,
            "nps": market_fit.nps,
            "avg_interest": market_fit.avg_interest,
        }
        
        return {
            "market_fit": market_fit,
            "history": [history_entry]
        }
    
    def _analyze_feedback_node(self, state: WorkflowState) -> dict:
        """Analyze market feedback and generate refinement suggestions."""
        # Get sample responses for detailed analysis
        sample_feedback = self.market_predictor.get_sample_feedback(
            state["persona_responses"],
            num_samples=5
        )
        
        # Generate critic feedback
        critic_feedback = self.critic.analyze_and_generate_feedback(
            state["current_concept"],
            state["market_fit"],
            sample_feedback,
            state["pmf_threshold"]
        )
        
        return {"critic_feedback": critic_feedback}
    
    def _decide_node(self, state: WorkflowState) -> dict:
        """Decide whether to continue iterating or finalize."""
        # Check if PMF threshold met
        if state["market_fit"].pmf_score >= state["pmf_threshold"]:
            self.logger.log_info(
                f"✅ PMF threshold met ({state['market_fit'].pmf_score:.1f}% >= {state['pmf_threshold']}%)"
            )
            return {"should_continue": False}
        
        # Check if max iterations reached
        if state["iteration"] >= state["max_iterations"]:
            self.logger.log_warning(
                f"Max iterations reached ({state['iteration']}/{state['max_iterations']})"
            )
            return {"should_continue": False}
        
        # Continue iterating
        self.logger.log_info(
            f"Continuing refinement (Iteration {state['iteration']}/{state['max_iterations']}, "
            f"PMF: {state['market_fit'].pmf_score:.1f}%)"
        )
        return {"should_continue": True}
    
    def _should_continue_routing(self, state: WorkflowState) -> str:
        """Route based on should_continue flag."""
        return "continue" if state.get("should_continue", True) else "finalize"
    
    def run(
        self,
        seed_idea: str,
        max_iterations: int = None,
        pmf_threshold: float = None,
        personas_count: int = None
    ) -> WorkflowState:
        """
        Run the complete workflow.
        
        Args:
            seed_idea: Initial product idea
            max_iterations: Maximum refinement iterations
            pmf_threshold: PMF score threshold to reach
            personas_count: Number of personas to simulate
        
        Returns:
            Final WorkflowState
        """
        # Use config defaults if not specified
        if max_iterations is None:
            max_iterations = self.config.max_iterations
        if pmf_threshold is None:
            pmf_threshold = self.config.pmf_threshold
        if personas_count is None:
            personas_count = self.config.personas_count
        
        # Log workflow start
        self.logger.start_workflow(seed_idea)
        
        # Initialize state
        initial_state: WorkflowState = {
            "seed_idea": seed_idea,
            "max_iterations": max_iterations,
            "pmf_threshold": pmf_threshold,
            "personas_count": personas_count,
            "iteration": 0,
            "current_concept": None,
            "personas": [],
            "persona_responses": [],
            "market_fit": None,
            "critic_feedback": None,
            "history": [],
            "should_continue": True,
        }
        
        # Run workflow
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        
        except Exception as e:
            import traceback
            self.logger.log_error("Workflow execution failed", str(e))
            self.logger.log_error("Full traceback", traceback.format_exc())
            raise


def create_workflow() -> ProductIdeationWorkflow:
    """Create and return workflow instance."""
    return ProductIdeationWorkflow()


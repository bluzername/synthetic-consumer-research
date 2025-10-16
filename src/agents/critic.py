"""Critic Agent - Analyze PMF results and generate refinement feedback."""

from typing import List
from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    ProductConcept,
    PersonaResponse,
    MarketFitScore,
    CriticFeedback,
)


class CriticAgent:
    """
    Analyzes product-market fit data and generates actionable refinement strategies.
    Provides specific, implementable recommendations for concept improvement.
    """
    
    def __init__(self):
        """Initialize Critic agent."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        # Model configuration
        self.model = self.config.critic_model
        self.temperature = self.config.get_setting("models", "critic_temperature", default=0.5)
        self.max_tokens = self.config.get_setting("models", "critic_max_tokens", default=2000)
        
        # Load prompts
        self.system_prompt = self.config.get_prompt("critic", "system_prompt")
        self.analyze_prompt_template = self.config.get_prompt("critic", "analyze_feedback_prompt")
    
    def analyze_and_generate_feedback(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore,
        sample_responses: str,
        threshold: float = 40.0
    ) -> CriticFeedback:
        """
        Analyze PMF results and generate refinement feedback.
        
        Args:
            concept: Product concept being analyzed
            market_fit: Market fit scores and data
            sample_responses: Sample persona responses
            threshold: PMF threshold target
        
        Returns:
            CriticFeedback object
        """
        self.logger.log_agent_start("Critic", "Analyzing market feedback")
        
        # Prepare product summary
        product_summary = concept.to_summary()
        
        # Format top benefits and concerns
        top_benefits = "\n".join(f"- {b}" for b in market_fit.top_benefits)
        top_concerns = "\n".join(f"- {c}" for c in market_fit.top_concerns)
        
        # Format prompt
        user_prompt = self.analyze_prompt_template.format(
            product_summary=product_summary,
            pmf_score=market_fit.pmf_score,
            pmf_threshold=threshold,
            nps=market_fit.nps,
            avg_interest=market_fit.avg_interest,
            top_benefits=top_benefits,
            top_concerns=top_concerns,
            sample_feedback=sample_responses,
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Call API with structured output
            feedback = self.client.chat_completion_with_structured_output(
                model=self.model,
                messages=messages,
                response_model=CriticFeedback,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            self.logger.log_agent_complete("Critic")
            return feedback
        
        except Exception as e:
            self.logger.log_error("Critic analysis failed", str(e))
            raise
    
    def generate_quick_feedback(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore
    ) -> str:
        """
        Generate quick text feedback without structured output.
        Useful for simpler refinement cycles.
        
        Args:
            concept: Product concept
            market_fit: Market fit scores
        
        Returns:
            Feedback text string
        """
        self.logger.log_agent_start("Critic", "Generating quick feedback")
        
        quick_prompt = f"""Analyze this product concept's market performance and provide brief refinement suggestions.

Product: {concept.name}
PMF Score: {market_fit.pmf_score}%
Top Benefits: {', '.join(market_fit.top_benefits[:3])}
Top Concerns: {', '.join(market_fit.top_concerns[:3])}

Provide 2-3 specific, actionable refinements to improve PMF score."""
        
        messages = [
            {"role": "system", "content": "You are a product strategist providing concise refinement advice."},
            {"role": "user", "content": quick_prompt}
        ]
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=500,
            )
            
            feedback = response.choices[0].message.content
            
            self.logger.log_agent_complete("Critic")
            return feedback
        
        except Exception as e:
            self.logger.log_error("Quick feedback generation failed", str(e))
            return "Unable to generate feedback. Continue with current concept."


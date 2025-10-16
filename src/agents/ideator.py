"""Ideator Agent - Creative product concept generator."""

from typing import List, Optional
from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    ProductConcept,
)


class IdeatorAgent:
    """
    Agent responsible for generating and refining product concepts.
    Uses creative LLMs to ideate innovative solutions.
    """
    
    def __init__(self):
        """Initialize Ideator agent."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        # Model configuration
        self.model = self.config.ideator_model
        self.temperature = self.config.ideator_temperature
        self.max_tokens = self.config.get_setting("models", "ideator_max_tokens", default=4000)
        
        # Load prompts
        self.system_prompt = self.config.get_prompt("ideator", "system_prompt")
        self.generate_prompt_template = self.config.get_prompt("ideator", "generate_prompt")
        self.refine_prompt_template = self.config.get_prompt("ideator", "refine_prompt")
    
    def generate_concept(
        self,
        seed_idea: str,
        market_signals: Optional[List[str]] = None
    ) -> ProductConcept:
        """
        Generate initial product concept from seed idea.
        
        Args:
            seed_idea: Initial product idea or problem statement
            market_signals: Optional market insights to incorporate
        
        Returns:
            ProductConcept object
        """
        self.logger.log_agent_start("Ideator", "Generating concept")
        
        # Prepare market signals context
        signals_context = ""
        if market_signals:
            signals_context = "\nMarket Signals:\n" + "\n".join(f"- {signal}" for signal in market_signals)
        
        # Format prompt
        user_prompt = self.generate_prompt_template.format(
            seed_idea=seed_idea,
            market_signals=signals_context
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call API with structured output
        try:
            concept = self.client.chat_completion_with_structured_output(
                model=self.model,
                messages=messages,
                response_model=ProductConcept,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            self.logger.log_agent_complete("Ideator")
            return concept
        
        except Exception as e:
            self.logger.log_error("Ideator concept generation failed", str(e))
            raise
    
    def refine_concept(
        self,
        current_concept: ProductConcept,
        feedback: str
    ) -> ProductConcept:
        """
        Refine existing concept based on market feedback.
        
        Args:
            current_concept: Current product concept
            feedback: Structured feedback from Critic agent
        
        Returns:
            Refined ProductConcept
        """
        self.logger.log_agent_start("Ideator", "Refining concept")
        
        # Format prompt with current concept details
        user_prompt = self.refine_prompt_template.format(
            product_name=current_concept.name,
            tagline=current_concept.tagline,
            target_market=current_concept.target_market,
            problem_solved=current_concept.problem_solved,
            features="\n".join(f"- {f}" for f in current_concept.features),
            feedback=feedback
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call API with structured output
        try:
            refined_concept = self.client.chat_completion_with_structured_output(
                model=self.model,
                messages=messages,
                response_model=ProductConcept,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            self.logger.log_agent_complete("Ideator")
            return refined_concept
        
        except Exception as e:
            self.logger.log_error("Ideator concept refinement failed", str(e))
            raise
    
    def generate_variants(
        self,
        seed_idea: str,
        num_variants: int = 3
    ) -> List[ProductConcept]:
        """
        Generate multiple concept variants for comparison.
        
        Args:
            seed_idea: Initial product idea
            num_variants: Number of variants to generate
        
        Returns:
            List of ProductConcept objects
        """
        self.logger.log_agent_start("Ideator", f"Generating {num_variants} variants")
        
        variants = []
        for i in range(num_variants):
            # Add variation instruction
            varied_prompt = f"{self.generate_prompt_template}\n\nGenerate variation #{i+1} with a different angle or approach."
            
            user_prompt = varied_prompt.format(
                seed_idea=seed_idea,
                market_signals=""
            )
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            try:
                concept = self.client.chat_completion_with_structured_output(
                    model=self.model,
                    messages=messages,
                    response_model=ProductConcept,
                    temperature=self.temperature + 0.1,  # Slightly higher for variety
                    max_tokens=self.max_tokens,
                )
                variants.append(concept)
            
            except Exception as e:
                self.logger.log_warning(f"Failed to generate variant {i+1}: {e}")
                continue
        
        self.logger.log_agent_complete("Ideator")
        return variants


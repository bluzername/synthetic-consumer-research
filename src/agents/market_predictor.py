"""Market Predictor Agent - Simulate market response and calculate PMF."""

from typing import List
import statistics
from collections import Counter
from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    ProductConcept,
    Persona,
    PersonaResponse,
    MarketFitScore,
    MarketSegmentation,
    DisappointmentLevel,
)


class MarketPredictorAgent:
    """
    Simulates market response by having personas evaluate product concepts.
    Calculates Product-Market Fit using Sean Ellis methodology.
    """
    
    def __init__(self):
        """Initialize Market Predictor agent."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        # Model configuration
        self.model = self.config.market_predictor_model
        self.temperature = self.config.get_setting("models", "market_predictor_temperature", default=0.6)
        
        # Load prompts
        self.system_prompt = self.config.get_prompt("market_predictor", "system_prompt")
        self.response_prompt_template = self.config.get_prompt("market_predictor", "simulate_response_prompt")
    
    def simulate_market_response(
        self,
        concept: ProductConcept,
        personas: List[Persona]
    ) -> List[PersonaResponse]:
        """
        Simulate market response from multiple personas.
        
        Args:
            concept: Product concept to evaluate
            personas: List of personas to simulate
        
        Returns:
            List of PersonaResponse objects
        """
        self.logger.log_agent_start("Market Predictor", f"Simulating {len(personas)} persona responses")
        
        responses = []
        
        # Progress bar
        progress = self.logger.create_progress_bar("Simulating responses", len(personas))
        
        if progress:
            progress.start()
            task = progress.add_task("Responses", total=len(personas))
        
        for persona in personas:
            try:
                response = self._simulate_single_response(persona, concept)
                responses.append(response)
                
                if progress:
                    progress.update(task, advance=1)
            
            except Exception as e:
                self.logger.log_warning(f"Failed to simulate response for {persona.name}: {e}")
                continue
        
        if progress:
            progress.stop()
        
        self.logger.log_agent_complete("Market Predictor")
        return responses
    
    def _simulate_single_response(
        self,
        persona: Persona,
        concept: ProductConcept
    ) -> PersonaResponse:
        """
        Simulate response from a single persona.
        
        Args:
            persona: Persona to simulate
            concept: Product concept
        
        Returns:
            PersonaResponse object
        """
        # Get persona context
        persona_ctx = persona.to_prompt_context()
        
        # Add product details
        product_ctx = {
            "product_name": concept.name,
            "product_tagline": concept.tagline,
            "problem_solved": concept.problem_solved,
            "target_market": concept.target_market,
            "features": "\n".join(f"- {f}" for f in concept.features),
            "pricing_model": concept.pricing_model,
        }
        
        # Combine contexts
        full_ctx = {**persona_ctx, **product_ctx}
        
        # Format prompt
        user_prompt = self.response_prompt_template.format(**full_ctx)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call API with structured output
        response = self.client.chat_completion_with_structured_output(
            model=self.model,
            messages=messages,
            response_model=PersonaResponse,
            temperature=self.temperature,
            max_tokens=1000,
        )
        
        # Add persona name to response
        response.persona_name = persona.name
        
        return response
    
    def calculate_pmf(
        self,
        responses: List[PersonaResponse],
        threshold: float = 40.0
    ) -> MarketFitScore:
        """
        Calculate Product-Market Fit score using Sean Ellis methodology.
        
        Args:
            responses: List of persona responses
            threshold: PMF threshold percentage
        
        Returns:
            MarketFitScore object
        """
        if not responses:
            raise ValueError("No responses to calculate PMF from")
        
        self.logger.log_agent_start("Market Predictor", "Calculating PMF score")
        
        total = len(responses)
        
        # 1. Traditional PMF Score: % "very disappointed" (Sean Ellis)
        very_disappointed = sum(1 for r in responses if r.is_very_disappointed())
        pmf_score = (very_disappointed / total) * 100
        
        # 2. Net Promoter Score (NPS)
        promoters = sum(1 for r in responses if r.is_promoter())
        detractors = sum(1 for r in responses if r.is_detractor())
        passives = total - promoters - detractors
        nps = int(((promoters - detractors) / total) * 100)
        
        # 3. Average Interest
        avg_interest = statistics.mean(r.interest_score for r in responses)
        
        # 4. Interest Distribution
        interest_dist = {i: sum(1 for r in responses if r.interest_score == i) for i in range(1, 6)}
        
        # 5. Identify Superfans (5/5 interest + VERY disappointed)
        superfans = sum(1 for r in responses if r.interest_score == 5 and r.is_very_disappointed())
        superfan_ratio = superfans / total
        
        # 6. Market Segmentation
        enthusiasts = sum(1 for r in responses if r.interest_score >= 4)
        interested = sum(1 for r in responses if r.interest_score == 3)
        skeptical = sum(1 for r in responses if r.interest_score <= 2)
        
        # Disappointment distribution
        somewhat_disappointed = sum(1 for r in responses if r.disappointment.value == "SOMEWHAT")
        not_disappointed = sum(1 for r in responses if r.disappointment.value == "NOT")
        
        segmentation = MarketSegmentation(
            superfans_pct=(superfans / total) * 100,
            enthusiasts_pct=(enthusiasts / total) * 100,
            interested_pct=(interested / total) * 100,
            skeptical_pct=(skeptical / total) * 100,
            very_disappointed_pct=(very_disappointed / total) * 100,
            somewhat_disappointed_pct=(somewhat_disappointed / total) * 100,
            not_disappointed_pct=(not_disappointed / total) * 100,
            promoters_pct=(promoters / total) * 100,
            passives_pct=(passives / total) * 100,
            detractors_pct=(detractors / total) * 100,
        )
        
        # 7. Target Market Size (superfans + enthusiasts)
        target_market_size_pct = segmentation.superfans_pct + segmentation.enthusiasts_pct
        
        # 8. Top Benefits
        all_benefits = [r.main_benefit for r in responses]
        benefit_counter = Counter(all_benefits)
        top_benefits = [benefit for benefit, _ in benefit_counter.most_common(5)]
        
        # 9. Top Concerns
        all_concerns = [concern for r in responses for concern in r.concerns]
        concern_counter = Counter(all_concerns)
        top_concerns = [concern for concern, _ in concern_counter.most_common(5)]
        
        # 10. Business Model Recommendation
        if superfan_ratio >= 0.10 and segmentation.enthusiasts_pct < 40:
            business_model = "Premium/Niche: Target superfans with high-value offering ($20-50/mo or $200-500 one-time)"
        elif superfan_ratio >= 0.10 and segmentation.enthusiasts_pct >= 40:
            business_model = "Freemium/Mass Market: Wide adoption with premium upsells ($0-10/mo free, $15-30/mo premium)"
        elif segmentation.enthusiasts_pct >= 30:
            business_model = "Mid-Market: Balance accessibility and value ($10-20/mo)"
        else:
            business_model = "Needs refinement: No clear monetization path yet"
        
        # 11. Strategic Recommendation (enhanced)
        if superfan_ratio >= 0.10:
            if segmentation.enthusiasts_pct >= 40:
                recommendation = "✅ PROCEED (MASS MARKET): Strong core + broad appeal - scale aggressively"
            else:
                recommendation = "✅ PROCEED (NICHE): Viable superfan segment - nail the niche first"
        elif segmentation.enthusiasts_pct >= 30:
            recommendation = "⚠️ REFINE: Moderate interest but needs passion - iterate value prop"
        elif segmentation.interested_pct >= 50:
            recommendation = "⚠️ REFINE: Lukewarm response - strengthen differentiation"
        else:
            recommendation = "❌ PIVOT: Weak fit - consider major changes or new market"
        
        market_fit = MarketFitScore(
            pmf_score=pmf_score,
            avg_interest=avg_interest,
            nps=nps,
            segmentation=segmentation,
            target_market_size_pct=target_market_size_pct,
            superfan_ratio=superfan_ratio,
            interest_distribution=interest_dist,
            top_benefits=top_benefits,
            top_concerns=top_concerns,
            recommendation=recommendation,
            business_model_fit=business_model,
            total_responses=total,
        )
        
        # Log results
        self.logger.log_pmf_results(
            pmf_score=pmf_score,
            nps=nps,
            avg_interest=avg_interest,
            threshold=threshold,
            meets_threshold=market_fit.meets_threshold(threshold),
            market_fit=market_fit
        )
        
        self.logger.log_agent_complete("Market Predictor")
        
        return market_fit
    
    def get_sample_feedback(
        self,
        responses: List[PersonaResponse],
        num_samples: int = 5
    ) -> str:
        """
        Get sample persona feedback for Critic analysis.
        
        Args:
            responses: List of persona responses
            num_samples: Number of sample responses to include
        
        Returns:
            Formatted feedback string
        """
        # Get mix of promoters and detractors
        promoters = [r for r in responses if r.is_promoter()]
        detractors = [r for r in responses if r.is_detractor()]
        passives = [r for r in responses if not r.is_promoter() and not r.is_detractor()]
        
        samples = []
        
        # Add diverse samples
        if promoters:
            samples.append(promoters[0])
        if detractors:
            samples.extend(detractors[:2])
        if passives:
            samples.append(passives[0])
        
        # Fill remaining with random
        remaining = num_samples - len(samples)
        if remaining > 0 and len(responses) > len(samples):
            for r in responses:
                if r not in samples:
                    samples.append(r)
                    if len(samples) >= num_samples:
                        break
        
        # Format feedback
        feedback_parts = []
        for i, response in enumerate(samples[:num_samples], 1):
            feedback_parts.append(f"""
{i}. {response.persona_name}:
   - Interest: {response.interest_score}/5
   - Disappointment: {response.disappointment}
   - Main Benefit: {response.main_benefit}
   - Concerns: {', '.join(response.concerns)}
   - Recommend: {response.likelihood_to_recommend}/10
""".strip())
        
        return "\n\n".join(feedback_parts)


"""Market Predictor Agent - Simulate market response and calculate PMF using SSR."""

from typing import List
import statistics
from collections import Counter
import numpy as np
import polars as po
from semantic_similarity_rating import ResponseRater

from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    ProductConcept,
    Persona,
    PersonaResponse,
    MarketFitScore,
    MarketSegmentation,
)


class MarketPredictorAgent:
    """
    Simulates market response by having personas evaluate product concepts.
    Calculates Product-Market Fit using SSR (Semantic Similarity Rating) methodology.
    
    This implementation follows the approach from:
    "LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings"
    """
    
    def __init__(self):
        """Initialize Market Predictor agent with SSR."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        # Model configuration
        self.model = self.config.market_predictor_model
        self.temperature = self.config.get_setting("models", "market_predictor_temperature", default=0.6)
        
        # Load prompts
        self.system_prompt = self.config.get_prompt("market_predictor", "system_prompt")
        self.response_prompt_template = self.config.get_prompt("market_predictor", "simulate_response_prompt")
        
        # Initialize SSR raters with reference sentences for each dimension
        self._initialize_ssr_raters()
    
    def _initialize_ssr_raters(self):
        """Initialize SSR ResponseRater objects for each rating dimension."""
        # Interest level (1-5 Likert scale)
        interest_references = po.DataFrame({
            "id": ["interest"] * 5,
            "int_response": [1, 2, 3, 4, 5],
            "sentence": [
                "Not interested at all",  # 1
                "Slightly interested",     # 2
                "Moderately interested",   # 3
                "Very interested",         # 4
                "Extremely interested"     # 5
            ]
        })
        
        # Disappointment level (1-5 scale: NOT -> VERY)
        disappointment_references = po.DataFrame({
            "id": ["disappointment"] * 5,
            "int_response": [1, 2, 3, 4, 5],
            "sentence": [
                "Wouldn't care at all",           # 1 (NOT disappointed)
                "Slightly disappointed",           # 2
                "Moderately disappointed",         # 3
                "Very disappointed",               # 4
                "Would be devastated"              # 5 (VERY disappointed)
            ]
        })
        
        # Recommendation likelihood (converted to 1-5 scale from NPS 0-10)
        # We map: 0-2 -> 1, 3-4 -> 2, 5-6 -> 3, 7-8 -> 4, 9-10 -> 5
        recommendation_references = po.DataFrame({
            "id": ["recommendation"] * 5,
            "int_response": [1, 2, 3, 4, 5],
            "sentence": [
                "Definitely would not recommend",  # 1 (NPS 0-2, detractor)
                "Probably would not recommend",    # 2 (NPS 3-4, detractor)
                "Might recommend",                 # 3 (NPS 5-6, detractor)
                "Probably would recommend",        # 4 (NPS 7-8, passive)
                "Absolutely would recommend"       # 5 (NPS 9-10, promoter)
            ]
        })
        
        # Initialize ResponseRater for each dimension
        self.logger.log_info("Initializing SSR ResponseRaters...")
        self.interest_rater = ResponseRater(interest_references, model_name="all-MiniLM-L6-v2")
        self.disappointment_rater = ResponseRater(disappointment_references, model_name="all-MiniLM-L6-v2")
        self.recommendation_rater = ResponseRater(recommendation_references, model_name="all-MiniLM-L6-v2")
        self.logger.log_info("SSR ResponseRaters initialized successfully")
    
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
        Calculate Product-Market Fit score using SSR (Semantic Similarity Rating) methodology.
        
        This implements the approach from "LLMs Reproduce Human Purchase Intent via 
        Semantic Similarity Elicitation of Likert Ratings" which converts natural language
        responses into probability distributions over Likert scales using semantic similarity.
        
        Instead of extracting direct numeric ratings (which the paper advises against),
        we use SSR to convert semantic responses into PMFs and then aggregate them.
        
        Args:
            responses: List of persona responses with natural language
            threshold: Traditional PMF threshold percentage (kept for comparison)
        
        Returns:
            MarketFitScore object with enhanced metrics
        """
        from ..utils.exceptions import InsufficientDataError
        
        if not responses:
            raise InsufficientDataError(required=10, actual=0)
        
        if len(responses) < 10:
            self.logger.log_warning(
                f"Only {len(responses)} responses available. "
                f"Results may not be statistically reliable. "
                f"Recommended: 50-100 responses for robust PMF calculation."
            )
        
        self.logger.log_agent_start("Market Predictor", "Calculating PMF score using SSR methodology")
        
        total = len(responses)
        
        # Extract natural language responses for SSR processing
        interest_texts = [r.interest_response for r in responses]
        disappointment_texts = [r.disappointment_response for r in responses]
        recommendation_texts = [r.recommendation_response for r in responses]
        
        # Convert to PMFs using SSR
        self.logger.log_info("Converting semantic responses to PMFs using SSR...")
        interest_pmfs = self.interest_rater.get_response_pmfs(
            "interest", interest_texts, temperature=1.0, epsilon=0.01
        )
        disappointment_pmfs = self.disappointment_rater.get_response_pmfs(
            "disappointment", disappointment_texts, temperature=1.0, epsilon=0.01
        )
        recommendation_pmfs = self.recommendation_rater.get_response_pmfs(
            "recommendation", recommendation_texts, temperature=1.0, epsilon=0.01
        )
        
        # Calculate expected values and distributions from PMFs
        # Interest: 1-5 scale directly
        interest_scores = np.array([np.dot(pmf, [1, 2, 3, 4, 5]) for pmf in interest_pmfs])
        avg_interest = float(np.mean(interest_scores))
        
        # Disappointment: 1-5 scale (1=NOT, 5=VERY)
        disappointment_scores = np.array([np.dot(pmf, [1, 2, 3, 4, 5]) for pmf in disappointment_pmfs])
        
        # Recommendation: 1-5 scale, convert to NPS 0-10
        # Map: 1->1, 2->3, 3->5, 4->7, 5->9 (midpoints of ranges)
        recommendation_scores_1_5 = np.array([np.dot(pmf, [1, 2, 3, 4, 5]) for pmf in recommendation_pmfs])
        nps_scores = (recommendation_scores_1_5 - 1) * 2.5  # Scale to 0-10
        
        # Calculate NPS (% promoters - % detractors)
        promoters = sum(1 for score in nps_scores if score >= 9)
        detractors = sum(1 for score in nps_scores if score <= 6)
        passives = total - promoters - detractors
        nps = int(((promoters - detractors) / total) * 100)
        
        # Traditional PMF Score: % "very disappointed" (threshold >= 4.0 on disappointment scale)
        # Use PMF to calculate probability of being "very disappointed" (scores 4-5)
        very_disappointed_probs = disappointment_pmfs[:, 3:5].sum(axis=1)  # indices 3,4 = scores 4,5
        pmf_score = float(np.mean(very_disappointed_probs) * 100)
        
        # Interest Distribution (aggregate PMFs to get count distribution)
        interest_dist_array = interest_pmfs.sum(axis=0)
        interest_dist = {i+1: int(round(interest_dist_array[i])) for i in range(5)}
        
        # Identify Superfans: high interest (≥4.5) + high disappointment (≥4.0)
        superfans = sum(1 for i, d in zip(interest_scores, disappointment_scores) if i >= 4.5 and d >= 4.0)
        superfan_ratio = superfans / total
        
        # Market Segmentation based on expected scores
        enthusiasts = sum(1 for score in interest_scores if score >= 4.0)
        interested = sum(1 for score in interest_scores if 2.5 <= score < 4.0)
        skeptical = sum(1 for score in interest_scores if score < 2.5)
        
        # Disappointment distribution
        very_disappointed_count = sum(1 for score in disappointment_scores if score >= 4.0)
        somewhat_disappointed = sum(1 for score in disappointment_scores if 2.5 <= score < 4.0)
        not_disappointed = sum(1 for score in disappointment_scores if score < 2.5)
        
        segmentation = MarketSegmentation(
            superfans_pct=(superfans / total) * 100,
            enthusiasts_pct=(enthusiasts / total) * 100,
            interested_pct=(interested / total) * 100,
            skeptical_pct=(skeptical / total) * 100,
            very_disappointed_pct=(very_disappointed_count / total) * 100,
            somewhat_disappointed_pct=(somewhat_disappointed / total) * 100,
            not_disappointed_pct=(not_disappointed / total) * 100,
            promoters_pct=(promoters / total) * 100,
            passives_pct=(passives / total) * 100,
            detractors_pct=(detractors / total) * 100,
        )
        
        # Target Market Size (superfans + enthusiasts)
        target_market_size_pct = segmentation.superfans_pct + segmentation.enthusiasts_pct
        
        # 8. Top Benefits
        all_benefits = [r.main_benefit for r in responses]
        benefit_counter = Counter(all_benefits)
        top_benefits = [benefit for benefit, _ in benefit_counter.most_common(5)]
        
        # 9. Top Concerns
        all_concerns = [concern for r in responses for concern in r.concerns]
        concern_counter = Counter(all_concerns)
        top_concerns = [concern for concern, _ in concern_counter.most_common(5)]
        
        # 10. Business Model Recommendation (based on market segmentation)
        if superfan_ratio >= 0.15:  # High superfan concentration
            if segmentation.enthusiasts_pct >= 40:
                business_model = "Freemium/Mass Market: Wide adoption with premium tier for superfans. Example: Spotify (free tier + premium). Pricing: $0 free, $15-30/mo premium"
            else:
                business_model = "Premium/Niche: Target superfans willing to pay premium. Example: high-end audio, professional tools. Pricing: $30-100/mo or $300-1000 one-time"
        elif superfan_ratio >= 0.10:  # Viable niche
            if segmentation.enthusiasts_pct >= 40:
                business_model = "Value-Based Pricing: Broad appeal with tiered pricing. Example: Notion, Figma. Pricing: $0-15/mo free, $20-40/mo pro"
            else:
                business_model = "Premium/Community: Target niche with strong community. Example: Peloton, CrossFit. Pricing: $20-50/mo or $200-500 one-time"
        elif segmentation.enthusiasts_pct >= 30:
            business_model = "Mid-Market/SaaS: Balance accessibility and value. Example: most B2B SaaS. Pricing: $10-30/mo per user"
        else:
            business_model = "Needs refinement: Insufficient market enthusiasm for clear monetization strategy. Iterate to create passionate advocates first."
        
        # Strategic Recommendation (enhanced - uses superfan ratio as PRIMARY metric)
        # NOTE: Traditional 40% PMF threshold is often unrealistic for early-stage concepts
        # Focus on superfan identification (10%+ with high interest + disappointment) instead
        if superfan_ratio >= 0.10:
            if segmentation.enthusiasts_pct >= 40:
                recommendation = "✅ PROCEED (MASS MARKET): Strong core (10%+ superfans) + broad appeal (40%+ enthusiasts) - scale aggressively. This is exceptional for early-stage."
            else:
                recommendation = "✅ PROCEED (NICHE): Viable superfan segment (10%+) - nail the niche first, expand later. Many successful products started here (Tesla, Peloton)."
        elif segmentation.enthusiasts_pct >= 30:
            recommendation = "⚠️ REFINE: Moderate interest (30%+ enthusiasts) but no superfans yet - iterate value prop to create passionate advocates"
        elif segmentation.interested_pct >= 50:
            recommendation = "⚠️ REFINE: Lukewarm response (50%+ mildly interested) - strengthen differentiation to convert interest into enthusiasm"
        else:
            recommendation = "❌ PIVOT: Weak market fit - consider major changes, different positioning, or new target market"
        
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
        # Just take a diverse sample of responses
        samples = responses[:num_samples] if len(responses) >= num_samples else responses
        
        # Format feedback
        feedback_parts = []
        for i, response in enumerate(samples, 1):
            feedback_parts.append(f"""
{i}. {response.persona_name}:
   - Interest: {response.interest_response}
   - Disappointment: {response.disappointment_response}
   - Recommendation: {response.recommendation_response}
   - Main Benefit: {response.main_benefit}
   - Concerns: {', '.join(response.concerns)}
""".strip())
        
        return "\n\n".join(feedback_parts)


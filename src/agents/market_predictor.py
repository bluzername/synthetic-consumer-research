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
        """Initialize SSR ResponseRater objects with multiple reference sets and psychometrically sound phrasing."""
        # Get configuration
        embedding_model = self.config.ssr_embedding_model
        
        self.logger.log_info(f"Initializing SSR with embedding model: {embedding_model}")
        
        # Interest level - 3 reference sets with psychometrically sound phrasing
        interest_references = po.DataFrame({
            "id": ["set1"]*5 + ["set2"]*5 + ["set3"]*5,
            "int_response": [1, 2, 3, 4, 5] * 3,
            "sentence": [
                # Set 1: Emotional appeal (validated consumer research phrasing)
                "This does not appeal to me at all",
                "This appeals to me a little",
                "This somewhat appeals to me",
                "This appeals to me quite a bit",
                "This appeals to me very much",
                
                # Set 2: Personal relevance
                "This is not at all relevant to my needs",
                "This is slightly relevant to my needs",
                "This is moderately relevant to my needs",
                "This is quite relevant to my needs",
                "This is extremely relevant to my needs",
                
                # Set 3: Interest intensity
                "I have no interest in this whatsoever",
                "I have minimal interest in this",
                "I have some interest in this",
                "I have considerable interest in this",
                "I am extremely interested in this"
            ]
        })
        
        # Purchase Intent - 3 reference sets (standard consumer research scale)
        purchase_intent_references = po.DataFrame({
            "id": ["set1"]*5 + ["set2"]*5 + ["set3"]*5,
            "int_response": [1, 2, 3, 4, 5] * 3,
            "sentence": [
                # Set 1: Direct purchase likelihood
                "I definitely would not purchase this",
                "I probably would not purchase this",
                "I might or might not purchase this",
                "I probably would purchase this",
                "I definitely would purchase this",
                
                # Set 2: Purchase probability
                "There is no chance I would buy this",
                "There is a small chance I would buy this",
                "There is a moderate chance I would buy this",
                "There is a good chance I would buy this",
                "I would almost certainly buy this",
                
                # Set 3: Behavioral intent
                "I would never consider buying this",
                "I would rarely consider buying this",
                "I would sometimes consider buying this",
                "I would often consider buying this",
                "I would always consider buying this"
            ]
        })
        
        # Disappointment level - 3 reference sets (Sean Ellis PMF phrasing)
        disappointment_references = po.DataFrame({
            "id": ["set1"]*5 + ["set2"]*5 + ["set3"]*5,
            "int_response": [1, 2, 3, 4, 5] * 3,
            "sentence": [
                # Set 1: Direct disappointment
                "I would not be disappointed at all",
                "I would be slightly disappointed",
                "I would be somewhat disappointed",
                "I would be very disappointed",
                "I would be extremely disappointed",
                
                # Set 2: Impact assessment
                "It would not affect me in any way",
                "It would have minimal impact on me",
                "It would have moderate impact on me",
                "It would significantly impact me",
                "It would have a major negative impact on me",
                
                # Set 3: Loss reaction
                "I would not care if it disappeared",
                "I would barely notice if it disappeared",
                "I would notice if it disappeared",
                "I would really miss it if it disappeared",
                "I could not manage without it"
            ]
        })
        
        # Recommendation - 3 reference sets (NPS-aligned phrasing)
        recommendation_references = po.DataFrame({
            "id": ["set1"]*5 + ["set2"]*5 + ["set3"]*5,
            "int_response": [1, 2, 3, 4, 5] * 3,
            "sentence": [
                # Set 1: Direct recommendation
                "I would definitely not recommend this",
                "I would probably not recommend this",
                "I might recommend this",
                "I would probably recommend this",
                "I would definitely recommend this",
                
                # Set 2: Advocacy level
                "I would actively discourage others from trying this",
                "I would not suggest this to others",
                "I would mention this if asked",
                "I would suggest this to others",
                "I would enthusiastically promote this to others",
                
                # Set 3: Word of mouth
                "I would never tell anyone about this",
                "I would rarely tell anyone about this",
                "I might tell some people about this",
                "I would often tell people about this",
                "I would tell everyone I know about this"
            ]
        })
        
        # Initialize ResponseRaters with larger model and use "mean" to average across reference sets
        self.logger.log_info("Creating ResponseRaters with multiple reference sets...")
        self.interest_rater = ResponseRater(interest_references, model_name=embedding_model)
        self.purchase_intent_rater = ResponseRater(purchase_intent_references, model_name=embedding_model)
        self.disappointment_rater = ResponseRater(disappointment_references, model_name=embedding_model)
        self.recommendation_rater = ResponseRater(recommendation_references, model_name=embedding_model)
        
        self.logger.log_info(f"SSR ResponseRaters initialized successfully")
        self.logger.log_info(f"Using model: {embedding_model}")
        self.logger.log_info(f"Temperature: {self.config.ssr_temperature}, Epsilon: {self.config.ssr_epsilon}")
    
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
        purchase_intent_texts = [r.purchase_intent_response for r in responses]
        disappointment_texts = [r.disappointment_response for r in responses]
        recommendation_texts = [r.recommendation_response for r in responses]
        
        # Get temperature and epsilon from config
        temperature = self.config.ssr_temperature
        epsilon = self.config.ssr_epsilon
        
        # Convert to PMFs using SSR with "mean" to average across reference sets
        self.logger.log_info(f"Converting responses to PMFs (temp={temperature}, eps={epsilon})...")
        interest_pmfs = self.interest_rater.get_response_pmfs(
            "mean", interest_texts, temperature=temperature, epsilon=epsilon
        )
        purchase_intent_pmfs = self.purchase_intent_rater.get_response_pmfs(
            "mean", purchase_intent_texts, temperature=temperature, epsilon=epsilon
        )
        disappointment_pmfs = self.disappointment_rater.get_response_pmfs(
            "mean", disappointment_texts, temperature=temperature, epsilon=epsilon
        )
        recommendation_pmfs = self.recommendation_rater.get_response_pmfs(
            "mean", recommendation_texts, temperature=temperature, epsilon=epsilon
        )
        
        # Aggregate PMFs to get survey-level probability distributions
        # This is the key SSR insight: maintain uncertainty through probability distributions
        survey_interest_pmf = interest_pmfs.mean(axis=0)  # Average across all personas
        survey_purchase_intent_pmf = purchase_intent_pmfs.mean(axis=0)
        survey_disappointment_pmf = disappointment_pmfs.mean(axis=0)
        survey_recommendation_pmf = recommendation_pmfs.mean(axis=0)
        
        # Log PMFs for debugging
        self.logger.log_info(f"Survey Interest PMF: {survey_interest_pmf}")
        self.logger.log_info(f"Survey Purchase Intent PMF: {survey_purchase_intent_pmf}")
        self.logger.log_info(f"Survey Disappointment PMF: {survey_disappointment_pmf}")
        
        # Calculate expected values from aggregated PMFs
        avg_interest = float(np.dot(survey_interest_pmf, [1, 2, 3, 4, 5]))
        avg_disappointment = float(np.dot(survey_disappointment_pmf, [1, 2, 3, 4, 5]))
        avg_recommendation = float(np.dot(survey_recommendation_pmf, [1, 2, 3, 4, 5]))
        
        # Traditional PMF Score: P(very disappointed) = P(level 4) + P(level 5)
        # This is the Sean Ellis PMF: probability of being "very disappointed"
        pmf_score = float((survey_disappointment_pmf[3] + survey_disappointment_pmf[4]) * 100)
        
        # NPS calculation from recommendation PMF
        # Convert 1-5 scale to NPS: map to midpoints [1, 3, 5, 7, 9]
        # Promoters: P(level 5) ≈ NPS 9-10
        # Passives: P(level 4) ≈ NPS 7-8
        # Detractors: P(levels 1-3) ≈ NPS 0-6
        nps_promoters_prob = survey_recommendation_pmf[4]  # Level 5
        nps_detractors_prob = survey_recommendation_pmf[0] + survey_recommendation_pmf[1] + survey_recommendation_pmf[2]  # Levels 1-3
        nps = int((nps_promoters_prob - nps_detractors_prob) * 100)
        
        # Market Segmentation based on PMF probabilities
        # Superfans: P(interest=5 AND disappointment≥4)
        # Calculate joint probability assuming independence (conservative estimate)
        prob_very_interested = survey_interest_pmf[4]  # Level 5
        prob_very_disappointed = survey_disappointment_pmf[3] + survey_disappointment_pmf[4]  # Levels 4-5
        superfan_ratio = float(prob_very_interested * prob_very_disappointed)
        
        # Enthusiasts: P(interest≥4)
        enthusiasts_pct = float((survey_interest_pmf[3] + survey_interest_pmf[4]) * 100)
        
        # Interested: P(interest=3)
        interested_pct = float(survey_interest_pmf[2] * 100)
        
        # Skeptical: P(interest≤2)
        skeptical_pct = float((survey_interest_pmf[0] + survey_interest_pmf[1]) * 100)
        
        # Disappointment distribution
        very_disappointed_pct = float((survey_disappointment_pmf[3] + survey_disappointment_pmf[4]) * 100)
        somewhat_disappointed_pct = float(survey_disappointment_pmf[2] * 100)
        not_disappointed_pct = float((survey_disappointment_pmf[0] + survey_disappointment_pmf[1]) * 100)
        
        # Recommendation distribution
        promoters_pct = float(survey_recommendation_pmf[4] * 100)  # Level 5
        passives_pct = float(survey_recommendation_pmf[3] * 100)  # Level 4
        detractors_pct = float((survey_recommendation_pmf[0] + survey_recommendation_pmf[1] + survey_recommendation_pmf[2]) * 100)
        
        # Calculate superfans_pct from the ratio (as percentage)
        superfans_pct = superfan_ratio * 100
        
        segmentation = MarketSegmentation(
            superfans_pct=superfans_pct,
            enthusiasts_pct=enthusiasts_pct,
            interested_pct=interested_pct,
            skeptical_pct=skeptical_pct,
            very_disappointed_pct=very_disappointed_pct,
            somewhat_disappointed_pct=somewhat_disappointed_pct,
            not_disappointed_pct=not_disappointed_pct,
            promoters_pct=promoters_pct,
            passives_pct=passives_pct,
            detractors_pct=detractors_pct,
        )
        
        # Target Market Size (superfans + enthusiasts)
        target_market_size_pct = superfans_pct + enthusiasts_pct
        
        # Interest Distribution: Report as probability distribution (not counts!)
        # This preserves the SSR methodology of maintaining uncertainty
        interest_dist = {
            i+1: float(survey_interest_pmf[i]) for i in range(5)
        }
        
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
   - Purchase Intent: {response.purchase_intent_response}
   - Disappointment: {response.disappointment_response}
   - Recommendation: {response.recommendation_response}
   - Main Benefit: {response.main_benefit}
   - Concerns: {', '.join(response.concerns)}
""".strip())
        
        return "\n\n".join(feedback_parts)


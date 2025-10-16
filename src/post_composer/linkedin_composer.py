"""LinkedIn post composer."""

from typing import List
from ..utils import (
    get_config,
    get_logger,
    ProductConcept,
    MarketFitScore,
    SocialMediaPost,
)


class LinkedInComposer:
    """
    Compose posts optimized for LinkedIn.
    
    Specifications:
    - 3000 character limit
    - Optimal: 1500 characters for engagement
    - 3-5 hashtags recommended
    - Image: 1200x627px (1.91:1)
    - Markdown formatting supported
    """
    
    def __init__(self):
        """Initialize LinkedIn composer."""
        self.config = get_config()
        self.logger = get_logger()
        
        self.max_chars = self.config.linkedin_max_chars
        self.optimal_length = self.config.get_setting("social_media", "linkedin", "optimal_length", default=1500)
        self.recommended_hashtags = self.config.get_setting("social_media", "linkedin", "hashtags_recommended", default=5)
    
    def compose_post(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore
    ) -> SocialMediaPost:
        """
        Compose LinkedIn post from concept and market data.
        
        Args:
            concept: Product concept
            market_fit: Market fit scores
        
        Returns:
            SocialMediaPost object
        """
        self.logger.log_agent_start("LinkedIn Composer", "Composing post")
        
        # Build post with LinkedIn formatting
        post_parts = []
        
        # Title/Hook
        post_parts.append(f"# Introducing: {concept.name}")
        post_parts.append("")
        post_parts.append(concept.tagline)
        post_parts.append("")
        
        # The Problem
        post_parts.append("## The Problem")
        post_parts.append("")
        post_parts.append(concept.problem_solved)
        post_parts.append("")
        post_parts.append(f"This challenge particularly affects **{concept.target_market}**.")
        post_parts.append("")
        
        # Our Solution
        post_parts.append("## Our Solution")
        post_parts.append("")
        for i, feature in enumerate(concept.features, 1):
            post_parts.append(f"**{i}. {feature}**")
        post_parts.append("")
        
        # Competitive Advantage
        if concept.differentiators:
            post_parts.append("## What Makes It Different")
            post_parts.append("")
            for diff in concept.differentiators[:3]:
                post_parts.append(f"✅ {diff}")
            post_parts.append("")
        
        # Market Validation
        post_parts.append("## Market Validation")
        post_parts.append("")
        post_parts.append(f"✅ **{market_fit.pmf_score:.1f}% Product-Market Fit** (Target: 40%+)")
        post_parts.append(f"✅ **{market_fit.nps} Net Promoter Score**")
        post_parts.append(f"✅ **{market_fit.avg_interest:.1f}/5.0 Average Interest**")
        post_parts.append("")
        
        # Top Benefits
        if market_fit.top_benefits:
            post_parts.append("**Top Benefits** identified by our market research:")
            for benefit in market_fit.top_benefits[:3]:
                post_parts.append(f"• {benefit}")
            post_parts.append("")
        
        # Business Model
        post_parts.append("## Business Model")
        post_parts.append("")
        post_parts.append(f"**Pricing Strategy:** {concept.pricing_model}")
        post_parts.append("")
        
        # AI Disclosure
        disclosure_template = self.config.linkedin_disclosure_template
        methodology_link = self.config.methodology_link
        personas_count = market_fit.total_responses
        
        disclosure = disclosure_template.format(
            link=methodology_link,
            personas_count=personas_count
        )
        post_parts.append(disclosure)
        post_parts.append("")
        
        # Hashtags
        hashtags = self._generate_hashtags(concept)
        hashtags_line = " ".join(hashtags)
        post_parts.append(hashtags_line)
        
        # Combine all parts
        post_text = "\n".join(post_parts)
        
        # Check length and trim if needed
        if len(post_text) > self.max_chars:
            # Remove some differentiators or benefits
            post_text = self._create_shorter_version(concept, market_fit, hashtags)
        
        # Create post object
        post = SocialMediaPost(
            platform="linkedin",
            text=post_text[:self.max_chars],
            char_count=len(post_text),
            image_paths=[],  # Will be populated by asset bundler
            hashtags=hashtags,
        )
        
        self.logger.log_agent_complete("LinkedIn Composer")
        return post
    
    def _create_shorter_version(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore,
        hashtags: List[str]
    ) -> str:
        """Create shorter version if post exceeds limit."""
        post_parts = []
        
        post_parts.append(f"# {concept.name}")
        post_parts.append("")
        post_parts.append(concept.tagline)
        post_parts.append("")
        
        post_parts.append("## The Challenge")
        post_parts.append(concept.problem_solved)
        post_parts.append("")
        
        post_parts.append("## Key Features")
        for i, feature in enumerate(concept.features[:3], 1):
            post_parts.append(f"{i}. {feature}")
        post_parts.append("")
        
        post_parts.append("## Validation")
        post_parts.append(f"✅ {market_fit.pmf_score:.1f}% PMF | {market_fit.nps} NPS")
        post_parts.append("")
        
        # Disclosure
        post_parts.append(f"🤖 AI-powered ideation with {market_fit.total_responses}+ synthetic personas.")
        post_parts.append("")
        
        post_parts.append(" ".join(hashtags))
        
        return "\n".join(post_parts)
    
    def _generate_hashtags(self, concept: ProductConcept) -> List[str]:
        """Generate relevant hashtags (3-5)."""
        hashtags = []
        
        # Industry/category hashtags
        hashtags.append("#ProductInnovation")
        hashtags.append("#AIpowered")
        
        # Add specific tags based on concept
        if "tech" in concept.target_market.lower() or "software" in concept.name.lower():
            hashtags.append("#TechInnovation")
        
        if "market" in concept.problem_solved.lower():
            hashtags.append("#MarketResearch")
        
        # Add product development tag
        hashtags.append("#ProductDevelopment")
        
        return hashtags[:self.recommended_hashtags]
    
    def compose_article_intro(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore
    ) -> str:
        """
        Compose introduction for a LinkedIn article.
        
        Args:
            concept: Product concept
            market_fit: Market fit scores
        
        Returns:
            Article introduction text
        """
        intro_parts = []
        
        intro_parts.append(f"# The Story Behind {concept.name}")
        intro_parts.append("")
        intro_parts.append("## Innovation Through AI-Powered Ideation")
        intro_parts.append("")
        intro_parts.append(
            f"In today's fast-paced market, identifying real problems and creating "
            f"viable solutions requires more than intuition—it demands data-driven validation."
        )
        intro_parts.append("")
        intro_parts.append(
            f"This is the story of how we developed **{concept.name}**, a product concept "
            f"that achieved a {market_fit.pmf_score:.1f}% product-market fit score through "
            f"AI-powered market simulation."
        )
        intro_parts.append("")
        intro_parts.append("## The Problem")
        intro_parts.append("")
        intro_parts.append(concept.problem_solved)
        intro_parts.append("")
        intro_parts.append("[Continue reading...]")
        
        return "\n".join(intro_parts)


"""X.com (Twitter) post composer."""

from typing import Dict, Any
from ..utils import (
    get_config,
    get_logger,
    ProductConcept,
    MarketFitScore,
    SocialMediaPost,
)


class XComposer:
    """
    Compose posts optimized for X.com (Twitter).
    
    Specifications:
    - 280 character limit
    - Optimal: 70-100 characters for engagement
    - Max 2 hashtags
    - Image: 1200x675px (16:9)
    """
    
    def __init__(self):
        """Initialize X composer."""
        self.config = get_config()
        self.logger = get_logger()
        
        self.max_chars = self.config.x_max_chars
        self.optimal_length = self.config.get_setting("social_media", "x", "optimal_length", default=100)
        self.max_hashtags = self.config.get_setting("social_media", "x", "hashtags_max", default=2)
        self.include_emoji = self.config.get_setting("social_media", "x", "include_emoji", default=True)
    
    def compose_post(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore
    ) -> SocialMediaPost:
        """
        Compose X.com post from concept and market data.
        
        Args:
            concept: Product concept
            market_fit: Market fit scores
        
        Returns:
            SocialMediaPost object
        """
        self.logger.log_agent_start("X Composer", "Composing post")
        
        # Build post components
        components = []
        
        # Opening with product name and tagline
        if self.include_emoji:
            opening = f"🚀 {concept.name}: {concept.tagline}"
        else:
            opening = f"{concept.name}: {concept.tagline}"
        
        components.append(opening)
        
        # Add top features (max 3, truncated)
        features_text = "\n\nKey features:"
        for i, feature in enumerate(concept.features[:3], 1):
            # Truncate long features
            feature_short = feature[:50] + "..." if len(feature) > 50 else feature
            features_text += f"\n• {feature_short}"
        
        # Market validation
        validation = f"\n\n✅ {market_fit.pmf_score:.0f}% market fit"
        if market_fit.nps > 0:
            validation += f" | NPS: {market_fit.nps}"
        
        # AI disclosure
        disclosure_template = self.config.x_disclosure_template
        methodology_link = self.config.methodology_link
        disclosure = "\n\n" + disclosure_template.format(link=methodology_link)
        
        # Assemble post
        post_text = opening + features_text + validation + disclosure
        
        # Check length and truncate if needed
        if len(post_text) > self.max_chars:
            # Try removing one feature
            features_text = "\n\nKey features:"
            for feature in concept.features[:2]:
                feature_short = feature[:40] + "..." if len(feature) > 40 else feature
                features_text += f"\n• {feature_short}"
            
            post_text = opening + features_text + validation + disclosure
        
        # Still too long? Simplify further
        if len(post_text) > self.max_chars:
            post_text = (
                f"{opening}\n\n"
                f"✅ {market_fit.pmf_score:.0f}% market fit\n"
                f"🤖 AI-powered ideation"
            )
        
        # Extract hashtags (from target market or features)
        hashtags = self._generate_hashtags(concept)
        
        # Create post object
        post = SocialMediaPost(
            platform="x",
            text=post_text[:self.max_chars],  # Ensure within limit
            char_count=len(post_text),
            image_paths=[],  # Will be populated by asset bundler
            hashtags=hashtags,
        )
        
        self.logger.log_agent_complete("X Composer")
        return post
    
    def _generate_hashtags(self, concept: ProductConcept) -> list:
        """Generate relevant hashtags (max 2)."""
        hashtags = []
        
        # Add innovation hashtag
        hashtags.append("#Innovation")
        
        # Add product category or target market
        if "AI" in concept.name or "ai" in concept.name.lower():
            hashtags.append("#AI")
        elif "tech" in concept.target_market.lower():
            hashtags.append("#Tech")
        else:
            hashtags.append("#Product")
        
        return hashtags[:self.max_hashtags]
    
    def compose_thread(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore
    ) -> list[SocialMediaPost]:
        """
        Compose a thread for more detailed sharing.
        
        Args:
            concept: Product concept
            market_fit: Market fit scores
        
        Returns:
            List of SocialMediaPost objects (thread)
        """
        self.logger.log_agent_start("X Composer", "Composing thread")
        
        thread = []
        
        # Tweet 1: Introduction
        tweet1 = f"🚀 Introducing {concept.name}\n\n{concept.tagline}\n\nA thread on why this matters 🧵"
        thread.append(SocialMediaPost(
            platform="x",
            text=tweet1,
            char_count=len(tweet1),
            image_paths=[],
            hashtags=[],
        ))
        
        # Tweet 2: Problem
        tweet2 = f"The Problem:\n\n{concept.problem_solved}\n\nThis affects {concept.target_market}"
        thread.append(SocialMediaPost(
            platform="x",
            text=tweet2,
            char_count=len(tweet2),
            image_paths=[],
            hashtags=[],
        ))
        
        # Tweet 3: Solution (features)
        tweet3 = f"Our Solution:\n\n"
        for i, feature in enumerate(concept.features[:3], 1):
            tweet3 += f"{i}. {feature[:60]}\n"
        thread.append(SocialMediaPost(
            platform="x",
            text=tweet3[:280],
            char_count=len(tweet3),
            image_paths=[],
            hashtags=[],
        ))
        
        # Tweet 4: Validation
        tweet4 = (
            f"Market Validation:\n\n"
            f"✅ {market_fit.pmf_score:.0f}% PMF Score\n"
            f"✅ {market_fit.nps} NPS\n"
            f"✅ {market_fit.avg_interest:.1f}/5.0 Interest\n\n"
            f"Validated with {market_fit.total_responses}+ personas"
        )
        thread.append(SocialMediaPost(
            platform="x",
            text=tweet4,
            char_count=len(tweet4),
            image_paths=[],
            hashtags=[],
        ))
        
        # Tweet 5: Call to action with disclosure
        methodology_link = self.config.methodology_link
        tweet5 = (
            f"Want to learn more?\n\n"
            f"🤖 This concept was developed using AI-powered ideation\n"
            f"📊 Full methodology: {methodology_link}\n\n"
            f"#Innovation #AIpowered"
        )
        thread.append(SocialMediaPost(
            platform="x",
            text=tweet5,
            char_count=len(tweet5),
            image_paths=[],
            hashtags=["#Innovation", "#AIpowered"],
        ))
        
        self.logger.log_agent_complete("X Composer")
        return thread


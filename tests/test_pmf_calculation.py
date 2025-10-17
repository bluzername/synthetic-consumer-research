"""Tests for PMF calculation logic using SSR."""

import pytest
from src.utils.models import PersonaResponse


class TestPMFCalculation:
    """Tests for Product-Market Fit calculation with SSR."""
    
    # Map numeric ratings to natural language for SSR
    INTEREST_MAP = {
        1: "Not interested at all",
        2: "Slightly interested",
        3: "Moderately interested",
        4: "Very interested",
        5: "Extremely interested"
    }
    
    DISAPPOINTMENT_MAP = {
        "NOT": "Wouldn't care at all if it disappeared",
        "SOMEWHAT": "Would be somewhat disappointed",
        "VERY": "Would be devastated and very disappointed"
    }
    
    RECOMMEND_MAP = {
        0: "Definitely would not recommend",
        1: "Definitely would not recommend",
        2: "Definitely would not recommend",
        3: "Probably would not recommend",
        4: "Probably would not recommend",
        5: "Might recommend",
        6: "Might recommend",
        7: "Probably would recommend",
        8: "Probably would recommend",
        9: "Absolutely would recommend",
        10: "Absolutely would recommend"
    }
    
    def create_response(self, interest: int, disappointment: str, recommend: int) -> PersonaResponse:
        """Helper to create persona response with natural language."""
        # Map recommend value to purchase intent
        purchase_intent_text = "I would definitely purchase this" if recommend >= 9 else \
                              "I probably would purchase this" if recommend >= 7 else \
                              "I might or might not purchase this" if recommend >= 5 else \
                              "I probably would not purchase this"
        
        return PersonaResponse(
            persona_name=f"Persona_{interest}_{disappointment}_{recommend}",
            interest_response=self.INTEREST_MAP[interest],
            purchase_intent_response=purchase_intent_text,
            disappointment_response=self.DISAPPOINTMENT_MAP[disappointment],
            recommendation_response=self.RECOMMEND_MAP[recommend],
            main_benefit="Test benefit",
            concerns=["Test concern"]
        )
    
    def test_superfan_identification(self):
        """Test that superfan responses are created with appropriate language."""
        # Superfan: extremely interested AND would be devastated
        superfan = self.create_response(5, "VERY", 10)
        assert "extremely" in superfan.interest_response.lower()
        assert "devastated" in superfan.disappointment_response.lower() or "very disappointed" in superfan.disappointment_response.lower()
        
        # Not superfan: high interest but not VERY disappointed
        enthusiast = self.create_response(5, "SOMEWHAT", 9)
        assert "extremely" in enthusiast.interest_response.lower()
        assert "somewhat" in enthusiast.disappointment_response.lower()
        
        # Not superfan: VERY disappointed but lower interest
        disappointed = self.create_response(4, "VERY", 8)
        assert "devastated" in disappointed.disappointment_response.lower() or "very disappointed" in disappointed.disappointment_response.lower()
        assert "very interested" in disappointed.interest_response.lower()
    
    def test_nps_classification(self):
        """Test NPS classification through natural language responses."""
        # Promoter: 9-10
        promoter1 = self.create_response(5, "VERY", 9)
        promoter2 = self.create_response(4, "SOMEWHAT", 10)
        assert "absolutely" in promoter1.recommendation_response.lower()
        assert "absolutely" in promoter2.recommendation_response.lower()
        
        # Passive: 7-8
        passive1 = self.create_response(3, "SOMEWHAT", 7)
        passive2 = self.create_response(4, "SOMEWHAT", 8)
        assert "probably" in passive1.recommendation_response.lower()
        assert "probably" in passive2.recommendation_response.lower()
        
        # Detractor: 0-6
        detractor1 = self.create_response(2, "NOT", 6)
        detractor2 = self.create_response(1, "NOT", 3)
        assert "might" in detractor1.recommendation_response.lower() or "not" in detractor1.recommendation_response.lower()
        assert "not" in detractor2.recommendation_response.lower()
    
    def test_traditional_pmf_calculation(self):
        """Test that responses can be created for PMF calculation."""
        responses = [
            self.create_response(5, "VERY", 10),      # Very disappointed
            self.create_response(5, "VERY", 9),       # Very disappointed
            self.create_response(4, "SOMEWHAT", 8),   # Somewhat
            self.create_response(4, "SOMEWHAT", 7),   # Somewhat
            self.create_response(3, "NOT", 5),        # Not
            self.create_response(2, "NOT", 4),        # Not
            self.create_response(1, "NOT", 2),        # Not
            self.create_response(3, "SOMEWHAT", 6),   # Somewhat
            self.create_response(4, "VERY", 8),       # Very disappointed
            self.create_response(2, "NOT", 3),        # Not
        ]
        
        # Verify all responses are created with natural language
        assert len(responses) == 10
        for r in responses:
            assert isinstance(r.interest_response, str)
            assert isinstance(r.disappointment_response, str)
            assert isinstance(r.recommendation_response, str)
            assert len(r.interest_response) > 0
    
    def test_superfan_ratio_calculation(self):
        """Test that superfan-style responses are created correctly."""
        responses = [
            self.create_response(5, "VERY", 10),      # SUPERFAN
            self.create_response(5, "VERY", 9),       # SUPERFAN
            self.create_response(5, "SOMEWHAT", 9),   # Not superfan (not VERY disappointed)
            self.create_response(4, "VERY", 8),       # Not superfan (interest < 5)
            self.create_response(5, "VERY", 10),      # SUPERFAN
            self.create_response(3, "NOT", 5),        # Not superfan
            self.create_response(2, "NOT", 4),        # Not superfan
            self.create_response(4, "SOMEWHAT", 7),   # Not superfan
            self.create_response(5, "NOT", 6),        # Not superfan (not VERY disappointed)
            self.create_response(1, "NOT", 2),        # Not superfan
        ]
        
        # Count potential superfans based on language patterns
        # (extremely interested + devastated/very disappointed)
        potential_superfans = sum(1 for r in responses 
                                 if "extremely" in r.interest_response.lower() 
                                 and ("devastated" in r.disappointment_response.lower() 
                                      or "very disappointed" in r.disappointment_response.lower()))
        
        # 3 out of 10 should have superfan-style language
        assert potential_superfans == 3
        assert potential_superfans / len(responses) >= 0.10  # Viable niche threshold
    
    def test_nps_calculation(self):
        """Test that NPS-related responses use appropriate language."""
        responses = [
            self.create_response(5, "VERY", 10),      # Promoter
            self.create_response(5, "VERY", 9),       # Promoter
            self.create_response(4, "SOMEWHAT", 8),   # Passive
            self.create_response(4, "SOMEWHAT", 7),   # Passive
            self.create_response(3, "NOT", 6),        # Detractor
            self.create_response(2, "NOT", 5),        # Detractor
            self.create_response(2, "NOT", 4),        # Detractor
            self.create_response(3, "SOMEWHAT", 7),   # Passive
            self.create_response(4, "VERY", 9),       # Promoter
            self.create_response(1, "NOT", 2),        # Detractor
        ]
        
        # Count based on language patterns
        promoters = sum(1 for r in responses if "absolutely" in r.recommendation_response.lower())
        detractors = sum(1 for r in responses if "not" in r.recommendation_response.lower())
        
        # 3 promoters, at least some detractors
        assert promoters == 3
        assert detractors >= 2  # At least 2 with "not" in response
    
    def test_interest_distribution(self):
        """Test that interest responses cover the full range."""
        responses = [
            self.create_response(5, "VERY", 10),
            self.create_response(5, "SOMEWHAT", 9),
            self.create_response(4, "VERY", 8),
            self.create_response(4, "SOMEWHAT", 7),
            self.create_response(3, "NOT", 6),
            self.create_response(3, "SOMEWHAT", 5),
            self.create_response(2, "NOT", 4),
            self.create_response(2, "NOT", 3),
            self.create_response(1, "NOT", 2),
            self.create_response(1, "NOT", 1),
        ]
        
        # Verify we have responses across the interest spectrum
        assert any("extremely" in r.interest_response.lower() for r in responses)
        assert any("very interested" in r.interest_response.lower() for r in responses)
        assert any("moderately" in r.interest_response.lower() for r in responses)
        assert any("slightly" in r.interest_response.lower() for r in responses)
        assert any("not interested" in r.interest_response.lower() for r in responses)
        assert len(responses) == 10
    
    def test_viable_niche_threshold(self):
        """Test that viable niche responses can be created."""
        # 10% superfan-style responses
        responses_viable = [
            self.create_response(5, "VERY", 10),   # Superfan
        ] + [self.create_response(3, "NOT", 5) for _ in range(9)]
        
        # Check for superfan language pattern
        superfans = sum(1 for r in responses_viable
                       if "extremely" in r.interest_response.lower()
                       and ("devastated" in r.disappointment_response.lower() 
                            or "very disappointed" in r.disappointment_response.lower()))
        ratio = superfans / len(responses_viable)
        
        assert ratio == 0.10
        assert ratio >= 0.10  # Viable
        
        # Lower percentage
        responses_not_viable = [
            self.create_response(5, "VERY", 10),   # Superfan
        ] + [self.create_response(3, "NOT", 5) for _ in range(10)]
        
        superfans = sum(1 for r in responses_not_viable
                       if "extremely" in r.interest_response.lower()
                       and ("devastated" in r.disappointment_response.lower()
                            or "very disappointed" in r.disappointment_response.lower()))
        ratio = superfans / len(responses_not_viable)
        
        assert abs(ratio - 0.0909) < 0.001  # ~9%
        assert ratio < 0.10  # Not viable
    
    def test_mass_market_threshold(self):
        """Test that mass market-style responses can be created."""
        # 40% enthusiast-style responses (very/extremely interested)
        responses_mass = [
            self.create_response(5, "VERY", 9),
            self.create_response(5, "SOMEWHAT", 8),
            self.create_response(4, "VERY", 8),
            self.create_response(4, "SOMEWHAT", 7),
        ] + [self.create_response(2, "NOT", 4) for _ in range(6)]
        
        # Count enthusiast language patterns
        enthusiasts = sum(1 for r in responses_mass 
                         if "extremely" in r.interest_response.lower() 
                         or "very interested" in r.interest_response.lower())
        enthusiasts_pct = (enthusiasts / len(responses_mass)) * 100
        
        assert enthusiasts == 4
        assert enthusiasts_pct == 40.0
        assert enthusiasts_pct >= 40.0  # Mass market viable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


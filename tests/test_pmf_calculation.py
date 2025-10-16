"""Tests for PMF calculation logic."""

import pytest
from src.utils.models import PersonaResponse, DisappointmentLevel


class TestPMFCalculation:
    """Tests for Product-Market Fit calculation."""
    
    def create_response(self, interest: int, disappointment: str, recommend: int) -> PersonaResponse:
        """Helper to create persona response."""
        return PersonaResponse(
            persona_name=f"Persona_{interest}_{disappointment}",
            interest_score=interest,
            disappointment=DisappointmentLevel(disappointment),
            main_benefit="Test benefit",
            concerns=["Test concern"],
            likelihood_to_recommend=recommend
        )
    
    def test_superfan_identification(self):
        """Test that superfans are correctly identified (5/5 interest + VERY disappointed)."""
        # Superfan: 5/5 interest AND VERY disappointed
        superfan = self.create_response(5, "VERY", 10)
        assert superfan.interest_score == 5
        assert superfan.is_very_disappointed()
        
        # Not superfan: high interest but not VERY disappointed
        enthusiast = self.create_response(5, "SOMEWHAT", 9)
        assert enthusiast.interest_score == 5
        assert not enthusiast.is_very_disappointed()
        
        # Not superfan: VERY disappointed but lower interest
        disappointed = self.create_response(4, "VERY", 8)
        assert disappointed.is_very_disappointed()
        assert disappointed.interest_score < 5
    
    def test_nps_classification(self):
        """Test NPS classification (promoters, passives, detractors)."""
        # Promoter: 9-10
        promoter1 = self.create_response(5, "VERY", 9)
        promoter2 = self.create_response(4, "SOMEWHAT", 10)
        assert promoter1.is_promoter()
        assert promoter2.is_promoter()
        assert not promoter1.is_detractor()
        
        # Passive: 7-8
        passive1 = self.create_response(3, "SOMEWHAT", 7)
        passive2 = self.create_response(4, "SOMEWHAT", 8)
        assert not passive1.is_promoter()
        assert not passive1.is_detractor()
        assert not passive2.is_promoter()
        assert not passive2.is_detractor()
        
        # Detractor: 0-6
        detractor1 = self.create_response(2, "NOT", 6)
        detractor2 = self.create_response(1, "NOT", 3)
        assert detractor1.is_detractor()
        assert detractor2.is_detractor()
        assert not detractor1.is_promoter()
    
    def test_traditional_pmf_calculation(self):
        """Test traditional Sean Ellis PMF calculation."""
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
        
        # Count "very disappointed"
        very_disappointed = sum(1 for r in responses if r.is_very_disappointed())
        pmf_score = (very_disappointed / len(responses)) * 100
        
        # 3 out of 10 are "very disappointed"
        assert very_disappointed == 3
        assert pmf_score == 30.0
    
    def test_superfan_ratio_calculation(self):
        """Test superfan ratio calculation (interest=5 AND disappointment=VERY)."""
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
        
        # Count superfans (5/5 AND VERY disappointed)
        superfans = sum(1 for r in responses 
                       if r.interest_score == 5 and r.is_very_disappointed())
        superfan_ratio = superfans / len(responses)
        
        # 3 out of 10 are superfans
        assert superfans == 3
        assert superfan_ratio == 0.30
        assert superfan_ratio >= 0.10  # Viable niche threshold
    
    def test_nps_calculation(self):
        """Test NPS calculation."""
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
        
        promoters = sum(1 for r in responses if r.is_promoter())
        detractors = sum(1 for r in responses if r.is_detractor())
        nps = ((promoters - detractors) / len(responses)) * 100
        
        # 3 promoters, 4 detractors
        assert promoters == 3
        assert detractors == 4
        assert nps == -10.0
    
    def test_interest_distribution(self):
        """Test interest score distribution."""
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
        
        distribution = {i: sum(1 for r in responses if r.interest_score == i) 
                       for i in range(1, 6)}
        
        assert distribution[5] == 2
        assert distribution[4] == 2
        assert distribution[3] == 2
        assert distribution[2] == 2
        assert distribution[1] == 2
        assert sum(distribution.values()) == 10
    
    def test_viable_niche_threshold(self):
        """Test 10% superfan threshold for viable niche."""
        # Exactly 10% superfans - should be viable
        responses_viable = [
            self.create_response(5, "VERY", 10),   # Superfan
        ] + [self.create_response(3, "NOT", 5) for _ in range(9)]
        
        superfans = sum(1 for r in responses_viable 
                       if r.interest_score == 5 and r.is_very_disappointed())
        ratio = superfans / len(responses_viable)
        
        assert ratio == 0.10
        assert ratio >= 0.10  # Viable
        
        # 9% superfans - not viable
        responses_not_viable = [
            self.create_response(5, "VERY", 10),   # Superfan
        ] + [self.create_response(3, "NOT", 5) for _ in range(10)]
        
        superfans = sum(1 for r in responses_not_viable 
                       if r.interest_score == 5 and r.is_very_disappointed())
        ratio = superfans / len(responses_not_viable)
        
        assert abs(ratio - 0.0909) < 0.001  # ~9%
        assert ratio < 0.10  # Not viable
    
    def test_mass_market_threshold(self):
        """Test 40% enthusiasts threshold for mass market."""
        # 40% enthusiasts (4-5 interest) - should be viable for mass market
        responses_mass = [
            self.create_response(5, "VERY", 9),
            self.create_response(5, "SOMEWHAT", 8),
            self.create_response(4, "VERY", 8),
            self.create_response(4, "SOMEWHAT", 7),
        ] + [self.create_response(2, "NOT", 4) for _ in range(6)]
        
        enthusiasts = sum(1 for r in responses_mass if r.interest_score >= 4)
        enthusiasts_pct = (enthusiasts / len(responses_mass)) * 100
        
        assert enthusiasts == 4
        assert enthusiasts_pct == 40.0
        assert enthusiasts_pct >= 40.0  # Mass market viable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

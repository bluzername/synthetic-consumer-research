"""Tests for Pydantic data models."""

import pytest
from src.utils.models import (
    ProductConcept,
    Persona,
    PersonaResponse,
    MarketFitScore,
    MarketSegmentation,
    CriticFeedback,
    DisappointmentLevel,
)


class TestProductConcept:
    """Tests for ProductConcept model."""
    
    def test_create_valid_concept(self):
        """Test creating a valid product concept."""
        concept = ProductConcept(
            name="Smart Water Bottle",
            tagline="Stay hydrated with AI-powered reminders",
            target_market="Health-conscious professionals aged 25-45",
            problem_solved="People forget to drink water throughout the day",
            features=[
                "Tracks water intake via weight sensors",
                "Smart reminders based on activity level",
                "Syncs with health apps"
            ],
            differentiators=[
                "AI-powered personalized hydration goals",
                "Sleek design that fits in cup holders"
            ],
            pricing_model="$49 one-time purchase"
        )
        
        assert concept.name == "Smart Water Bottle"
        assert len(concept.features) == 3
        assert len(concept.differentiators) == 2
    
    def test_concept_to_summary(self):
        """Test concept summary generation."""
        concept = ProductConcept(
            name="Test Product",
            tagline="Test tagline",
            target_market="Test market",
            problem_solved="Test problem",
            features=["Feature 1", "Feature 2"],
            differentiators=["Diff 1"],
            pricing_model="$10"
        )
        
        summary = concept.to_summary()
        assert "Test Product" in summary
        assert "Test tagline" in summary
        assert "Feature 1" in summary


class TestPersona:
    """Tests for Persona model."""
    
    def test_create_valid_persona(self):
        """Test creating a valid persona."""
        persona = Persona(
            name="Alice Johnson",
            age=32,
            occupation="Software Engineer",
            income_bracket="Upper middle class",
            location_type="Urban",
            tech_savviness=5,
            values=["Innovation", "Efficiency"],
            pain_points=["Time management", "Work-life balance"],
            personality_traits="High openness, conscientious",
            shopping_behavior="Research-focused, reads reviews"
        )
        
        assert persona.age == 32
        assert persona.tech_savviness == 5
        assert len(persona.values) == 2
    
    def test_age_validation(self):
        """Test that age is validated."""
        with pytest.raises(Exception):  # Pydantic validation error
            Persona(
                name="Invalid",
                age=15,  # Below minimum
                occupation="Student",
                income_bracket="Low",
                location_type="Urban",
                tech_savviness=3,
                values=["Education"],
                pain_points=["Homework"],
                personality_traits="Young",
                shopping_behavior="Impulsive"
            )
    
    def test_tech_savviness_validation(self):
        """Test that tech_savviness is validated."""
        with pytest.raises(Exception):  # Pydantic validation error
            Persona(
                name="Invalid",
                age=30,
                occupation="Teacher",
                income_bracket="Middle",
                location_type="Suburban",
                tech_savviness=6,  # Above maximum
                values=["Education"],
                pain_points=["Funding"],
                personality_traits="Patient",
                shopping_behavior="Careful"
            )
    
    def test_persona_to_prompt_context(self):
        """Test persona conversion to prompt context."""
        persona = Persona(
            name="Bob Smith",
            age=45,
            occupation="Manager",
            income_bracket="High",
            location_type="Suburban",
            tech_savviness=3,
            values=["Quality", "Reliability"],
            pain_points=["Efficiency", "Cost"],
            personality_traits="Pragmatic",
            shopping_behavior="Value-focused"
        )
        
        context = persona.to_prompt_context()
        assert context["persona_name"] == "Bob Smith"
        assert context["persona_age"] == 45
        assert "Quality" in context["persona_values"]


class TestPersonaResponse:
    """Tests for PersonaResponse model."""
    
    def test_create_valid_response(self):
        """Test creating a valid persona response."""
        response = PersonaResponse(
            persona_name="Alice Johnson",
            interest_score=4,
            disappointment=DisappointmentLevel.SOMEWHAT,
            main_benefit="Helps me stay healthy",
            concerns=["Price seems high", "Battery life unclear"],
            likelihood_to_recommend=7
        )
        
        assert response.interest_score == 4
        assert response.disappointment == DisappointmentLevel.SOMEWHAT
        assert len(response.concerns) == 2
    
    def test_is_very_disappointed(self):
        """Test very disappointed check."""
        response = PersonaResponse(
            persona_name="Test",
            interest_score=5,
            disappointment=DisappointmentLevel.VERY,
            main_benefit="Essential",
            concerns=[],
            likelihood_to_recommend=10
        )
        
        assert response.is_very_disappointed() is True
    
    def test_is_promoter(self):
        """Test promoter identification."""
        response = PersonaResponse(
            persona_name="Test",
            interest_score=5,
            disappointment=DisappointmentLevel.VERY,
            main_benefit="Great",
            concerns=[],
            likelihood_to_recommend=9
        )
        
        assert response.is_promoter() is True
        assert response.is_detractor() is False
    
    def test_is_detractor(self):
        """Test detractor identification."""
        response = PersonaResponse(
            persona_name="Test",
            interest_score=2,
            disappointment=DisappointmentLevel.NOT,
            main_benefit="Nothing special",
            concerns=["Too expensive", "Unnecessary"],
            likelihood_to_recommend=5
        )
        
        assert response.is_detractor() is True
        assert response.is_promoter() is False


class TestMarketSegmentation:
    """Tests for MarketSegmentation model."""
    
    def test_create_segmentation(self):
        """Test creating market segmentation."""
        seg = MarketSegmentation(
            superfans_pct=12.0,
            enthusiasts_pct=28.0,
            interested_pct=35.0,
            skeptical_pct=25.0,
            very_disappointed_pct=15.0,
            somewhat_disappointed_pct=30.0,
            not_disappointed_pct=55.0,
            promoters_pct=20.0,
            passives_pct=30.0,
            detractors_pct=50.0
        )
        
        assert seg.superfans_pct == 12.0
        assert seg.enthusiasts_pct == 28.0
        # Check percentages add up approximately to 100
        total_interest = seg.superfans_pct + seg.enthusiasts_pct + seg.interested_pct + seg.skeptical_pct
        assert abs(total_interest - 100.0) < 1.0  # Allow for rounding


class TestMarketFitScore:
    """Tests for MarketFitScore model."""
    
    def test_create_market_fit_score(self):
        """Test creating a market fit score."""
        segmentation = MarketSegmentation(
            superfans_pct=15.0,
            enthusiasts_pct=25.0,
            interested_pct=30.0,
            skeptical_pct=30.0,
            very_disappointed_pct=18.0,
            somewhat_disappointed_pct=32.0,
            not_disappointed_pct=50.0,
            promoters_pct=22.0,
            passives_pct=28.0,
            detractors_pct=50.0
        )
        
        score = MarketFitScore(
            pmf_score=18.0,
            avg_interest=3.2,
            nps=-28,
            segmentation=segmentation,
            target_market_size_pct=40.0,
            superfan_ratio=0.15,
            interest_distribution={1: 20, 2: 10, 3: 30, 4: 25, 5: 15},
            top_benefits=["Easy to use", "Solves real problem"],
            top_concerns=["Price", "Battery life"],
            recommendation="PROCEED (NICHE)",
            business_model_fit="Premium/Niche targeting",
            total_responses=100
        )
        
        assert score.pmf_score == 18.0
        assert score.superfan_ratio == 0.15
        assert score.total_responses == 100
    
    def test_is_viable_niche(self):
        """Test niche viability check."""
        segmentation = MarketSegmentation(
            superfans_pct=12.0,
            enthusiasts_pct=20.0,
            interested_pct=30.0,
            skeptical_pct=38.0,
            very_disappointed_pct=12.0,
            somewhat_disappointed_pct=30.0,
            not_disappointed_pct=58.0,
            promoters_pct=15.0,
            passives_pct=25.0,
            detractors_pct=60.0
        )
        
        score = MarketFitScore(
            pmf_score=12.0,
            avg_interest=2.8,
            nps=-45,
            segmentation=segmentation,
            target_market_size_pct=32.0,
            superfan_ratio=0.12,  # Above 10% threshold
            interest_distribution={1: 38, 2: 22, 3: 8, 4: 20, 5: 12},
            top_benefits=["Unique feature"],
            top_concerns=["Price", "Complexity"],
            recommendation="PROCEED (NICHE)",
            business_model_fit="Premium",
            total_responses=100
        )
        
        assert score.is_viable_niche() is True
    
    def test_is_viable_mass_market(self):
        """Test mass market viability check."""
        segmentation = MarketSegmentation(
            superfans_pct=15.0,
            enthusiasts_pct=45.0,  # Above 40% threshold
            interested_pct=25.0,
            skeptical_pct=15.0,
            very_disappointed_pct=20.0,
            somewhat_disappointed_pct=40.0,
            not_disappointed_pct=40.0,
            promoters_pct=35.0,
            passives_pct=40.0,
            detractors_pct=25.0
        )
        
        score = MarketFitScore(
            pmf_score=20.0,
            avg_interest=4.1,
            nps=10,
            segmentation=segmentation,
            target_market_size_pct=60.0,
            superfan_ratio=0.15,
            interest_distribution={1: 15, 2: 8, 3: 25, 4: 37, 5: 15},
            top_benefits=["Easy", "Affordable", "Useful"],
            top_concerns=["Competition"],
            recommendation="PROCEED (MASS MARKET)",
            business_model_fit="Freemium",
            total_responses=100
        )
        
        assert score.is_viable_mass_market() is True
    
    def test_should_proceed(self):
        """Test overall proceed recommendation."""
        segmentation = MarketSegmentation(
            superfans_pct=11.0,
            enthusiasts_pct=25.0,
            interested_pct=30.0,
            skeptical_pct=34.0,
            very_disappointed_pct=12.0,
            somewhat_disappointed_pct=28.0,
            not_disappointed_pct=60.0,
            promoters_pct=18.0,
            passives_pct=30.0,
            detractors_pct=52.0
        )
        
        score = MarketFitScore(
            pmf_score=12.0,
            avg_interest=3.0,
            nps=-34,
            segmentation=segmentation,
            target_market_size_pct=36.0,
            superfan_ratio=0.11,  # Above 10% - viable!
            interest_distribution={1: 34, 2: 20, 3: 15, 4: 20, 5: 11},
            top_benefits=["Innovative"],
            top_concerns=["Price", "Unproven"],
            recommendation="PROCEED (NICHE)",
            business_model_fit="Premium/Niche",
            total_responses=100
        )
        
        # Should proceed because superfan_ratio >= 0.10
        assert score.should_proceed() is True
    
    def test_get_viability_summary(self):
        """Test viability summary generation."""
        segmentation = MarketSegmentation(
            superfans_pct=10.0,
            enthusiasts_pct=30.0,
            interested_pct=35.0,
            skeptical_pct=25.0,
            very_disappointed_pct=10.0,
            somewhat_disappointed_pct=30.0,
            not_disappointed_pct=60.0,
            promoters_pct=15.0,
            passives_pct=30.0,
            detractors_pct=55.0
        )
        
        score = MarketFitScore(
            pmf_score=10.0,
            avg_interest=3.1,
            nps=-40,
            segmentation=segmentation,
            target_market_size_pct=40.0,
            superfan_ratio=0.10,
            interest_distribution={1: 25, 2: 18, 3: 22, 4: 25, 5: 10},
            top_benefits=["Solves problem", "Easy to use"],
            top_concerns=["Price", "Reliability"],
            recommendation="PROCEED (NICHE)",
            business_model_fit="Premium",
            total_responses=100
        )
        
        summary = score.get_viability_summary()
        
        assert "viable" in summary
        assert "rating" in summary
        assert "superfan_ratio" in summary
        assert summary["key_strength"] == "Solves problem"
        assert summary["key_concern"] == "Price"


class TestCriticFeedback:
    """Tests for CriticFeedback model."""
    
    def test_create_feedback(self):
        """Test creating critic feedback."""
        feedback = CriticFeedback(
            strengths_to_amplify=[
                "Strong value proposition",
                "Clear target market"
            ],
            critical_gaps=[
                "Pricing concerns from 40% of respondents",
                "Technical feasibility questions"
            ],
            specific_refinements={
                "features": ["Add battery life specs", "Clarify AI capabilities"],
                "pricing": ["Consider tiered pricing", "Offer trial period"],
                "positioning": ["Emphasize health benefits more"]
            },
            strategic_direction="Double down on health benefits while addressing price concerns through value demonstration"
        )
        
        assert len(feedback.strengths_to_amplify) == 2
        assert len(feedback.critical_gaps) == 2
        assert "features" in feedback.specific_refinements
    
    def test_to_refinement_prompt(self):
        """Test conversion to refinement prompt."""
        feedback = CriticFeedback(
            strengths_to_amplify=["Strong value prop"],
            critical_gaps=["High price"],
            specific_refinements={
                "features": ["Add X"],
                "pricing": ["Lower to $29"]
            },
            strategic_direction="Focus on value"
        )
        
        prompt = feedback.to_refinement_prompt()
        
        assert "Strong value prop" in prompt
        assert "High price" in prompt
        assert "Add X" in prompt
        assert "Focus on value" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

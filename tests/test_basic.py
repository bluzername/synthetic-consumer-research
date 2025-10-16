"""Basic tests to verify system setup and structure."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def test_config_files_exist():
    """Verify configuration files exist."""
    config_dir = Path("config")
    
    assert (config_dir / "settings.yaml").exists(), "settings.yaml not found"
    assert (config_dir / "prompts.yaml").exists(), "prompts.yaml not found"


def test_source_structure():
    """Verify source code structure."""
    src_dir = Path("src")
    
    # Check main modules exist
    assert (src_dir / "agents").is_dir(), "agents module missing"
    assert (src_dir / "utils").is_dir(), "utils module missing"
    assert (src_dir / "orchestration").is_dir(), "orchestration module missing"
    assert (src_dir / "visualization").is_dir(), "visualization module missing"
    assert (src_dir / "post_composer").is_dir(), "post_composer module missing"
    
    # Check main entry point
    assert (src_dir / "main.py").exists(), "main.py missing"


def test_documentation_exists():
    """Verify documentation files exist."""
    docs_dir = Path("docs")
    
    assert (docs_dir / "README.md").exists(), "docs README missing"
    assert (docs_dir / "SETUP.md").exists(), "SETUP.md missing"
    assert (docs_dir / "METHODOLOGY.md").exists(), "METHODOLOGY.md missing"
    assert (docs_dir / "ETHICS.md").exists(), "ETHICS.md missing"


def test_imports():
    """Test that core modules can be imported."""
    try:
        # Test utils imports
        from src.utils import (
            get_config,
            ProductConcept,
            Persona,
            MarketFitScore,
        )
        
        # Test agent imports
        from src.agents import (
            IdeatorAgent,
            PersonaGenerator,
            MarketPredictorAgent,
            CriticAgent,
        )
        
        # Test workflow
        from src.orchestration import create_workflow
        
        # Test visualization
        from src.visualization import ImageGenerator, InfographicGenerator
        
        # Test composers
        from src.post_composer import XComposer, LinkedInComposer, AssetBundler
        
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_pydantic_models():
    """Test that Pydantic models work correctly."""
    from src.utils import ProductConcept, Persona, MarketFitScore
    
    # Test ProductConcept
    concept = ProductConcept(
        name="Test Product",
        tagline="A test tagline",
        target_market="Test market",
        problem_solved="Test problem",
        features=["Feature 1", "Feature 2"],
        differentiators=["Diff 1"],
        pricing_model="Subscription"
    )
    
    assert concept.name == "Test Product"
    assert len(concept.features) == 2
    
    # Test Persona
    persona = Persona(
        name="Test User",
        age=30,
        occupation="Engineer",
        income_bracket="Middle",
        location_type="Urban",
        tech_savviness=4,
        values=["Quality", "Innovation"],
        pain_points=["Time", "Cost"],
        personality_traits="Analytical",
        shopping_behavior="Research-focused"
    )
    
    assert persona.age == 30
    assert persona.tech_savviness >= 1 and persona.tech_savviness <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


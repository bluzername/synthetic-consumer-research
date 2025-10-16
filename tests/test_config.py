"""Tests for configuration loader."""

import os
import pytest
import tempfile
from pathlib import Path
from src.utils.config_loader import Config
from src.utils.exceptions import ConfigurationError, AuthenticationError


class TestConfigValidation:
    """Tests for configuration validation."""
    
    def test_missing_api_key(self, monkeypatch):
        """Test that missing API key raises error."""
        # Remove API key from environment
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        
        with pytest.raises(AuthenticationError) as exc_info:
            Config()
        
        assert "OPENROUTER_API_KEY" in str(exc_info.value)
        assert "https://openrouter.ai/keys" in str(exc_info.value)
    
    def test_invalid_api_key_format(self, monkeypatch):
        """Test that invalid API key format raises error."""
        # Set invalid API key
        monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-key-format")
        
        with pytest.raises(AuthenticationError) as exc_info:
            Config()
        
        assert "invalid" in str(exc_info.value).lower()
        assert "sk-or-v1-" in str(exc_info.value)


@pytest.fixture
def valid_config(monkeypatch):
    """Fixture to provide a valid config for testing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")


class TestConfigAccess:
    """Tests for configuration access methods."""
    
    def test_model_configs(self, monkeypatch):
        """Test accessing model configurations."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test that model configs are accessible
        assert config.ideator_model is not None
        assert config.market_predictor_model is not None
        assert config.critic_model is not None
        assert config.persona_generator_model is not None
        assert config.image_generator_model is not None
    
    def test_workflow_configs(self, monkeypatch):
        """Test accessing workflow configurations."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test workflow parameters
        assert isinstance(config.max_iterations, int)
        assert config.max_iterations > 0
        assert isinstance(config.pmf_threshold, (int, float))
        assert 0 <= config.pmf_threshold <= 100
        assert isinstance(config.personas_count, int)
        assert config.personas_count >= 10
    
    def test_social_media_configs(self, monkeypatch):
        """Test accessing social media configurations."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test social media settings
        assert config.x_max_chars > 0
        assert config.linkedin_max_chars > 0
        # x_image_size can be either list or tuple from YAML
        assert isinstance(config.x_image_size, (list, tuple))
        assert len(config.x_image_size) == 2
    
    def test_feature_flags(self, monkeypatch):
        """Test feature flag checking."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test feature flags
        assert isinstance(config.is_feature_enabled("enable_image_generation"), bool)
        assert isinstance(config.is_feature_enabled("enable_infographics"), bool)
        assert isinstance(config.is_feature_enabled("enable_social_posts"), bool)
    
    def test_prompt_access(self, monkeypatch):
        """Test accessing prompt templates."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test prompt retrieval
        ideator_system = config.get_prompt("ideator", "system_prompt")
        assert ideator_system is not None
        assert isinstance(ideator_system, str)
        assert len(ideator_system) > 0
        
        # Test nested prompt access
        generate_prompt = config.get_prompt("ideator", "generate_prompt")
        assert generate_prompt is not None
        assert "{seed_idea}" in generate_prompt


class TestConfigSettingAccess:
    """Tests for generic setting access."""
    
    def test_get_setting_nested(self, monkeypatch):
        """Test getting nested settings."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test nested access
        rate_limit = config.get_setting("api", "rate_limit_calls")
        assert isinstance(rate_limit, int)
        assert rate_limit > 0
    
    def test_get_setting_with_default(self, monkeypatch):
        """Test getting setting with default value."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test with non-existent setting
        value = config.get_setting("nonexistent", "setting", default=42)
        assert value == 42
    
    def test_get_setting_deeply_nested(self, monkeypatch):
        """Test deeply nested setting access."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key-for-testing")
        config = Config()
        
        # Test deeply nested (e.g., social_media -> x -> max_characters)
        x_max = config.get_setting("social_media", "x", "max_characters")
        if x_max is not None:
            assert isinstance(x_max, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


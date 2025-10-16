"""Configuration loader for settings and prompts."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Central configuration manager."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        if config_dir is None:
            # Default to config/ directory in project root
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.settings_path = self.config_dir / "settings.yaml"
        self.prompts_path = self.config_dir / "prompts.yaml"
        
        # Load environment variables
        load_dotenv()
        
        # Load configurations
        self.settings = self._load_yaml(self.settings_path)
        self.prompts = self._load_yaml(self.prompts_path)
        
        # Validate required settings
        self._validate()
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")
    
    def _validate(self):
        """Validate required configuration fields."""
        # Check for OpenRouter API key
        if not os.getenv("OPENROUTER_API_KEY"):
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        # Validate required settings sections
        required_sections = ["models", "workflow", "social_media"]
        for section in required_sections:
            if section not in self.settings:
                raise ValueError(f"Missing required configuration section: {section}")
    
    # Model configurations
    @property
    def ideator_model(self) -> str:
        """Get ideator model name."""
        return self.settings["models"]["ideator"]
    
    @property
    def ideator_temperature(self) -> float:
        """Get ideator temperature."""
        return self.settings["models"]["ideator_temperature"]
    
    @property
    def market_predictor_model(self) -> str:
        """Get market predictor model name."""
        return self.settings["models"]["market_predictor"]
    
    @property
    def critic_model(self) -> str:
        """Get critic model name."""
        return self.settings["models"]["critic"]
    
    @property
    def persona_generator_model(self) -> str:
        """Get persona generator model name."""
        return self.settings["models"]["persona_generator"]
    
    @property
    def image_generator_model(self) -> str:
        """Get image generator model name."""
        return self.settings["models"]["image_generator"]
    
    @property
    def fallback_model(self) -> str:
        """Get fallback model name."""
        return self.settings["models"]["fallback_model"]
    
    # Workflow configurations
    @property
    def max_iterations(self) -> int:
        """Get maximum workflow iterations."""
        return self.settings["workflow"]["max_iterations"]
    
    @property
    def pmf_threshold(self) -> float:
        """Get PMF score threshold."""
        return self.settings["workflow"]["pmf_threshold"]
    
    @property
    def personas_count(self) -> int:
        """Get number of personas to generate."""
        return self.settings["workflow"]["personas_count"]
    
    # Social media configurations
    @property
    def x_max_chars(self) -> int:
        """Get X.com character limit."""
        return self.settings["social_media"]["x"]["max_characters"]
    
    @property
    def linkedin_max_chars(self) -> int:
        """Get LinkedIn character limit."""
        return self.settings["social_media"]["linkedin"]["max_characters"]
    
    @property
    def x_image_size(self) -> tuple:
        """Get X.com image dimensions."""
        return tuple(self.settings["social_media"]["x"]["image_size"])
    
    @property
    def linkedin_image_size(self) -> tuple:
        """Get LinkedIn image dimensions."""
        return tuple(self.settings["social_media"]["linkedin"]["image_size"])
    
    # Ethics configurations
    @property
    def ai_disclosure_enabled(self) -> bool:
        """Check if AI disclosure is enabled."""
        return self.settings["ethics"]["ai_disclosure"]
    
    @property
    def x_disclosure_template(self) -> str:
        """Get X.com AI disclosure template."""
        return self.settings["ethics"]["x_disclosure"]
    
    @property
    def linkedin_disclosure_template(self) -> str:
        """Get LinkedIn AI disclosure template."""
        return self.settings["ethics"]["linkedin_disclosure"]
    
    @property
    def methodology_link(self) -> str:
        """Get methodology documentation link."""
        return self.settings["ethics"]["methodology_link"]
    
    # Prompt templates
    def get_prompt(self, agent: str, prompt_type: str) -> str:
        """
        Get prompt template.
        
        Args:
            agent: Agent name (ideator, market_predictor, critic, etc.)
            prompt_type: Prompt type (system_prompt, generate_prompt, etc.)
        
        Returns:
            Prompt template string
        """
        try:
            return self.prompts[agent][prompt_type]
        except KeyError:
            raise ValueError(f"Prompt not found: {agent}.{prompt_type}")
    
    # Feature flags
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.settings.get("features", {}).get(feature, False)
    
    # API configurations
    @property
    def api_rate_limit(self) -> int:
        """Get API rate limit calls per period."""
        return self.settings["api"]["rate_limit_calls"]
    
    @property
    def api_rate_period(self) -> int:
        """Get API rate limit period in seconds."""
        return self.settings["api"]["rate_limit_period"]
    
    @property
    def api_retry_attempts(self) -> int:
        """Get number of retry attempts."""
        return self.settings["api"]["retry_attempts"]
    
    @property
    def api_timeout(self) -> int:
        """Get API timeout in seconds."""
        return self.settings["api"]["timeout"]
    
    # Output configurations
    @property
    def output_base_dir(self) -> str:
        """Get base output directory."""
        return self.settings["system"]["output_base_dir"]
    
    # Logging configurations
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.settings["logging"]["level"]
    
    @property
    def track_costs(self) -> bool:
        """Check if cost tracking is enabled."""
        return self.settings["logging"]["track_costs"]
    
    def get_setting(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested setting by keys.
        
        Args:
            *keys: Nested keys path
            default: Default value if not found
        
        Returns:
            Setting value or default
        """
        value = self.settings
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config():
    """Reload configuration from files."""
    global _config
    _config = Config()
    return _config


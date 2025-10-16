"""Custom exceptions for the Product Ideation System."""


class ProductIdeationError(Exception):
    """Base exception for all product ideation system errors."""
    pass


class ConfigurationError(ProductIdeationError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(ProductIdeationError):
    """Base exception for API-related errors."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "OpenRouter rate limit exceeded. "
                "Try reducing 'personas_count' in config/settings.yaml or "
                "adjusting 'api.rate_limit_calls' settings."
            )
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "OpenRouter API authentication failed. "
                "Please check that OPENROUTER_API_KEY is set correctly in .env file. "
                "Get a key at: https://openrouter.ai/keys"
            )
        super().__init__(message)


class ModelNotFoundError(APIError):
    """Raised when specified model is not available."""
    
    def __init__(self, model: str):
        message = (
            f"Model '{model}' not found or not available. "
            f"Check available models at https://openrouter.ai/models or "
            f"update your model selection in config/settings.yaml"
        )
        super().__init__(message)


class IdeationError(ProductIdeationError):
    """Raised when concept generation fails."""
    pass


class PersonaGenerationError(ProductIdeationError):
    """Raised when persona generation fails."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Failed to generate personas. This may be due to:\n"
                "  1. API timeout or rate limiting\n"
                "  2. JSON parsing errors from the model\n"
                "  3. Model not supporting structured output\n"
                "Try reducing 'personas_count' or switching to a different model."
            )
        super().__init__(message)


class MarketSimulationError(ProductIdeationError):
    """Raised when market simulation fails."""
    pass


class ValidationError(ProductIdeationError):
    """Raised when input validation fails."""
    pass


class InsufficientDataError(ProductIdeationError):
    """Raised when insufficient data for analysis."""
    
    def __init__(self, required: int, actual: int):
        message = (
            f"Insufficient data for reliable analysis. "
            f"Required at least {required} responses, got {actual}. "
            f"Increase 'personas_count' in config/settings.yaml for better results."
        )
        super().__init__(message)


class WorkflowError(ProductIdeationError):
    """Raised when workflow execution fails."""
    pass


class ImageGenerationError(ProductIdeationError):
    """Raised when image generation fails."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Image generation failed. This may be due to:\n"
                "  1. Model not supporting image generation\n"
                "  2. Content policy violation\n"
                "  3. API timeout\n"
                "You can disable image generation in config/settings.yaml: "
                "features.enable_image_generation = false"
            )
        super().__init__(message)


class OutputGenerationError(ProductIdeationError):
    """Raised when output packaging fails."""
    pass


class FileOperationError(ProductIdeationError):
    """Raised when file operations fail."""
    
    def __init__(self, operation: str, path: str, reason: str = None):
        message = f"Failed to {operation} file: {path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)

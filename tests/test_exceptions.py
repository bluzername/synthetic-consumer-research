"""Tests for custom exceptions."""

import pytest
from src.utils.exceptions import (
    ProductIdeationError,
    ConfigurationError,
    APIError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    IdeationError,
    PersonaGenerationError,
    MarketSimulationError,
    ValidationError,
    InsufficientDataError,
    WorkflowError,
    ImageGenerationError,
    OutputGenerationError,
    FileOperationError,
)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""
    
    def test_base_exception(self):
        """Test that all exceptions inherit from ProductIdeationError."""
        exceptions = [
            ConfigurationError,
            APIError,
            RateLimitError,
            AuthenticationError,
            ModelNotFoundError,
            IdeationError,
            PersonaGenerationError,
            MarketSimulationError,
            ValidationError,
            InsufficientDataError,
            WorkflowError,
            ImageGenerationError,
            OutputGenerationError,
            FileOperationError,
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, ProductIdeationError)
    
    def test_api_error_hierarchy(self):
        """Test that API-related exceptions inherit from APIError."""
        api_exceptions = [
            RateLimitError,
            AuthenticationError,
            ModelNotFoundError,
        ]
        
        for exc_class in api_exceptions:
            assert issubclass(exc_class, APIError)
            assert issubclass(exc_class, ProductIdeationError)


class TestExceptionMessages:
    """Tests for exception default messages."""
    
    def test_rate_limit_error_default_message(self):
        """Test RateLimitError default message."""
        exc = RateLimitError()
        message = str(exc)
        
        assert "rate limit" in message.lower()
        assert "personas_count" in message
        assert "config/settings.yaml" in message
    
    def test_authentication_error_default_message(self):
        """Test AuthenticationError default message."""
        exc = AuthenticationError()
        message = str(exc)
        
        assert "authentication" in message.lower()
        assert "OPENROUTER_API_KEY" in message
        assert "https://openrouter.ai/keys" in message
    
    def test_model_not_found_error_message(self):
        """Test ModelNotFoundError message with model name."""
        exc = ModelNotFoundError("anthropic/claude-3.5-sonnet")
        message = str(exc)
        
        assert "claude-3.5-sonnet" in message
        assert "not found" in message.lower()
        assert "config/settings.yaml" in message
    
    def test_persona_generation_error_default_message(self):
        """Test PersonaGenerationError default message."""
        exc = PersonaGenerationError()
        message = str(exc)
        
        assert "persona" in message.lower()
        assert "JSON" in message
        assert "model" in message.lower()
    
    def test_insufficient_data_error_message(self):
        """Test InsufficientDataError message."""
        exc = InsufficientDataError(required=50, actual=10)
        message = str(exc)
        
        assert "50" in message
        assert "10" in message
        assert "insufficient" in message.lower()
    
    def test_image_generation_error_default_message(self):
        """Test ImageGenerationError default message."""
        exc = ImageGenerationError()
        message = str(exc)
        
        assert "image" in message.lower()
        assert "enable_image_generation" in message
        assert "config/settings.yaml" in message
    
    def test_file_operation_error_message(self):
        """Test FileOperationError message."""
        exc = FileOperationError("write", "/path/to/file.txt", "Permission denied")
        message = str(exc)
        
        assert "write" in message
        assert "/path/to/file.txt" in message
        assert "Permission denied" in message


class TestExceptionCustomization:
    """Tests for custom exception messages."""
    
    def test_custom_rate_limit_message(self):
        """Test RateLimitError with custom message."""
        custom_msg = "Custom rate limit message"
        exc = RateLimitError(custom_msg)
        
        assert str(exc) == custom_msg
    
    def test_custom_authentication_message(self):
        """Test AuthenticationError with custom message."""
        custom_msg = "Custom auth message"
        exc = AuthenticationError(custom_msg)
        
        assert str(exc) == custom_msg
    
    def test_custom_persona_generation_message(self):
        """Test PersonaGenerationError with custom message."""
        custom_msg = "Custom persona error"
        exc = PersonaGenerationError(custom_msg)
        
        assert str(exc) == custom_msg
    
    def test_custom_image_generation_message(self):
        """Test ImageGenerationError with custom message."""
        custom_msg = "Custom image error"
        exc = ImageGenerationError(custom_msg)
        
        assert str(exc) == custom_msg


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""
    
    def test_raise_and_catch_specific(self):
        """Test raising and catching specific exception."""
        with pytest.raises(RateLimitError):
            raise RateLimitError()
    
    def test_catch_with_base_class(self):
        """Test catching exception with base class."""
        with pytest.raises(APIError):
            raise RateLimitError()
        
        with pytest.raises(ProductIdeationError):
            raise ConfigurationError("test")
    
    def test_exception_inheritance_chain(self):
        """Test that exception can be caught at any level."""
        try:
            raise RateLimitError()
        except APIError:
            pass  # Should catch
        except Exception:
            pytest.fail("Should have been caught as APIError")
        
        try:
            raise RateLimitError()
        except ProductIdeationError:
            pass  # Should catch
        except Exception:
            pytest.fail("Should have been caught as ProductIdeationError")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


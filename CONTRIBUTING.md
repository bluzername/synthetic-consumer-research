# Contributing to Product Ideation System

Thank you for your interest in contributing to the Product Ideation System! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Adding New Features](#adding-new-features)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community and the project
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/product-ideation-system.git
   cd product-ideation-system
   ```
3. **Set up the development environment** (see below)
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.13+
- UV package manager
- OpenRouter API key (for testing)

### Installation

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run tests to verify setup
uv run pytest tests/ -v
```

## Project Structure

```
product-ideation-system/
├── src/
│   ├── agents/          # AI agents (ideator, critic, etc.)
│   ├── orchestration/   # LangGraph workflow
│   ├── post_composer/   # Social media composers
│   ├── utils/           # Utilities and models
│   └── visualization/   # Image and chart generation
├── config/              # Configuration files
├── docs/                # Documentation
├── tests/               # Test suite
└── outputs/             # Generated outputs (git-ignored)
```

### Key Components

- **Agents** (`src/agents/`): Each agent is responsible for a specific task (ideation, persona generation, market prediction, criticism)
- **Models** (`src/utils/models.py`): Pydantic models for data validation
- **Workflow** (`src/orchestration/workflow.py`): LangGraph state machine
- **Configuration** (`config/`): YAML-based configuration system

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function parameters and return values
- Write **docstrings** for all public functions, classes, and modules (Google style)
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Example

```python
from typing import List, Optional
from pydantic import BaseModel


class ProductConcept(BaseModel):
    """Represents a product concept with market validation."""
    
    name: str
    features: List[str]
    
    def to_summary(self) -> str:
        """Generate a human-readable summary.
        
        Returns:
            str: Formatted summary of the product concept
        """
        return f"{self.name}: {', '.join(self.features)}"
```

### Code Organization

1. **Imports**: Standard library, third-party, then local imports (separated by blank lines)
2. **Constants**: At module level, UPPER_CASE
3. **Classes**: PascalCase
4. **Functions/Methods**: snake_case
5. **Private members**: prefix with `_`

### Configuration

- Never hardcode values - use `config/settings.yaml`
- Access config through `get_config()` utility
- Document all new configuration options

### Error Handling

- Use custom exceptions from `src/utils/exceptions.py`
- Provide helpful error messages with actionable suggestions
- Never swallow exceptions silently
- Log errors appropriately

```python
from ..utils.exceptions import PersonaGenerationError

try:
    personas = generate_personas(count=100)
except Exception as e:
    raise PersonaGenerationError(
        f"Failed to generate personas: {e}. "
        f"Try reducing personas_count in config/settings.yaml"
    ) from e
```

## Making Changes

### Before You Start

1. **Check existing issues** - Someone might already be working on it
2. **Open an issue** - Discuss significant changes before implementing
3. **Read related code** - Understand the context and patterns used

### While Coding

1. **Write tests** - Add tests for new functionality
2. **Update documentation** - Keep docs in sync with code
3. **Follow patterns** - Match existing code style and structure
4. **Keep commits atomic** - One logical change per commit
5. **Write clear commit messages**:
   ```
   feat: Add support for custom persona templates
   
   - Added PersonaTemplate class
   - Updated persona generator to accept templates
   - Added tests for template functionality
   ```

### Commit Message Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_models.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common setup

```python
import pytest
from src.utils.models import ProductConcept


class TestProductConcept:
    """Tests for ProductConcept model."""
    
    def test_create_valid_concept(self):
        """Test creating a valid product concept."""
        concept = ProductConcept(
            name="Test Product",
            tagline="Test tagline",
            target_market="Test market",
            problem_solved="Test problem",
            features=["Feature 1", "Feature 2"],
            differentiators=["Diff 1"],
            pricing_model="$10"
        )
        
        assert concept.name == "Test Product"
        assert len(concept.features) == 2
    
    def test_invalid_concept_missing_fields(self):
        """Test that missing required fields raise error."""
        with pytest.raises(Exception):
            ProductConcept(name="Incomplete")
```

### Test Coverage

- Aim for 80%+ code coverage
- Focus on critical paths and business logic
- Test edge cases and error conditions
- Mock external API calls

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: `uv run pytest tests/ -v`
2. **Update documentation** if needed
3. **Add tests** for new functionality
4. **Update CHANGELOG.md** (if applicable)
5. **Rebase on latest main**: `git pull --rebase origin main`

### PR Guidelines

1. **Create descriptive PR title**:
   - Good: "Add support for Instagram post generation"
   - Bad: "Update code"

2. **Provide clear description**:
   ```markdown
   ## Changes
   - Added Instagram composer class
   - Updated asset bundler to support Instagram
   - Added Instagram-specific image dimensions
   
   ## Testing
   - Added tests in test_instagram_composer.py
   - Manual testing with sample concepts
   
   ## Documentation
   - Updated README with Instagram support
   - Added Instagram section to SETUP.md
   ```

3. **Link related issues**: "Closes #123"

4. **Request review** from maintainers

5. **Respond to feedback** promptly and professionally

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No unnecessary dependencies added
- [ ] Configuration changes documented
- [ ] Commit messages are clear and descriptive

## Adding New Features

### Adding a New Agent

1. Create agent file in `src/agents/`:
   ```python
   """New agent description."""
   
   from ..utils import get_config, get_openrouter_client, get_logger
   
   
   class NewAgent:
       """Brief description of what this agent does."""
       
       def __init__(self):
           """Initialize agent."""
           self.config = get_config()
           self.client = get_openrouter_client()
           self.logger = get_logger()
       
       def process(self, input_data):
           """Main processing method."""
           pass
   ```

2. Add configuration to `config/settings.yaml`
3. Add prompts to `config/prompts.yaml`
4. Update `src/agents/__init__.py` to export the agent
5. Add tests in `tests/test_agents.py`
6. Update documentation

### Adding a New Social Media Platform

1. Create composer in `src/post_composer/`:
   ```python
   """Platform composer for new platform."""
   
   from ..utils import SocialMediaPost, ProductConcept, MarketFitScore
   
   
   class NewPlatformComposer:
       """Compose posts for new platform."""
       
       def compose_post(
           self,
           concept: ProductConcept,
           market_fit: MarketFitScore
       ) -> SocialMediaPost:
           """Compose platform-specific post."""
           pass
   ```

2. Add platform specs to `config/settings.yaml`
3. Update `AssetBundler` to support new platform
4. Add tests
5. Update documentation

### Adding New Metrics

1. Update `MarketFitScore` or `MarketSegmentation` in `src/utils/models.py`
2. Update calculation logic in `src/agents/market_predictor.py`
3. Update visualizations in `src/visualization/infographic.py`
4. Add tests for new calculations
5. Update documentation

## Questions?

- **Check existing documentation** in `docs/`
- **Look at existing code** for patterns
- **Open an issue** for clarification
- **Join discussions** on existing issues/PRs

## Thank You!

Your contributions help make this project better for everyone. We appreciate your time and effort!

---

**Remember**: Good code is code that others can understand and maintain. When in doubt, prioritize clarity over cleverness.


# Setup Guide

Complete installation and configuration guide for the Product Ideation System.

## Prerequisites

- **macOS** (10.13+) or Linux
- **Python** 3.13+
- **OpenRouter API Key** ([Get one here](https://openrouter.ai/keys))

## Installation

### 1. Install UV Package Manager

UV is a fast Python package manager (10-100x faster than pip):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone/Download Project

The project is already initialized in your workspace.

### 3. Install Dependencies

Dependencies are already installed via UV. To reinstall or update:

```bash
cd /Users/xx/Documents/EB/Projects/red_to_x
uv sync
```

### 4. Configure API Keys

Create your `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_key_here
```

To get an OpenRouter API key:
1. Visit https://openrouter.ai/
2. Sign up for an account
3. Go to https://openrouter.ai/keys
4. Create a new API key
5. Copy and paste into `.env`

### 5. Verify Installation

Test the configuration:

```bash
uv run python -m src.main config
```

You should see your model configuration displayed.

## Configuration

### Basic Configuration

Edit `config/settings.yaml` to customize:

```yaml
models:
  ideator: "anthropic/claude-3.5-sonnet"
  market_predictor: "google/gemini-2.5-pro"
  image_generator: "google/gemini-2.5-flash-image"

workflow:
  max_iterations: 5
  pmf_threshold: 40.0
  personas_count: 100
```

### Model Selection

OpenRouter provides access to many models. Choose based on your needs:

**For Ideation (Creative):**
- `anthropic/claude-3.5-sonnet` - Excellent creative generation
- `openai/gpt-4o` - Strong structured output
- `google/gemini-2.5-pro` - High context window

**For Market Prediction (Analytical):**
- `google/gemini-2.5-pro` - Best for large persona batches
- `anthropic/claude-3.5-sonnet` - Consistent responses
- `openai/gpt-4o` - Structured JSON output

**For Images:**
- `google/gemini-2.5-flash-image` - Fast, good quality
- `openai/dall-e-3` - Highest quality (if supported)

### Workflow Parameters

**Max Iterations** (`max_iterations`):
- How many refinement cycles before stopping
- Recommended: 3-5
- Higher = more refined but costlier

**PMF Threshold** (`pmf_threshold`):
- Target Product-Market Fit score (%)
- Standard: 40% (Sean Ellis benchmark)
- Lower = faster completion, higher = better validation

**Personas Count** (`personas_count`):
- Number of synthetic consumers to simulate
- Recommended: 100
- More = better validation but slower/costlier

### Feature Flags

Enable/disable features in `config/settings.yaml`:

```yaml
features:
  enable_image_generation: true   # Generate product renders
  enable_infographics: true       # Create PMF dashboards
  enable_social_posts: true       # Format social media posts
  enable_cost_tracking: true      # Track API costs
```

## First Run

Generate your first concept:

```bash
uv run python -m src.main generate "portable espresso maker for remote workers"
```

This will:
1. Generate a product concept
2. Create 100 synthetic personas
3. Simulate market responses
4. Calculate PMF score
5. Refine until threshold met or max iterations reached
6. Generate images and infographics
7. Create social media posts
8. Package everything in `outputs/` folder

Expected runtime: 2-5 minutes depending on API speed and iterations.

## Troubleshooting

### "OPENROUTER_API_KEY not found"

**Solution**: Make sure `.env` file exists and contains your API key.

```bash
cat .env
```

Should show:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

### "Rate limit exceeded"

**Solution**: Reduce personas count or add delays in `config/settings.yaml`:

```yaml
api:
  rate_limit_calls: 30  # Reduce from 50
  rate_limit_period: 60
```

### "Image generation failed"

**Solution**: 
1. Check if model supports image generation
2. Disable image generation temporarily:

```yaml
features:
  enable_image_generation: false
```

### "Module not found" errors

**Solution**: Reinstall dependencies:

```bash
uv sync --reinstall
```

### Slow execution

**Solutions**:
- Reduce personas count to 50
- Use faster models (e.g., `google/gemini-2.5-flash`)
- Disable image generation
- Reduce max iterations to 3

## Advanced Configuration

### Custom Prompts

Edit `config/prompts.yaml` to customize AI behavior:

```yaml
ideator:
  system_prompt: |
    Your custom instructions here...
  
  generate_prompt: |
    Your custom generation prompt...
```

### API Rate Limiting

Adjust rate limits to match your OpenRouter tier:

```yaml
api:
  rate_limit_calls: 50      # Calls per period
  rate_limit_period: 60     # Period in seconds
  retry_attempts: 3         # Number of retries
  timeout: 30              # Request timeout
```

### Output Directory

Change where outputs are saved:

```yaml
system:
  output_base_dir: "my_outputs"
```

### Social Media Specifications

Customize platform requirements:

```yaml
social_media:
  x:
    max_characters: 280
    image_size: [1200, 675]
    hashtags_max: 2
  
  linkedin:
    max_characters: 3000
    image_size: [1200, 627]
    hashtags_recommended: 5
```

## Cost Optimization

### Use Cheaper Models

```yaml
models:
  ideator: "google/gemini-2.5-flash"  # Instead of Claude
  market_predictor: "google/gemini-2.5-flash"
```

### Reduce Personas

```yaml
workflow:
  personas_count: 50  # Instead of 100
```

### Lower Iterations

```yaml
workflow:
  max_iterations: 3  # Instead of 5
```

### Disable Features

```yaml
features:
  enable_image_generation: false
  enable_infographics: false
```

## Environment Variables

All available environment variables:

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Optional (for debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=product-ideation

# Debug mode
DEBUG=false
```

## Verification

After setup, verify everything works:

```bash
# 1. Check config
uv run python -m src.main config

# 2. Check version
uv run python -m src.main version

# 3. Run a quick test
uv run python -m src.main generate "test product" --iterations 1 --personas 10
```

If all commands work, you're ready to go!

## Next Steps

1. Read [METHODOLOGY.md](METHODOLOGY.md) to understand the AI process
2. Read [ETHICS.md](ETHICS.md) for responsible AI guidelines
3. Generate your first real concept
4. Review output package in `outputs/` folder
5. Share on social media with AI disclosure

## Getting Help

- Check configuration: `./run.sh config`
- Review logs in output folders
- Check API costs: `./run.sh costs`
- Validate `.env` file exists and has correct API key

## Updates

To update the system:

```bash
# Update dependencies
uv sync --upgrade

# Update UV itself
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

You're all set! Start generating innovative product concepts with AI-powered market validation.


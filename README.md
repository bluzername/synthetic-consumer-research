# Synthetic Consumer Research
> Transform weeks of product research into hours of AI-assisted innovation

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/yourusername/product-ideation-system/workflows/CI/badge.svg)](https://github.com/yourusername/product-ideation-system/actions)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208-blue)](https://www.python.org/dev/peps/pep-0008/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-green.svg)](docs/README.md)
[![OpenRouter](https://img.shields.io/badge/API-OpenRouter-orange.svg)](https://openrouter.ai/)

## What Is This?

An end-to-end AI-powered system that:
- 🚀 Generates innovative product concepts from seed ideas
- 📊 Validates them with 100+ synthetic consumer personas
- 📈 Calculates Product-Market Fit using Sean Ellis methodology
- 🔄 Iteratively refines concepts based on market feedback
- 🎨 Creates professional product renders and infographics
- 📱 Exports ready-to-post content for X.com and LinkedIn
- 🤖 Maintains full AI methodology transparency

## Quick Start

```bash
# 1. Set up your API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 2. Generate your first concept (easier with convenience script)
./run.sh generate "AI-powered desk organizer for remote workers"

# Alternative: Full command
# uv run python -m src.main generate "AI-powered desk organizer for remote workers"

# 3. Check your outputs
ls outputs/
```

That's it! Your complete package with images, posts, and analytics is ready.

## Example Output

For a concept like **"Smart Coffee Maker for Remote Workers"**:

```
outputs/smart_coffee_maker_20250115_143052/
├── README.md                    ← Complete concept overview
├── POSTING_GUIDE.md             ← Step-by-step social media guide
├── concept.json                 ← Structured data
├── images/
│   ├── x_product_render.png    ← 1200x675 for X.com
│   ├── linkedin_product_render.png  ← 1200x627 for LinkedIn
│   └── pmf_dashboard.png        ← Market metrics visualization
├── posts/
│   ├── x_post.md                ← Ready-to-copy X post
│   └── linkedin_post.md         ← Ready-to-copy LinkedIn post
└── analytics/
    ├── market_fit.json          ← PMF: 48%, NPS: 52
    └── iteration_history.json   ← 3 iterations to reach threshold
```

## Features

### 🤖 AI-Powered Ideation
- **Models**: Claude 3.5 Sonnet, GPT-4o, Gemini 2.5 Pro (via OpenRouter)
- **Framework**: LangGraph for iterative refinement loops
- **Output**: Structured product concepts with features, differentiators, pricing

### 📊 Market Validation
- **Method**: Sean Ellis Product-Market Fit methodology
- **Data**: 100+ diverse synthetic consumer personas
- **Metrics**: PMF Score, NPS, Average Interest, Benefits/Concerns
- **Target**: 40%+ PMF score (industry benchmark)

### 🎨 Professional Visuals
- **Product Renders**: Gemini 2.5 Flash Image (AI-generated)
- **Infographics**: Matplotlib + Seaborn dashboards
- **Formats**: Optimized for X.com (1200x675), LinkedIn (1200x627)

### 📱 Social Media Export
- **Platforms**: X.com and LinkedIn
- **Features**: Platform-specific formatting, AI disclosure, methodology links
- **Format**: Drag-and-drop ready markdown files

### 🔍 Full Transparency
- Complete methodology documentation
- AI disclosure on all outputs
- Open-source prompts and configuration
- Cost tracking and analytics

## Installation

### Prerequisites
- macOS or Linux
- Python 3.13+
- OpenRouter API key ([get one free](https://openrouter.ai/keys))

### Setup

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (already done via UV)
uv sync

# Configure API key
cp .env.example .env
# Edit .env: add OPENROUTER_API_KEY=your_key_here

# Verify installation
uv run python -m src.main config
```

Full setup guide: [docs/SETUP.md](docs/SETUP.md)

## Usage

### Convenience Script (Recommended)

We provide a convenience script that makes commands shorter:

```bash
# Generate concept
./run.sh generate "your product idea"

# View configuration
./run.sh config

# Check costs
./run.sh costs
```

### Full Commands

If you prefer the full commands:

```bash
# Basic usage
uv run python -m src.main generate "your product idea"

# With custom parameters
uv run python -m src.main generate "smart water bottle" \
  --iterations 3 \
  --threshold 35 \
  --personas 50

# View configuration
uv run python -m src.main config

# Check costs
uv run python -m src.main costs
```

## How It Works

```
1. IDEATE
   ↓
   Claude 3.5 Sonnet generates product concept
   
2. GENERATE PERSONAS
   ↓
   Gemini creates 100+ diverse synthetic consumers
   
3. SIMULATE MARKET
   ↓
   Each persona evaluates the concept
   
4. CALCULATE PMF
   ↓
   Sean Ellis methodology: % "very disappointed"
   
5. ANALYZE & DECIDE
   ↓
   PMF ≥ 40% OR iterations ≥ 5?
   
   NO → REFINE
   ↓     ↓
   Critic identifies improvements
   ↓
   Loop back to step 1
   
   YES → FINALIZE
   ↓
6. GENERATE VISUALS
   ↓
   Product renders + infographics
   
7. CREATE POSTS
   ↓
   Format for X.com + LinkedIn
   
8. PACKAGE OUTPUT
   ↓
   Complete folder with all materials
```

## Configuration

Highly configurable via `config/settings.yaml`:

```yaml
models:
  ideator: "anthropic/claude-3.5-sonnet"
  market_predictor: "google/gemini-2.5-pro"
  image_generator: "google/gemini-2.5-flash-image"

workflow:
  max_iterations: 5
  pmf_threshold: 40.0
  personas_count: 100

features:
  enable_image_generation: true
  enable_infographics: true
  enable_social_posts: true
```

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Complete installation and configuration
- **[Methodology](docs/METHODOLOGY.md)** - Full transparency on AI processes
- **[Ethics](docs/ETHICS.md)** - Responsible AI use and disclosure
- **[Main Docs](docs/README.md)** - Comprehensive system documentation

## Cost Estimates

With OpenRouter API:
- **Indie** (10 concepts/month): ~$25-50/month
- **Professional** (50 concepts/month): ~$100-200/month
- **Agency** (200 concepts/month): ~$300-500/month

## Technology Stack

- **Python**: 3.13
- **Package Manager**: UV (10-100x faster than pip)
- **LLM Provider**: OpenRouter (unified API)
- **Orchestration**: LangGraph
- **Visualization**: Matplotlib, Seaborn
- **CLI**: Typer, Rich

## Success Metrics

- ✅ PMF Score: Target 40%+
- ✅ NPS: Net Promoter Score
- ✅ Interest: Average 1-5 rating
- ✅ Iterations: Cycles to reach threshold

## Limitations

This system:
- ✅ Accelerates early-stage ideation
- ✅ Provides data-driven validation
- ✅ Generates professional materials

This system does NOT:
- ❌ Replace real user research
- ❌ Guarantee market success
- ❌ Capture all human behavior
- ❌ Validate pricing or timing

**Always validate with real users before major investments.**

## Ethics & Transparency

All outputs include:
- 🤖 AI disclosure
- 📚 Methodology documentation
- ⚠️ Limitation notices
- 🔗 Process transparency

We believe in responsible AI that augments human creativity while maintaining trust.

## Example Concepts

Test the system with these seed ideas:

```bash
# Consumer products
uv run python -m src.main generate "portable espresso maker for remote workers"

# Tech products
uv run python -m src.main generate "AI fitness tracker for seniors"

# Sustainability
uv run python -m src.main generate "sustainable meal prep containers"
```

## Troubleshooting

**"API key not found"**:
```bash
# Check .env file exists
cat .env
# Should show: OPENROUTER_API_KEY=sk-or-v1-...
```

**"Rate limit exceeded"**:
```yaml
# Reduce in config/settings.yaml
workflow:
  personas_count: 50  # Instead of 100
```

**Slow execution**:
- Use faster models (Gemini Flash)
- Reduce personas to 50
- Disable image generation temporarily

Full troubleshooting: [docs/SETUP.md#troubleshooting](docs/SETUP.md#troubleshooting)

## Contributing

This is a production system. For modifications:
1. Test with sample seeds
2. Validate PMF calculations
3. Update documentation
4. Maintain AI disclosure

## License

MIT License - See LICENSE file

## Support

- 📖 Check documentation in `docs/`
- ⚙️ Review configuration in `config/`
- 📊 Examine output analytics
- 💰 Track costs with `costs` command

## Acknowledgments

Built on:
- Sean Ellis PMF Methodology
- LangChain/LangGraph framework
- OpenRouter API platform
- Big Five personality model
- Open-source Python ecosystem

---

**Transform your product ideas into validated concepts with AI-powered market research.**

🚀 **Start now**: `./run.sh generate "your idea here"`

Built with transparency • Powered by AI • Designed for innovation


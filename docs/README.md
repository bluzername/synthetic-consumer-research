# Product Ideation System

AI-powered product concept generation and market validation workflow with automated social media export.

## Overview

Transform product ideation from weeks of manual research into hours of AI-assisted innovation. This system generates product concepts, simulates market reactions with synthetic personas, creates professional visuals, and outputs drag-and-drop social media content—all while maintaining full methodology transparency.

## Features

- 🤖 **AI-Powered Ideation**: Generate innovative product concepts using state-of-the-art LLMs
- 📊 **Market Simulation**: Validate concepts with 100+ diverse synthetic consumer personas
- 📈 **PMF Scoring**: Calculate Product-Market Fit using Sean Ellis methodology
- 🔄 **Iterative Refinement**: Automatically improve concepts based on market feedback
- 🎨 **Visual Generation**: Create professional product renders and infographics
- 📱 **Social Media Export**: Ready-to-post content for X.com and LinkedIn
- 🔍 **Full Transparency**: Complete AI methodology disclosure and documentation
- 💰 **Cost Tracking**: Monitor API usage and estimated costs

## Quick Start

```bash
# Set up environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Install dependencies (already done with UV)
uv sync

# Generate your first concept
uv run python -m src.main generate "AI-powered desk organizer for remote workers"
```

## System Architecture

```
User Input (Seed Idea)
    ↓
[Ideator Agent] → Generate concept
    ↓
[Persona Generator] → Create 100+ synthetic consumers
    ↓
[Market Predictor] → Simulate market response
    ↓
[PMF Calculator] → Calculate Sean Ellis score
    ↓
Decision: PMF ≥ 40% OR iterations ≥ 5?
    ↓ NO
[Critic Agent] → Analyze feedback + identify improvements
    ↓ (Refine and loop back)
    ↓ YES
[Image Generator] → Product renders (Gemini Flash Image)
    ↓
[Infographic Generator] → PMF dashboards and charts
    ↓
[Post Composer] → Format for X.com + LinkedIn
    ↓
[Asset Bundler] → Package complete output
    ↓
Output Folder: Ready-to-post materials
```

## Technology Stack

- **Python**: 3.13
- **Package Manager**: UV (10-100x faster than pip)
- **LLM Provider**: OpenRouter (unified API for multiple models)
- **Orchestration**: LangGraph (iterative feedback loops)
- **Models**:
  - Ideator: Claude 3.5 Sonnet (creative generation)
  - Market Predictor: Gemini 2.5 Pro (high-context analysis)
  - Image Generator: Gemini 2.5 Flash Image
- **Visualization**: Matplotlib + Seaborn
- **CLI**: Typer + Rich

## Commands

### Generate Product Concept

```bash
# Basic usage
uv run python -m src.main generate "your product idea"

# With custom parameters
uv run python -m src.main generate "smart water bottle" \
  --iterations 3 \
  --threshold 35 \
  --personas 50
```

### View Configuration

```bash
# Show all configuration
uv run python -m src.main config

# Show only models
uv run python -m src.main config --models
```

### Check API Costs

```bash
uv run python -m src.main costs
```

## Output Structure

Each concept generation creates a timestamped output folder:

```
outputs/product_name_20250115_143052/
├── README.md                    # Full concept overview
├── POSTING_GUIDE.md             # Social media instructions
├── concept.json                 # Structured data
│
├── images/
│   ├── x_product_render.png    # 1200x675 for X.com
│   ├── linkedin_product_render.png  # 1200x627 for LinkedIn
│   ├── pmf_dashboard.png        # Market metrics visualization
│   └── iteration_history.png    # PMF improvement chart
│
├── posts/
│   ├── x_post.md                # Ready-to-copy X post
│   └── linkedin_post.md         # Ready-to-copy LinkedIn post
│
└── analytics/
    ├── market_fit.json          # PMF scores, NPS, etc.
    ├── iteration_history.json   # Refinement tracking
    └── cost_summary.json        # API usage costs
```

## Configuration

All settings are managed in `config/settings.yaml`:

- **Models**: Choose which LLMs to use for each agent
- **Workflow**: Set max iterations, PMF threshold, personas count
- **Social Media**: Platform specifications and formats
- **Ethics**: AI disclosure templates and methodology links
- **Features**: Enable/disable image generation, infographics, etc.

## Success Metrics

- **PMF Score**: Target 40%+ (percentage who would be "very disappointed" if product disappeared)
- **NPS**: Net Promoter Score (promoters - detractors)
- **Average Interest**: Mean interest level (1-5 scale)
- **Iteration Efficiency**: Number of cycles to reach threshold

## Cost Estimates

With OpenRouter API:
- **Indie Creator** (10 concepts/month): ~$25-50/month
- **Professional** (50 concepts/month): ~$100-200/month
- **Agency** (200 concepts/month): ~$300-500/month

*Costs vary based on models used and optimization strategies*

## Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration
- [Methodology](METHODOLOGY.md) - Full transparency on AI processes
- [Ethics Guidelines](ETHICS.md) - Responsible AI use and disclosure

## Methodology Transparency

This system uses:
- **Synthetic Personas**: AI-generated consumer profiles based on demographic and psychographic frameworks
- **Sean Ellis PMF**: Industry-standard product-market fit methodology
- **Iterative Refinement**: Self-refine loop with critic feedback
- **Full Disclosure**: All outputs include AI methodology documentation

## Limitations

- Synthetic personas may not capture all human unpredictability
- Best for early-stage validation, not replacement for real user research
- LLM outputs may reflect training data biases
- Always validate critical decisions with real users before major investments

## Contributing

This is a production system. For modifications:
1. Test changes with sample seeds
2. Validate PMF calculations
3. Update documentation
4. Maintain AI disclosure standards

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Check documentation in `docs/`
- Review configuration in `config/settings.yaml`
- Examine output logs and analytics

---

**Built with transparency, powered by AI, designed for innovation.**


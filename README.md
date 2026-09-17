# Synthetic Consumer Research

> Product ideation and validation with synthetic consumers: generate a concept, put it in front of a stratified panel of LLM personas, score product-market fit, iterate, and export launch-ready posts and images.

[![CI](https://github.com/bluzername/synthetic-consumer-research/actions/workflows/ci.yml/badge.svg)](https://github.com/bluzername/synthetic-consumer-research/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Research](https://img.shields.io/badge/research-validated-purple.svg)](https://arxiv.org/abs/2510.08338)

## What it does

A LangGraph workflow (`src/orchestration/workflow.py`) runs these agents in a loop until the concept clears the PMF threshold or the iteration cap is reached:

1. **Ideator** (`src/agents/ideator.py`) turns a seed idea into a structured product concept.
2. **Persona generator** (`src/agents/persona_generator.py`) builds a stratified panel of synthetic consumers (age, income, region, attitudes) so the sample is not just "tech-savvy millennials".
3. **Market predictor** (`src/agents/market_predictor.py`) has every persona react to the concept. Responses are scored with Semantic Similarity Rating (SSR, `semantic-similarity-rating` from pymc-labs) rather than by asking the model for a number.
4. **PMF scoring** (`src/utils/models.py`) applies the Sean Ellis test ("how would you feel if you could no longer use it") plus NPS, interest and a superfan ratio.
5. **Critic** (`src/agents/critic.py`) explains what to change; the loop returns to step 1.
6. **Visualisation and export** (`src/visualization`, `src/post_composer`) render product images, a PMF dashboard and X / LinkedIn posts with AI disclosure into `outputs/<concept>_<timestamp>/`.

All LLM calls go through OpenRouter (`src/utils/api_manager.py`); one API key covers every model.

## Install

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/bluzername/synthetic-consumer-research.git
cd synthetic-consumer-research
uv sync
cp .env.example .env      # add OPENROUTER_API_KEY (https://openrouter.ai/keys)
./run.sh config            # verify configuration
```

## Usage

`./run.sh` is a thin wrapper around `uv run python -m src.main`.

```bash
./run.sh generate "AI-powered desk organizer for remote workers"
./run.sh generate "smart water bottle" --iterations 3 --threshold 35 --personas 50
./run.sh config --models   # show which model handles each role
./run.sh costs             # token usage and estimated spend for the session
./run.sh version
```

Each run writes:

```
outputs/<concept>_<timestamp>/
  README.md               concept overview
  POSTING_GUIDE.md        how to post the assets
  concept.json
  images/                 product renders (X and LinkedIn sizes), pmf_dashboard.png
  posts/                  x_post.md, linkedin_post.md
  analytics/              market_fit.json, iteration_history.json
```

## Configuration

`config/settings.yaml` holds the model per role, workflow limits, PMF thresholds, image sizes and social settings; `config/prompts.yaml` holds every prompt. Defaults use `google/gemini-2.5-flash` for ideation, personas, prediction and critique (the Claude and Gemini Pro alternatives are commented in the file because of cost) and `google/gemini-2.5-flash-image` for renders. Edit the YAML or override per run with the CLI flags.

`.env`: `OPENROUTER_API_KEY` (required), optional `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` for LangSmith tracing.

## Development

```bash
uv sync
uv run pytest tests/ -v      # models, PMF maths, config loading, exceptions
```

CI (`.github/workflows/ci.yml`) runs the test suite with a dummy API key, a compile check and a repository structure check. Dependencies are locked in `uv.lock`; the SSR library is pinned to a commit.

## Documentation

- [Methodology](docs/METHODOLOGY.md): Sean Ellis PMF, SSR, persona stratification, academic references
- [Persona diversity strategy](docs/PERSONA_DIVERSITY_STRATEGY.md) and [SSR implementation notes](docs/SSR_IMPLEMENTATION.md)
- [Ethics and disclosure](docs/ETHICS.md)
- [Setup](docs/SETUP.md), [Quickstart](QUICKSTART.md), [Enhanced metrics proposal](docs/ENHANCED_METRICS_PROPOSAL.md)
- [Contributing](CONTRIBUTING.md), [Changelog](CHANGELOG.md)

## Caveats

Synthetic personas are a screening tool, not a substitute for talking to customers. Outputs carry an AI disclosure and a link to the methodology; keep it there.

## License

[MIT](LICENSE)

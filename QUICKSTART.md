# Quick Start Guide

Get your first AI-generated product concept in 5 minutes.

## Prerequisites

✅ You already have:
- Python 3.13 installed
- UV package manager installed
- All dependencies installed
- Project structure created

## Step 1: Get OpenRouter API Key (2 minutes)

1. Go to https://openrouter.ai/
2. Sign up for a free account
3. Visit https://openrouter.ai/keys
4. Click "Create Key"
5. Copy your API key (starts with `sk-or-v1-...`)

## Step 2: Configure Environment (1 minute)

```bash
# Navigate to project
cd /Users/xx/Documents/EB/Projects/red_to_x

# Create .env file from template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Add your API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

Save and exit (Ctrl+X, Y, Enter in nano).

## Step 3: Verify Setup (30 seconds)

```bash
# Option A: Using the convenience script (easier)
./run.sh config

# Option B: Using the full command
uv run python -m src.main config
```

You should see your model configuration displayed. If you get an error about the API key, go back to Step 2.

## Step 4: Generate Your First Concept (2 minutes)

```bash
# Option A: Using the convenience script (easier)
./run.sh generate "AI-powered desk organizer for remote workers"

# Option B: Using the full command
uv run python -m src.main generate "AI-powered desk organizer for remote workers"
```

Watch as the system:
- ✨ Generates a product concept
- 👥 Creates 100 synthetic personas
- 📊 Simulates market responses
- 📈 Calculates PMF score
- 🔄 Refines the concept (if needed)
- 🎨 Generates product images
- 📱 Creates social media posts

**Time**: 2-5 minutes depending on API speed.

## Step 5: Review Your Output

```bash
# List your outputs
ls outputs/

# Open the latest output folder
cd outputs/*_*  # Tab completion will help
```

Your folder contains:
- 📄 `README.md` - Complete concept overview
- 📝 `POSTING_GUIDE.md` - Social media instructions
- 🖼️  `images/` - Product renders and infographics
- 📱 `posts/` - Ready-to-copy X.com and LinkedIn posts
- 📊 `analytics/` - PMF scores and metrics

### View Results

```bash
# Read the concept overview
cat README.md

# View PMF score
cat analytics/market_fit.json | grep pmf_score

# See X.com post
cat posts/x_post.md

# See LinkedIn post
cat posts/linkedin_post.md
```

### Open in Finder (macOS)

```bash
open .
```

## What You'll See

Example output for "AI-powered desk organizer":

```
Product: SmartDesk Hub
PMF Score: 45.2%
NPS: 38
Average Interest: 4.1/5.0

Top Benefits:
1. Space optimization
2. Cable management
3. Wireless charging

Iterations: 2
Status: ✅ PROCEED - Strong product-market fit
```

## Try More Examples

```bash
# Consumer products
./run.sh generate "portable espresso maker for coffee lovers"

# Tech products
./run.sh generate "AI fitness tracker for seniors"

# Sustainability
./run.sh generate "eco-friendly meal prep containers"

# B2B
./run.sh generate "meeting productivity tool for remote teams"
```

## Customize Your Run

### Fewer Personas (Faster, Cheaper)

```bash
./run.sh generate "smart water bottle" --personas 50
```

### Lower PMF Threshold

```bash
./run.sh generate "smart water bottle" --threshold 35
```

### Fewer Iterations

```bash
./run.sh generate "smart water bottle" --iterations 3
```

### All Together

```bash
./run.sh generate "smart water bottle" \
  --personas 50 \
  --threshold 35 \
  --iterations 3
```

## Check Your Costs

```bash
./run.sh costs
```

Example output:
```
Total API Calls: 103
Successful Calls: 103
Failed Calls: 0

Usage by Model:
anthropic/claude-3.5-sonnet: 5 calls, 12,450 tokens
google/gemini-2.5-pro: 100 calls, 234,890 tokens
```

Estimated cost per concept: $1-3 depending on iterations.

## Share Your Concept

### On X.com (Twitter)

1. Open `posts/x_post.md`
2. Copy the text
3. Open `images/x_product_render.png`
4. Create new post on X.com
5. Paste text + attach image
6. Post!

### On LinkedIn

1. Open `posts/linkedin_post.md`
2. Copy the text
3. Open `images/linkedin_product_render.png`
4. Create new post on LinkedIn
5. Paste text + attach image
6. Post!

Both include AI disclosure for transparency.

## Troubleshooting

### "API key not found"

Fix:
```bash
cat .env
# Should show: OPENROUTER_API_KEY=sk-or-v1-...
```

If empty, edit `.env` and add your key.

### "Rate limit exceeded"

Fix: Reduce personas in `config/settings.yaml`:
```yaml
workflow:
  personas_count: 50  # Instead of 100
```

### "Image generation failed"

Images are optional. The system continues without them. To disable:
```yaml
features:
  enable_image_generation: false
```

### Slow execution

Solutions:
- Reduce personas: `--personas 50`
- Use faster model in `config/settings.yaml`
- Reduce iterations: `--iterations 3`

## Next Steps

1. ✅ Generate 3-5 test concepts
2. 📖 Read [METHODOLOGY.md](docs/METHODOLOGY.md) to understand the process
3. ⚙️ Customize `config/settings.yaml` for your needs
4. 🤖 Review [ETHICS.md](docs/ETHICS.md) for responsible AI use
5. 📱 Share concepts on social media with AI disclosure

## Learn More

- **Full Documentation**: [docs/README.md](docs/README.md)
- **Setup Guide**: [docs/SETUP.md](docs/SETUP.md)
- **Configuration**: `config/settings.yaml`
- **Customization**: `config/prompts.yaml`

## Support

Need help?
1. Check `docs/SETUP.md` troubleshooting section
2. Review configuration: `./run.sh config`
3. Verify API key in `.env` file
4. Check costs: `./run.sh costs`

---

**You're all set!** 🚀

Start generating innovative product concepts with AI-powered market validation.

```bash
./run.sh generate "your next big idea"
```


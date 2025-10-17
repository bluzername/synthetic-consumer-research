# SSR Implementation v3 - Changelog

**Date:** October 17, 2025  
**Based on:** [Maier et al. (2025) - arXiv:2510.08338](https://arxiv.org/abs/2510.08338)

## Summary

Upgraded SSR implementation to fully align with the paper's methodology recommendations, including multiple reference sets, larger embedding model, psychometrically sound phrasing, and standard consumer research questions.

## Changes Implemented

### 1. Configuration (`config/settings.yaml`)

**Added SSR configuration section:**
```yaml
ssr:
  embedding_model: "all-mpnet-base-v2"  # Upgraded from all-MiniLM-L6-v2
  temperature: 1.0  # Now configurable
  epsilon: 0.01     # Now configurable
```

### 2. Config Loader (`src/utils/config_loader.py`)

**Added properties:**
- `ssr_embedding_model` - Get embedding model from config
- `ssr_temperature` - Get temperature parameter
- `ssr_epsilon` - Get epsilon regularization parameter

### 3. Models (`src/utils/models.py`)

**Updated `PersonaResponse`:**
- Added `purchase_intent_response: str` field
- Now captures 4 dimensions: interest, purchase intent, disappointment, recommendation

### 4. Prompts (`config/prompts.yaml`)

**Completely rewrote market_predictor prompts:**
- Framed as professional consumer research study
- Survey-style question formatting
- Added Question 2: "Purchase Likelihood" (standard consumer research)
- Natural, conversational tone
- Removed numeric rating instructions
- Professional formatting with clear sections

**Before:** "How interested are you in this product?"  
**After:** "After reading about this product concept, please describe your initial reaction and level of interest. How does this product concept make you feel?"

### 5. Market Predictor (`src/agents/market_predictor.py`)

**Major refactor of `_initialize_ssr_raters()`:**

#### Multiple Reference Sets (3 per dimension)
Each dimension now has 3 different phrasings:

**Interest:**
- Set 1: Appeal-based ("does not appeal to me at all" ... "appeals to me very much")
- Set 2: Relevance ("not at all relevant to my needs" ... "extremely relevant")  
- Set 3: Intensity ("no interest whatsoever" ... "extremely interested")

**Purchase Intent (NEW):**
- Set 1: Direct likelihood ("definitely would not purchase" ... "definitely would purchase")
- Set 2: Probability ("no chance I would buy" ... "almost certainly buy")
- Set 3: Behavioral ("never consider buying" ... "always consider buying")

**Disappointment:**
- Set 1: Direct emotion ("not disappointed at all" ... "extremely disappointed")
- Set 2: Impact ("not affect me" ... "major negative impact")
- Set 3: Loss reaction ("not care if disappeared" ... "could not manage without")

**Recommendation:**
- Set 1: Direct ("definitely not recommend" ... "definitely recommend")
- Set 2: Advocacy ("actively discourage" ... "enthusiastically promote")
- Set 3: Word of mouth ("never tell anyone" ... "tell everyone I know")

#### Configurable Parameters
```python
# Before
interest_pmfs = self.interest_rater.get_response_pmfs(
    "interest", texts, temperature=1.0, epsilon=0.01
)

# After
temperature = self.config.ssr_temperature
epsilon = self.config.ssr_epsilon
interest_pmfs = self.interest_rater.get_response_pmfs(
    "mean", texts, temperature=temperature, epsilon=epsilon
)
```

#### Larger Model
```python
# Before: all-MiniLM-L6-v2 (22M parameters)
# After: all-mpnet-base-v2 (110M parameters)
embedding_model = self.config.ssr_embedding_model
self.interest_rater = ResponseRater(refs, model_name=embedding_model)
```

#### Purchase Intent Processing
Added complete processing pipeline for purchase intent PMFs, including aggregation and logging.

### 6. Asset Bundler (`src/post_composer/asset_bundler.py`)

**Updated persona response saving:**
- Now includes `purchase_intent_response` in saved JSON
- Provides complete picture of consumer responses

### 7. Tests (`tests/`)

**Updated test files:**
- `test_models.py`: Added purchase_intent_response to all PersonaResponse test cases
- `test_pmf_calculation.py`: Added purchase intent mapping in helper functions

All tests passing ✅

### 8. Documentation (`SSR_IMPLEMENTATION.md`)

**Added v3 section documenting:**
- All improvements aligned with paper
- Technical implementation details
- Configuration options
- Expected improvements
- Validation notes

## Key Improvements

### 1. Multiple Reference Sets
✅ **Paper Recommendation:** Use multiple reference sets to reduce single-phrasing bias  
✅ **Implementation:** 3 sets per dimension, averaged via `"mean"` parameter

### 2. Larger Embedding Model  
✅ **Paper Recommendation:** Model choice significantly affects quality  
✅ **Implementation:** Upgraded to all-mpnet-base-v2 (5x larger, better semantic understanding)

### 3. Psychometric Phrasing
✅ **Paper Recommendation:** Use validated consumer research language  
✅ **Implementation:** Professional phrasing across multiple semantic angles

### 4. Configurable Parameters
✅ **Paper Recommendation:** Temperature and epsilon affect distribution quality  
✅ **Implementation:** Both configurable in settings.yaml

### 5. Standard Purchase Intent
✅ **Paper Focus:** Consumer research best practices  
✅ **Implementation:** Added standard purchase likelihood question

### 6. Survey-Style Prompts
✅ **Paper Recommendation:** Elicit natural, authentic responses  
✅ **Implementation:** Professional survey formatting and question framing

## Example Output

### Interest Distribution (Probability)
```json
{
  "1": 0.108,  // 10.8% probability
  "2": 0.140,  // 14.0% probability  
  "3": 0.246,  // 24.6% probability
  "4": 0.193,  // 19.3% probability
  "5": 0.313   // 31.3% probability
}
```

### Natural Language Response
```json
{
  "persona_name": "Sarah Chen",
  "interest_response": "My initial reaction is quite positive...",
  "purchase_intent_response": "I would be very likely to purchase...",
  "disappointment_response": "I would be quite disappointed...",
  "recommendation_response": "Yes, I would absolutely tell others..."
}
```

## Testing

All tests pass:
```bash
pytest tests/test_models.py::TestPersonaResponse  # 3 passed
pytest tests/test_models.py::TestMarketFitScore   # 5 passed
pytest tests/test_pmf_calculation.py              # 8 passed
```

Integration test successful with 5 personas showing proper SSR conversion.

## Migration Guide

### For Users

**No action required** - changes are backward compatible. The SSR improvements are automatic.

**Optional:** Tune SSR parameters in `config/settings.yaml`:
```yaml
ssr:
  embedding_model: "all-mpnet-base-v2"  # Can change to all-MiniLM-L6-v2 for speed
  temperature: 1.0  # Lower = sharper, higher = more uncertain
  epsilon: 0.01     # Higher = more smoothing
```

### For Developers

If extending the code:
1. New persona response fields must include `purchase_intent_response`
2. Reference sets should follow 3-set pattern with psychometric phrasing
3. Use `"mean"` parameter when calling `get_response_pmfs()` for multiple sets
4. Temperature and epsilon should come from config, not hardcoded

## Expected Benefits

Based on the paper's validation (90% test-retest reliability, KS similarity > 0.85):

1. **More reliable distributions** - Multiple reference sets reduce bias
2. **Better semantic understanding** - Larger model captures nuance
3. **Professional alignment** - Survey-style prompts elicit authentic responses
4. **Tunable behavior** - Temperature/epsilon allow optimization
5. **Complete picture** - Purchase intent complements other dimensions

## References

- Paper: [LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings](https://arxiv.org/abs/2510.08338)
- SSR Package: https://github.com/pymc-labs/semantic-similarity-rating
- Implementation: Based on v1.0.0 of semantic-similarity-rating package

## Notes

- No human validation conducted (paper had 9,300 human responses)
- Temperature/epsilon defaults match paper recommendations
- Model choice (all-mpnet-base-v2) provides good balance of quality/speed
- All 4 dimensions now use consistent SSR methodology


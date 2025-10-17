# SSR Implementation Summary

## Overview

This document describes the implementation of **Semantic Similarity Rating (SSR)** methodology as described in the paper "LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings" (Maier et al., 2025).

## What Changed

### Problem Addressed

The previous implementation directly extracted Likert-scale numeric ratings from LLM responses (e.g., `interest_score: int`), which the paper explicitly advises against. This approach loses information and doesn't properly model the uncertainty inherent in LLM responses.

### Solution: SSR Methodology

SSR converts natural language responses into **probability distributions** over Likert scales using semantic similarity. Instead of forcing a single numeric rating, SSR:

1. Captures natural language responses from personas
2. Uses semantic embeddings to measure similarity with reference statements
3. Converts similarities into probability mass functions (PMFs)
4. Aggregates PMFs to calculate market fit metrics

## Implementation Details

### 1. Updated `PersonaResponse` Model (`src/utils/models.py`)

**Before:**
```python
class PersonaResponse(BaseModel):
    persona_name: str
    interest_score: int  # Direct Likert score 1-5
    disappointment: DisappointmentLevel  # Enum: VERY/SOMEWHAT/NOT
    likelihood_to_recommend: int  # Direct NPS score 0-10
    # ...
```

**After:**
```python
class PersonaResponse(BaseModel):
    persona_name: str
    interest_response: str  # Natural language response
    disappointment_response: str  # Natural language response
    recommendation_response: str  # Natural language response
    # ...
```

### 2. Updated Prompts (`config/prompts.yaml`)

**Before:** Asked for numeric ratings:
```yaml
"interest_score": <number 1-5>
"disappointment": "<VERY or SOMEWHAT or NOT>"
"likelihood_to_recommend": <number 0-10>
```

**After:** Asks for natural language:
```yaml
"interest_response": "<your natural language response>"
"disappointment_response": "<your natural language response>"
"recommendation_response": "<your natural language response>"
```

Prompt instructs: "Express your opinions naturally and conversationally. Don't use numbers or scales."

### 3. Refactored Market Predictor (`src/agents/market_predictor.py`)

#### Added SSR Initialization

```python
def _initialize_ssr_raters(self):
    """Initialize SSR ResponseRater objects for each rating dimension."""
    # Define reference sentences for each Likert scale point
    interest_references = po.DataFrame({
        "id": ["interest"] * 5,
        "int_response": [1, 2, 3, 4, 5],
        "sentence": [
            "Not interested at all",
            "Slightly interested",
            "Moderately interested",
            "Very interested",
            "Extremely interested"
        ]
    })
    
    # Initialize ResponseRater for text-to-PMF conversion
    self.interest_rater = ResponseRater(interest_references)
    # Similar for disappointment and recommendation...
```

#### Refactored PMF Calculation

**Before:** Direct counting of numeric ratings:
```python
very_disappointed = sum(1 for r in responses if r.is_very_disappointed())
pmf_score = (very_disappointed / total) * 100
avg_interest = statistics.mean(r.interest_score for r in responses)
```

**After:** SSR-based PMF aggregation:
```python
# Convert natural language to PMFs using SSR
interest_pmfs = self.interest_rater.get_response_pmfs(
    "interest", [r.interest_response for r in responses], 
    temperature=1.0, epsilon=0.01
)

# Calculate expected values from PMFs
interest_scores = np.array([np.dot(pmf, [1, 2, 3, 4, 5]) for pmf in interest_pmfs])
avg_interest = float(np.mean(interest_scores))

# Calculate PMF score using probability distributions
very_disappointed_probs = disappointment_pmfs[:, 3:5].sum(axis=1)
pmf_score = float(np.mean(very_disappointed_probs) * 100)
```

### 4. Updated Dependencies (`pyproject.toml`)

Added required packages:
```toml
"numpy>=1.24.0",
"polars>=0.20.0",
"scipy>=1.10.0",
"sentence-transformers>=2.2.0",
"semantic-similarity-rating @ git+https://github.com/pymc-labs/semantic-similarity-rating.git",
```

### 5. Updated Tests

**test_models.py:**
- Removed tests for `is_very_disappointed()`, `is_promoter()`, `is_detractor()` (no longer exist)
- Added tests for natural language response fields

**test_pmf_calculation.py:**
- Updated to create responses with natural language instead of numeric ratings
- Tests now verify language patterns rather than exact numeric values
- Example:
  ```python
  # Before: assert response.interest_score == 5
  # After: assert "extremely" in response.interest_response.lower()
  ```

## Key Benefits

1. **Follows Paper's Methodology:** Implements the exact approach recommended in the paper
2. **Preserves Uncertainty:** PMFs capture distribution of possible ratings instead of single value
3. **More Realistic:** Natural language responses are closer to real survey behavior
4. **Statistically Rigorous:** Uses semantic embeddings and probability theory

## Reference Sentences

The implementation uses three sets of reference sentences:

**Interest (1-5):**
1. Not interested at all
2. Slightly interested
3. Moderately interested
4. Very interested
5. Extremely interested

**Disappointment (1-5):**
1. Wouldn't care at all
2. Slightly disappointed
3. Moderately disappointed
4. Very disappointed
5. Would be devastated

**Recommendation (1-5, mapped to NPS 0-10):**
1. Definitely would not recommend (NPS 0-2)
2. Probably would not recommend (NPS 3-4)
3. Might recommend (NPS 5-6)
4. Probably would recommend (NPS 7-8)
5. Absolutely would recommend (NPS 9-10)

## Example Usage

```python
# Natural language response from persona
response = PersonaResponse(
    persona_name="Alice",
    interest_response="I'm quite interested in this, it seems useful",
    disappointment_response="I would be somewhat disappointed if it went away",
    recommendation_response="I would probably recommend it to colleagues",
    main_benefit="Solves my time management problem",
    concerns=["Price seems a bit high"]
)

# SSR converts to PMF automatically in calculate_pmf()
market_fit = market_predictor.calculate_pmf(responses)
# Result: pmf_score uses probability distributions, not binary counts
```

## Migration Notes

If upgrading from the previous version:
1. Update any code that accessed `PersonaResponse.interest_score` → use SSR PMFs instead
2. Remove references to `is_very_disappointed()`, `is_promoter()`, `is_detractor()` methods
3. Update prompts to request natural language instead of numeric ratings
4. Install new dependencies: `pip install numpy polars scipy sentence-transformers`

## References

- Paper: "LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings" (Maier et al., 2025)
- SSR Package: https://github.com/pymc-labs/semantic-similarity-rating
- Methodology: Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings and cosine similarity for PMF generation

## Testing

All tests pass with the new implementation:
```bash
pytest tests/test_models.py          # 17 passed
pytest tests/test_pmf_calculation.py # 8 passed
```

The SSR implementation is production-ready and follows best practices from the academic literature.

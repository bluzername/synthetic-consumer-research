# Persona Diversity & Representativeness Strategy

## Problem Statement

Current persona generation relies on LLM interpretation of "ensure diversity," which can lead to:
1. **Biased distributions** - LLMs over-represent certain demographics (urban, tech-savvy, professional)
2. **Insufficient diversity** - Small samples (5-50 personas) won't naturally cover market segments
3. **No validation** - We can't verify if personas match real population distributions

## Solution: Stratified Sampling Framework

### Approach

Use **stratified sampling** to ensure personas match real-world demographic distributions:

1. **Define target distributions** based on census data
2. **Calculate quotas** for each persona batch
3. **Guide LLM generation** with explicit distribution requirements
4. **Validate** generated personas against targets
5. **Adjust** subsequent batches to correct imbalances

## Target Distributions

### Based on U.S. Census / Consumer Research Data:

#### Age Distribution (Adults 18+)
```yaml
age_distribution:
  18-24: 12%   # Gen Z adults
  25-34: 18%   # Young Millennials
  35-44: 17%   # Older Millennials
  45-54: 16%   # Gen X
  55-64: 16%   # Boomers
  65-74: 13%   # Older Boomers
  75+:    8%   # Silent Gen
```

#### Income Distribution
```yaml
income_distribution:
  Low (<$35k):           20%
  Lower-middle ($35-75k): 30%
  Middle ($75-125k):     30%
  Upper-middle ($125-200k): 15%
  High (>$200k):         5%
```

#### Location Type
```yaml
location_distribution:
  Urban:     32%
  Suburban:  55%
  Rural:     13%
```

#### Tech Savviness (Pew Research)
```yaml
tech_distribution:
  Level 1 (Low):     15%  # Tech-resistant
  Level 2 (Basic):   25%  # Basic users
  Level 3 (Average): 35%  # Comfortable users
  Level 4 (High):    20%  # Early adopters
  Level 5 (Expert):  5%   # Tech enthusiasts
```

#### Gender (if relevant)
```yaml
gender_distribution:
  Female: 52%
  Male:   48%
```

## Implementation Strategy

### Option 1: **Quota-Based Generation** (Recommended for small samples)

For small samples (5-50 personas), use **explicit quotas**:

```python
# For 20 personas
quotas = {
    "age_groups": {
        "18-24": 2,   # 10%
        "25-34": 4,   # 20%
        "35-44": 4,   # 20%
        "45-54": 3,   # 15%
        "55-64": 3,   # 15%
        "65-74": 3,   # 15%
        "75+": 1      # 5%
    },
    "tech_levels": {
        1: 3,  # 15%
        2: 5,  # 25%
        3: 7,  # 35%
        4: 4,  # 20%
        5: 1   # 5%
    },
    "locations": {
        "Urban": 6,     # 30%
        "Suburban": 11, # 55%
        "Rural": 3      # 15%
    }
}
```

**Benefits:**
- Guaranteed coverage of all segments
- No over-representation of popular demographics
- Deterministic for testing

### Option 2: **Weighted Random Sampling** (For larger samples)

For 50-100+ personas, use **weighted random selection**:

```python
import random
import numpy as np

def sample_age():
    return np.random.choice(
        ['18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+'],
        p=[0.12, 0.18, 0.17, 0.16, 0.16, 0.13, 0.08]
    )
```

**Benefits:**
- More natural variation
- Statistically correct in aggregate
- Easier to generate large samples

### Option 3: **Hybrid Approach** (Best for production)

1. **Generate seed personas** with quota-based method (ensures coverage)
2. **Fill remaining** with weighted random (adds variation)
3. **Validate distributions** post-generation
4. **Regenerate outliers** if distributions are off

## Enhanced Prompt Strategy

### Current Prompt Issues:
```yaml
# Too vague:
"Ensure diversity: different ages, occupations, income levels..."
```

### Improved Prompt with Explicit Quotas:
```yaml
generate_batch_prompt: |
  Generate exactly {count} consumer personas with the following distribution:
  
  AGE REQUIREMENTS:
  {age_quotas}
  
  INCOME REQUIREMENTS:
  {income_quotas}
  
  LOCATION REQUIREMENTS:
  {location_quotas}
  
  TECH SAVVINESS REQUIREMENTS:
  {tech_quotas}
  
  Each persona must be realistic and internally consistent. For example:
  - A 70-year-old retired teacher would likely have tech_savviness 1-2
  - A 28-year-old software engineer would likely have tech_savviness 4-5
  - Urban locations correlate with slightly higher tech levels
  
  Return JSON: {{"personas": [...]}}
```

## Validation & Metrics

### Post-Generation Validation

```python
def validate_persona_distribution(personas: List[Persona], targets: dict) -> dict:
    """Validate generated personas against target distributions."""
    
    actual = {
        "age": Counter([get_age_bucket(p.age) for p in personas]),
        "income": Counter([p.income_bracket for p in personas]),
        "location": Counter([p.location_type for p in personas]),
        "tech": Counter([p.tech_savviness for p in personas])
    }
    
    # Calculate chi-square goodness of fit
    metrics = {}
    for dimension, counts in actual.items():
        chi2_stat = calculate_chi_square(counts, targets[dimension])
        p_value = chi2_pvalue(chi2_stat, df=len(counts)-1)
        metrics[dimension] = {
            "chi_square": chi2_stat,
            "p_value": p_value,
            "passes": p_value > 0.05  # Not significantly different from target
        }
    
    return metrics
```

### Key Metrics:
- **Chi-square test**: Are distributions significantly different from targets?
- **Coverage**: Are all segments represented?
- **Bias score**: How far from target for each dimension?

## Occupation Diversity

### Common LLM Bias:
Over-represents: Software engineers, consultants, managers  
Under-represents: Blue-collar, service workers, stay-at-home parents

### Balanced Occupation List (by prevalence):

```yaml
occupation_distribution:
  # Professional/Technical (20%)
  - Software Engineer, Data Analyst, Accountant, Lawyer, Teacher
  
  # Management/Business (15%)
  - Manager, Small Business Owner, Sales Representative
  
  # Healthcare (15%)
  - Nurse, Healthcare Administrator, Medical Technician
  
  # Service (20%)
  - Retail Worker, Server, Customer Service, Childcare Provider
  
  # Blue Collar (15%)
  - Construction Worker, Mechanic, Electrician, Factory Worker
  
  # Other (15%)
  - Retired, Homemaker, Student, Freelancer, Artist
```

## Implementation Checklist

### Phase 1: Immediate Improvements
- [ ] Add explicit distribution requirements to prompts
- [ ] Implement quota-based generation for small samples
- [ ] Add distribution validation logging

### Phase 2: Advanced Features
- [ ] Weighted random sampling for large samples
- [ ] Chi-square validation tests
- [ ] Automatic rebalancing
- [ ] Dashboard showing persona distributions

### Phase 3: Market-Specific
- [ ] Allow custom distributions (e.g., "tech early adopters" market)
- [ ] Support international markets (different demographics)
- [ ] Industry-specific occupation lists

## Expected Impact

### Before:
```
Sample of 20 personas might have:
- Age: Heavily skewed to 25-40 (LLM bias)
- Tech: Over-represented level 4-5
- Location: 60% urban (reality: 32%)
- Occupations: 40% tech/professional
```

### After:
```
Sample of 20 personas will have:
- Age: Proper distribution across all age groups
- Tech: Matches Pew Research distribution
- Location: 32% urban, 55% suburban, 13% rural
- Occupations: Balanced across all sectors
```

## Configuration Example

```yaml
# config/settings.yaml

persona_generation:
  # Sampling strategy: "quota", "weighted_random", or "hybrid"
  strategy: "quota"
  
  # Target distributions (percentages)
  distributions:
    age:
      18-24: 12
      25-34: 18
      35-44: 17
      45-54: 16
      55-64: 16
      65-74: 13
      75+: 8
    
    income:
      "Low (<$35k)": 20
      "Lower-middle ($35-75k)": 30
      "Middle ($75-125k)": 30
      "Upper-middle ($125-200k)": 15
      "High (>$200k)": 5
    
    location:
      Urban: 32
      Suburban: 55
      Rural: 13
    
    tech_savviness:
      1: 15
      2: 25
      3: 35
      4: 20
      5: 5
  
  # Validation settings
  validation:
    enabled: true
    chi_square_threshold: 0.05
    require_full_coverage: true  # All segments must have at least 1 persona
```

## References

- U.S. Census Bureau: Age and Income Distributions
- Pew Research Center: Technology Adoption Studies
- Nielsen Consumer Research: Shopping Behavior Segmentation
- Marketing textbooks: Stratified sampling best practices

## Next Steps

1. **Implement quota-based generation** (highest priority)
2. **Add distribution validation** to logs
3. **Create persona analytics dashboard** showing distributions
4. **Test with different sample sizes** (5, 20, 50, 100)
5. **Validate SSR results** correlate better with balanced personas


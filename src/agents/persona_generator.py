"""Persona Generator - Create diverse synthetic consumer personas."""

from typing import List, Dict, Tuple
import json
from collections import Counter
from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    Persona,
)


class PersonaGenerator:
    """
    Generates diverse synthetic consumer personas for market simulation.
    Uses demographic and psychographic frameworks for realistic profiles.
    """
    
    def __init__(self):
        """Initialize Persona Generator."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        # Model configuration
        self.model = self.config.persona_generator_model
        self.temperature = self.config.get_setting("models", "persona_temperature", default=0.8)
        
        # Load prompts
        self.system_prompt = self.config.get_prompt("persona_generator", "system_prompt")
        self.batch_prompt_template = self.config.get_prompt("persona_generator", "generate_batch_prompt")
        
        # Cache personas for reuse
        self._persona_cache: List[Persona] = []
        
        # Load target distributions for stratified sampling
        self.target_distributions = self._load_target_distributions()
        self.use_stratified = self.config.get_setting("persona_generation", "strategy", default="stratified") == "stratified"
    
    def _load_target_distributions(self) -> Dict:
        """Load target demographic distributions from config."""
        try:
            return {
                "age_brackets": self.config.get_setting("persona_generation", "distributions", "age_brackets", default={}),
                "income_levels": self.config.get_setting("persona_generation", "distributions", "income_levels", default={}),
                "location_types": self.config.get_setting("persona_generation", "distributions", "location_types", default={}),
                "tech_savviness_levels": self.config.get_setting("persona_generation", "distributions", "tech_savviness_levels", default={})
            }
        except Exception as e:
            self.logger.log_warning(f"Could not load target distributions: {e}")
            return {}
    
    def generate_personas(self, count: int = 100) -> List[Persona]:
        """
        Generate diverse consumer personas.
        
        Uses stratified sampling if enabled to ensure proper demographic representation.
        
        Args:
            count: Number of personas to generate
        
        Returns:
            List of Persona objects
        """
        # Check cache first
        if len(self._persona_cache) >= count:
            self.logger.log_info(f"Using {count} cached personas")
            return self._persona_cache[:count]
        
        # Use stratified generation if enabled
        if self.use_stratified and self.target_distributions:
            return self.generate_personas_stratified(count)
        
        # Otherwise fall back to original method
        self.logger.log_agent_start("Persona Generator", f"Generating {count} personas (random sampling)")
        
        personas = []
        batch_size = 5  # Generate in smaller batches to avoid JSON errors
        failed_batches = 0
        max_failed_batches = 3
        
        # Use progress bar if available
        progress = self.logger.create_progress_bar("Generating personas", count)
        
        if progress:
            progress.start()
            task = progress.add_task("Personas", total=count)
        
        while len(personas) < count:
            remaining = count - len(personas)
            current_batch_size = min(batch_size, remaining)
            
            # Generate batch
            batch = self._generate_batch(current_batch_size)
            
            # Check if batch is empty (failed to parse any personas)
            if not batch:
                failed_batches += 1
                self.logger.log_warning(f"Batch failed ({failed_batches}/{max_failed_batches})")
                
                if failed_batches >= max_failed_batches:
                    from ..utils.exceptions import PersonaGenerationError
                    self.logger.log_error(f"Failed to generate personas after {max_failed_batches} attempts. Check prompt formatting.")
                    raise PersonaGenerationError(
                        f"Failed to generate personas after {max_failed_batches} attempts. "
                        f"Successfully generated {len(personas)} personas before failures. "
                        f"This may be due to:\n"
                        f"  1. Model not supporting structured JSON output reliably\n"
                        f"  2. Rate limiting or API timeouts\n"
                        f"  3. Prompt complexity issues\n"
                        f"Try: Using a different model (e.g., 'google/gemini-2.5-flash') or reducing batch size."
                    )
            else:
                failed_batches = 0  # Reset counter on success
            
            personas.extend(batch)
            
            if progress:
                progress.update(task, completed=len(personas))
        
        if progress:
            progress.stop()
        
        # Cache for reuse
        self._persona_cache = personas
        
        self.logger.log_agent_complete("Persona Generator")
        return personas
    
    def generate_personas_stratified(self, count: int = 20) -> List[Persona]:
        """
        Generate personas using stratified sampling for proper market representation.
        
        Ensures personas match real demographic distributions based on census data
        rather than LLM biases toward certain demographics.
        
        Args:
            count: Number of personas to generate
        
        Returns:
            List of Persona objects with proper demographic distribution
        """
        self.logger.log_agent_start("Persona Generator", 
            f"Generating {count} stratified personas")
        
        # Calculate quotas for each demographic segment
        quotas = self._calculate_quotas(count)
        self.logger.log_info(f"Target quotas calculated for {count} personas")
        
        personas = []
        batch_size = 5
        max_failed_batches = 3
        failed_batches = 0
        
        # Progress bar
        progress = self.logger.create_progress_bar("Generating stratified personas", count)
        if progress:
            progress.start()
            task = progress.add_task("Personas", total=count)
        
        while len(personas) < count:
            remaining = count - len(personas)
            current_batch_size = min(batch_size, remaining)
            
            # Generate batch with quota requirements
            batch = self._generate_batch_with_quotas(current_batch_size, quotas)
            
            if not batch:
                failed_batches += 1
                self.logger.log_warning(f"Stratified batch failed ({failed_batches}/{max_failed_batches})")
                
                if failed_batches >= max_failed_batches:
                    self.logger.log_error("Falling back to random generation")
                    # Fall back to original method
                    return self._generate_fallback_personas(count - len(personas), personas)
            else:
                failed_batches = 0
            
            personas.extend(batch)
            
            if progress:
                progress.update(task, completed=len(personas))
        
        if progress:
            progress.stop()
        
        # Validate final distribution
        validation = self._validate_distribution(personas[:count])
        self._log_distribution_report(validation, quotas)
        
        # Cache for reuse
        self._persona_cache = personas
        
        self.logger.log_agent_complete("Persona Generator")
        return personas[:count]
    
    def _calculate_quotas(self, total_count: int) -> Dict:
        """Calculate specific quotas for each demographic segment."""
        quotas = {}
        
        # Age quotas
        if "age_brackets" in self.target_distributions:
            age_quotas = {}
            for bracket, pct in self.target_distributions["age_brackets"].items():
                count = max(1, round(total_count * (pct / 100)))
                age_quotas[bracket] = count
            quotas["age"] = age_quotas
        
        # Income quotas
        if "income_levels" in self.target_distributions:
            income_quotas = {}
            for level, pct in self.target_distributions["income_levels"].items():
                count = max(1, round(total_count * (pct / 100)))
                income_quotas[level] = count
            quotas["income"] = income_quotas
        
        # Location quotas
        if "location_types" in self.target_distributions:
            loc_quotas = {}
            for location, pct in self.target_distributions["location_types"].items():
                count = max(1, round(total_count * (pct / 100)))
                loc_quotas[location] = count
            quotas["location"] = loc_quotas
        
        # Tech level quotas
        if "tech_savviness_levels" in self.target_distributions:
            tech_quotas = {}
            for level, pct in self.target_distributions["tech_savviness_levels"].items():
                count = max(1, round(total_count * (pct / 100)))
                tech_quotas[int(level)] = count
            quotas["tech"] = tech_quotas
        
        return quotas
    
    def _generate_batch_with_quotas(self, batch_size: int, quotas: Dict) -> List[Persona]:
        """Generate a batch of personas with explicit quota requirements."""
        # Format quota requirements for prompt
        quota_text = self._format_quotas_for_prompt(quotas, batch_size)
        
        # Enhanced prompt with explicit requirements
        user_prompt = f"""Generate exactly {batch_size} consumer personas with the following distribution requirements:

{quota_text}

IMPORTANT: Match these distributions as closely as possible. Each persona must be realistic and internally consistent:
- A 70-year-old retired teacher would typically have tech_savviness 1-2, not 5
- A 28-year-old software engineer would typically have tech_savviness 4-5, not 1
- Urban locations often correlate with slightly higher tech levels
- Income should match occupation realistically

Return JSON with this structure (no additional text, just valid JSON):
{{"personas": [{{"name": "...", "age": ..., "occupation": "...", "income_bracket": "...", "location_type": "...", "tech_savviness": ..., "values": [...], "pain_points": [...], "personality_traits": "...", "shopping_behavior": "..."}}]}}

Each persona must have ALL these fields: name (string), age (number 18-85), occupation (string), income_bracket (string matching quotas), location_type (string matching quotas), tech_savviness (number 1-5 matching quotas), values (array of 2 strings), pain_points (array of 2 strings), personality_traits (string), shopping_behavior (string).
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            
            # Parse and validate
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                content_fixed = content.replace(",]", "]").replace(",}", "}")
                try:
                    data = json.loads(content_fixed)
                except json.JSONDecodeError:
                    return []
            
            # Extract personas
            personas_data = self._extract_personas_from_response(data)
            
            # Convert to Persona objects
            personas = []
            for p_data in personas_data:
                try:
                    persona = Persona(**p_data)
                    personas.append(persona)
                except Exception as e:
                    self.logger.log_warning(f"Failed to parse persona: {e}")
                    continue
            
            return personas
        
        except Exception as e:
            self.logger.log_error("Stratified batch generation failed", str(e))
            return []
    
    def _format_quotas_for_prompt(self, quotas: Dict, batch_size: int) -> str:
        """Format quota requirements for prompt."""
        lines = []
        
        if "age" in quotas:
            lines.append("AGE DISTRIBUTION:")
            for bracket, count in quotas["age"].items():
                pct = (count / sum(quotas["age"].values())) * 100
                lines.append(f"  - {bracket} years: {count} personas ({pct:.0f}%)")
        
        if "income" in quotas:
            lines.append("\nINCOME DISTRIBUTION:")
            for level, count in quotas["income"].items():
                pct = (count / sum(quotas["income"].values())) * 100
                lines.append(f"  - {level}: {count} personas ({pct:.0f}%)")
        
        if "location" in quotas:
            lines.append("\nLOCATION DISTRIBUTION:")
            for location, count in quotas["location"].items():
                pct = (count / sum(quotas["location"].values())) * 100
                lines.append(f"  - {location}: {count} personas ({pct:.0f}%)")
        
        if "tech" in quotas:
            lines.append("\nTECH SAVVINESS DISTRIBUTION:")
            for level, count in quotas["tech"].items():
                pct = (count / sum(quotas["tech"].values())) * 100
                lines.append(f"  - Level {level}: {count} personas ({pct:.0f}%)")
        
        return "\n".join(lines)
    
    def _validate_distribution(self, personas: List[Persona]) -> Dict:
        """Validate persona distribution against targets."""
        total = len(personas)
        
        # Count actual distributions
        age_dist = Counter([self._get_age_bracket(p.age) for p in personas])
        income_dist = Counter([p.income_bracket for p in personas])
        location_dist = Counter([p.location_type for p in personas])
        tech_dist = Counter([p.tech_savviness for p in personas])
        
        # Calculate percentages
        validation = {
            "total_personas": total,
            "age_distribution": {k: (v/total)*100 for k, v in age_dist.items()},
            "income_distribution": {k: (v/total)*100 for k, v in income_dist.items()},
            "location_distribution": {k: (v/total)*100 for k, v in location_dist.items()},
            "tech_distribution": {k: (v/total)*100 for k, v in tech_dist.items()},
            "coverage": {
                "age_brackets_covered": len(age_dist),
                "income_levels_covered": len(income_dist),
                "locations_covered": len(location_dist),
                "tech_levels_covered": len(tech_dist)
            }
        }
        
        return validation
    
    def _get_age_bracket(self, age: int) -> str:
        """Get age bracket for an age."""
        if 18 <= age <= 24: return "18-24"
        elif 25 <= age <= 34: return "25-34"
        elif 35 <= age <= 44: return "35-44"
        elif 45 <= age <= 54: return "45-54"
        elif 55 <= age <= 64: return "55-64"
        elif 65 <= age <= 74: return "65-74"
        else: return "75-85"
    
    def _log_distribution_report(self, validation: Dict, quotas: Dict):
        """Log distribution validation report."""
        self.logger.log_info("=" * 60)
        self.logger.log_info("PERSONA DISTRIBUTION VALIDATION")
        self.logger.log_info("=" * 60)
        
        total = validation["total_personas"]
        self.logger.log_info(f"Total personas generated: {total}")
        
        # Age distribution
        if "age_distribution" in validation:
            self.logger.log_info("\nAge Distribution:")
            for bracket, pct in sorted(validation["age_distribution"].items()):
                target_pct = self.target_distributions.get("age_brackets", {}).get(bracket, 0)
                deviation = abs(pct - target_pct)
                status = "✓" if deviation < 10 else "⚠️"
                self.logger.log_info(f"  {status} {bracket}: {pct:.1f}% (target: {target_pct}%)")
        
        # Income distribution
        if "income_distribution" in validation:
            self.logger.log_info("\nIncome Distribution:")
            for level, pct in validation["income_distribution"].items():
                target_pct = self.target_distributions.get("income_levels", {}).get(level, 0)
                deviation = abs(pct - target_pct)
                status = "✓" if deviation < 10 else "⚠️"
                self.logger.log_info(f"  {status} {level}: {pct:.1f}% (target: {target_pct}%)")
        
        # Location distribution
        if "location_distribution" in validation:
            self.logger.log_info("\nLocation Distribution:")
            for location, pct in validation["location_distribution"].items():
                target_pct = self.target_distributions.get("location_types", {}).get(location, 0)
                deviation = abs(pct - target_pct)
                status = "✓" if deviation < 10 else "⚠️"
                self.logger.log_info(f"  {status} {location}: {pct:.1f}% (target: {target_pct}%)")
        
        # Tech distribution
        if "tech_distribution" in validation:
            self.logger.log_info("\nTech Savviness Distribution:")
            for level, pct in sorted(validation["tech_distribution"].items()):
                target_pct = self.target_distributions.get("tech_savviness_levels", {}).get(level, 0)
                deviation = abs(pct - target_pct)
                status = "✓" if deviation < 10 else "⚠️"
                self.logger.log_info(f"  {status} Level {level}: {pct:.1f}% (target: {target_pct}%)")
        
        # Coverage summary
        coverage = validation.get("coverage", {})
        self.logger.log_info(f"\nCoverage: {coverage.get('age_brackets_covered', 0)} age brackets, "
                            f"{coverage.get('tech_levels_covered', 0)} tech levels, "
                            f"{coverage.get('locations_covered', 0)} locations")
        self.logger.log_info("=" * 60)
    
    def _extract_personas_from_response(self, data) -> List[Dict]:
        """Extract persona list from API response (handles different formats)."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Look for personas in various possible keys
            for key in data.keys():
                clean_key = key.strip().strip('"').strip("'").lower()
                if 'persona' in clean_key:
                    return data[key]
            
            # If not found, get first list value
            return next((v for v in data.values() if isinstance(v, list)), [])
        
        return []
    
    def _generate_fallback_personas(self, count: int, existing: List[Persona]) -> List[Persona]:
        """Fallback to random generation if stratified fails."""
        self.logger.log_warning("Falling back to random persona generation")
        
        # Use original method
        fallback = []
        batch_size = 5
        
        while len(fallback) < count:
            batch = self._generate_batch(min(batch_size, count - len(fallback)))
            fallback.extend(batch)
        
        return existing + fallback[:count]
    
    def _generate_batch(self, count: int) -> List[Persona]:
        """
        Generate a batch of personas.
        
        Args:
            count: Number of personas in batch
        
        Returns:
            List of Persona objects
        """
        # Format prompt
        user_prompt = self.batch_prompt_template.format(count=count)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt + "\n\nReturn a JSON array of persona objects."}
        ]
        
        try:
            # Call API
            response = self.client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Debug: log first 500 chars of response
            self.logger.log_info(f"API response preview: {content[:500]}")
            
            # Try to parse JSON with repair logic if needed
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                self.logger.log_warning(f"JSON parsing failed, attempting repair: {e}")
                
                # Remove any trailing commas before closing brackets
                content_fixed = content.replace(",]", "]").replace(",}", "}")
                
                # Try parsing the fixed version
                try:
                    data = json.loads(content_fixed)
                except json.JSONDecodeError:
                    # If still failing, return empty list to continue workflow
                    self.logger.log_error("JSON repair failed, skipping this batch")
                    return []
            
            # Clean up dictionary keys (remove newlines, extra quotes, etc)
            if isinstance(data, dict):
                clean_data = {}
                for key, value in data.items():
                    # Clean the key - remove newlines, quotes, extra spaces
                    clean_key = key.strip().strip('\n').strip('\r').strip('"').strip("'").strip()
                    clean_data[clean_key] = value
                data = clean_data
            
            # Handle different response formats - be flexible with key names
            personas_data = []
            
            if isinstance(data, list):
                # Response is directly a list
                personas_data = data
            elif isinstance(data, dict):
                # Look for personas in various possible keys
                for key in data.keys():
                    # Clean the key (remove whitespace, quotes, etc)
                    clean_key = key.strip().strip('"').strip("'").lower()
                    if 'persona' in clean_key:
                        personas_data = data[key]
                        break
                
                # If still not found, get first list value
                if not personas_data:
                    personas_data = next(
                        (v for v in data.values() if isinstance(v, list)),
                        []
                    )
            
            # Convert to Persona objects
            personas = []
            for i, p_data in enumerate(personas_data):
                try:
                    persona = Persona(**p_data)
                    personas.append(persona)
                except Exception as e:
                    self.logger.log_warning(f"Failed to parse persona {i+1}: {e}")
                    # Log the actual data to help debug
                    self.logger.log_warning(f"Persona data was: {str(p_data)[:200]}")
                    continue
            
            return personas
        
        except Exception as e:
            self.logger.log_error("Persona batch generation failed", str(e))
            # Return empty list to continue workflow
            return []
    
    def generate_targeted_personas(
        self,
        target_market: str,
        count: int = 50
    ) -> List[Persona]:
        """
        Generate personas targeted to a specific market segment.
        
        Args:
            target_market: Target market description
            count: Number of personas
        
        Returns:
            List of Persona objects
        """
        self.logger.log_agent_start("Persona Generator", f"Generating {count} targeted personas")
        
        # Modified prompt for targeted generation
        targeted_prompt = f"""Generate {count} diverse consumer personas specifically for this target market:

Target Market: {target_market}

While focusing on this target market, still ensure diversity in:
- Age (within the target demographic)
- Income levels
- Occupations
- Values and priorities
- Pain points
- Tech-savviness

Provide realistic personas that would be interested in products targeting this market.

Return a JSON array of persona objects."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": targeted_prompt}
        ]
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Parse personas
            if "personas" in data:
                personas_data = data["personas"]
            elif isinstance(data, list):
                personas_data = data
            else:
                personas_data = next(
                    (v for v in data.values() if isinstance(v, list)),
                    []
                )
            
            personas = []
            for p_data in personas_data:
                try:
                    persona = Persona(**p_data)
                    personas.append(persona)
                except Exception as e:
                    self.logger.log_warning(f"Failed to parse persona: {e}")
                    continue
            
            self.logger.log_agent_complete("Persona Generator")
            return personas
        
        except Exception as e:
            self.logger.log_error("Targeted persona generation failed", str(e))
            # Fallback to general personas
            return self.generate_personas(count)
    
    def clear_cache(self):
        """Clear persona cache."""
        self._persona_cache = []
        self.logger.log_info("Persona cache cleared")


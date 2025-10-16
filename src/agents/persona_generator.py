"""Persona Generator - Create diverse synthetic consumer personas."""

from typing import List
import json
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
    
    def generate_personas(self, count: int = 100) -> List[Persona]:
        """
        Generate diverse consumer personas.
        
        Args:
            count: Number of personas to generate
        
        Returns:
            List of Persona objects
        """
        # Check cache first
        if len(self._persona_cache) >= count:
            self.logger.log_info(f"Using {count} cached personas")
            return self._persona_cache[:count]
        
        self.logger.log_agent_start("Persona Generator", f"Generating {count} personas")
        
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
                    self.logger.log_error(f"Failed to generate personas after {max_failed_batches} attempts. Check prompt formatting.")
                    break
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


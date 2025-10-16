"""Image generation using OpenRouter API (Gemini Flash Image)."""

from typing import List, Tuple, Optional
from pathlib import Path
import requests
from io import BytesIO

from ..utils import (
    get_config,
    get_openrouter_client,
    get_logger,
    ProductConcept,
)


class ImageGenerator:
    """
    Generate product renders and marketing images using AI.
    Uses google/gemini-2.5-flash-image via OpenRouter.
    """
    
    def __init__(self):
        """Initialize image generator."""
        self.config = get_config()
        self.client = get_openrouter_client()
        self.logger = get_logger()
        
        self.model = self.config.image_generator_model
    
    def generate_product_render(
        self,
        concept: ProductConcept,
        platform: str = "x",
        num_images: int = 1
    ) -> List[bytes]:
        """
        Generate professional product render images.
        
        Args:
            concept: Product concept to visualize
            platform: Target platform (x, linkedin, instagram)
            num_images: Number of images to generate
        
        Returns:
            List of image data (bytes)
        """
        self.logger.log_agent_start("Image Generator", f"Generating {num_images} product renders")
        
        # Get image size for platform
        if platform == "x":
            size = self.config.x_image_size
        elif platform == "linkedin":
            size = self.config.linkedin_image_size
        else:
            size = (1024, 1024)
        
        # Create detailed prompt
        prompt = self._create_product_prompt(concept)
        
        # Generate images
        try:
            image_urls = self.client.generate_image(
                prompt=prompt,
                model=self.model,
                size=f"{size[0]}x{size[1]}",
                n=num_images
            )
            
            if not image_urls:
                self.logger.log_warning("Image generation returned no URLs")
                return []
            
            # Download images
            images = []
            for url in image_urls:
                image_data = self._download_image(url)
                if image_data:
                    images.append(image_data)
            
            self.logger.log_agent_complete("Image Generator")
            return images
        
        except Exception as e:
            self.logger.log_error("Image generation failed", str(e))
            return []
    
    def _create_product_prompt(self, concept: ProductConcept) -> str:
        """
        Create detailed image generation prompt.
        
        Args:
            concept: Product concept
        
        Returns:
            Image generation prompt
        """
        # Base prompt structure for professional product photography
        prompt = f"""Professional product photography of {concept.name}.

Product Description: {concept.tagline}

Key Features to highlight:
{chr(10).join(f'- {feature}' for feature in concept.features[:3])}

Style: Modern, clean, professional product photography
Lighting: Studio lighting with soft shadows
Background: Clean white or minimalist gradient
Composition: Product centered, clear focus, high detail
Quality: 4K resolution, photorealistic, commercial grade

The product should look innovative, appealing to {concept.target_market}.
Emphasize the problem it solves: {concept.problem_solved}"""
        
        return prompt
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """
        Download image from URL.
        
        Args:
            url: Image URL
        
        Returns:
            Image data as bytes or None if failed
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        
        except Exception as e:
            self.logger.log_warning(f"Failed to download image from {url}: {e}")
            return None
    
    def save_image(self, image_data: bytes, filepath: Path):
        """
        Save image data to file.
        
        Args:
            image_data: Image bytes
            filepath: Path to save file
        """
        with open(filepath, 'wb') as f:
            f.write(image_data)
    
    def generate_multiple_platforms(
        self,
        concept: ProductConcept
    ) -> dict:
        """
        Generate images for all major platforms.
        
        Args:
            concept: Product concept
        
        Returns:
            Dict mapping platform names to image data
        """
        self.logger.log_agent_start("Image Generator", "Generating for all platforms")
        
        images = {}
        
        # X.com
        x_images = self.generate_product_render(concept, platform="x", num_images=1)
        if x_images:
            images["x"] = x_images[0]
        
        # LinkedIn
        linkedin_images = self.generate_product_render(concept, platform="linkedin", num_images=1)
        if linkedin_images:
            images["linkedin"] = linkedin_images[0]
        
        self.logger.log_agent_complete("Image Generator")
        return images
    
    def generate_feature_illustration(
        self,
        feature_description: str,
        platform: str = "x"
    ) -> Optional[bytes]:
        """
        Generate illustration for a specific feature.
        
        Args:
            feature_description: Description of the feature
            platform: Target platform
        
        Returns:
            Image data or None
        """
        prompt = f"""Minimalist illustration of: {feature_description}

Style: Clean, modern, professional
Background: Solid color or simple gradient
Composition: Centered, clear, icon-like
Quality: High resolution, sharp, clean lines"""
        
        try:
            image_urls = self.client.generate_image(
                prompt=prompt,
                model=self.model,
                n=1
            )
            
            if image_urls:
                return self._download_image(image_urls[0])
        
        except Exception as e:
            self.logger.log_warning(f"Feature illustration failed: {e}")
        
        return None


"""Asset bundler - Package complete output with all materials."""

from typing import Dict, List
from pathlib import Path
from datetime import datetime
import json

from ..utils import (
    get_config,
    get_logger,
    FileManager,
    ProductConcept,
    MarketFitScore,
    WorkflowState,
    OutputPackage,
)
from ..visualization import ImageGenerator, InfographicGenerator
from .x_composer import XComposer
from .linkedin_composer import LinkedInComposer


class AssetBundler:
    """
    Package complete output folder with all marketing materials.
    
    Creates:
    - README.md with concept overview
    - POSTING_GUIDE.md with instructions
    - concept.json with structured data
    - images/ folder with renders and infographics
    - posts/ folder with ready-to-copy posts
    - analytics/ folder with metrics
    """
    
    def __init__(self):
        """Initialize asset bundler."""
        self.config = get_config()
        self.logger = get_logger()
        self.file_manager = FileManager(self.config.output_base_dir)
        
        # Initialize composers and generators
        self.x_composer = XComposer()
        self.linkedin_composer = LinkedInComposer()
        self.image_gen = ImageGenerator()
        self.infographic_gen = InfographicGenerator()
    
    def create_complete_package(
        self,
        workflow_state: WorkflowState
    ) -> OutputPackage:
        """
        Create complete output package.
        
        Args:
            workflow_state: Final workflow state with all data
        
        Returns:
            OutputPackage with metadata
        """
        self.logger.log_agent_start("Asset Bundler", "Creating output package")
        
        concept = workflow_state["current_concept"]
        market_fit = workflow_state["market_fit"]
        history = workflow_state["history"]
        
        # Create output directory
        output_dir = self.file_manager.create_output_directory(concept.name)
        
        # Check if product is viable (using enhanced metrics)
        # Product is viable if it meets PMF threshold OR has 10%+ superfans (niche viability)
        pmf_score = market_fit.pmf_score if market_fit else 0
        pmf_threshold = workflow_state["pmf_threshold"]
        is_viable = (pmf_score >= pmf_threshold) or (market_fit and market_fit.is_viable_niche())
        
        # 1. Generate images (only if viable and feature enabled)
        image_files = []
        if is_viable and self.config.is_feature_enabled("enable_image_generation"):
            image_files = self._generate_images(concept, output_dir)
        
        # 2. Generate infographics (always generate for analysis)
        if self.config.is_feature_enabled("enable_infographics"):
            infographic_files = self._generate_infographics(market_fit, history, output_dir)
            image_files.extend(infographic_files)
        
        # 3. Create social media posts (only if viable)
        posts = []
        if is_viable and self.config.is_feature_enabled("enable_social_posts"):
            posts = self._create_social_posts(concept, market_fit, output_dir, image_files)
        elif not is_viable:
            if market_fit:
                viability_msg = f"Product not viable (Traditional PMF: {pmf_score:.1f}%, Superfans: {market_fit.superfan_ratio*100:.1f}%)"
            else:
                viability_msg = f"PMF threshold not met ({pmf_score:.1f}% < {pmf_threshold}%)"
            self.logger.log_warning(f"{viability_msg} - skipping social media posts and product images")
        
        # 4. Save concept data
        self._save_concept_data(concept, output_dir)
        
        # 5. Save analytics
        analytics_files = self._save_analytics(workflow_state, output_dir)
        
        # 6. Create README
        self._create_readme(workflow_state, output_dir)
        
        # 7. Create POSTING_GUIDE
        self._create_posting_guide(posts, output_dir)
        
        # Create output package metadata
        package = OutputPackage(
            product_name=concept.name,
            timestamp=datetime.now().isoformat(),
            output_dir=str(output_dir),
            concept=concept,
            market_fit=market_fit,
            iterations=workflow_state["iteration"],
            total_personas=len(workflow_state["personas"]),
            posts=posts,
            image_files=image_files,
            analytics_files=analytics_files,
        )
        
        self.logger.log_agent_complete("Asset Bundler")
        return package
    
    def _generate_images(self, concept: ProductConcept, output_dir: Path) -> List[str]:
        """Generate product images for all platforms."""
        image_files = []
        
        try:
            # Generate for different platforms
            images = self.image_gen.generate_multiple_platforms(concept)
            
            for platform, image_data in images.items():
                filename = f"{platform}_product_render.png"
                filepath = output_dir / "images" / filename
                self.file_manager.save_image(image_data, filepath)
                image_files.append(str(filepath))
                self.logger.log_info(f"Generated image: {filename}")
        
        except Exception as e:
            self.logger.log_warning(f"Image generation failed: {e}")
        
        return image_files
    
    def _generate_infographics(
        self,
        market_fit: MarketFitScore,
        history: List[Dict],
        output_dir: Path
    ) -> List[str]:
        """Generate infographic visualizations."""
        infographic_files = []
        
        try:
            # Market Segmentation Chart (NEW - shows distribution)
            segmentation_path = output_dir / "images" / "market_segmentation.png"
            self.infographic_gen.create_market_segmentation_chart(
                market_fit,
                save_path=segmentation_path
            )
            infographic_files.append(str(segmentation_path))
            self.logger.log_info("Generated market segmentation chart")
            
            # PMF Dashboard
            dashboard_path = output_dir / "images" / "pmf_dashboard.png"
            self.infographic_gen.create_pmf_dashboard(
                market_fit,
                threshold=self.config.pmf_threshold,
                save_path=dashboard_path
            )
            infographic_files.append(str(dashboard_path))
            self.logger.log_info("Generated PMF dashboard")
            
            # Iteration history (if multiple iterations)
            if len(history) > 1:
                history_path = output_dir / "images" / "iteration_history.png"
                self.infographic_gen.create_iteration_history(
                    history,
                    save_path=history_path
                )
                infographic_files.append(str(history_path))
                self.logger.log_info("Generated iteration history")
        
        except Exception as e:
            self.logger.log_warning(f"Infographic generation failed: {e}")
        
        return infographic_files
    
    def _create_social_posts(
        self,
        concept: ProductConcept,
        market_fit: MarketFitScore,
        output_dir: Path,
        image_files: List[str]
    ) -> List:
        """Create social media posts."""
        posts = []
        
        # X.com post
        x_post = self.x_composer.compose_post(concept, market_fit)
        
        # Add image paths
        x_images = [f for f in image_files if "x_" in f]
        if x_images:
            x_post.image_paths = [x_images[0]]
        
        # Save X post
        x_post_path = output_dir / "posts" / "x_post.md"
        self._save_post(x_post, x_post_path)
        posts.append(x_post)
        
        # LinkedIn post
        linkedin_post = self.linkedin_composer.compose_post(concept, market_fit)
        
        # Add image paths
        linkedin_images = [f for f in image_files if "linkedin_" in f]
        if linkedin_images:
            linkedin_post.image_paths = [linkedin_images[0]]
        
        # Save LinkedIn post
        linkedin_post_path = output_dir / "posts" / "linkedin_post.md"
        self._save_post(linkedin_post, linkedin_post_path)
        posts.append(linkedin_post)
        
        return posts
    
    def _save_post(self, post, filepath: Path):
        """Save social media post to markdown file."""
        content = f"# {post.platform.upper()} Post\n\n"
        content += f"**Character Count:** {post.char_count}/{280 if post.platform == 'x' else 3000}\n\n"
        
        if post.image_paths:
            content += f"**Images:**\n"
            for img in post.image_paths:
                content += f"- {img}\n"
            content += "\n"
        
        content += "---\n\n"
        content += post.text
        
        self.file_manager.save_text(content, filepath)
    
    def _save_concept_data(self, concept: ProductConcept, output_dir: Path):
        """Save concept as JSON."""
        concept_path = output_dir / "concept.json"
        self.file_manager.save_json(concept.model_dump(), concept_path)
    
    def _save_analytics(self, workflow_state: WorkflowState, output_dir: Path) -> List[str]:
        """Save analytics data."""
        analytics_files = []
        
        # Market fit data
        market_fit_path = output_dir / "analytics" / "market_fit.json"
        self.file_manager.save_json(
            workflow_state["market_fit"].model_dump(),
            market_fit_path
        )
        analytics_files.append(str(market_fit_path))
        
        # Iteration history
        history_path = output_dir / "analytics" / "iteration_history.json"
        self.file_manager.save_json(
            {"iterations": workflow_state["history"]},
            history_path
        )
        analytics_files.append(str(history_path))
        
        # Cost summary (if API client available)
        try:
            from ..utils import get_openrouter_client
            client = get_openrouter_client()
            cost_summary = client.get_cost_summary()
            
            cost_path = output_dir / "analytics" / "cost_summary.json"
            self.file_manager.save_json(cost_summary, cost_path)
            analytics_files.append(str(cost_path))
        except Exception as e:
            self.logger.log_warning(f"Could not save cost summary: {e}")
        
        return analytics_files
    
    def _create_readme(self, workflow_state: WorkflowState, output_dir: Path):
        """Create README.md with concept overview."""
        concept = workflow_state["current_concept"]
        market_fit = workflow_state["market_fit"]
        
        # Load template
        template = self.config.get_prompt("output", "readme_template")
        
        # Format lists
        features_list = "\n".join(f"{i}. {feature}" for i, feature in enumerate(concept.features, 1))
        differentiators_list = "\n".join(f"- {diff}" for diff in concept.differentiators)
        top_benefits_list = "\n".join(f"{i}. {benefit}" for i, benefit in enumerate(market_fit.top_benefits, 1))
        top_concerns_list = "\n".join(f"{i}. {concern}" for i, concern in enumerate(market_fit.top_concerns, 1))
        
        # Fill template
        readme_content = template.format(
            product_name=concept.name,
            tagline=concept.tagline,
            target_market=concept.target_market,
            problem_solved=concept.problem_solved,
            pricing_model=concept.pricing_model,
            features_list=features_list,
            differentiators_list=differentiators_list,
            pmf_score=market_fit.pmf_score,
            pmf_threshold=self.config.pmf_threshold,
            nps=market_fit.nps,
            avg_interest=market_fit.avg_interest,
            iteration_count=workflow_state["iteration"],
            personas_count=len(workflow_state["personas"]),
            top_benefits_list=top_benefits_list,
            top_concerns_list=top_concerns_list,
            recommendation=market_fit.recommendation,
            ideator_model=self.config.ideator_model,
            market_predictor_model=self.config.market_predictor_model,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        
        readme_path = output_dir / "README.md"
        self.file_manager.save_text(readme_content, readme_path)
    
    def _create_posting_guide(self, posts, output_dir: Path):
        """Create POSTING_GUIDE.md with instructions."""
        template = self.config.get_prompt("output", "posting_guide_template")
        
        # Get char counts
        x_char_count = next((p.char_count for p in posts if p.platform == "x"), 0)
        linkedin_char_count = next((p.char_count for p in posts if p.platform == "linkedin"), 0)
        
        guide_content = template.format(
            x_char_count=x_char_count,
            linkedin_char_count=linkedin_char_count,
        )
        
        guide_path = output_dir / "POSTING_GUIDE.md"
        self.file_manager.save_text(guide_content, guide_path)


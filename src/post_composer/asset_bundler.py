"""Asset bundler - Package complete output with all materials."""

from typing import Dict, List
from pathlib import Path
from datetime import datetime
import json
from collections import Counter

from ..utils import (
    get_config,
    get_logger,
    FileManager,
    ProductConcept,
    MarketFitScore,
    WorkflowState,
    OutputPackage,
    Persona,
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
        
        # Save personas for debugging
        personas_path = output_dir / "analytics" / "personas.json"
        personas_data = [
            {
                "name": p.name,
                "age": p.age,
                "occupation": p.occupation,
                "income_bracket": p.income_bracket,
                "location_type": p.location_type,
                "tech_savviness": p.tech_savviness,
                "values": p.values,
                "pain_points": p.pain_points,
                "personality_traits": p.personality_traits,
                "shopping_behavior": p.shopping_behavior
            }
            for p in workflow_state["personas"]
        ]
        self.file_manager.save_json(personas_data, personas_path)
        analytics_files.append(str(personas_path))
        
        # Save persona distribution analytics
        distribution_path = output_dir / "analytics" / "persona_distribution.json"
        distribution_analytics = self._calculate_persona_distribution(workflow_state["personas"])
        self.file_manager.save_json(distribution_analytics, distribution_path)
        analytics_files.append(str(distribution_path))
        
        # Save persona responses for debugging
        responses_path = output_dir / "analytics" / "persona_responses.json"
        responses_data = [
            {
                "persona_name": r.persona_name,
                "interest_response": r.interest_response,
                "purchase_intent_response": r.purchase_intent_response,
                "disappointment_response": r.disappointment_response,
                "recommendation_response": r.recommendation_response,
                "main_benefit": r.main_benefit,
                "concerns": r.concerns
            }
            for r in workflow_state["persona_responses"]
        ]
        self.file_manager.save_json(responses_data, responses_path)
        analytics_files.append(str(responses_path))
        
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
    
    def _calculate_persona_distribution(self, personas: List[Persona]) -> Dict:
        """Calculate demographic distribution analytics for personas."""
        total = len(personas)
        
        # Age distribution
        def get_age_bracket(age: int) -> str:
            if 18 <= age <= 24: return "18-24"
            elif 25 <= age <= 34: return "25-34"
            elif 35 <= age <= 44: return "35-44"
            elif 45 <= age <= 54: return "45-54"
            elif 55 <= age <= 64: return "55-64"
            elif 65 <= age <= 74: return "65-74"
            else: return "75-85"
        
        age_dist = Counter([get_age_bracket(p.age) for p in personas])
        income_dist = Counter([p.income_bracket for p in personas])
        location_dist = Counter([p.location_type for p in personas])
        tech_dist = Counter([p.tech_savviness for p in personas])
        occupation_dist = Counter([p.occupation for p in personas])
        
        # Load target distributions for comparison
        try:
            targets = {
                "age_brackets": self.config.get_setting("persona_generation", "distributions", "age_brackets", default={}),
                "income_levels": self.config.get_setting("persona_generation", "distributions", "income_levels", default={}),
                "location_types": self.config.get_setting("persona_generation", "distributions", "location_types", default={}),
                "tech_savviness_levels": self.config.get_setting("persona_generation", "distributions", "tech_savviness_levels", default={})
            }
        except:
            targets = {}
        
        return {
            "total_personas": total,
            "distributions": {
                "age": {
                    "actual": {k: round((v/total)*100, 1) for k, v in age_dist.items()},
                    "target": targets.get("age_brackets", {}),
                    "counts": dict(age_dist)
                },
                "income": {
                    "actual": {k: round((v/total)*100, 1) for k, v in income_dist.items()},
                    "target": targets.get("income_levels", {}),
                    "counts": dict(income_dist)
                },
                "location": {
                    "actual": {k: round((v/total)*100, 1) for k, v in location_dist.items()},
                    "target": targets.get("location_types", {}),
                    "counts": dict(location_dist)
                },
                "tech_savviness": {
                    "actual": {k: round((v/total)*100, 1) for k, v in tech_dist.items()},
                    "target": targets.get("tech_savviness_levels", {}),
                    "counts": dict(tech_dist)
                },
                "occupation": {
                    "counts": dict(occupation_dist.most_common(10)),
                    "unique_count": len(occupation_dist)
                }
            },
            "coverage": {
                "age_brackets": len(age_dist),
                "income_levels": len(income_dist),
                "locations": len(location_dist),
                "tech_levels": len(tech_dist),
                "occupations": len(occupation_dist)
            },
            "diversity_score": self._calculate_diversity_score(age_dist, income_dist, location_dist, tech_dist, total)
        }
    
    def _calculate_diversity_score(self, age_dist: Counter, income_dist: Counter, 
                                   location_dist: Counter, tech_dist: Counter, total: int) -> float:
        """Calculate overall diversity score (0-100)."""
        # Higher score = more diverse (more even distribution)
        # Use Shannon entropy as diversity measure
        import math
        
        def entropy(dist: Counter, total: int) -> float:
            if total == 0: return 0
            probs = [count/total for count in dist.values()]
            return -sum(p * math.log2(p) if p > 0 else 0 for p in probs)
        
        # Calculate entropy for each dimension
        age_entropy = entropy(age_dist, total)
        income_entropy = entropy(income_dist, total)
        location_entropy = entropy(location_dist, total)
        tech_entropy = entropy(tech_dist, total)
        
        # Max possible entropy for each (log2 of number of categories)
        max_age_entropy = math.log2(7)  # 7 age brackets
        max_income_entropy = math.log2(5)  # 5 income levels
        max_location_entropy = math.log2(3)  # 3 location types
        max_tech_entropy = math.log2(5)  # 5 tech levels
        
        # Normalized entropy (0-1) for each dimension
        age_score = age_entropy / max_age_entropy if max_age_entropy > 0 else 0
        income_score = income_entropy / max_income_entropy if max_income_entropy > 0 else 0
        location_score = location_entropy / max_location_entropy if max_location_entropy > 0 else 0
        tech_score = tech_entropy / max_tech_entropy if max_tech_entropy > 0 else 0
        
        # Average across dimensions, scale to 0-100
        overall_score = ((age_score + income_score + location_score + tech_score) / 4) * 100
        
        return round(overall_score, 1)


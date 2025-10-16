"""Main CLI entry point for Product Ideation System."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .orchestration import create_workflow
from .post_composer import AssetBundler
from .utils import get_config, get_logger, get_openrouter_client

app = typer.Typer(
    name="product-ideation",
    help="AI-Powered Product Ideation and Market Validation System",
    add_completion=False,
)

console = Console()


@app.command()
def generate(
    seed_idea: str = typer.Argument(..., help="Product idea or problem statement to explore"),
    iterations: Optional[int] = typer.Option(None, "--iterations", "-i", help="Maximum iterations (default: from config)"),
    pmf_threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="PMF threshold % (default: from config)"),
    personas: Optional[int] = typer.Option(None, "--personas", "-p", help="Number of personas to simulate (default: from config)"),
):
    """
    Generate and validate a product concept.
    
    This command runs the complete workflow:
    1. Generates product concept from seed idea
    2. Simulates market response with synthetic personas
    3. Calculates Product-Market Fit score
    4. Iterates to improve PMF if needed
    5. Generates images and social media posts
    6. Bundles complete output package
    
    Example:
        product-ideation generate "AI-powered desk organizer for remote workers"
    """
    try:
        # Load config
        config = get_config()
        logger = get_logger()
        
        # Display startup info
        console.print()
        console.print(Panel.fit(
            "[bold blue]🚀 AI-Powered Product Ideation System[/bold blue]\n\n"
            f"Seed Idea: {seed_idea}",
            border_style="blue"
        ))
        console.print()
        
        # Create and run workflow
        workflow = create_workflow()
        
        final_state = workflow.run(
            seed_idea=seed_idea,
            max_iterations=iterations,
            pmf_threshold=pmf_threshold,
            personas_count=personas,
        )
        
        # Create output package
        bundler = AssetBundler()
        package = bundler.create_complete_package(final_state)
        
        # Display final results
        _display_results(package, logger)
        
        console.print()
        console.print(f"[bold green]✅ Complete! Output saved to:[/bold green] {package.output_dir}")
        console.print()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Workflow interrupted by user[/yellow]")
        raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"\n\n[bold red]❌ Error:[/bold red] {str(e)}")
        console.print("\nFor debugging, check the logs or run with --verbose")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(True, "--show", "-s", help="Show current configuration"),
    models: bool = typer.Option(False, "--models", "-m", help="Show model configuration"),
):
    """
    Display current configuration.
    
    Shows the active configuration including models, workflow parameters,
    and feature flags.
    """
    try:
        cfg = get_config()
        
        console.print()
        console.print("[bold]Product Ideation System - Configuration[/bold]")
        console.print()
        
        if models or show:
            # Models table
            models_table = Table(title="Models Configuration", show_header=True)
            models_table.add_column("Agent", style="cyan")
            models_table.add_column("Model", style="green")
            models_table.add_column("Temperature", style="yellow")
            
            models_table.add_row("Ideator", cfg.ideator_model, str(cfg.ideator_temperature))
            models_table.add_row("Market Predictor", cfg.market_predictor_model, "-")
            models_table.add_row("Critic", cfg.critic_model, "-")
            models_table.add_row("Persona Generator", cfg.persona_generator_model, "-")
            models_table.add_row("Image Generator", cfg.image_generator_model, "-")
            
            console.print(models_table)
            console.print()
        
        if show:
            # Workflow parameters table
            workflow_table = Table(title="Workflow Parameters", show_header=True)
            workflow_table.add_column("Parameter", style="cyan")
            workflow_table.add_column("Value", style="green")
            
            workflow_table.add_row("Max Iterations", str(cfg.max_iterations))
            workflow_table.add_row("PMF Threshold", f"{cfg.pmf_threshold}%")
            workflow_table.add_row("Personas Count", str(cfg.personas_count))
            
            console.print(workflow_table)
            console.print()
            
            # Feature flags
            features_table = Table(title="Feature Flags", show_header=True)
            features_table.add_column("Feature", style="cyan")
            features_table.add_column("Enabled", style="green")
            
            features = [
                ("Image Generation", "enable_image_generation"),
                ("Infographics", "enable_infographics"),
                ("Social Posts", "enable_social_posts"),
                ("Cost Tracking", "enable_cost_tracking"),
            ]
            
            for name, key in features:
                enabled = "✅ Yes" if cfg.is_feature_enabled(key) else "❌ No"
                features_table.add_row(name, enabled)
            
            console.print(features_table)
            console.print()
    
    except Exception as e:
        console.print(f"[bold red]Error loading configuration:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def costs():
    """
    Display API usage and cost summary.
    
    Shows token usage, API calls, and estimated costs for the current session.
    """
    try:
        client = get_openrouter_client()
        summary = client.get_cost_summary()
        
        console.print()
        console.print("[bold]API Usage Summary[/bold]")
        console.print()
        
        # Overall stats
        stats_table = Table(title="Overall Statistics", show_header=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total API Calls", str(summary["total_calls"]))
        stats_table.add_row("Successful Calls", str(summary["successful_calls"]))
        stats_table.add_row("Failed Calls", str(summary["failed_calls"]))
        
        console.print(stats_table)
        console.print()
        
        # Per-model stats
        if summary["model_stats"]:
            model_table = Table(title="Usage by Model", show_header=True)
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Calls", style="green")
            model_table.add_column("Input Tokens", style="yellow")
            model_table.add_column("Output Tokens", style="yellow")
            
            for model, stats in summary["model_stats"].items():
                model_table.add_row(
                    model,
                    str(stats["calls"]),
                    f"{stats['input_tokens']:,}",
                    f"{stats['output_tokens']:,}"
                )
            
            console.print(model_table)
            console.print()
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def version():
    """Display version information."""
    console.print()
    console.print("[bold blue]Product Ideation System[/bold blue]")
    console.print("Version: 1.0.0")
    console.print("Python AI-powered product concept generation and market validation")
    console.print()


def _display_results(package, logger):
    """Display final results summary."""
    # Results table
    results_table = Table(title="Final Results", show_header=True, show_lines=True)
    results_table.add_column("Metric", style="cyan", width=30)
    results_table.add_column("Value", style="green")
    
    results_table.add_row("Product Name", package.concept.name)
    results_table.add_row("Tagline", package.concept.tagline)
    results_table.add_row("PMF Score", f"{package.market_fit.pmf_score:.1f}%")
    results_table.add_row("NPS", str(package.market_fit.nps))
    results_table.add_row("Avg Interest", f"{package.market_fit.avg_interest:.1f}/5.0")
    results_table.add_row("Iterations", str(package.iterations))
    results_table.add_row("Personas Simulated", str(package.total_personas))
    results_table.add_row("Recommendation", package.market_fit.recommendation)
    
    console.print()
    console.print(results_table)
    console.print()
    
    # Top benefits
    if package.market_fit.top_benefits:
        console.print("[bold cyan]Top Benefits:[/bold cyan]")
        for i, benefit in enumerate(package.market_fit.top_benefits[:3], 1):
            console.print(f"  {i}. {benefit}")
        console.print()
    
    # Generated files
    console.print("[bold cyan]Generated Files:[/bold cyan]")
    console.print(f"  • Product images: {len(package.image_files)}")
    console.print(f"  • Social posts: {len(package.posts)}")
    console.print(f"  • Analytics files: {len(package.analytics_files)}")
    console.print()


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()


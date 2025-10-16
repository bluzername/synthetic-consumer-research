"""Logging and analytics utilities."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class SystemLogger:
    """Enhanced logger with Rich console output and analytics tracking."""
    
    def __init__(self, level: str = "INFO", use_rich: bool = True):
        """
        Initialize logger.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            use_rich: Use Rich formatting for console output
        """
        self.level = level
        self.use_rich = use_rich
        
        # Set up standard logging
        logging.basicConfig(
            level=getattr(logging, level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("product-ideation")
        
        # Rich console for beautiful output
        if use_rich:
            self.console = Console()
        else:
            self.console = None
        
        # Analytics tracking
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.events: list = []
    
    def start_workflow(self, seed_idea: str):
        """Log workflow start."""
        self.start_time = datetime.now()
        
        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"[bold blue]🚀 Starting AI Product Ideation Workflow[/bold blue]\n\n"
                f"Seed Idea: {seed_idea}\n"
                f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                border_style="blue"
            ))
            self.console.print()
        else:
            self.logger.info(f"Starting workflow with seed: {seed_idea}")
        
        self.events.append({
            "event": "workflow_start",
            "timestamp": self.start_time.isoformat(),
            "seed_idea": seed_idea,
        })
    
    def log_iteration(self, iteration: int, pmf_score: float, concept_name: str):
        """Log iteration details."""
        if self.console:
            self.console.print(f"[bold cyan]Iteration {iteration}[/bold cyan]: "
                             f"{concept_name} - PMF: [bold]{pmf_score:.1f}%[/bold]")
        else:
            self.logger.info(f"Iteration {iteration}: {concept_name} - PMF: {pmf_score}%")
        
        self.events.append({
            "event": "iteration",
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "concept_name": concept_name,
            "pmf_score": pmf_score,
        })
    
    def log_agent_start(self, agent_name: str, operation: str):
        """Log agent operation start."""
        if self.console:
            self.console.print(f"  [yellow]→[/yellow] {agent_name}: {operation}...")
        else:
            self.logger.info(f"{agent_name} - {operation}")
    
    def log_agent_complete(self, agent_name: str):
        """Log agent operation complete."""
        if self.console:
            self.console.print(f"  [green]✓[/green] {agent_name} complete")
        else:
            self.logger.info(f"{agent_name} complete")
    
    def log_pmf_results(self, pmf_score: float, nps: int, avg_interest: float,
                       threshold: float, meets_threshold: bool, market_fit=None):
        """Log PMF analysis results with enhanced metrics."""
        if self.console:
            # Create results table
            table = Table(title="Enhanced Market Fit Analysis", show_header=True)
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("Score", style="bold", width=15)
            table.add_column("Status", style="bold", width=30)
            
            # If we have enhanced metrics, show them
            if market_fit:
                # Viability Assessment
                viable_status = ""
                if market_fit.is_viable_mass_market():
                    viable_status = "[green]✅ MASS MARKET VIABLE[/green]"
                elif market_fit.is_viable_niche():
                    viable_status = "[green]✅ NICHE VIABLE[/green]"
                else:
                    viable_status = "[red]❌ NEEDS WORK[/red]"
                
                table.add_row("Overall Viability", "", viable_status)
                table.add_section()
                
                # Key viability metrics
                superfan_color = "green" if market_fit.superfan_ratio >= 0.10 else "yellow" if market_fit.superfan_ratio >= 0.05 else "red"
                table.add_row(
                    "Superfans (5/5 + VERY)",
                    f"{market_fit.superfan_ratio*100:.1f}%",
                    f"[{superfan_color}]{'✅' if market_fit.superfan_ratio >= 0.10 else '⚠️'} Target: 10%+[/{superfan_color}]"
                )
                
                enthusiast_color = "green" if market_fit.segmentation.enthusiasts_pct >= 40 else "yellow" if market_fit.segmentation.enthusiasts_pct >= 25 else "red"
                table.add_row(
                    "Enthusiasts (4-5/5)",
                    f"{market_fit.segmentation.enthusiasts_pct:.1f}%",
                    f"[{enthusiast_color}]{'✅' if market_fit.segmentation.enthusiasts_pct >= 25 else '⚠️'} Early adopters[/{enthusiast_color}]"
                )
                
                table.add_row(
                    "Target Market Size",
                    f"{market_fit.target_market_size_pct:.1f}%",
                    f"{'✅' if market_fit.target_market_size_pct >= 35 else '⚠️'} Addressable market"
                )
                
                table.add_section()
                
                # Traditional metrics for comparison
                table.add_row(
                    "Traditional PMF",
                    f"{pmf_score:.1f}%",
                    f"{'✅' if pmf_score >= 15 else '⚠️'} (concepts: 15%+ good)"
                )
            else:
                # Legacy display
                pmf_status = "✅ PASS" if meets_threshold else "❌ NEEDS WORK"
                pmf_color = "green" if meets_threshold else "red"
                table.add_row(
                    "PMF Score",
                    f"{pmf_score:.1f}%",
                    f"[{pmf_color}]{pmf_status}[/{pmf_color}] (target: {threshold}%)"
                )
            
            # NPS
            nps_status = "✅ Good" if nps > 0 else "⚠️  Negative"
            table.add_row("Net Promoter Score", str(nps), nps_status)
            
            # Interest
            interest_status = "✅ Strong" if avg_interest >= 4.0 else "✅ Good" if avg_interest >= 3.5 else "⚠️  Moderate"
            table.add_row("Avg Interest", f"{avg_interest:.1f}/5.0", interest_status)
            
            self.console.print()
            self.console.print(table)
            self.console.print()
        else:
            self.logger.info(f"PMF: {pmf_score}%, NPS: {nps}, Interest: {avg_interest}/5.0")
    
    def log_workflow_complete(self, output_dir: str, iterations: int, final_pmf: float):
        """Log workflow completion."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if self.console:
            self.console.print()
            self.console.print(Panel(
                f"[bold green]✅ Workflow Complete![/bold green]\n\n"
                f"Final PMF Score: [bold]{final_pmf:.1f}%[/bold]\n"
                f"Iterations: {iterations}\n"
                f"Duration: {duration:.1f}s\n"
                f"Output: {output_dir}",
                border_style="green"
            ))
            self.console.print()
        else:
            self.logger.info(f"Workflow complete - PMF: {final_pmf}%, Iterations: {iterations}")
        
        self.events.append({
            "event": "workflow_complete",
            "timestamp": self.end_time.isoformat(),
            "duration_seconds": duration,
            "iterations": iterations,
            "final_pmf": final_pmf,
            "output_dir": output_dir,
        })
    
    def log_error(self, error: str, details: Optional[str] = None):
        """Log error."""
        if self.console:
            error_text = f"[bold red]❌ Error:[/bold red] {error}"
            if details:
                error_text += f"\n\nDetails: {details}"
            self.console.print()
            self.console.print(Panel(error_text, border_style="red"))
            self.console.print()
        else:
            self.logger.error(f"{error} - {details}" if details else error)
        
        self.events.append({
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "details": details,
        })
    
    def log_warning(self, message: str):
        """Log warning."""
        if self.console:
            self.console.print(f"[yellow]⚠️  Warning:[/yellow] {message}")
        else:
            self.logger.warning(message)
    
    def log_info(self, message: str):
        """Log info message."""
        if self.console:
            self.console.print(f"[blue]ℹ️  {message}[/blue]")
        else:
            self.logger.info(message)
    
    def create_progress_bar(self, description: str, total: int) -> Progress:
        """Create Rich progress bar."""
        if self.console:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
            )
        return None
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        if not self.start_time or not self.end_time:
            return {"events": self.events}
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Count event types
        event_counts = {}
        for event in self.events:
            event_type = event.get("event")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "event_counts": event_counts,
            "events": self.events,
        }


# Global logger instance
_logger: Optional[SystemLogger] = None


def get_logger() -> SystemLogger:
    """Get global logger instance."""
    global _logger
    if _logger is None:
        _logger = SystemLogger()
    return _logger


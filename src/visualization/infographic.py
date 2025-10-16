"""Infographic generation using matplotlib and seaborn."""

from typing import List, Dict
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from io import BytesIO

from ..utils import (
    get_config,
    get_logger,
    MarketFitScore,
)


class InfographicGenerator:
    """
    Generate data visualizations and infographics for market analysis.
    Uses matplotlib and seaborn for professional-grade charts.
    """
    
    def __init__(self):
        """Initialize infographic generator."""
        self.config = get_config()
        self.logger = get_logger()
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 150
        plt.rcParams['font.size'] = 10
        plt.rcParams['font.family'] = 'sans-serif'
    
    def create_market_segmentation_chart(
        self,
        market_fit: MarketFitScore,
        save_path: Path = None
    ) -> bytes:
        """
        Create market segmentation visualization showing interest distribution.
        
        Args:
            market_fit: Market fit with segmentation data
            save_path: Optional path to save file
        
        Returns:
            Image data as bytes
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Market Segmentation Analysis', fontsize=16, fontweight='bold')
        
        # Interest Distribution Histogram
        interest_levels = list(market_fit.interest_distribution.keys())
        counts = list(market_fit.interest_distribution.values())
        colors = ['#d32f2f', '#ff6f00', '#fbc02d', '#7cb342', '#2e7d32']  # Red to green
        
        bars = ax1.bar(interest_levels, counts, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('Interest Level', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Number of Personas', fontsize=12, fontweight='bold')
        ax1.set_title('Interest Distribution', fontsize=14)
        ax1.set_xticks(interest_levels)
        ax1.set_xticklabels(['1\n(None)', '2\n(Low)', '3\n(Moderate)', '4\n(High)', '5\n(Extreme)'])
        ax1.grid(axis='y', alpha=0.3)
        
        # Add percentage labels on bars
        total = sum(counts)
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            pct = (count / total) * 100
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(count)}\n({pct:.1f}%)',
                    ha='center', va='bottom', fontweight='bold')
        
        # Highlight target market
        superfan_idx = 4  # Index for interest level 5
        if counts[superfan_idx] > 0:
            bars[superfan_idx].set_edgecolor('gold')
            bars[superfan_idx].set_linewidth(3)
        
        # Market Segments Pie Chart
        segments = {
            'Superfans\n(5/5 + VERY)': market_fit.segmentation.superfans_pct,
            'Enthusiasts\n(4-5/5)': market_fit.segmentation.enthusiasts_pct - market_fit.segmentation.superfans_pct,
            'Interested\n(3/5)': market_fit.segmentation.interested_pct,
            'Skeptical\n(1-2/5)': market_fit.segmentation.skeptical_pct,
        }
        
        colors_pie = ['#2e7d32', '#7cb342', '#fbc02d', '#d32f2f']
        explode = (0.1 if market_fit.superfan_ratio >= 0.10 else 0, 0, 0, 0)
        
        wedges, texts, autotexts = ax2.pie(
            segments.values(),
            labels=segments.keys(),
            colors=colors_pie,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            textprops={'fontweight': 'bold'}
        )
        
        ax2.set_title('Market Segments', fontsize=14)
        
        # Add viability indicator
        if market_fit.is_viable_niche():
            viability_text = '✓ VIABLE\n(10%+ superfans)'
            viability_color = 'green'
        else:
            viability_text = '⚠ NEEDS WORK\n(<10% superfans)'
            viability_color = 'red'
        
        ax2.text(0, -1.4, viability_text,
                ha='center', va='center',
                fontsize=12, fontweight='bold',
                color=viability_color,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=viability_color, linewidth=2))
        
        plt.tight_layout()
        
        # Save or return
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            self.logger.log_info(f"Market segmentation chart saved")
        
        # Return as bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf.read()
    
    def create_pmf_dashboard(
        self,
        market_fit: MarketFitScore,
        threshold: float = 40.0,
        save_path: Path = None
    ) -> bytes:
        """
        Create comprehensive PMF dashboard infographic.
        
        Args:
            market_fit: Market fit scores
            threshold: PMF threshold
            save_path: Optional path to save file
        
        Returns:
            Image data as bytes
        """
        self.logger.log_agent_start("Infographic Generator", "Creating PMF dashboard")
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Product-Market Fit Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. PMF Score Gauge
        self._create_pmf_gauge(ax1, market_fit.pmf_score, threshold)
        
        # 2. NPS Score
        self._create_nps_chart(ax2, market_fit.nps)
        
        # 3. Interest Distribution
        self._create_interest_chart(ax3, market_fit.avg_interest)
        
        # 4. Top Benefits vs Concerns
        self._create_benefits_concerns_chart(ax4, market_fit)
        
        plt.tight_layout()
        
        # Save to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        image_data = buffer.read()
        plt.close(fig)
        
        # Save to file if path provided
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(image_data)
        
        self.logger.log_agent_complete("Infographic Generator")
        return image_data
    
    def _create_pmf_gauge(self, ax, pmf_score: float, threshold: float):
        """Create PMF score gauge chart."""
        # Determine color based on score
        if pmf_score >= 40:
            color = '#2ecc71'  # Green
        elif pmf_score >= 30:
            color = '#f39c12'  # Orange
        else:
            color = '#e74c3c'  # Red
        
        # Create gauge
        ax.barh([0], [pmf_score], color=color, height=0.5)
        ax.barh([0], [100 - pmf_score], left=[pmf_score], color='lightgray', height=0.5)
        
        # Add threshold line
        ax.axvline(x=threshold, color='black', linestyle='--', linewidth=2, label=f'Target ({threshold}%)')
        
        # Add score text
        ax.text(pmf_score / 2, 0, f'{pmf_score:.1f}%', 
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel('PMF Score (%)', fontsize=12)
        ax.set_title('Product-Market Fit Score', fontsize=14, fontweight='bold')
        ax.set_yticks([])
        ax.legend()
        ax.grid(False)
    
    def _create_nps_chart(self, ax, nps: int):
        """Create NPS score chart."""
        # Determine color
        if nps > 50:
            color = '#2ecc71'
        elif nps > 0:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        
        # Create bar
        ax.bar(['NPS'], [nps], color=color, width=0.4)
        
        # Add reference lines
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax.axhline(y=50, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Excellent (>50)')
        
        # Add score text
        ax.text(0, nps + (5 if nps > 0 else -5), f'{nps}', 
                ha='center', va='bottom' if nps > 0 else 'top', 
                fontsize=14, fontweight='bold')
        
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Net Promoter Score', fontsize=14, fontweight='bold')
        ax.set_ylim(-100, 100)
        ax.legend()
    
    def _create_interest_chart(self, ax, avg_interest: float):
        """Create average interest chart."""
        # Create bars for scale
        colors = ['#e74c3c', '#e67e22', '#f39c12', '#2ecc71', '#27ae60']
        bars = ax.barh(range(1, 6), [1]*5, color=colors, alpha=0.3)
        
        # Highlight average
        highlight_idx = int(avg_interest) - 1
        bars[highlight_idx].set_alpha(1.0)
        
        # Add average line
        ax.axvline(x=0.5, color='black', linestyle='--', linewidth=2)
        
        # Add text
        ax.text(0.5, avg_interest, f'{avg_interest:.1f}', 
                ha='right', va='center', fontsize=14, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='black'))
        
        ax.set_yticks(range(1, 6))
        ax.set_yticklabels(['1 - Low', '2', '3 - Medium', '4', '5 - High'])
        ax.set_xlim(0, 1)
        ax.set_title('Average Interest Level', fontsize=14, fontweight='bold')
        ax.set_xlabel('')
        ax.set_xticks([])
    
    def _create_benefits_concerns_chart(self, ax, market_fit: MarketFitScore):
        """Create benefits vs concerns comparison."""
        # Take top 3 of each
        benefits = market_fit.top_benefits[:3]
        concerns = market_fit.top_concerns[:3]
        
        # Truncate long text
        benefits = [b[:30] + '...' if len(b) > 30 else b for b in benefits]
        concerns = [c[:30] + '...' if len(c) > 30 else c for c in concerns]
        
        y_pos = list(range(len(benefits) + len(concerns)))
        
        # Create horizontal bars
        benefit_bars = ax.barh(y_pos[:len(benefits)], [1]*len(benefits), 
                               color='#2ecc71', alpha=0.7, label='Benefits')
        concern_bars = ax.barh(y_pos[len(benefits):], [1]*len(concerns), 
                               color='#e74c3c', alpha=0.7, label='Concerns')
        
        # Set labels
        labels = benefits + concerns
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_xlabel('')
        ax.set_xticks([])
        ax.set_title('Top Benefits & Concerns', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(False)
    
    def create_iteration_history(
        self,
        history: List[Dict],
        save_path: Path = None
    ) -> bytes:
        """
        Create chart showing PMF improvement across iterations.
        
        Args:
            history: List of iteration history dicts
            save_path: Optional save path
        
        Returns:
            Image data
        """
        self.logger.log_agent_start("Infographic Generator", "Creating iteration history")
        
        if not history:
            # Return empty/placeholder
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No iteration history available', 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # Extract data
            iterations = [h['iteration'] for h in history]
            pmf_scores = [h['pmf_score'] for h in history]
            nps_scores = [h['nps'] for h in history]
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.suptitle('Iteration Progress', fontsize=16, fontweight='bold')
            
            # PMF score progression
            ax1.plot(iterations, pmf_scores, marker='o', linewidth=2, 
                    markersize=8, color='#3498db', label='PMF Score')
            ax1.axhline(y=40, color='green', linestyle='--', label='Target (40%)')
            ax1.set_xlabel('Iteration', fontsize=12)
            ax1.set_ylabel('PMF Score (%)', fontsize=12)
            ax1.set_title('PMF Score Progression', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # NPS progression
            ax2.plot(iterations, nps_scores, marker='s', linewidth=2, 
                    markersize=8, color='#e74c3c', label='NPS')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
            ax2.set_xlabel('Iteration', fontsize=12)
            ax2.set_ylabel('NPS Score', fontsize=12)
            ax2.set_title('Net Promoter Score Progression', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        image_data = buffer.read()
        plt.close(fig)
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(image_data)
        
        self.logger.log_agent_complete("Infographic Generator")
        return image_data


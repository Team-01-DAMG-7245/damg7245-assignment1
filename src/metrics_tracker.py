#!/usr/bin/env python3
# metrics_tracker.py
# Track metrics over time and detect distribution drift

import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import argparse
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class MetricsTracker:
    """Track parsing metrics over time and detect drift"""
    
    def __init__(self, results_dir="evaluation_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def load_historical_metrics(self) -> pd.DataFrame:
        """Load all historical metrics into a DataFrame"""
        
        metric_files = list(self.results_dir.glob("metrics_*.json"))
        if not metric_files:
            print("❌ No metrics files found")
            return pd.DataFrame()
        
        all_data = []
        
        for file in sorted(metric_files):
            with open(file, 'r') as f:
                data = json.load(f)
            
            timestamp = data['timestamp']
            
            # Convert to datetime
            try:
                dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
            except:
                # Fallback for different timestamp formats
                dt = datetime.fromtimestamp(file.stat().st_mtime)
            
            # Extract metrics for each page
            for page_name, metrics in data['results'].items():
                row = {
                    'timestamp': dt,
                    'file': file.name,
                    'page': page_name,
                    **metrics  # Unpack all metrics
                }
                all_data.append(row)
        
        df = pd.DataFrame(all_data)
        df = df.sort_values('timestamp')
        
        print(f"📊 Loaded {len(df)} metric records from {len(metric_files)} files")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    
    def calculate_drift_metrics(self, df: pd.DataFrame, window_size: int = 5) -> Dict:
        """Calculate drift metrics between recent and historical performance"""
        
        if len(df) < window_size * 2:
            print(f"⚠️  Not enough data for drift detection (need at least {window_size * 2} records)")
            return {}
        
        # Get recent and historical windows
        recent = df.tail(window_size)
        historical = df.iloc[:-window_size].tail(window_size)  # Previous window
        
        drift_results = {}
        
        # Metrics to check for drift
        metrics_to_check = ['text_wer', 'text_cer', 'table_f1', 'chunk_length_mean', 'numeric_token_ratio']
        
        for metric in metrics_to_check:
            if metric in df.columns:
                recent_values = recent[metric].values
                historical_values = historical[metric].values
                
                # Remove any NaN values
                recent_values = recent_values[~np.isnan(recent_values)]
                historical_values = historical_values[~np.isnan(historical_values)]
                
                if len(recent_values) > 0 and len(historical_values) > 0:
                    # Statistical tests for drift
                    try:
                        # Mann-Whitney U test (non-parametric)
                        statistic, p_value = stats.mannwhitneyu(historical_values, recent_values, 
                                                               alternative='two-sided')
                        
                        # Effect size (difference in means)
                        effect_size = np.mean(recent_values) - np.mean(historical_values)
                        
                        # Relative change
                        historical_mean = np.mean(historical_values)
                        if historical_mean != 0:
                            relative_change = effect_size / historical_mean
                        else:
                            relative_change = 0
                        
                        drift_results[metric] = {
                            'recent_mean': np.mean(recent_values),
                            'historical_mean': np.mean(historical_values),
                            'effect_size': effect_size,
                            'relative_change': relative_change,
                            'p_value': p_value,
                            'significant_drift': p_value < 0.05,
                            'drift_direction': 'improvement' if effect_size < 0 and metric.endswith(('_wer', '_cer')) 
                                             else 'improvement' if effect_size > 0 and not metric.endswith(('_wer', '_cer'))
                                             else 'degradation'
                        }
                        
                    except Exception as e:
                        print(f"Warning: Could not calculate drift for {metric}: {e}")
        
        return drift_results
    
    def visualize_metrics_over_time(self, df: pd.DataFrame, save_plot: bool = True) -> None:
        """Create time series visualizations of key metrics"""
        
        if df.empty:
            print("No data to visualize")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('Parsing Metrics Over Time', fontsize=16)
        
        # Aggregate by timestamp (average across pages)
        time_grouped = df.groupby('timestamp').agg({
            'text_wer': 'mean',
            'text_cer': 'mean', 
            'table_f1': 'mean',
            'chunk_length_mean': 'mean',
            'numeric_token_ratio': 'mean',
            'total_blocks': 'mean'
        }).reset_index()
        
        # Plot 1: Text WER over time
        axes[0, 0].plot(time_grouped['timestamp'], time_grouped['text_wer'], 'o-', color='red', alpha=0.7)
        axes[0, 0].set_title('Word Error Rate Over Time')
        axes[0, 0].set_ylabel('WER (Lower = Better)')
        axes[0, 0].axhline(y=0.1, color='green', linestyle='--', alpha=0.5, label='Good (<0.1)')
        axes[0, 0].axhline(y=0.3, color='orange', linestyle='--', alpha=0.5, label='Fair (<0.3)')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Character Error Rate
        axes[0, 1].plot(time_grouped['timestamp'], time_grouped['text_cer'], 'o-', color='darkred', alpha=0.7)
        axes[0, 1].set_title('Character Error Rate Over Time')
        axes[0, 1].set_ylabel('CER (Lower = Better)')
        axes[0, 1].axhline(y=0.05, color='green', linestyle='--', alpha=0.5, label='Good (<0.05)')
        axes[0, 1].axhline(y=0.15, color='orange', linestyle='--', alpha=0.5, label='Fair (<0.15)')
        axes[0, 1].legend()
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Plot 3: Table F1 Score
        axes[1, 0].plot(time_grouped['timestamp'], time_grouped['table_f1'], 'o-', color='green', alpha=0.7)
        axes[1, 0].set_title('Table F1-Score Over Time')
        axes[1, 0].set_ylabel('F1 Score (Higher = Better)')
        axes[1, 0].axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Good (>0.8)')
        axes[1, 0].axhline(y=0.6, color='orange', linestyle='--', alpha=0.5, label='Fair (>0.6)')
        axes[1, 0].legend()
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Chunk Length Distribution
        axes[1, 1].plot(time_grouped['timestamp'], time_grouped['chunk_length_mean'], 'o-', color='blue', alpha=0.7)
        axes[1, 1].set_title('Average Chunk Length Over Time')
        axes[1, 1].set_ylabel('Characters')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Plot 5: Numeric Token Ratio
        axes[2, 0].plot(time_grouped['timestamp'], time_grouped['numeric_token_ratio'], 'o-', color='purple', alpha=0.7)
        axes[2, 0].set_title('Numeric Token Ratio Over Time')
        axes[2, 0].set_ylabel('Ratio')
        axes[2, 0].tick_params(axis='x', rotation=45)
        
        # Plot 6: Total Blocks
        axes[2, 1].plot(time_grouped['timestamp'], time_grouped['total_blocks'], 'o-', color='brown', alpha=0.7)
        axes[2, 1].set_title('Average Blocks Per Page Over Time')
        axes[2, 1].set_ylabel('Block Count')
        axes[2, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_plot:
            plot_file = self.results_dir / f"metrics_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"📊 Saved timeline plot: {plot_file}")
        
        plt.show()
    
    def visualize_distribution_drift(self, df: pd.DataFrame, save_plot: bool = True) -> None:
        """Visualize distribution changes over time"""
        
        if df.empty or len(df) < 10:
            print("Not enough data for distribution analysis")
            return
        
        # Split data into early and recent periods
        mid_point = len(df) // 2
        early_data = df.iloc[:mid_point]
        recent_data = df.iloc[mid_point:]
        
        # Create comparison plots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Distribution Drift Analysis', fontsize=16)
        
        metrics_to_plot = ['text_wer', 'text_cer', 'table_f1', 'chunk_length_mean', 'numeric_token_ratio']
        
        for i, metric in enumerate(metrics_to_plot):
            if metric not in df.columns:
                continue
            
            row = i // 3
            col = i % 3
            
            # Remove NaN values
            early_values = early_data[metric].dropna()
            recent_values = recent_data[metric].dropna()
            
            if len(early_values) > 0 and len(recent_values) > 0:
                # Histogram comparison
                axes[row, col].hist(early_values, alpha=0.5, label=f'Early (n={len(early_values)})', 
                                   bins=15, density=True, color='blue')
                axes[row, col].hist(recent_values, alpha=0.5, label=f'Recent (n={len(recent_values)})', 
                                   bins=15, density=True, color='red')
                
                axes[row, col].set_title(f'{metric} Distribution')
                axes[row, col].set_ylabel('Density')
                axes[row, col].legend()
                
                # Add mean lines
                axes[row, col].axvline(early_values.mean(), color='blue', linestyle='--', alpha=0.8)
                axes[row, col].axvline(recent_values.mean(), color='red', linestyle='--', alpha=0.8)
        
        # Box plot comparison for chunk lengths
        if len(axes[1]) > 2:  # Make sure we have the subplot
            chunk_data = []
            periods = []
            
            for _, row in early_data.iterrows():
                if not pd.isna(row['chunk_length_mean']):
                    chunk_data.append(row['chunk_length_mean'])
                    periods.append('Early')
            
            for _, row in recent_data.iterrows():
                if not pd.isna(row['chunk_length_mean']):
                    chunk_data.append(row['chunk_length_mean'])
                    periods.append('Recent')
            
            if chunk_data:
                box_df = pd.DataFrame({'chunk_length': chunk_data, 'period': periods})
                sns.boxplot(data=box_df, x='period', y='chunk_length', ax=axes[1, 2])
                axes[1, 2].set_title('Chunk Length Distribution Comparison')
        
        plt.tight_layout()
        
        if save_plot:
            plot_file = self.results_dir / f"distribution_drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"📊 Saved drift analysis plot: {plot_file}")
        
        plt.show()
    
    def generate_drift_report(self, drift_results: Dict, df: pd.DataFrame) -> str:
        """Generate a drift analysis report"""
        
        if not drift_results:
            return "# Drift Analysis Report\n\nInsufficient data for drift analysis."
        
        report = f"""# Parsing Quality Drift Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total evaluations**: {len(df)}
- **Date range**: {df['timestamp'].min()} to {df['timestamp'].max()}
- **Metrics analyzed**: {len(drift_results)}

## Drift Detection Results

"""
        
        # Categorize drift results
        significant_improvements = []
        significant_degradations = []
        no_significant_change = []
        
        for metric, results in drift_results.items():
            if results['significant_drift']:
                if results['drift_direction'] == 'improvement':
                    significant_improvements.append((metric, results))
                else:
                    significant_degradations.append((metric, results))
            else:
                no_significant_change.append((metric, results))
        
        # Significant improvements
        if significant_improvements:
            report += "### 🟢 Significant Improvements\n\n"
            for metric, results in significant_improvements:
                report += f"""**{metric}**:
- Recent: {results['recent_mean']:.4f} vs Historical: {results['historical_mean']:.4f}
- Change: {results['relative_change']:+.2%}
- p-value: {results['p_value']:.4f}

"""
        
        # Significant degradations  
        if significant_degradations:
            report += "### 🔴 Significant Degradations\n\n"
            for metric, results in significant_degradations:
                report += f"""**{metric}**:
- Recent: {results['recent_mean']:.4f} vs Historical: {results['historical_mean']:.4f}
- Change: {results['relative_change']:+.2%}
- p-value: {results['p_value']:.4f}

"""
        
        # No significant change
        if no_significant_change:
            report += "### ⚪ Stable Metrics\n\n"
            for metric, results in no_significant_change:
                report += f"""**{metric}**: {results['recent_mean']:.4f} (change: {results['relative_change']:+.2%}, p={results['p_value']:.3f})
"""
        
        # Overall assessment
        report += f"""

## Overall Assessment

"""
        
        if significant_degradations:
            report += "⚠️ **WARNING**: Significant degradation detected in parsing quality.\n"
            report += "**Action required**: Investigate recent changes and consider rollback.\n\n"
        elif significant_improvements:
            report += "✅ **GOOD**: Parsing quality has improved significantly.\n"
            report += "**Recommendation**: Consider deploying these improvements to production.\n\n"
        else:
            report += "✅ **STABLE**: No significant changes in parsing quality detected.\n"
            report += "**Status**: System performance is stable.\n\n"
        
        # Recommendations
        report += """## Recommendations

"""
        
        if any('text_wer' in metric or 'text_cer' in metric for metric, _ in significant_degradations):
            report += "- 🔧 **Text extraction**: Review OCR settings, layout detection, or text processing pipeline\n"
        
        if any('table' in metric for metric, _ in significant_degradations):
            report += "- 📊 **Table extraction**: Check table detection algorithms and parsing logic\n"
        
        if any('chunk_length' in metric for metric, _ in significant_degradations):
            report += "- 📝 **Content segmentation**: Review text chunking and block merging logic\n"
        
        report += """
---
*This report helps track system performance and catch regressions early.*
"""
        
        return report
    
    def run_drift_analysis(self, window_size: int = 5) -> Dict:
        """Run complete drift analysis"""
        
        print("🔍 Running drift analysis...")
        
        # Load historical data
        df = self.load_historical_metrics()
        
        if df.empty:
            print("❌ No historical data available")
            return {}
        
        # Calculate drift metrics
        drift_results = self.calculate_drift_metrics(df, window_size)
        
        if not drift_results:
            print("⚠️ Insufficient data for drift analysis")
            return {}
        
        # Generate report
        report = self.generate_drift_report(drift_results, df)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.results_dir / f"drift_analysis_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Create visualizations
        self.visualize_metrics_over_time(df)
        self.visualize_distribution_drift(df)
        
        print(f"✅ Drift analysis complete!")
        print(f"   📝 Report: {report_file}")
        print(f"   📊 Visualizations saved")
        
        # Print summary
        degradations = sum(1 for r in drift_results.values() 
                         if r['significant_drift'] and r['drift_direction'] == 'degradation')
        improvements = sum(1 for r in drift_results.values() 
                         if r['significant_drift'] and r['drift_direction'] == 'improvement')
        
        print(f"\n📋 Drift Summary:")
        print(f"   🔴 Degradations: {degradations}")
        print(f"   🟢 Improvements: {improvements}")
        print(f"   ⚪ Stable: {len(drift_results) - degradations - improvements}")
        
        return {
            'drift_results': drift_results,
            'report': report,
            'report_file': str(report_file),
            'summary': {
                'degradations': degradations,
                'improvements': improvements,
                'stable': len(drift_results) - degradations - improvements
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Track parsing metrics and detect drift")
    parser.add_argument("--action", choices=["timeline", "drift", "both"], default="both",
                       help="Type of analysis to perform")
    parser.add_argument("--window-size", type=int, default=5,
                       help="Window size for drift detection")
    parser.add_argument("--results-dir", default="evaluation_results",
                       help="Directory containing evaluation results")
    
    args = parser.parse_args()
    
    tracker = MetricsTracker(args.results_dir)
    
    if args.action in ["timeline", "both"]:
        print("📈 Creating timeline visualizations...")
        df = tracker.load_historical_metrics()
        if not df.empty:
            tracker.visualize_metrics_over_time(df)
        else:
            print("❌ No data available for timeline analysis")
    
    if args.action in ["drift", "both"]:
        print("🔍 Running drift detection...")
        result = tracker.run_drift_analysis(args.window_size)
        
        if result:
            # Exit with error code if significant degradations detected
            if result['summary']['degradations'] > 0:
                print("\n❌ DRIFT DETECTED: Significant quality degradations found!")
                exit(1)
            else:
                print("\n✅ NO SIGNIFICANT DRIFT: Quality remains stable or improved")
        else:
            print("⚠️ Could not perform drift analysis")


if __name__ == "__main__":
    main()
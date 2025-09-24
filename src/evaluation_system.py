#!/usr/bin/env python3
# evaluation_system.py
# Complete system for evaluating PDF parsing quality and detecting regressions

import json
import csv
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
from difflib import SequenceMatcher
import re
import statistics
from dataclasses import dataclass
import yaml


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    text_wer: float
    text_cer: float
    table_precision: float
    table_recall: float
    table_f1: float
    chunk_length_mean: float
    chunk_length_std: float
    numeric_token_ratio: float
    total_blocks: int
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'text_wer': self.text_wer,
            'text_cer': self.text_cer,
            'table_precision': self.table_precision,
            'table_recall': self.table_recall,
            'table_f1': self.table_f1,
            'chunk_length_mean': self.chunk_length_mean,
            'chunk_length_std': self.chunk_length_std,
            'numeric_token_ratio': self.numeric_token_ratio,
            'total_blocks': self.total_blocks
        }


class GroundTruthManager:
    """Manage ground truth datasets for evaluation"""
    
    def __init__(self, ground_truth_dir="data/ground_truth"):
        self.ground_truth_dir = Path(ground_truth_dir)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.ground_truth_dir / "text").mkdir(exist_ok=True)
        (self.ground_truth_dir / "tables").mkdir(exist_ok=True)
        (self.ground_truth_dir / "metadata").mkdir(exist_ok=True)
    
    def create_ground_truth_template(self, pdf_name: str, page_num: int, 
                                   parsed_content: Dict) -> None:
        """Create ground truth templates for manual annotation"""
        
        # Text ground truth template
        text_template = {
            "pdf_name": pdf_name,
            "page_number": page_num,
            "created_date": datetime.now().isoformat(),
            "instructions": "Manually correct the extracted text below. Keep structure but fix OCR errors.",
            "blocks": []
        }
        
        # Table ground truth template
        table_template = {
            "pdf_name": pdf_name,
            "page_number": page_num,
            "created_date": datetime.now().isoformat(),
            "instructions": "Manually correct table data. Each table should be a 2D array of strings.",
            "tables": []
        }
        
        # Process parsed content
        for block in parsed_content.get("blocks", []):
            if block["type"] in ["Text", "Title", "List"]:
                text_template["blocks"].append({
                    "block_id": block["block_id"],
                    "type": block["type"],
                    "bbox": block["bbox"],
                    "extracted_text": block["text"],
                    "ground_truth_text": block["text"]  # To be manually corrected
                })
            
            elif block["type"] == "Table" and block.get("table_data"):
                table_template["tables"].append({
                    "block_id": block["block_id"],
                    "bbox": block["bbox"],
                    "extracted_table": block["table_data"],
                    "ground_truth_table": block["table_data"]  # To be manually corrected
                })
        
        # Save templates
        text_file = self.ground_truth_dir / "text" / f"{pdf_name}_page_{page_num:03d}.json"
        table_file = self.ground_truth_dir / "tables" / f"{pdf_name}_page_{page_num:03d}.json"
        
        with open(text_file, 'w', encoding='utf-8') as f:
            json.dump(text_template, f, indent=2, ensure_ascii=False)
        
        if table_template["tables"]:
            with open(table_file, 'w', encoding='utf-8') as f:
                json.dump(table_template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created ground truth templates:")
        print(f"   📝 Text: {text_file}")
        if table_template["tables"]:
            print(f"   📊 Tables: {table_file}")
    
    def load_ground_truth(self, pdf_name: str, page_num: int) -> Tuple[Dict, Dict]:
        """Load ground truth data for a specific page"""
        text_file = self.ground_truth_dir / "text" / f"{pdf_name}_page_{page_num:03d}.json"
        table_file = self.ground_truth_dir / "tables" / f"{pdf_name}_page_{page_num:03d}.json"
        
        text_gt = {}
        table_gt = {}
        
        if text_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                text_gt = json.load(f)
        
        if table_file.exists():
            with open(table_file, 'r', encoding='utf-8') as f:
                table_gt = json.load(f)
        
        return text_gt, table_gt
    
    def list_available_ground_truth(self) -> List[Tuple[str, int]]:
        """List all available ground truth files"""
        available = []
        
        for text_file in (self.ground_truth_dir / "text").glob("*.json"):
            # Parse filename: {pdf_name}_page_{num}.json
            name_parts = text_file.stem.split("_page_")
            if len(name_parts) == 2:
                pdf_name = name_parts[0]
                page_num = int(name_parts[1])
                available.append((pdf_name, page_num))
        
        return sorted(available)


class MetricsCalculator:
    """Calculate various evaluation metrics"""
    
    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate"""
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        
        if len(ref_words) == 0:
            return 0.0 if len(hyp_words) == 0 else 1.0
        
        # Use SequenceMatcher to find edit distance
        matcher = SequenceMatcher(None, ref_words, hyp_words)
        matches = sum(triple.size for triple in matcher.get_matching_blocks())
        
        # WER = (S + D + I) / N where S=substitutions, D=deletions, I=insertions, N=reference length
        wer = 1.0 - (matches / len(ref_words))
        return max(0.0, min(1.0, wer))
    
    @staticmethod
    def calculate_cer(reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate"""
        if len(reference) == 0:
            return 0.0 if len(hypothesis) == 0 else 1.0
        
        matcher = SequenceMatcher(None, reference, hypothesis)
        matches = sum(triple.size for triple in matcher.get_matching_blocks())
        
        cer = 1.0 - (matches / len(reference))
        return max(0.0, min(1.0, cer))
    
    @staticmethod
    def calculate_table_metrics(ground_truth_table: List[List[str]], 
                              extracted_table: List[List[str]]) -> Tuple[float, float, float]:
        """Calculate precision, recall, and F1 for table extraction"""
        if not ground_truth_table or not extracted_table:
            return 0.0, 0.0, 0.0
        
        # Flatten tables to compare individual cells
        gt_cells = set()
        ext_cells = set()
        
        for i, row in enumerate(ground_truth_table):
            for j, cell in enumerate(row):
                gt_cells.add((i, j, str(cell).strip().lower()))
        
        for i, row in enumerate(extracted_table):
            for j, cell in enumerate(row):
                ext_cells.add((i, j, str(cell).strip().lower()))
        
        if len(ext_cells) == 0:
            precision = 0.0
        else:
            precision = len(gt_cells & ext_cells) / len(ext_cells)
        
        if len(gt_cells) == 0:
            recall = 0.0
        else:
            recall = len(gt_cells & ext_cells) / len(gt_cells)
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        
        return precision, recall, f1


class ParsingEvaluator:
    """Main evaluation system for PDF parsing quality"""
    
    def __init__(self, parsed_dir="data/parsed/converted", 
                 ground_truth_dir="data/ground_truth",
                 results_dir="evaluation_results"):
        self.parsed_dir = Path(parsed_dir)
        self.ground_truth_manager = GroundTruthManager(ground_truth_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
    
    def create_ground_truth_templates(self, pdf_name: str, max_pages: int = 3) -> None:
        """Create ground truth templates for the first few pages of a PDF"""
        
        print(f"🔍 Creating ground truth templates for {pdf_name} (first {max_pages} pages)...")
        
        # Load parsed JSON data
        json_file = self.parsed_dir / "json" / f"{pdf_name}.json"
        if not json_file.exists():
            print(f"❌ Parsed JSON file not found: {json_file}")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        created_count = 0
        for page_data in parsed_data["pages"][:max_pages]:
            page_num = page_data["page_number"]
            
            # Create combined content for this page
            page_content = {
                "blocks": []
            }
            
            # Add all content types as blocks
            for content_type in ["titles", "text_blocks", "lists", "tables", "figures"]:
                for item in page_data["content"][content_type]:
                    block = {
                        "block_id": item["block_id"],
                        "type": content_type.rstrip('s').title(),  # titles -> Title
                        "bbox": item["bbox"],
                        "text": item["text"]
                    }
                    
                    if content_type == "tables" and "table_data" in item:
                        block["table_data"] = item["table_data"]
                    
                    page_content["blocks"].append(block)
            
            self.ground_truth_manager.create_ground_truth_template(
                pdf_name, page_num, page_content
            )
            created_count += 1
        
        print(f"✅ Created {created_count} ground truth templates")
        print(f"📝 Next steps:")
        print(f"   1. Edit the JSON files in data/ground_truth/text/ to correct text errors")
        print(f"   2. Edit the JSON files in data/ground_truth/tables/ to correct table data")
        print(f"   3. Run evaluation after manual corrections are complete")
    
    def evaluate_parsing_quality(self, pdf_name: str = None) -> Dict[str, EvaluationMetrics]:
        """Evaluate parsing quality against ground truth"""
        
        print(f"📊 Evaluating parsing quality...")
        
        available_gt = self.ground_truth_manager.list_available_ground_truth()
        if not available_gt:
            print("❌ No ground truth data found!")
            print("Create ground truth templates first with create_ground_truth_templates()")
            return {}
        
        if pdf_name:
            available_gt = [(name, page) for name, page in available_gt if name == pdf_name]
        
        print(f"Found ground truth for {len(available_gt)} pages")
        
        results = {}
        
        for gt_pdf_name, page_num in available_gt:
            print(f"  Evaluating {gt_pdf_name} page {page_num}...")
            
            # Load ground truth
            text_gt, table_gt = self.ground_truth_manager.load_ground_truth(gt_pdf_name, page_num)
            
            # Load parsed data
            parsed_file = self.parsed_dir / "json" / f"{gt_pdf_name}.json"
            if not parsed_file.exists():
                print(f"    ❌ Parsed file not found: {parsed_file}")
                continue
            
            with open(parsed_file, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
            
            # Find the corresponding page
            page_data = None
            for page in parsed_data["pages"]:
                if page["page_number"] == page_num:
                    page_data = page
                    break
            
            if not page_data:
                print(f"    ❌ Page {page_num} not found in parsed data")
                continue
            
            # Calculate metrics
            metrics = self._calculate_page_metrics(text_gt, table_gt, page_data)
            results[f"{gt_pdf_name}_page_{page_num}"] = metrics
        
        return results
    
    def _calculate_page_metrics(self, text_gt: Dict, table_gt: Dict, page_data: Dict) -> EvaluationMetrics:
        """Calculate metrics for a single page"""
        
        # Text metrics
        text_wer_scores = []
        text_cer_scores = []
        
        if text_gt.get("blocks"):
            for gt_block in text_gt["blocks"]:
                gt_text = gt_block.get("ground_truth_text", "")
                block_id = gt_block["block_id"]
                
                # Find corresponding extracted text
                extracted_text = ""
                for content_type in page_data["content"].values():
                    if isinstance(content_type, list):
                        for item in content_type:
                            if item.get("block_id") == block_id:
                                extracted_text = item.get("text", "")
                                break
                
                if gt_text.strip():
                    wer = self.metrics_calculator.calculate_wer(gt_text, extracted_text)
                    cer = self.metrics_calculator.calculate_cer(gt_text, extracted_text)
                    text_wer_scores.append(wer)
                    text_cer_scores.append(cer)
        
        # Table metrics
        table_precisions = []
        table_recalls = []
        table_f1s = []
        
        if table_gt.get("tables"):
            for gt_table in table_gt["tables"]:
                gt_data = gt_table.get("ground_truth_table", [])
                block_id = gt_table["block_id"]
                
                # Find corresponding extracted table
                extracted_data = []
                for table_item in page_data["content"]["tables"]:
                    if table_item.get("block_id") == block_id:
                        extracted_data = table_item.get("table_data", [])
                        break
                
                if gt_data:
                    precision, recall, f1 = self.metrics_calculator.calculate_table_metrics(
                        gt_data, extracted_data
                    )
                    table_precisions.append(precision)
                    table_recalls.append(recall)
                    table_f1s.append(f1)
        
        # Distribution metrics
        all_text = []
        numeric_tokens = 0
        total_tokens = 0
        
        for content_type in page_data["content"].values():
            if isinstance(content_type, list):
                for item in content_type:
                    text = item.get("text", "")
                    if text.strip():
                        all_text.append(text)
                        
                        # Count tokens for numeric ratio
                        tokens = re.findall(r'\b\w+\b', text.lower())
                        for token in tokens:
                            total_tokens += 1
                            if re.match(r'^\d+\.?\d*$', token):
                                numeric_tokens += 1
        
        # Calculate chunk statistics
        chunk_lengths = [len(text) for text in all_text]
        chunk_length_mean = statistics.mean(chunk_lengths) if chunk_lengths else 0
        chunk_length_std = statistics.stdev(chunk_lengths) if len(chunk_lengths) > 1 else 0
        
        numeric_token_ratio = numeric_tokens / total_tokens if total_tokens > 0 else 0
        
        return EvaluationMetrics(
            text_wer=statistics.mean(text_wer_scores) if text_wer_scores else 1.0,
            text_cer=statistics.mean(text_cer_scores) if text_cer_scores else 1.0,
            table_precision=statistics.mean(table_precisions) if table_precisions else 0.0,
            table_recall=statistics.mean(table_recalls) if table_recalls else 0.0,
            table_f1=statistics.mean(table_f1s) if table_f1s else 0.0,
            chunk_length_mean=chunk_length_mean,
            chunk_length_std=chunk_length_std,
            numeric_token_ratio=numeric_token_ratio,
            total_blocks=len(page_data.get("content", {}).get("text_blocks", []))
        )
    
    def generate_evaluation_report(self, results: Dict[str, EvaluationMetrics]) -> str:
        """Generate comprehensive evaluation report"""
        
        if not results:
            return "No evaluation results available."
        
        # Calculate aggregate statistics
        all_metrics = list(results.values())
        
        avg_metrics = {
            'text_wer': statistics.mean([m.text_wer for m in all_metrics]),
            'text_cer': statistics.mean([m.text_cer for m in all_metrics]),
            'table_precision': statistics.mean([m.table_precision for m in all_metrics]),
            'table_recall': statistics.mean([m.table_recall for m in all_metrics]),
            'table_f1': statistics.mean([m.table_f1 for m in all_metrics]),
            'chunk_length_mean': statistics.mean([m.chunk_length_mean for m in all_metrics]),
            'numeric_token_ratio': statistics.mean([m.numeric_token_ratio for m in all_metrics])
        }
        
        report = f"""# PDF Parsing Quality Evaluation Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Pages evaluated**: {len(results)}
- **Overall text quality**: {'🟢 Good' if avg_metrics['text_wer'] < 0.1 else '🟡 Fair' if avg_metrics['text_wer'] < 0.3 else '🔴 Poor'}
- **Overall table quality**: {'🟢 Good' if avg_metrics['table_f1'] > 0.8 else '🟡 Fair' if avg_metrics['table_f1'] > 0.5 else '🔴 Poor'}

## Aggregate Metrics

### Text Extraction Quality
- **Word Error Rate (WER)**: {avg_metrics['text_wer']:.3f} ({'lower is better, <0.1 is good'})
- **Character Error Rate (CER)**: {avg_metrics['text_cer']:.3f} ({'lower is better, <0.05 is good'})

### Table Extraction Quality  
- **Precision**: {avg_metrics['table_precision']:.3f} ({'higher is better, >0.8 is good'})
- **Recall**: {avg_metrics['table_recall']:.3f} ({'higher is better, >0.8 is good'})
- **F1-Score**: {avg_metrics['table_f1']:.3f} ({'higher is better, >0.8 is good'})

### Content Distribution
- **Average chunk length**: {avg_metrics['chunk_length_mean']:.1f} characters
- **Numeric token ratio**: {avg_metrics['numeric_token_ratio']:.3f} ({'proportion of tokens that are numbers'})

## Per-Page Results

"""
        
        for page_name, metrics in results.items():
            report += f"""
### {page_name}
- WER: {metrics.text_wer:.3f} | CER: {metrics.text_cer:.3f}
- Table P/R/F1: {metrics.table_precision:.3f}/{metrics.table_recall:.3f}/{metrics.table_f1:.3f}
- Blocks: {metrics.total_blocks} | Avg chunk: {metrics.chunk_length_mean:.1f} chars
"""
        
        report += f"""

## Quality Thresholds
- ✅ **Pass**: WER < 0.2 AND Table F1 > 0.6
- ⚠️  **Warning**: WER < 0.4 AND Table F1 > 0.4  
- ❌ **Fail**: WER >= 0.4 OR Table F1 <= 0.4

## Recommendations
"""
        
        if avg_metrics['text_wer'] > 0.3:
            report += "- 🔧 **Text extraction needs improvement**: Consider better OCR preprocessing or layout detection\n"
        
        if avg_metrics['table_f1'] < 0.6:
            report += "- 📊 **Table extraction needs improvement**: Review table detection algorithm or add more training data\n"
        
        if avg_metrics['chunk_length_mean'] < 50:
            report += "- 📝 **Chunks may be too fragmented**: Consider merging adjacent text blocks\n"
        
        if avg_metrics['numeric_token_ratio'] < 0.05:
            report += "- 🔢 **Low numeric content**: Verify financial/quantitative data extraction\n"
        
        report += "\n---\n*This report helps track parsing quality over time and catch regressions.*"
        
        return report
    
    def save_metrics(self, results: Dict[str, EvaluationMetrics], 
                    timestamp: str = None) -> Path:
        """Save metrics to JSON file with timestamp"""
        
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        metrics_data = {
            'timestamp': timestamp,
            'results': {name: metrics.to_dict() for name, metrics in results.items()}
        }
        
        metrics_file = self.results_dir / f"metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        return metrics_file
    
    def visualize_metrics(self, results: Dict[str, EvaluationMetrics], 
                         save_plots: bool = True) -> None:
        """Create visualizations of parsing metrics"""
        
        if not results:
            print("No results to visualize")
            return
        
        # Prepare data
        pages = list(results.keys())
        metrics = list(results.values())
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('PDF Parsing Quality Metrics', fontsize=16)
        
        # Text quality metrics
        wer_scores = [m.text_wer for m in metrics]
        cer_scores = [m.text_cer for m in metrics]
        
        axes[0, 0].bar(range(len(pages)), wer_scores, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('Word Error Rate (Lower = Better)')
        axes[0, 0].set_ylabel('WER')
        axes[0, 0].axhline(y=0.1, color='green', linestyle='--', alpha=0.7, label='Good (<0.1)')
        axes[0, 0].axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='Fair (<0.3)')
        axes[0, 0].legend()
        
        axes[0, 1].bar(range(len(pages)), cer_scores, color='lightcoral', alpha=0.7)
        axes[0, 1].set_title('Character Error Rate (Lower = Better)')
        axes[0, 1].set_ylabel('CER')
        axes[0, 1].axhline(y=0.05, color='green', linestyle='--', alpha=0.7, label='Good (<0.05)')
        axes[0, 1].axhline(y=0.15, color='orange', linestyle='--', alpha=0.7, label='Fair (<0.15)')
        axes[0, 1].legend()
        
        # Table quality metrics
        table_f1_scores = [m.table_f1 for m in metrics]
        axes[0, 2].bar(range(len(pages)), table_f1_scores, color='lightgreen', alpha=0.7)
        axes[0, 2].set_title('Table F1-Score (Higher = Better)')
        axes[0, 2].set_ylabel('F1-Score')
        axes[0, 2].axhline(y=0.8, color='green', linestyle='--', alpha=0.7, label='Good (>0.8)')
        axes[0, 2].axhline(y=0.6, color='orange', linestyle='--', alpha=0.7, label='Fair (>0.6)')
        axes[0, 2].legend()
        
        # Distribution metrics
        chunk_lengths = [m.chunk_length_mean for m in metrics]
        axes[1, 0].bar(range(len(pages)), chunk_lengths, color='gold', alpha=0.7)
        axes[1, 0].set_title('Average Chunk Length')
        axes[1, 0].set_ylabel('Characters')
        
        numeric_ratios = [m.numeric_token_ratio for m in metrics]
        axes[1, 1].bar(range(len(pages)), numeric_ratios, color='mediumpurple', alpha=0.7)
        axes[1, 1].set_title('Numeric Token Ratio')
        axes[1, 1].set_ylabel('Ratio')
        
        # Overall quality score (combined metric)
        quality_scores = [1 - (m.text_wer + m.text_cer)/2 + m.table_f1 for m in metrics]
        axes[1, 2].bar(range(len(pages)), quality_scores, color='orange', alpha=0.7)
        axes[1, 2].set_title('Combined Quality Score')
        axes[1, 2].set_ylabel('Score')
        
        # Format x-axes
        for ax in axes.flat:
            ax.set_xticks(range(len(pages)))
            ax.set_xticklabels([p.split('_page_')[0][-10:] + f'_p{p.split("_page_")[1]}' 
                               for p in pages], rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_plots:
            plot_file = self.results_dir / f"metrics_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"📊 Saved metrics plot: {plot_file}")
        
        plt.show()
    
    def run_full_evaluation(self, pdf_name: str = None) -> Dict[str, Any]:
        """Run complete evaluation pipeline"""
        
        print("🚀 Running full PDF parsing evaluation...")
        
        # Evaluate parsing quality
        results = self.evaluate_parsing_quality(pdf_name)
        
        if not results:
            print("❌ No evaluation results generated")
            return {}
        
        # Generate report
        report = self.generate_evaluation_report(results)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics_file = self.save_metrics(results, timestamp)
        
        report_file = self.results_dir / f"evaluation_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Create visualizations
        self.visualize_metrics(results)
        
        print(f"✅ Evaluation complete!")
        print(f"   📊 Metrics: {metrics_file}")
        print(f"   📝 Report: {report_file}")
        print(f"   📈 Visualizations saved")
        
        return {
            'results': results,
            'report': report,
            'metrics_file': str(metrics_file),
            'report_file': str(report_file)
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluate PDF parsing quality")
    parser.add_argument("--action", choices=["create-gt", "evaluate"], required=True,
                       help="Action to perform")
    parser.add_argument("--pdf", help="PDF name to process (optional)")
    parser.add_argument("--max-pages", type=int, default=3, 
                       help="Max pages for ground truth creation")
    parser.add_argument("--parsed-dir", default="data/parsed/converted",
                       help="Directory with parsed results")
    parser.add_argument("--ground-truth-dir", default="data/ground_truth",
                       help="Directory for ground truth data")
    
    args = parser.parse_args()
    
    evaluator = ParsingEvaluator(args.parsed_dir, args.ground_truth_dir)
    
    if args.action == "create-gt":
        if not args.pdf:
            print("❌ PDF name required for ground truth creation")
            print("Available PDFs:")
            json_dir = Path(args.parsed_dir) / "json"
            for json_file in json_dir.glob("*.json"):
                print(f"  - {json_file.stem}")
            return
        
        evaluator.create_ground_truth_templates(args.pdf, args.max_pages)
        
    elif args.action == "evaluate":
        results = evaluator.run_full_evaluation(args.pdf)
        
        if results:
            print(f"\n📋 Quick Summary:")
            avg_wer = sum(m.text_wer for m in results['results'].values()) / len(results['results'])
            avg_table_f1 = sum(m.table_f1 for m in results['results'].values()) / len(results['results'])
            
            status = "🟢 PASS" if avg_wer < 0.2 and avg_table_f1 > 0.6 else "⚠️  WARN" if avg_wer < 0.4 and avg_table_f1 > 0.4 else "❌ FAIL"
            print(f"   Status: {status}")
            print(f"   Average WER: {avg_wer:.3f}")
            print(f"   Average Table F1: {avg_table_f1:.3f}")


if __name__ == "__main__":
    main()
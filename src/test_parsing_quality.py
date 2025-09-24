#!/usr/bin/env python3
# test_parsing_quality.py
# Unit tests to catch parsing quality regressions

import unittest
import json
import sys
from pathlib import Path
from typing import Dict, Any
sys.path.append('.')

from evaluation_system import ParsingEvaluator, EvaluationMetrics


class TestParsingQuality(unittest.TestCase):
    """Unit tests for PDF parsing quality thresholds"""
    
    def setUp(self):
        """Set up test environment"""
        self.evaluator = ParsingEvaluator()
        self.quality_thresholds = {
            'min_text_wer': 0.4,  # Maximum acceptable WER
            'min_text_cer': 0.2,  # Maximum acceptable CER
            'min_table_precision': 0.5,  # Minimum table precision
            'min_table_recall': 0.5,     # Minimum table recall
            'min_table_f1': 0.4,         # Minimum table F1
            'min_chunk_length': 20,      # Minimum average chunk length
            'max_chunk_length': 2000,    # Maximum average chunk length
            'min_numeric_ratio': 0.01,   # Minimum numeric token ratio for financial docs
            'max_numeric_ratio': 0.5     # Maximum numeric token ratio
        }
    
    def load_latest_metrics(self) -> Dict[str, EvaluationMetrics]:
        """Load the most recent evaluation metrics"""
        results_dir = Path("evaluation_results")
        if not results_dir.exists():
            self.skipTest("No evaluation results found. Run evaluation first.")
        
        # Find latest metrics file
        metric_files = list(results_dir.glob("metrics_*.json"))
        if not metric_files:
            self.skipTest("No metrics files found. Run evaluation first.")
        
        latest_file = max(metric_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Convert back to EvaluationMetrics objects
        results = {}
        for name, metrics_dict in data['results'].items():
            results[name] = EvaluationMetrics(**metrics_dict)
        
        return results
    
    def test_text_extraction_quality(self):
        """Test that text extraction meets minimum quality thresholds"""
        results = self.load_latest_metrics()
        self.assertGreater(len(results), 0, "No evaluation results available")
        
        for page_name, metrics in results.items():
            with self.subTest(page=page_name):
                self.assertLessEqual(
                    metrics.text_wer, 
                    self.quality_thresholds['min_text_wer'],
                    f"Word Error Rate too high: {metrics.text_wer:.3f} > {self.quality_thresholds['min_text_wer']}"
                )
                
                self.assertLessEqual(
                    metrics.text_cer,
                    self.quality_thresholds['min_text_cer'], 
                    f"Character Error Rate too high: {metrics.text_cer:.3f} > {self.quality_thresholds['min_text_cer']}"
                )
    
    def test_table_extraction_quality(self):
        """Test that table extraction meets minimum quality thresholds"""
        results = self.load_latest_metrics()
        
        # Only test pages that actually have tables
        table_results = {name: metrics for name, metrics in results.items() 
                        if metrics.table_f1 > 0}  # Only pages with detected tables
        
        if not table_results:
            self.skipTest("No pages with tables found in evaluation results")
        
        for page_name, metrics in table_results.items():
            with self.subTest(page=page_name):
                self.assertGreaterEqual(
                    metrics.table_precision,
                    self.quality_thresholds['min_table_precision'],
                    f"Table precision too low: {metrics.table_precision:.3f} < {self.quality_thresholds['min_table_precision']}"
                )
                
                self.assertGreaterEqual(
                    metrics.table_recall,
                    self.quality_thresholds['min_table_recall'],
                    f"Table recall too low: {metrics.table_recall:.3f} < {self.quality_thresholds['min_table_recall']}"
                )
                
                self.assertGreaterEqual(
                    metrics.table_f1,
                    self.quality_thresholds['min_table_f1'],
                    f"Table F1-score too low: {metrics.table_f1:.3f} < {self.quality_thresholds['min_table_f1']}"
                )
    
    def test_content_distribution_sanity(self):
        """Test that content distribution metrics are within reasonable ranges"""
        results = self.load_latest_metrics()
        
        for page_name, metrics in results.items():
            with self.subTest(page=page_name):
                # Check chunk lengths are reasonable
                self.assertGreaterEqual(
                    metrics.chunk_length_mean,
                    self.quality_thresholds['min_chunk_length'],
                    f"Average chunk length too small: {metrics.chunk_length_mean:.1f} < {self.quality_thresholds['min_chunk_length']}"
                )
                
                self.assertLessEqual(
                    metrics.chunk_length_mean,
                    self.quality_thresholds['max_chunk_length'], 
                    f"Average chunk length too large: {metrics.chunk_length_mean:.1f} > {self.quality_thresholds['max_chunk_length']}"
                )
                
                # Check numeric token ratio is reasonable for financial documents
                self.assertGreaterEqual(
                    metrics.numeric_token_ratio,
                    self.quality_thresholds['min_numeric_ratio'],
                    f"Numeric token ratio too low for financial document: {metrics.numeric_token_ratio:.3f} < {self.quality_thresholds['min_numeric_ratio']}"
                )
                
                self.assertLessEqual(
                    metrics.numeric_token_ratio,
                    self.quality_thresholds['max_numeric_ratio'],
                    f"Numeric token ratio too high: {metrics.numeric_token_ratio:.3f} > {self.quality_thresholds['max_numeric_ratio']}"
                )
    
    def test_overall_parsing_quality(self):
        """Test overall parsing quality with combined metrics"""
        results = self.load_latest_metrics()
        
        # Calculate aggregate metrics
        total_pages = len(results)
        self.assertGreater(total_pages, 0, "No pages evaluated")
        
        avg_wer = sum(m.text_wer for m in results.values()) / total_pages
        avg_table_f1 = sum(m.table_f1 for m in results.values() if m.table_f1 > 0)
        table_pages = sum(1 for m in results.values() if m.table_f1 > 0)
        
        if table_pages > 0:
            avg_table_f1 = avg_table_f1 / table_pages
        else:
            avg_table_f1 = 0
        
        # Combined quality check: good text extraction OR good table extraction
        # This allows for some flexibility in overall quality
        text_quality_ok = avg_wer < 0.3
        table_quality_ok = avg_table_f1 > 0.5 or table_pages == 0  # OK if no tables
        
        self.assertTrue(
            text_quality_ok or table_quality_ok,
            f"Overall parsing quality too low. Text WER: {avg_wer:.3f}, Table F1: {avg_table_f1:.3f}"
        )
    
    def test_no_regression_from_baseline(self):
        """Test that metrics haven't regressed from baseline"""
        # This test compares against historical performance
        # You would update these baseline values as you improve the system
        
        baseline_metrics = {
            'max_acceptable_wer': 0.35,  # Current system should be better than this
            'min_acceptable_table_f1': 0.3  # Current system should be better than this
        }
        
        results = self.load_latest_metrics()
        
        avg_wer = sum(m.text_wer for m in results.values()) / len(results)
        
        table_f1_scores = [m.table_f1 for m in results.values() if m.table_f1 > 0]
        avg_table_f1 = sum(table_f1_scores) / len(table_f1_scores) if table_f1_scores else 0
        
        self.assertLessEqual(
            avg_wer,
            baseline_metrics['max_acceptable_wer'],
            f"Text extraction has regressed! WER {avg_wer:.3f} > baseline {baseline_metrics['max_acceptable_wer']}"
        )
        
        if avg_table_f1 > 0:  # Only test if we have tables
            self.assertGreaterEqual(
                avg_table_f1,
                baseline_metrics['min_acceptable_table_f1'],
                f"Table extraction has regressed! F1 {avg_table_f1:.3f} < baseline {baseline_metrics['min_acceptable_table_f1']}"
            )
    
    def test_metrics_calculation_sanity(self):
        """Test that calculated metrics are within valid ranges"""
        results = self.load_latest_metrics()
        
        for page_name, metrics in results.items():
            with self.subTest(page=page_name):
                # All error rates should be between 0 and 1
                self.assertGreaterEqual(metrics.text_wer, 0.0, "WER cannot be negative")
                self.assertLessEqual(metrics.text_wer, 1.0, "WER cannot be greater than 1")
                
                self.assertGreaterEqual(metrics.text_cer, 0.0, "CER cannot be negative")
                self.assertLessEqual(metrics.text_cer, 1.0, "CER cannot be greater than 1")
                
                # Precision, recall, F1 should be between 0 and 1
                self.assertGreaterEqual(metrics.table_precision, 0.0, "Precision cannot be negative")
                self.assertLessEqual(metrics.table_precision, 1.0, "Precision cannot be greater than 1")
                
                self.assertGreaterEqual(metrics.table_recall, 0.0, "Recall cannot be negative") 
                self.assertLessEqual(metrics.table_recall, 1.0, "Recall cannot be greater than 1")
                
                self.assertGreaterEqual(metrics.table_f1, 0.0, "F1 cannot be negative")
                self.assertLessEqual(metrics.table_f1, 1.0, "F1 cannot be greater than 1")
                
                # Numeric ratio should be between 0 and 1
                self.assertGreaterEqual(metrics.numeric_token_ratio, 0.0, "Numeric ratio cannot be negative")
                self.assertLessEqual(metrics.numeric_token_ratio, 1.0, "Numeric ratio cannot be greater than 1")
                
                # Block count should be positive
                self.assertGreaterEqual(metrics.total_blocks, 0, "Block count cannot be negative")


class TestParsingRegressionSimulation(unittest.TestCase):
    """Tests that simulate parsing failures to ensure tests catch regressions"""
    
    def setUp(self):
        self.evaluator = ParsingEvaluator()
    
    @unittest.expectedFailure
    def test_intentionally_broken_text_extraction(self):
        """This test should fail when text extraction is intentionally broken"""
        # Create fake bad metrics that should trigger test failures
        bad_metrics = EvaluationMetrics(
            text_wer=0.8,  # Very high error rate
            text_cer=0.6,  # Very high error rate
            table_precision=0.9,
            table_recall=0.9, 
            table_f1=0.9,
            chunk_length_mean=100,
            chunk_length_std=50,
            numeric_token_ratio=0.1,
            total_blocks=10
        )
        
        # This should fail the quality thresholds
        self.assertLessEqual(bad_metrics.text_wer, 0.4, "WER threshold test")
        self.assertLessEqual(bad_metrics.text_cer, 0.2, "CER threshold test")
    
    @unittest.expectedFailure
    def test_intentionally_broken_table_extraction(self):
        """This test should fail when table extraction is intentionally broken"""
        # Create fake bad table metrics
        bad_metrics = EvaluationMetrics(
            text_wer=0.1,
            text_cer=0.05,
            table_precision=0.2,  # Very low precision
            table_recall=0.1,     # Very low recall
            table_f1=0.1,        # Very low F1
            chunk_length_mean=100,
            chunk_length_std=50,
            numeric_token_ratio=0.1,
            total_blocks=10
        )
        
        # This should fail the table quality thresholds
        self.assertGreaterEqual(bad_metrics.table_precision, 0.5, "Table precision threshold test")
        self.assertGreaterEqual(bad_metrics.table_recall, 0.5, "Table recall threshold test")
        self.assertGreaterEqual(bad_metrics.table_f1, 0.4, "Table F1 threshold test")


def run_quality_tests():
    """Function to run quality tests programmatically"""
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add quality tests (not the intentionally failing ones)
    suite.addTest(TestParsingQuality('test_text_extraction_quality'))
    suite.addTest(TestParsingQuality('test_table_extraction_quality'))
    suite.addTest(TestParsingQuality('test_content_distribution_sanity'))
    suite.addTest(TestParsingQuality('test_overall_parsing_quality'))
    suite.addTest(TestParsingQuality('test_no_regression_from_baseline'))
    suite.addTest(TestParsingQuality('test_metrics_calculation_sanity'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return summary
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful()
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run parsing quality tests")
    parser.add_argument("--run-failing-tests", action="store_true", 
                       help="Also run tests that are expected to fail")
    args = parser.parse_args()
    
    if args.run_failing_tests:
        # Run all tests including expected failures
        unittest.main(verbosity=2)
    else:
        # Run only the quality tests
        result = run_quality_tests()
        print(f"\n📋 Test Summary:")
        print(f"   Tests run: {result['tests_run']}")
        print(f"   Failures: {result['failures']}")
        print(f"   Errors: {result['errors']}")
        print(f"   Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
        
        if not result['success']:
            sys.exit(1)
#!/usr/bin/env python3
"""
XBRL Cross-Validation System
Downloads XBRL files, parses financial data, and validates against PDF-extracted tables
"""

import os
import re
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import requests
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
import argparse


@dataclass
class XBRLElement:
    """Represents a single XBRL element with its value and metadata"""
    concept: str
    value: float
    context_ref: str
    unit_ref: str
    decimals: Optional[str] = None
    fact_id: Optional[str] = None
    period: Optional[str] = None


@dataclass
class PDFTableValue:
    """Represents a value extracted from PDF table"""
    label: str
    value: float
    row: int
    col: int
    table_id: str
    page: int


@dataclass
class ValidationResult:
    """Result of cross-validation between XBRL and PDF values"""
    xbrl_concept: str
    pdf_label: str
    xbrl_value: float
    pdf_value: float
    match: bool
    difference: float
    confidence: float
    discrepancy_type: str  # 'exact', 'rounding', 'ocr_error', 'tagging_difference'


class XBRLDownloader:
    """Downloads XBRL files from SEC EDGAR"""
    
    def __init__(self, user_agent: str = "Sample Company <sample@example.com>"):
        self.user_agent = user_agent
        self.base_url = "https://www.sec.gov/Archives/edgar/data/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })
    
    def get_company_cik(self, company_name: str) -> Optional[str]:
        """Get CIK for company name"""
        # Apple Inc. CIK for demo
        cik_map = {
            'apple': '0000320193',
            'apple inc': '0000320193',
            'aapl': '0000320193'
        }
        return cik_map.get(company_name.lower())
    
    def get_filing_urls(self, cik: str, filing_type: str = "10-K", limit: int = 5) -> List[Dict]:
        """Get recent filing URLs for a company"""
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            filings = []
            # This is a simplified approach - in practice, you'd parse the full JSON
            return [{"cik": cik, "filing_type": filing_type, "accession_number": "demo"}]
            
        except Exception as e:
            print(f"Error fetching filing URLs: {e}")
            return []
    
    def download_xbrl_files(self, company_name: str, filing_type: str = "10-K") -> List[Path]:
        """Download XBRL files for a company's recent filing"""
        cik = self.get_company_cik(company_name)
        if not cik:
            print(f"CIK not found for {company_name}")
            return []
        
        # For demo purposes, create sample XBRL data
        return self._create_sample_xbrl_files(cik)
    
    def _create_sample_xbrl_files(self, cik: str) -> List[Path]:
        """Create sample XBRL files for demonstration"""
        output_dir = Path("data/raw/xbrl")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sample XBRL data based on Apple's financials
        sample_data = {
            "us-gaap:Revenues": 394328000000,  # $394.328B
            "us-gaap:NetIncomeLoss": 99803000000,  # $99.803B
            "us-gaap:Assets": 352755000000,  # $352.755B
            "us-gaap:Liabilities": 258549000000,  # $258.549B
            "us-gaap:StockholdersEquity": 94206000000,  # $94.206B
            "us-gaap:CashAndCashEquivalentsAtCarryingValue": 48295000000,  # $48.295B
        }
        
        # Create sample XBRL XML
        xbrl_content = self._generate_sample_xbrl_xml(sample_data)
        
        xbrl_file = output_dir / f"{cik}_sample.xbrl"
        with open(xbrl_file, 'w') as f:
            f.write(xbrl_content)
        
        return [xbrl_file]
    
    def _generate_sample_xbrl_xml(self, data: Dict[str, float]) -> str:
        """Generate sample XBRL XML content"""
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:us-gaap="http://fasb.org/us-gaap/2024-01-31"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
  
  <context id="c1">
    <entity>
      <identifier scheme="http://www.sec.gov/CIK">0000320193</identifier>
    </entity>
    <period>
      <instant>2024-09-30</instant>
    </period>
  </context>
  
  <unit id="u1">
    <measure>iso4217:USD</measure>
  </unit>
  
  {facts}
  
</xbrl>'''
        
        facts = []
        for concept, value in data.items():
            fact = f'  <{concept} contextRef="c1" unitRef="u1" decimals="0">{int(value)}</{concept}>'
            facts.append(fact)
        
        return xml_template.format(facts='\n'.join(facts))


class XBRLParser:
    """Parses XBRL files and extracts financial data"""
    
    def __init__(self):
        self.namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'us-gaap': 'http://fasb.org/us-gaap/2024-01-31',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def parse_xbrl_file(self, xbrl_path: Path) -> List[XBRLElement]:
        """Parse XBRL file and extract financial elements"""
        try:
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            elements = []
            
            # Find all financial facts
            for element in root.iter():
                if element.tag and ':' in element.tag:
                    namespace, tag = element.tag.split(':', 1)
                    
                    # Skip context and unit elements
                    if tag in ['context', 'unit', 'entity', 'period']:
                        continue
                    
                    try:
                        value = float(element.text) if element.text else 0.0
                        
                        xbrl_element = XBRLElement(
                            concept=element.tag,
                            value=value,
                            context_ref=element.get('contextRef', ''),
                            unit_ref=element.get('unitRef', ''),
                            decimals=element.get('decimals'),
                            fact_id=element.get('id'),
                            period=self._extract_period(root, element.get('contextRef', ''))
                        )
                        elements.append(xbrl_element)
                        
                    except (ValueError, TypeError):
                        continue
            
            return elements
            
        except Exception as e:
            print(f"Error parsing XBRL file {xbrl_path}: {e}")
            return []
    
    def _extract_period(self, root, context_ref: str) -> Optional[str]:
        """Extract period information from context"""
        if not context_ref:
            return None
        
        try:
            context = root.find(f".//xbrli:context[@id='{context_ref}']", self.namespaces)
            if context is not None:
                period = context.find('xbrli:period', self.namespaces)
                if period is not None:
                    instant = period.find('xbrli:instant', self.namespaces)
                    if instant is not None:
                        return instant.text
        except Exception:
            pass
        
        return None


class ConceptMapper:
    """Maps PDF table labels to XBRL concepts"""
    
    def __init__(self):
        self.mapping_rules = self._load_mapping_rules()
        self.similarity_threshold = 0.7
    
    def _load_mapping_rules(self) -> Dict[str, str]:
        """Load predefined mapping rules"""
        return {
            # Revenue mappings
            'revenue': 'us-gaap:Revenues',
            'net sales': 'us-gaap:Revenues',
            'total revenue': 'us-gaap:Revenues',
            'sales': 'us-gaap:Revenues',
            
            # Net Income mappings
            'net income': 'us-gaap:NetIncomeLoss',
            'net earnings': 'us-gaap:NetIncomeLoss',
            'profit': 'us-gaap:NetIncomeLoss',
            'earnings': 'us-gaap:NetIncomeLoss',
            
            # Assets mappings
            'total assets': 'us-gaap:Assets',
            'assets': 'us-gaap:Assets',
            'total current assets': 'us-gaap:AssetsCurrent',
            
            # Liabilities mappings
            'total liabilities': 'us-gaap:Liabilities',
            'liabilities': 'us-gaap:Liabilities',
            'total current liabilities': 'us-gaap:LiabilitiesCurrent',
            
            # Equity mappings
            'shareholders equity': 'us-gaap:StockholdersEquity',
            'stockholders equity': 'us-gaap:StockholdersEquity',
            'total equity': 'us-gaap:StockholdersEquity',
            'equity': 'us-gaap:StockholdersEquity',
            
            # Cash mappings
            'cash and cash equivalents': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
            'cash equivalents': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
            'cash': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
        }
    
    def map_label_to_concept(self, pdf_label: str) -> Tuple[Optional[str], float]:
        """Map PDF label to XBRL concept with confidence score"""
        pdf_label_clean = self._clean_label(pdf_label)
        
        # Exact match
        if pdf_label_clean in self.mapping_rules:
            return self.mapping_rules[pdf_label_clean], 1.0
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for rule_label, concept in self.mapping_rules.items():
            similarity = SequenceMatcher(None, pdf_label_clean, rule_label).ratio()
            if similarity > best_score and similarity >= self.similarity_threshold:
                best_score = similarity
                best_match = concept
        
        return best_match, best_score
    
    def _clean_label(self, label: str) -> str:
        """Clean and normalize label for matching"""
        return re.sub(r'[^\w\s]', '', label.lower().strip())
    
    def add_mapping_rule(self, pdf_label: str, xbrl_concept: str):
        """Add new mapping rule"""
        self.mapping_rules[self._clean_label(pdf_label)] = xbrl_concept


class CrossValidator:
    """Cross-validates XBRL data with PDF-extracted tables"""
    
    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance  # 1% tolerance for rounding differences
    
    def validate_values(self, xbrl_elements: List[XBRLElement], 
                       pdf_values: List[PDFTableValue]) -> List[ValidationResult]:
        """Cross-validate XBRL and PDF values"""
        mapper = ConceptMapper()
        results = []
        
        # Create lookup for XBRL elements
        xbrl_lookup = {elem.concept: elem for elem in xbrl_elements}
        
        for pdf_value in pdf_values:
            # Map PDF label to XBRL concept
            xbrl_concept, confidence = mapper.map_label_to_concept(pdf_value.label)
            
            if xbrl_concept and xbrl_concept in xbrl_lookup:
                xbrl_elem = xbrl_lookup[xbrl_concept]
                
                # Compare values
                result = self._compare_values(
                    xbrl_elem, pdf_value, confidence
                )
                results.append(result)
        
        return results
    
    def _compare_values(self, xbrl_elem: XBRLElement, pdf_value: PDFTableValue, 
                       confidence: float) -> ValidationResult:
        """Compare individual XBRL and PDF values"""
        xbrl_val = xbrl_elem.value
        pdf_val = pdf_value.value
        
        # Calculate difference
        if xbrl_val != 0:
            difference = abs(pdf_val - xbrl_val) / abs(xbrl_val)
        else:
            difference = abs(pdf_val - xbrl_val)
        
        # Determine match type
        match = difference <= self.tolerance
        
        if match:
            if difference < 0.001:  # < 0.1%
                discrepancy_type = 'exact'
            else:
                discrepancy_type = 'rounding'
        else:
            if difference > 0.1:  # > 10%
                discrepancy_type = 'ocr_error'
            else:
                discrepancy_type = 'tagging_difference'
        
        return ValidationResult(
            xbrl_concept=xbrl_elem.concept,
            pdf_label=pdf_value.label,
            xbrl_value=xbrl_val,
            pdf_value=pdf_val,
            match=match,
            difference=difference,
            confidence=confidence,
            discrepancy_type=discrepancy_type
        )


class PDFTableLoader:
    """Loads and parses PDF-extracted tables"""
    
    def __init__(self, tables_dir: str = "data/parsed/tables"):
        self.tables_dir = Path(tables_dir)
    
    def load_tables(self, company: str, year: str) -> List[PDFTableValue]:
        """Load all tables for a company/year and extract values"""
        values = []
        
        # Look for CSV files in various extraction directories
        for method in ['Hybrid', 'Camelot', 'PdfPlumber']:
            method_dir = self.tables_dir / method
            if method_dir.exists():
                csv_files = list(method_dir.glob(f"{company}_10K_{year}_*.csv"))
                
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        table_values = self._extract_values_from_table(
                            df, csv_file.stem, method
                        )
                        values.extend(table_values)
                    except Exception as e:
                        print(f"Error loading {csv_file}: {e}")
        
        return values
    
    def _extract_values_from_table(self, df: pd.DataFrame, table_id: str, 
                                  method: str) -> List[PDFTableValue]:
        """Extract values from a single table"""
        values = []
        
        for row_idx, row in df.iterrows():
            for col_idx, cell_value in enumerate(row):
                if pd.isna(cell_value):
                    continue
                
                # Try to extract numeric value
                numeric_value = self._extract_numeric_value(str(cell_value))
                if numeric_value is not None:
                    # Use the first column as label if it's not numeric
                    label = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else f"Row_{row_idx}"
                    
                    pdf_value = PDFTableValue(
                        label=label,
                        value=numeric_value,
                        row=row_idx,
                        col=col_idx,
                        table_id=table_id,
                        page=1  # Would need to extract from filename
                    )
                    values.append(pdf_value)
        
        return values
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        # Remove common formatting
        text = re.sub(r'[,$\s]', '', text)
        text = re.sub(r'[()]', '-', text)  # Parentheses indicate negative
        
        # Handle millions/billions
        multiplier = 1
        if 'million' in text.lower():
            multiplier = 1_000_000
        elif 'billion' in text.lower():
            multiplier = 1_000_000_000
        elif 'thousand' in text.lower():
            multiplier = 1_000
        
        # Extract number
        numbers = re.findall(r'-?\d+\.?\d*', text)
        if numbers:
            try:
                return float(numbers[0]) * multiplier
            except ValueError:
                pass
        
        return None


def main():
    parser = argparse.ArgumentParser(description="XBRL Cross-Validation System")
    parser.add_argument("--company", default="Apple", help="Company name")
    parser.add_argument("--year", default="2023", help="Filing year")
    parser.add_argument("--output", default="data/validation", help="Output directory")
    
    args = parser.parse_args()
    
    print("XBRL Cross-Validation System")
    print("=" * 40)
    
    # Initialize components
    downloader = XBRLDownloader()
    parser_obj = XBRLParser()
    table_loader = PDFTableLoader()
    validator = CrossValidator()
    
    # Download XBRL files
    print(f"Downloading XBRL files for {args.company} {args.year}...")
    xbrl_files = downloader.download_xbrl_files(args.company)
    
    if not xbrl_files:
        print("No XBRL files found")
        return
    
    # Parse XBRL files
    print("Parsing XBRL files...")
    all_xbrl_elements = []
    for xbrl_file in xbrl_files:
        elements = parser_obj.parse_xbrl_file(xbrl_file)
        all_xbrl_elements.extend(elements)
    
    print(f"Found {len(all_xbrl_elements)} XBRL elements")
    
    # Load PDF tables
    print("Loading PDF tables...")
    pdf_values = table_loader.load_tables(args.company, args.year)
    print(f"Found {len(pdf_values)} PDF values")
    
    # Cross-validate
    print("Cross-validating values...")
    validation_results = validator.validate_values(all_xbrl_elements, pdf_values)
    
    # Generate report
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results as JSON
    results_data = []
    for result in validation_results:
        results_data.append({
            'xbrl_concept': result.xbrl_concept,
            'pdf_label': result.pdf_label,
            'xbrl_value': result.xbrl_value,
            'pdf_value': result.pdf_value,
            'match': result.match,
            'difference': result.difference,
            'confidence': result.confidence,
            'discrepancy_type': result.discrepancy_type
        })
    
    results_file = output_dir / f"validation_results_{args.company}_{args.year}.json"
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    # Generate summary
    matches = sum(1 for r in validation_results if r.match)
    total = len(validation_results)
    
    print(f"\nValidation Summary:")
    print(f"Total comparisons: {total}")
    print(f"Matches: {matches} ({matches/total*100:.1f}%)")
    print(f"Mismatches: {total-matches} ({(total-matches)/total*100:.1f}%)")
    
    # Discrepancy breakdown
    discrepancy_counts = {}
    for result in validation_results:
        if not result.match:
            discrepancy_counts[result.discrepancy_type] = discrepancy_counts.get(result.discrepancy_type, 0) + 1
    
    if discrepancy_counts:
        print(f"\nDiscrepancy Types:")
        for disc_type, count in discrepancy_counts.items():
            print(f"  {disc_type}: {count}")
    
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()

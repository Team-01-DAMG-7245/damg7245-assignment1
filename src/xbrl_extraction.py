# Complete system for downloading, parsing, and validating XBRL data against PDF extractions

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from sec_edgar_downloader import Downloader
import zipfile
import tempfile
import re
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

try:
    from arelle import ModelManager, Cntlr, ModelXbrl
    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False
    print("Arelle not available. Install with: pip install arelle")

try:
    import python_xbrl
    PYTHON_XBRL_AVAILABLE = True
except ImportError:
    PYTHON_XBRL_AVAILABLE = False
    print("python-xbrl not available. Install with: pip install python-xbrl")


class XBRLDownloader:
    """Download XBRL files for SEC filings"""
    
    def __init__(self, download_dir="data/xbrl"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = Downloader("MyCompany", "myemail@company.com", str(self.download_dir))
    
    def download_filing_xbrl(self, ticker: str, filing_type: str, 
                            count: int = 1, year: int = None) -> List[Path]:
        """Download XBRL files for a specific ticker and filing type"""
        
        print(f"Downloading {filing_type} XBRL files for {ticker}...")
        
        try:
            # Download the filings
            if year:
                filings = self.downloader.get(filing_type, ticker, limit=count, 
                                            after=f"{year}-01-01", before=f"{year}-12-31")
            else:
                filings = self.downloader.get(filing_type, ticker, limit=count)
            
            # Find XBRL files
            xbrl_files = []
            filing_dir = self.download_dir / "sec-edgar-filings" / ticker / filing_type
            
            for filing_folder in filing_dir.iterdir():
                if filing_folder.is_dir():
                    # Look for XBRL instance documents
                    for file in filing_folder.rglob("*.xml"):
                        if self._is_xbrl_instance(file):
                            xbrl_files.append(file)
                            print(f"Found XBRL file: {file}")
            
            return xbrl_files
            
        except Exception as e:
            print(f"Error downloading XBRL files: {e}")
            return []
    
    def _is_xbrl_instance(self, file_path: Path) -> bool:
        """Check if XML file is an XBRL instance document"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check for XBRL namespaces
            xbrl_namespaces = [
                'http://www.xbrl.org/2003/instance',
                'http://xbrl.sec.gov/dei/',
                'http://fasb.org/us-gaap/'
            ]
            
            for ns_uri, ns_prefix in root.nsmap.items() if hasattr(root, 'nsmap') else {}:
                if any(xbrl_ns in str(ns_uri) for xbrl_ns in xbrl_namespaces):
                    return True
            
            return False
            
        except Exception:
            return False


class XBRLParser:
    """Parse XBRL files and extract financial data"""
    
    def __init__(self):
        self.financial_concepts = {
            # Income Statement
            'Revenue': ['Revenue', 'Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
            'NetIncome': ['NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
            'GrossProfit': ['GrossProfit', 'GrossMargin'],
            'OperatingIncome': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
            
            # Balance Sheet
            'TotalAssets': ['Assets', 'AssetsCurrent', 'AssetsNoncurrent'],
            'TotalLiabilities': ['Liabilities', 'LiabilitiesAndStockholdersEquity'],
            'StockholdersEquity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
            'Cash': ['CashAndCashEquivalentsAtCarryingValue', 'Cash'],
            
            # Cash Flow
            'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities', 'CashFlowsFromUsedInOperatingActivities'],
            'InvestingCashFlow': ['NetCashProvidedByUsedInInvestingActivities'],
            'FinancingCashFlow': ['NetCashProvidedByUsedInFinancingActivities'],
        }
    
    def parse_xbrl_file(self, xbrl_path: Path) -> Dict[str, Any]:
        """Parse XBRL file and extract financial data"""
        
        print(f"Parsing XBRL file: {xbrl_path}")
        
        if ARELLE_AVAILABLE:
            return self._parse_with_arelle(xbrl_path)
        else:
            return self._parse_with_xml(xbrl_path)
    
    def _parse_with_arelle(self, xbrl_path: Path) -> Dict[str, Any]:
        """Parse XBRL using Arelle library"""
        
        try:
            # Initialize Arelle controller
            cntlr = Cntlr.Cntlr()
            
            # Load the XBRL instance
            model_xbrl = ModelXbrl.load(cntlr.modelManager, str(xbrl_path))
            
            financial_data = {}
            contexts = {}
            
            # Extract contexts (time periods)
            for context in model_xbrl.contexts.values():
                contexts[context.id] = {
                    'period': self._extract_period(context),
                    'entity': context.entityIdentifier[1] if context.entityIdentifier else None
                }
            
            # Extract facts
            facts = []
            for fact in model_xbrl.facts:
                if fact.isNumeric and fact.value is not None:
                    concept_name = fact.concept.name if fact.concept else str(fact.qname)
                    
                    facts.append({
                        'concept': concept_name,
                        'value': float(fact.value),
                        'unit': fact.unit.measures[0][0].localName if fact.unit and fact.unit.measures else None,
                        'context_id': fact.contextID,
                        'period': contexts.get(fact.contextID, {}).get('period'),
                        'decimals': fact.decimals
                    })
            
            # Map to standardized financial concepts
            financial_data = self._map_financial_concepts(facts)
            
            cntlr.close()
            
            return {
                'financial_data': financial_data,
                'raw_facts': facts,
                'contexts': contexts,
                'parsing_method': 'arelle'
            }
            
        except Exception as e:
            print(f"Error parsing with Arelle: {e}")
            return self._parse_with_xml(xbrl_path)
    
    def _parse_with_xml(self, xbrl_path: Path) -> Dict[str, Any]:
        """Parse XBRL using basic XML parsing"""
        
        try:
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            # Extract namespaces
            namespaces = {}
            for prefix, uri in root.nsmap.items() if hasattr(root, 'nsmap') else {}:
                if prefix:
                    namespaces[prefix] = uri
            
            # Find all numeric facts
            facts = []
            contexts = {}
            
            # Extract contexts
            for context in root.findall('.//xbrli:context', namespaces):
                context_id = context.get('id')
                period_elem = context.find('.//xbrli:period', namespaces)
                
                if period_elem is not None:
                    instant = period_elem.find('xbrli:instant', namespaces)
                    start_date = period_elem.find('xbrli:startDate', namespaces)
                    end_date = period_elem.find('xbrli:endDate', namespaces)
                    
                    if instant is not None:
                        contexts[context_id] = {'period': instant.text, 'type': 'instant'}
                    elif start_date is not None and end_date is not None:
                        contexts[context_id] = {
                            'period': f"{start_date.text} to {end_date.text}",
                            'type': 'duration',
                            'start_date': start_date.text,
                            'end_date': end_date.text
                        }
            
            # Extract numeric facts
            for elem in root.iter():
                if elem.text and elem.get('contextRef'):
                    try:
                        value = float(elem.text.replace(',', ''))
                        concept_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        
                        facts.append({
                            'concept': concept_name,
                            'value': value,
                            'unit': elem.get('unitRef'),
                            'context_id': elem.get('contextRef'),
                            'period': contexts.get(elem.get('contextRef'), {}).get('period'),
                            'decimals': elem.get('decimals')
                        })
                        
                    except (ValueError, TypeError):
                        continue
            
            # Map to standardized financial concepts
            financial_data = self._map_financial_concepts(facts)
            
            return {
                'financial_data': financial_data,
                'raw_facts': facts,
                'contexts': contexts,
                'parsing_method': 'xml'
            }
            
        except Exception as e:
            print(f"Error parsing XBRL file: {e}")
            return {}
    
    def _extract_period(self, context):
        """Extract period information from Arelle context"""
        if hasattr(context, 'period'):
            if hasattr(context.period, 'instant'):
                return context.period.instant.isoformat()
            elif hasattr(context.period, 'startDate') and hasattr(context.period, 'endDate'):
                return f"{context.period.startDate.isoformat()} to {context.period.endDate.isoformat()}"
        return None
    
    def _map_financial_concepts(self, facts: List[Dict]) -> Dict[str, List[Dict]]:
        """Map XBRL facts to standardized financial concepts"""
        
        mapped_data = {}
        
        for standard_concept, xbrl_concepts in self.financial_concepts.items():
            mapped_data[standard_concept] = []
            
            for fact in facts:
                concept_name = fact['concept']
                
                # Check if this fact matches any of the XBRL concepts for this standard concept
                for xbrl_concept in xbrl_concepts:
                    if xbrl_concept.lower() in concept_name.lower():
                        mapped_data[standard_concept].append(fact)
                        break
        
        return mapped_data
    
    def get_latest_annual_values(self, financial_data: Dict) -> Dict[str, float]:
        """Extract the most recent annual values for each financial concept"""
        
        latest_values = {}
        
        for concept, facts in financial_data.items():
            if not facts:
                continue
            
            # Filter for annual data (look for 12-month periods or year-end dates)
            annual_facts = []
            for fact in facts:
                period = fact.get('period', '')
                if self._is_annual_period(period):
                    annual_facts.append(fact)
            
            if annual_facts:
                # Get the most recent value
                latest_fact = max(annual_facts, key=lambda x: x.get('period', ''))
                latest_values[concept] = latest_fact['value']
        
        return latest_values
    
    def _is_annual_period(self, period: str) -> bool:
        """Check if a period represents annual data"""
        if not period:
            return False
        
        # Look for patterns indicating annual data
        annual_patterns = [
            r'\d{4}-12-31',  # Year-end dates
            r'\d{4}-09-30',  # Fiscal year end (common for tech companies)
            r'to \d{4}-\d{2}-\d{2}.*12 months',  # 12-month duration
        ]
        
        for pattern in annual_patterns:
            if re.search(pattern, period):
                return True
        
        # Check if it's a duration of approximately 12 months
        if ' to ' in period:
            try:
                start_str, end_str = period.split(' to ')
                start_date = pd.to_datetime(start_str.strip())
                end_date = pd.to_datetime(end_str.strip())
                duration_days = (end_date - start_date).days
                return 300 <= duration_days <= 400  # Approximately 12 months
            except:
                pass
        
        return False


class PDFXBRLValidator:
    """Validate PDF-extracted data against XBRL data"""
    
    def __init__(self, pdf_tables_dir="data/parsed/tables", 
                 tolerance_percent=5.0):
        self.pdf_tables_dir = Path(pdf_tables_dir)
        self.tolerance_percent = tolerance_percent
    
    def load_pdf_tables(self, company_name: str) -> Dict[str, pd.DataFrame]:
        """Load PDF-extracted tables for a company"""
        
        tables = {}
        company_tables_dir = self.pdf_tables_dir / company_name
        
        if not company_tables_dir.exists():
            print(f"No PDF tables found for {company_name}")
            return tables
        
        # Load CSV files
        for csv_file in company_tables_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                table_name = csv_file.stem
                tables[table_name] = df
                print(f"Loaded PDF table: {table_name} ({len(df)} rows)")
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
        
        return tables
    
    def extract_financial_values_from_tables(self, tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Extract financial values from PDF tables"""
        
        financial_values = {}
        
        # Define patterns to look for financial line items
        patterns = {
            'Revenue': [r'revenue', r'net sales', r'total revenue', r'sales'],
            'NetIncome': [r'net income', r'net earnings', r'profit', r'net profit'],
            'TotalAssets': [r'total assets', r'assets total'],
            'GrossProfit': [r'gross profit', r'gross margin'],
            'OperatingIncome': [r'operating income', r'operating profit', r'income from operations'],
            'Cash': [r'cash and cash equivalents', r'cash', r'cash equivalents'],
            'TotalLiabilities': [r'total liabilities', r'liabilities total'],
            'StockholdersEquity': [r'stockholders equity', r'shareholders equity', r'total equity'],
        }
        
        for table_name, df in tables.items():
            for financial_concept, search_patterns in patterns.items():
                value = self._find_value_in_table(df, search_patterns)
                if value is not None:
                    if financial_concept not in financial_values:
                        financial_values[financial_concept] = value
                    else:
                        # If we find multiple values, take the most recent or largest
                        financial_values[financial_concept] = max(financial_values[financial_concept], value)
        
        return financial_values
    
    def _find_value_in_table(self, df: pd.DataFrame, patterns: List[str]) -> Optional[float]:
        """Find a financial value in a table using text patterns"""
        
        try:
            # Convert all text to lowercase for matching
            df_lower = df.astype(str).apply(lambda x: x.str.lower())
            
            for pattern in patterns:
                # Look for the pattern in any column
                for col in df_lower.columns:
                    matches = df_lower[col].str.contains(pattern, regex=True, na=False)
                    if matches.any():
                        # Found a matching row, now look for numeric values in other columns
                        matching_rows = df[matches]
                        
                        for _, row in matching_rows.iterrows():
                            for value in row:
                                if isinstance(value, (int, float)) and not pd.isna(value):
                                    return float(value)
                                elif isinstance(value, str):
                                    # Try to extract number from string
                                    numeric_value = self._extract_number_from_string(value)
                                    if numeric_value is not None:
                                        return numeric_value
            
            return None
            
        except Exception as e:
            print(f"Error searching table: {e}")
            return None
    
    def _extract_number_from_string(self, text: str) -> Optional[float]:
        """Extract numeric value from string, handling common financial formatting"""
        
        try:
            # Remove common formatting
            cleaned = re.sub(r'[,$()%\s]', '', str(text))
            
            # Handle parentheses as negative
            is_negative = '(' in str(text) and ')' in str(text)
            
            # Try to convert to float
            if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
                value = float(cleaned)
                return -value if is_negative else value
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def validate_against_xbrl(self, pdf_values: Dict[str, float], 
                             xbrl_values: Dict[str, float]) -> Dict[str, Any]:
        """Compare PDF-extracted values with XBRL values"""
        
        validation_results = {
            'matches': [],
            'mismatches': [],
            'pdf_only': [],
            'xbrl_only': [],
            'summary': {}
        }
        
        # Find common financial concepts
        common_concepts = set(pdf_values.keys()) & set(xbrl_values.keys())
        
        for concept in common_concepts:
            pdf_val = pdf_values[concept]
            xbrl_val = xbrl_values[concept]
            
            # Calculate percentage difference
            if xbrl_val != 0:
                percent_diff = abs(pdf_val - xbrl_val) / abs(xbrl_val) * 100
            else:
                percent_diff = float('inf') if pdf_val != 0 else 0
            
            is_match = percent_diff <= self.tolerance_percent
            
            result = {
                'concept': concept,
                'pdf_value': pdf_val,
                'xbrl_value': xbrl_val,
                'difference': pdf_val - xbrl_val,
                'percent_difference': percent_diff,
                'is_match': is_match
            }
            
            if is_match:
                validation_results['matches'].append(result)
            else:
                validation_results['mismatches'].append(result)
        
        # Find concepts only in PDF
        pdf_only = set(pdf_values.keys()) - set(xbrl_values.keys())
        for concept in pdf_only:
            validation_results['pdf_only'].append({
                'concept': concept,
                'pdf_value': pdf_values[concept]
            })
        
        # Find concepts only in XBRL
        xbrl_only = set(xbrl_values.keys()) - set(pdf_values.keys())
        for concept in xbrl_only:
            validation_results['xbrl_only'].append({
                'concept': concept,
                'xbrl_value': xbrl_values[concept]
            })
        
        # Calculate summary statistics
        total_comparisons = len(validation_results['matches']) + len(validation_results['mismatches'])
        if total_comparisons > 0:
            match_rate = len(validation_results['matches']) / total_comparisons * 100
        else:
            match_rate = 0
        
        validation_results['summary'] = {
            'total_comparisons': total_comparisons,
            'matches': len(validation_results['matches']),
            'mismatches': len(validation_results['mismatches']),
            'match_rate_percent': match_rate,
            'pdf_only_count': len(validation_results['pdf_only']),
            'xbrl_only_count': len(validation_results['xbrl_only'])
        }
        
        return validation_results
    
    def generate_validation_report(self, validation_results: Dict[str, Any], 
                                 company_name: str, filing_year: str) -> str:
        """Generate a comprehensive validation report"""
        
        report = f"""# XBRL-PDF Validation Report: {company_name} ({filing_year})

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Comparisons**: {validation_results['summary']['total_comparisons']}
- **Matches**: {validation_results['summary']['matches']} ({validation_results['summary']['match_rate_percent']:.1f}%)
- **Mismatches**: {validation_results['summary']['mismatches']}
- **PDF Only**: {validation_results['summary']['pdf_only_count']}
- **XBRL Only**: {validation_results['summary']['xbrl_only_count']}

## Matches (PDF ≈ XBRL within {self.tolerance_percent}% tolerance)

"""
        
        if validation_results['matches']:
            for match in validation_results['matches']:
                report += f"""**{match['concept']}**:
- PDF: ${match['pdf_value']:,.0f}
- XBRL: ${match['xbrl_value']:,.0f}
- Difference: {match['percent_difference']:.2f}%

"""
        else:
            report += "No matches found.\n\n"
        
        report += "## Mismatches (Significant Differences)\n\n"
        
        if validation_results['mismatches']:
            for mismatch in validation_results['mismatches']:
                report += f"""**{mismatch['concept']}** - {mismatch['percent_difference']:.1f}% difference:
- PDF: ${mismatch['pdf_value']:,.0f}
- XBRL: ${mismatch['xbrl_value']:,.0f}
- Difference: ${mismatch['difference']:,.0f}

"""
        else:
            report += "No significant mismatches found.\n\n"
        
        if validation_results['pdf_only']:
            report += "## Values Found Only in PDF\n\n"
            for item in validation_results['pdf_only']:
                report += f"- **{item['concept']}**: ${item['pdf_value']:,.0f}\n"
            report += "\n"
        
        if validation_results['xbrl_only']:
            report += "## Values Found Only in XBRL\n\n"
            for item in validation_results['xbrl_only']:
                report += f"- **{item['concept']}**: ${item['xbrl_value']:,.0f}\n"
            report += "\n"
        
        report += """## Analysis and Recommendations

### Potential Causes of Mismatches:
1. **OCR Errors**: PDF text extraction may have misread numbers
2. **Table Parsing Issues**: Complex table structures may cause extraction errors
3. **Different Reporting Periods**: PDF and XBRL data may be from different time periods
4. **Rounding Differences**: Values may be reported at different precision levels
5. **Taxonomic Mapping**: Different concepts may be mapped to the same category

### Recommendations:
"""
        
        if validation_results['summary']['match_rate_percent'] < 50:
            report += "- **Critical**: Low match rate suggests systematic issues with PDF parsing or XBRL mapping\n"
            report += "- Review table extraction algorithms and improve OCR accuracy\n"
        elif validation_results['summary']['match_rate_percent'] < 80:
            report += "- **Moderate**: Some discrepancies found, review mapping logic\n"
            report += "- Focus on improving extraction of mismatched concepts\n"
        else:
            report += "- **Good**: High match rate indicates reliable extraction pipeline\n"
            report += "- Fine-tune remaining mismatches for improved accuracy\n"
        
        report += f"\n---\n*Report generated using {self.tolerance_percent}% tolerance threshold*"
        
        return report


class XBRLValidationSystem:
    """Complete system for XBRL download, parsing, and validation"""
    
    def __init__(self, output_dir="data/xbrl_validation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloader = XBRLDownloader()
        self.parser = XBRLParser()
        self.validator = PDFXBRLValidator()
    
    def run_complete_validation(self, ticker: str, filing_type: str = "10-K", 
                               year: int = 2023) -> Dict[str, Any]:
        """Run complete XBRL validation pipeline"""
        
        print(f"Starting XBRL validation for {ticker} {filing_type} {year}")
        
        results = {
            'ticker': ticker,
            'filing_type': filing_type,
            'year': year,
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 1: Download XBRL files
        print("Step 1: Downloading XBRL files...")
        xbrl_files = self.downloader.download_filing_xbrl(ticker, filing_type, 1, year)
        
        if not xbrl_files:
            print("No XBRL files found")
            results['status'] = 'failed'
            results['error'] = 'No XBRL files found'
            return results
        
        # Step 2: Parse XBRL data
        print("Step 2: Parsing XBRL data...")
        xbrl_data = self.parser.parse_xbrl_file(xbrl_files[0])
        
        if not xbrl_data:
            print("Failed to parse XBRL file")
            results['status'] = 'failed'
            results['error'] = 'Failed to parse XBRL file'
            return results
        
        xbrl_values = self.parser.get_latest_annual_values(xbrl_data['financial_data'])
        
        # Step 3: Load PDF tables
        print("Step 3: Loading PDF tables...")
        pdf_tables = self.validator.load_pdf_tables(f"{ticker}_{filing_type}_{year}")
        
        if not pdf_tables:
            print("No PDF tables found")
            results['status'] = 'failed' 
            results['error'] = 'No PDF tables found'
            return results
        
        pdf_values = self.validator.extract_financial_values_from_tables(pdf_tables)
        
        # Step 4: Validate and compare
        print("Step 4: Validating PDF vs XBRL data...")
        validation_results = self.validator.validate_against_xbrl(pdf_values, xbrl_values)
        
        # Step 5: Generate report
        print("Step 5: Generating validation report...")
        report = self.validator.generate_validation_report(
            validation_results, ticker, str(year)
        )
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results
        results_file = self.output_dir / f"{ticker}_{filing_type}_{year}_validation_{timestamp}.json"
        results.update({
            'status': 'completed',
            'xbrl_values': xbrl_values,
            'pdf_values': pdf_values,
            'validation_results': validation_results,
            'xbrl_file': str(xbrl_files[0]),
            'pdf_tables_count': len(pdf_tables)
        })
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save report
        report_file = self.output_dir / f"{ticker}_{filing_type}_{year}_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Validation complete!")
        print(f"Results saved to: {results_file}")
        print(f"Report saved to: {report_file}")
        print(f"Match rate: {validation_results['summary']['match_rate_percent']:.1f}%")
        
        return results


def main():
    """Main function to run XBRL validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="XBRL-PDF Validation System")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol")
    parser.add_argument("--filing-type", default="10-K", help="Filing type (10-K, 10-Q)")
    parser.add_argument("--year", type=int, default=2023, help="Filing year")
    parser.add_argument("--output-dir", default="data/xbrl_validation", 
                       help="Output directory for results")
    
    args = parser.parse_args()
    
    # Initialize validation system
    validator = XBRLValidationSystem(args.output_dir)
    
    # Run validation
    results = validator.run_complete_validation(
        args.ticker, args.filing_type, args.year
    )
    
    if results['status'] == 'completed':
        validation_summary = results['validation_results']['summary']
        print(f"\nValidation Summary:")
        print(f"  Matches: {validation_summary['matches']}")
        print(f"  Mismatches: {validation_summary['mismatches']}")
        print(f"  Match Rate: {validation_summary['match_rate_percent']:.1f}%")
    else:
        print(f"Validation failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
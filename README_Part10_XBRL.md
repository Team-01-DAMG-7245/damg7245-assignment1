# Part 10 — XBRL Cross-Validation

Cross-validate key numbers extracted from PDFs with structured XBRL data to ensure accuracy and traceability.

## Overview
- Download XBRL files from SEC EDGAR for the same filings
- Parse XBRL XML and extract financial line items
- Map PDF table labels to XBRL concepts using fuzzy matching
- Cross-validate numerical values between PDF tables and XBRL data
- Analyze discrepancies and identify potential causes

## Components

### Core Classes (`src/xbrl_validation.py`)

#### XBRLDownloader
- Downloads XBRL files from SEC EDGAR API
- Handles authentication and rate limiting
- Creates sample XBRL data for demonstration

#### XBRLParser  
- Parses XBRL XML files using ElementTree
- Extracts financial facts with metadata
- Handles namespaces and context references

#### ConceptMapper
- Maps PDF table labels to XBRL concepts
- Uses fuzzy string matching with confidence scoring
- Predefined rules for common financial terms
- Extensible mapping dictionary

#### CrossValidator
- Compares XBRL vs PDF values with configurable tolerance
- Classifies discrepancy types (exact, rounding, OCR error, tagging difference)
- Generates detailed validation results

#### PDFTableLoader
- Loads CSV tables from extraction pipeline
- Extracts numeric values and labels
- Handles multiple extraction methods (Hybrid, Camelot, PdfPlumber)

## Usage

### Command Line
```bash
# Basic cross-validation
python src/xbrl_validation.py --company Apple --year 2023

# Custom output directory
python src/xbrl_validation.py --company Apple --year 2023 --output data/validation

# Help
python src/xbrl_validation.py --help
```

### Jupyter Notebook
```bash
jupyter notebook notebooks/xbrl_cross_validation.ipynb
```

The notebook provides:
- Interactive analysis workflow
- Data visualization and charts
- Detailed mismatch investigation
- Recommendations generation

## Output Files

### Validation Results
- `validation_results_{company}_{year}.json`: Detailed comparison results
- `xbrl_validation_{company}_{year}.csv`: Tabular format for analysis
- `validation_summary_{company}_{year}.json`: High-level statistics

### Sample Output Structure
```json
{
  "xbrl_concept": "us-gaap:Revenues",
  "pdf_label": "Revenue",
  "xbrl_value": 394328000000,
  "pdf_value": 394328000000,
  "match": true,
  "difference": 0.0,
  "confidence": 1.0,
  "discrepancy_type": "exact"
}
```

## Mapping Rules

### Financial Term Mappings
| PDF Label | XBRL Concept | Confidence |
|-----------|--------------|------------|
| Revenue | us-gaap:Revenues | 1.0 |
| Net Income | us-gaap:NetIncomeLoss | 1.0 |
| Total Assets | us-gaap:Assets | 1.0 |
| Cash and Cash Equivalents | us-gaap:CashAndCashEquivalentsAtCarryingValue | 1.0 |

### Fuzzy Matching
- Uses `SequenceMatcher` for similarity scoring
- Configurable threshold (default: 0.7)
- Confidence-based mapping selection

## Validation Logic

### Tolerance Levels
- **Exact Match**: Difference < 0.1%
- **Rounding**: Difference < 1% (configurable)
- **Tagging Difference**: Difference < 10%
- **OCR Error**: Difference > 10%

### Discrepancy Types
1. **exact**: Values match exactly
2. **rounding**: Small differences due to rounding
3. **ocr_error**: Large differences suggesting OCR issues
4. **tagging_difference**: Mapping or tagging inconsistencies

## Analysis Features

### Summary Statistics
- Total comparisons performed
- Match rate percentage
- Discrepancy breakdown by type
- Confidence vs accuracy correlation

### Visualizations
- Match/mismatch distribution pie chart
- Difference percentage histogram
- Confidence vs difference scatter plot
- Discrepancy type bar chart

### Detailed Analysis
- Individual mismatch investigation
- Potential cause identification
- Confidence scoring analysis
- Recommendations for improvement

## Prerequisites

### Python Packages
```bash
pip install pandas numpy matplotlib seaborn requests
```

### Optional Dependencies
```bash
# For enhanced XBRL parsing
pip install python-xbrl

# For better fuzzy matching
pip install fuzzywuzzy python-levenshtein
```

## Configuration

### Tolerance Settings
```python
# Adjust validation tolerance
validator = CrossValidator(tolerance=0.01)  # 1% tolerance

# Adjust mapping confidence threshold
mapper = ConceptMapper()
mapper.similarity_threshold = 0.8  # Higher threshold
```

### Custom Mapping Rules
```python
# Add new mapping rules
mapper.add_mapping_rule("Custom Revenue", "us-gaap:Revenues")
```

## Troubleshooting

### Common Issues

#### No XBRL Files Found
- Ensure SEC EDGAR API access
- Check company CIK mapping
- Verify filing type and date

#### No PDF Values Loaded
- Run table extraction pipeline first
- Check CSV file paths and formats
- Verify table extraction methods

#### Low Match Rates
- Review concept mapping rules
- Check OCR quality in PDFs
- Adjust tolerance settings
- Improve label preprocessing

#### Mapping Confidence Issues
- Add more mapping rules
- Adjust similarity threshold
- Improve label cleaning logic
- Use domain-specific preprocessing

## Best Practices

### Data Quality
1. **Preprocessing**: Clean and normalize labels before mapping
2. **Validation**: Set appropriate tolerance levels
3. **Monitoring**: Track match rates over time
4. **Review**: Manually verify low-confidence mappings

### Automation
1. **Batch Processing**: Validate multiple documents
2. **Alerting**: Set up notifications for large discrepancies
3. **Reporting**: Generate regular validation reports
4. **Maintenance**: Update mapping rules regularly

### Performance
1. **Caching**: Cache XBRL parsing results
2. **Parallel Processing**: Process multiple files simultaneously
3. **Incremental Updates**: Only revalidate changed data
4. **Resource Management**: Monitor memory usage for large datasets

## Integration

### Pipeline Integration
```bash
# Add to DVC pipeline
dvc run -n xbrl_validation \
  -d data/parsed/tables \
  -d data/raw/xbrl \
  -o data/validation \
  python src/xbrl_validation.py --company Apple --year 2023
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: XBRL Validation
  run: |
    python src/xbrl_validation.py --company Apple --year 2023
    # Check match rate threshold
    python -c "
    import json
    with open('data/validation/validation_summary_Apple_2023.json') as f:
        data = json.load(f)
    assert data['match_rate'] > 80, f'Match rate too low: {data[\"match_rate\"]}%'
    "
```

## Future Enhancements

### Machine Learning
- Train ML models for concept mapping
- Use embeddings for semantic similarity
- Implement active learning for mapping improvement

### Advanced Validation
- Cross-validate across multiple periods
- Implement business rule validation
- Add anomaly detection for unusual values

### Scalability
- Support for batch processing
- Real-time validation APIs
- Distributed processing capabilities

---

*This system provides comprehensive cross-validation between PDF-extracted financial data and structured XBRL filings, ensuring data accuracy and enabling automated quality assurance.*

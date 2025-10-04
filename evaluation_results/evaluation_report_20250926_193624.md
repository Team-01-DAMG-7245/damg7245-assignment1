# PDF Parsing Quality Evaluation Report
Generated on: 2025-09-26 19:36:24

## Summary
- **Pages evaluated**: 5
- **Overall text quality**: 🔴 Poor
- **Overall table quality**: 🔴 Poor

## Aggregate Metrics

### Text Extraction Quality
- **Word Error Rate (WER)**: 0.858 (lower is better, <0.1 is good)
- **Character Error Rate (CER)**: 0.842 (lower is better, <0.05 is good)

### Table Extraction Quality  
- **Precision**: 0.000 (higher is better, >0.8 is good)
- **Recall**: 0.000 (higher is better, >0.8 is good)
- **F1-Score**: 0.000 (higher is better, >0.8 is good)

### Content Distribution
- **Average chunk length**: 49.8 characters
- **Numeric token ratio**: 0.017 (proportion of tokens that are numbers)

## Per-Page Results


### Apple_10K_2023_page_1
- WER: 0.846 | CER: 0.848
- Table P/R/F1: 0.000/0.000/0.000
- Blocks: 0 | Avg chunk: 12.0 chars

### Apple_10K_2023_page_2
- WER: 0.600 | CER: 0.551
- Table P/R/F1: 0.000/0.000/0.000
- Blocks: 3 | Avg chunk: 156.5 chars

### Apple_10K_2023_page_3
- WER: 1.000 | CER: 1.000
- Table P/R/F1: 0.000/0.000/0.000
- Blocks: 0 | Avg chunk: 0.0 chars

### Apple_10K_2023_page_4
- WER: 1.000 | CER: 1.000
- Table P/R/F1: 0.000/0.000/0.000
- Blocks: 2 | Avg chunk: 0.0 chars

### Apple_10K_2023_page_5
- WER: 0.844 | CER: 0.811
- Table P/R/F1: 0.000/0.000/0.000
- Blocks: 0 | Avg chunk: 80.2 chars


## Quality Thresholds
- ✅ **Pass**: WER < 0.2 AND Table F1 > 0.6
- ⚠️  **Warning**: WER < 0.4 AND Table F1 > 0.4  
- ❌ **Fail**: WER >= 0.4 OR Table F1 <= 0.4

## Recommendations
- 🔧 **Text extraction needs improvement**: Consider better OCR preprocessing or layout detection
- 📊 **Table extraction needs improvement**: Review table detection algorithm or add more training data
- 📝 **Chunks may be too fragmented**: Consider merging adjacent text blocks
- 🔢 **Low numeric content**: Verify financial/quantitative data extraction

---
*This report helps track parsing quality over time and catch regressions.*
# DAMG7245 Assignment 1: AI-Powered PDF Parsing System

## Project Overview
Comprehensive document processing pipeline for SEC EDGAR filings, specifically Apple Inc.'s 10-K annual reports (2023 & 2024). Combines open-source tools with managed cloud services to extract text, tables, and metadata with optimal cost-efficiency and quality.

**Key Features**:
- Multi-format document extraction (PDF → TXT, MD, JSON)
- Advanced table detection using 3 methods (pdfplumber, Camelot, hybrid)
- Document structure analysis with LayoutParser
- Provenance tagging for complete data lineage
- Azure AI Document Intelligence integration with cost comparison
- DVC-based reproducible pipeline with versioning
- Comprehensive quality evaluation and regression testing
- XBRL cross-validation system

## Team Contributions

| Team Member | Parts | Key Contributions |
|-------------|-------|-------------------|
| **Swara** | 1, 4, 7 | Text extraction with OCR fallback, Docling integration, Azure AI analysis |
| **Natnicha** | 3, 6, 8, 9 | Layout detection, format comparison, DVC pipeline, quality evaluation system |
| **Kundana** | 2, 5, 10 | Table extraction, provenance tagging, performance benchmarking |

**Links**:
- GitHub: https://github.com/Team-01-DAMG-7245/damg7245-assignment1
- Demo: https://youtu.be/pdaxnsWtFEM
- Documentation: https://codelabs-preview.appspot.com/?file_id=1U1xF5oAFuT8DK0EQjOYFJxlDfXBcOCj1FJ1kPFaD-lA
  
## Directory Structure
```
damg7245-assignment1/
├── data/
│   ├── raw/                         # Source PDFs and XBRL files
│   ├── parsed/                      # Processed outputs
│   │   ├── text/                    # Per-page text files
│   │   ├── tables/                  # Extracted tables (pdfplumber/camelot/hybrid)
│   │   ├── layout/                  # Layout detection results
│   │   ├── docling/                 # Docling outputs
│   │   ├── converted/               # Multi-format conversions (MD/JSON/TXT)
│   │   └── provenance/              # Metadata and lineage
│   ├── ground_truth/                # Manual corrections for evaluation
│   └── xbrl_validation/             # XBRL cross-validation results
├── src/                             # Source code
├── reports/                         # Analysis reports
├── evaluation_results/              # Quality metrics and reports
├── notebooks/                       # Jupyter notebooks
├── dvc.yaml                         # DVC pipeline definition
├── dvc.lock                         # Pipeline state
└── requirements.txt                 # Dependencies
```

## Installation

### Prerequisites
- Python 3.9+
- Git
- Tesseract OCR (system requirement)

### System-Specific Installation
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Setup
```bash
git clone <repository-url>
cd damg7245-assignment1
pip install -r requirements.txt

# Optional: Configure Azure credentials
# Add to config.env:
# AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
# AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
```

## Quick Start

### Run Complete Pipeline with DVC
```bash
# Initialize DVC
dvc init
dvc repro

# Or run individual stages
dvc repro download
dvc repro extract_text
dvc repro extract_tables_hybrid
```

### Manual Execution
```bash
# Download filings
python src/SEC_filings.py

# Extract text
python src/extract_pdf_text.py

# Extract tables
python src/hybrid_tables.py --pdf data/raw/Apple_10K_2023.pdf --out data/parsed/tables

# Layout detection
python src/layout_detection.py

# Format conversion
python src/format_converter.py

# Quality evaluation
python src/evaluation_system.py --action evaluate
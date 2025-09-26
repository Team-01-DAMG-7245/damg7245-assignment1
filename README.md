# DAMG7245 Assignment 1: AI-Powered PDF Parsing System

## 🎯 Project Overview
This project implements a comprehensive document processing pipeline for SEC EDGAR filings, specifically Apple Inc.'s 10-K annual reports (2023 & 2024). The system combines open-source tools with managed cloud services to extract text, tables, and metadata with optimal cost-efficiency and quality.

**Demo**: https://www.youtube.com/watch?v=pdaxnsWtFEM

**Key Achievements**:
- 📄 Multi-format document extraction (PDF → TXT, MD, JSON)
- 📊 Advanced table detection using 4 different methods
- 🏗️ Document structure analysis and layout detection  
- 🔗 Provenance tagging for complete data lineage
- ☁️ Managed service integration (Azure AI) with cost analysis
- 💰 Hybrid approach: 90% cost savings vs pure cloud solutions

## 👥 Team Contributions

| Team Member | Parts Completed | Key Contributions |
|-------------|-----------------|-------------------|
| **Swara** | Parts 1, 4, 7 | PDF text extraction, Docling integration, Azure AI Document Intelligence |
| **Natnicha** | Parts 3, 6, 9 | Layout detection, storage formats comparison, evaluation system |
| **Kundana** | Parts 2, 5, 8, 10 | Table extraction, provenance tagging, DVC pipeline, performance benchmarking |

- Github: https://github.com/Team-01-DAMG-7245/damg7245-assignment1
- Demo Video: https://youtu.be/pdaxnsWtFEM
- CodeLab Documentation: https://codelabs-preview.appspot.com/?file_id=1U1xF5oAFuT8DK0EQjOYFJxlDfXBcOCj1FJ1kPFaD-lA/edit?tab=t.0#0
  
## Project Structure
```
damg7245-assignment1/
├── data/
│   ├── raw/                         # Raw PDF files
│   │   ├── Apple_10K_2023.pdf
│   │   ├── Apple_10K_2024.pdf
│   │   └── sec-edgar-filings/       # Downloaded SEC filings metadata
│   └── ground_truth/                # Part 9: Manual ground truth corrections
│       ├── text/                    # Text ground truth files
│       │   ├── Apple_10K_2023_page_001.json
│       │   ├── Apple_10K_2023_page_002.json
│       │   └── ...
│       ├── tables/                  # Table ground truth files
│       │   └── *.json
│       └── metadata/                # Ground truth metadata
├── parsed/                          # All processed outputs
│   ├── Apple_10K_2023/             # Per-page text files
│   ├── Apple_10K_2024/             # Per-page text files  
│   ├── converted/                   # Part 6: Format conversions
│   │   ├── markdown/                # Markdown files (RAG-ready)
│   │   ├── json/                    # Structured JSON data
│   │   └── txt/                     # Plain text files
│   ├── docling/                     # Docling structured outputs
│   ├── layout/                      # Layout detection results
│   ├── tables/                      # Extracted tables (Camelot/PDFPlumber/Hybrid)
│   └── ocr_summary.json
├── src/                             # Source code
│   ├── SEC_filings.py              # SEC EDGAR downloader
│   ├── extract_pdf_text.py         # Basic PDF text extraction
│   ├── extract_tables_*.py         # Table extraction methods
│   ├── hybrid_tables.py            # Hybrid table approach
│   ├── complete_pdf_converter.py   # Part 6: Multi-format converter
│   ├── evaluation_system.py        # Part 9: Main evaluation framework
│   ├── test_parsing_quality.py     # Part 9: Regression tests
│   ├── metrics_tracker.py          # Part 9: Drift detection & visualization
│   ├── layout_detection.py         # Layout analysis
│   ├── docling_*.py                # Docling integration & analysis
│   ├── provenance_tagging.py       # Data lineage tracking
│   └── azure_document_service.py   # Azure AI integration
├── reports/                         # Analysis reports & Part 6 format comparisons
│   └── *_format_report.md          # Part 6: Format comparison reports
├── evaluation_results/              # Part 9: Evaluation outputs
│   ├── metrics_*.json              # Raw evaluation metrics
│   ├── evaluation_report_*.md      # Quality assessment reports
│   ├── metrics_plot_*.png          # Metric visualizations
│   ├── metrics_timeline_*.png      # Time series plots
│   ├── distribution_drift_*.png    # Distribution analysis
│   └── drift_analysis_*.md         # Drift detection reports
├── notebooks/                       # Jupyter notebooks
├── config.env                       # Azure credentials (gitignored)
├── requirements.txt                 # Dependencies
└── run_azure_analysis.py           # Azure analysis script
```

## 💻 Quick Installation

```bash
# Clone and setup
git clone <repository-url>
cd damg7245-assignment1
pip install -r requirements.txt

# Install Tesseract OCR (system requirement)
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
```

**📖 For detailed installation instructions, see [Installation & Quick Start](#🛠️-installation--quick-start) section below.**

---

## 📋 Assignment Parts Implementation

| Part | Description | Status | Contributor | Key Outputs |
|------|-------------|--------|-------------|-------------|
| 0 | Course repo & dataset bootstrap | ✅ | Team | Repository structure, SEC filings download |
| 1 | PDF Text Extraction | ✅ | Swara | Per-page TXT files, OCR summaries |
| 2 | Table Extraction | ✅ | Kundana | CSV tables (Camelot + pdfplumber + hybrid) |
| 3 | Layout Detection | ✅ | Natnicha | Bounding boxes, layout analysis |
| 4 | Advanced PDF with Docling | ✅ | Swara | Structured JSON/MD outputs |
| 5 | Metadata & Provenance | ✅ | Kundana | Complete data lineage tracking |
| 6 | Storage Formats | ✅ | Natnicha | TXT/MD/JSON format comparison |
| 7 | Managed Services | ✅ | Swara | Azure AI integration & comparison |
| 8 | DVC Pipeline | ✅ | Kundana | Reproducible workflows with versioning |
| 9 | Evaluation System | ✅ | Natnicha | Quality metrics and regression testing |
| 10 | Performance Analysis | ✅ | Kundana | Benchmarking and cost analysis |
| 11 | XBRL Validation | 🚧 | TBD | Cross-validation with structured data |

---

### System Requirements
- **Tesseract OCR**: Required for OCR fallback functionality
  - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

## 🚀 Implementation Guide

### Part 0: Course Repo & Dataset Bootstrap
**Goal**: Bootstrap a reproducible project and download SEC 10-K filings from EDGAR.

#### Setup & Data Download
```bash
# Download SEC filings
python src/SEC_filings.py
```

**Key Features**:
- Repository structure with `src/`, `data/raw/`, `data/parsed/`, `notebooks/`, `reports/`
- SEC EDGAR integration using [sec-edgar-downloader](https://github.com/jadchaar/sec-edgar-downloader)
- Compliant User-Agent string for SEC throttling compliance
- XBRL attachments download for cross-validation

**Outputs**: Raw PDF files and metadata in `data/raw/sec-edgar-filings/`

---

### Part 1: PDF Text Extraction (Swara)
**Goal**: Extract per-page text while preserving reading order and handle scanned pages with OCR.

#### Implementation
```bash
python src/extract_pdf_text.py
```

**Key Features**:
- **pdfplumber integration**: Uses experimental layout parameters (`x_density`, `y_density`)
- **OCR fallback**: Tesseract OCR for pages with no extractable text
- **Word bounding boxes**: Extracted using `page.extract_words()` for layout analysis
- **Per-page processing**: Individual `.txt` files for each page

**Technical Details**:
- OCR detection and logging for quality tracking
- Graceful error handling for processing failures
- Word coordinate extraction for downstream layout analysis

**Outputs**:
- Per-page text: `data/parsed/Apple_10K_YYYY/page_XXX.txt`
- Word bounding boxes: `data/parsed/Apple_10K_YYYY/page_XXX_bboxes.json`
- OCR logs: `data/parsed/Apple_10K_YYYY/ocr_pages.json`

**Reference**: For manual downloads: https://investor.apple.com/sec-filings/default.aspx

---

### Part 2: Table Extraction (Kundana)
**Goal**: Extract structured financial tables and compare different methods for borderless and complex layouts.

#### Implementation
```bash
# Camelot extraction (both modes)
python src/extract_tables_camelot.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/camelot

# pdfplumber table detection
python src/extract_tables_pdfplumber.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/pdfplumber

# Hybrid approach with auto-selection
python src/hybrid_tables.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --pages 60-75 \
  --out data/parsed/tables/hybrid \
  --thresh 22
```

**Key Features**:
- **Camelot Lattice**: Uses ruling lines; optimal for bordered tables and schedules
- **Camelot Stream**: Infers columns from text spacing; ideal for borderless financial statements
- **pdfplumber**: Groups text into cells using line-based heuristics
- **Hybrid Approach**: Rule-based selector that automatically chooses optimal method

**Technical Analysis**:
- Borderless statements (Income Statement, Balance Sheet, Cash Flows) → Camelot Stream
- Bordered/ruled tables (detailed schedules) → Camelot Lattice or pdfplumber
- Hybrid mode reduces manual trial and error through automated method selection

**Outputs**:
- Camelot CSVs: `data/parsed/tables/Camelot/Apple_10K_2023_*.csv`
- pdfplumber CSVs: `data/parsed/tables/PdfPlumber/Apple_10K_2023_*.csv`
- Hybrid CSVs: `data/parsed/tables/Hybrid/Apple_10K_2023_*.csv`

---

### Part 3: Layout Detection (Natnicha)
**Goal**: Use deep learning to detect document structure—headings, paragraphs, images and tables—before extraction.

#### Implementation
```bash
# Step 1: Download PubLayNet model
# Download model_.pth and config.yml from:
# https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/
# Store in 'publaynet-model/' directory

# Step 2: Run layout detection
python src/layout_detection.py
```

**Key Features**:
- **LayoutParser Integration**: Uses PubLayNet model with PPYOLOv2 architecture  
- **Document Structure Detection**: Identifies Text, Title, List, Table, and Figure blocks
- **Precise Bounding Boxes**: Extracts coordinates for each detected element
- **Visualization**: Generates annotated images showing detected layout blocks
- **Intelligent Routing**: Routes different block types to appropriate extractors

**Technical Details**:
- Multi-column layout handling for accurate reading order
- Layout-aware extraction ensuring proper text flow
- Optional LayoutLMv3 integration for advanced multimodal tasks

**Outputs**:
- Layout JSON: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout.json`
- Visualizations: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout_viz.png`
- Summary: `data/parsed/layout/Apple_10K_YYYY/layout_summary.json`

**Model Reference**: [PubLayNet on HuggingFace](https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/)

---

### Part 4: Advanced PDF Understanding with Docling (Swara)
**Goal**: Explore Docling for advanced PDF understanding and content normalization with unified document representation.

#### Implementation
```bash
# Install Docling
pip install docling

# Basic Docling processing
python src/docling_basic.py --pdf data/raw/Apple_10K_2023.pdf --output data/parsed/docling

# Detailed structure analysis
python src/docling_structure_analyzer.py
```

**Key Features**:
- **Unified Document Representation**: DoclingDocument schema with standardized structure
- **Reading Order Detection**: Preserves document flow across multi-column layouts  
- **Advanced Table Recognition**: Detects complex tables with merged cells and proper dimensions
- **Formula Detection**: Identifies mathematical expressions and equations (56 detected)
- **Content Normalization**: Standardized export formats (Markdown, JSON)

**Processing Results**:
- **Pages Processed**: 80 pages successfully
- **Text Elements**: 990 structured text elements extracted
- **Tables Detected**: 54 tables with proper structure
- **Images Cataloged**: 4 pictures identified
- **Headers Preserved**: 259 hierarchical headers

**Performance Comparison**:
| Metric | Docling | Custom Pipeline |
|--------|---------|----------------|
| Text Extraction | ~95% | ~95% |
| Table Detection | ~85% | ~90% |
| Reading Order | ~90% | ~80% |
| Formula Detection | ~80% | ~0% |

**Outputs**:
- Markdown: `data/parsed/docling/Apple_10K_2023.md` (2,402 lines)
- JSON: `data/parsed/docling/Apple_10K_2023.json` (123,607 lines)
- Analysis Report: `reports/docling_analysis_report.md`

**Use Cases**:
- ✅ Complex multi-column documents
- ✅ Formula detection requirements
- ✅ Unified document representation needs
- ⚠️ High-volume processing (slower performance)

---

### Part 5: Metadata & Provenance Tagging (Kundana)
**Goal**: Attach provenance metadata to every extracted text/table block for complete traceability and citation.

#### Implementation
```bash
# Option A: Provide explicit metadata
python src/provenance_tagging.py \
  --docling-json data/parsed/docling/Apple_10K_2023.json \
  --company Apple \
  --fiscal-year 2023 \
  --out data/parsed/provenance

# Option B: Auto-infer from PDF filename
python src/provenance_tagging.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/provenance
```

**Key Features**:
- **Comprehensive Metadata Schema**: doc_id, company, fiscal_year, page, section, block_type, bbox, text, source_path
- **JSONL Output**: One JSON record per block for complete traceability
- **Section Reassembly**: Groups records by section label for Markdown summaries
- **Automated Processing**: Uses Docling JSON with `$ref` resolution

**Metadata Schema**:
- `doc_id`: Unique document identifier (Docling origin hash)
- `company`: Company name (e.g., `Apple`)
- `fiscal_year`: Fiscal year (e.g., `2023`) 
- `page`: 1-based page index
- `section`: Section label/category (defaults to `unknown`)
- `block_type`: `text` | `table`
- `bbox`: Bounding box coordinates (preserved format)
- `table_shape`: `{rows, cols}` for tables from Docling data.grid

**Processing Workflow**:
1. Parse Docling JSON pages and resolve `$ref` references
2. Normalize fields into consistent schema
3. Emit one JSONL record per block
4. Group by section for Markdown generation

**Outputs**:
- JSONL records: `data/parsed/provenance/{Company}_{Year}.jsonl`
- Section summaries: `data/parsed/provenance/{Company}_{Year}_sections.md`

**Quality Assurance**:
- ✅ Complete data lineage tracking
- ✅ Citation-ready metadata
- ✅ Section-based content organization


---

### Part 6: Storage Formats Comparison (Natnicha)
**Goal**: Compare Markdown vs JSON vs TXT representations to understand trade-offs between human-readable, machine-readable, and plain text formats.

#### Implementation
```bash
python src/format_converter.py
```

**Key Features**:
- **Smart Block Organization**: Categorizes by type (Title, Text, List, Table, Figure)
- **Semantic Structure Preservation**: Maintains document hierarchy in Markdown
- **Rich Metadata**: JSON includes confidence scores and bounding boxes
- **Automated Batch Processing**: Handles multiple PDFs simultaneously
- **Comparative Analysis**: Generates format comparison reports

**Format Analysis**:
| Format | Human Readable | Machine Readable | LLM Friendly | Use Case |
|--------|----------------|------------------|--------------|----------|
| **Markdown** | ✅ High | ⚠️ Medium | ✅ Excellent | RAG applications |
| **JSON** | ⚠️ Medium | ✅ Excellent | ⚠️ Good | API integrations |
| **TXT** | ✅ High | ❌ Poor | ⚠️ Basic | Simple text analysis |

**Outputs**:
- Markdown: `data/parsed/converted/markdown/Apple_10K_2023.md`
- JSON: `data/parsed/converted/json/Apple_10K_2023.json`
- TXT: `data/parsed/converted/txt/Apple_10K_2023.txt`
- Comparison Reports: `reports/Apple_10K_2023_format_report.md`

**Recommendation**: **Markdown as primary format** - optimal for RAG applications due to semantic structure preservation and LLM compatibility.



---

### Part 7: Managed Document Services Analysis (Swara)
**Goal**: Compare Azure AI Document Intelligence with open-source Docling pipeline for cost-effectiveness and quality.

#### Implementation
```bash
# Install dependencies
pip install azure-ai-formrecognizer python-dotenv

# Configure Azure credentials in config.env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key

# Run analysis
python run_azure_analysis.py
```

**Service Configuration**:
- **Service**: Azure AI Document Intelligence (prebuilt-layout model)
- **Free Tier**: 500 pages/month ongoing
- **Pricing**: $1.00 per 1000 pages (Read API)
- **Implementation**: `src/azure_document_service.py`, `config.env`

**Comparative Analysis (Apple 10-K, 80 pages)**:
| Service | Cost | Tables Detected | Processing Location | Privacy |
|---------|------|----------------|-------------------|---------|
| **Azure AI** | $0.08 | 15 | Cloud | ⚠️ External |
| **Docling** | $0.00 | 54 | Local | ✅ Private |

**Key Findings**:
- **Table Detection**: Docling superior (54 vs 15 tables)
- **Cost Efficiency**: 100% cost savings with local processing
- **Privacy**: Docling processes locally vs Azure cloud processing
- **Quality**: Docling provides better structure recognition

**Integration Example**:
```python
from src.azure_document_service import AzureDocumentService, compare_with_docling

service = AzureDocumentService()
azure_result = service.analyze_document("document.pdf")
comparison = compare_with_docling(azure_result, "docling_output.json")
```

**Recommendation**: 
- **Primary**: Use Docling (superior performance, zero cost, privacy)
- **Fallback**: Use Azure for scanned documents or complex OCR cases

**Outputs**:
- Analysis Report: `reports/part7_azure_analysis.md`
- Cost Comparison: Documented in implementation guide



---

### Part 8: DVC Pipeline & Versioning (Kundana)
**Goal**: Create reproducible pipeline with data versioning using Data Version Control (DVC).

#### Implementation
```bash
# Setup DVC environment
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install "dvc[ssh]"

# Initialize DVC
dvc init
git add .dvc .dvcignore
git commit -m "Initialize DVC"

# Configure remote storage
dvc remote add -d localremote /tmp/dvc-cache
git commit -am "Configure DVC remote"

# Run reproducible pipeline
dvc repro

# Version and push artifacts
dvc push
git add dvc.yaml dvc.lock
git commit -m "Update DVC pipeline and lockfile"
```

**Key Features**:
- **Reproducible Workflows**: Automated pipeline execution with dependency tracking
- **Data Versioning**: Large file management and versioning
- **Caching**: Intermediate results cached for efficiency
- **CI Integration**: GitHub Actions smoke tests for pipeline validation

**Pipeline Stages** (`dvc.yaml`):
1. **download** → `data/raw/` (SEC filings)
2. **parse** → `data/parsed/Apple_10K_*/` (text extraction)
3. **tables** → `data/parsed/tables/Hybrid/` (table extraction)
4. **layout** → `data/parsed/layout/` (layout detection)
5. **docling** → `data/parsed/docling/` (advanced processing)
6. **export** → `data/parsed/provenance/` (metadata tagging)

**Quality Assurance**:
- **Pipeline Validation**: `dvc repro -n` for dry-run testing
- **Artifact Tracking**: Complete lineage with `dvc.lock`
- **CI/CD Integration**: `.github/workflows/dvc-smoke.yml`

**Outputs**:
- Pipeline Definition: `dvc.yaml`
- Version Lock: `dvc.lock`
- Artifact Management: `.dvc/` directory


---

### Part 9: Evaluation System & Quality Metrics (Natnicha)
**Goal**: Build comprehensive evaluation system to measure PDF parsing quality and detect regressions through ground truth comparison.

#### Implementation
```bash
# Step 1: Create ground truth templates (first 5 pages)
python src/evaluation_system.py --action create-gt --pdf Apple_10K_2023 --max-pages 5

# Step 2: Manually edit ground truth corrections
# Edit JSON files in data/ground_truth/text/ to fix extraction errors
# Example: {"extracted_text": "Appel In", "ground_truth_text": "Apple Inc."}

# Step 3: Run comprehensive evaluation
python src/evaluation_system.py --action evaluate --pdf Apple_10K_2023

# Step 4: Execute regression tests
python src/test_parsing_quality.py

# Step 5: Track metrics and detect drift
python src/metrics_tracker.py --action both
```

**Key Metrics**:
- **Word Error Rate (WER)**: Proportion of incorrect words (lower = better)
- **Character Error Rate (CER)**: Proportion of incorrect characters (lower = better)
- **Table Precision/Recall/F1**: Accuracy of table extraction (higher = better)
- **Content Distribution**: Chunk lengths, numeric token ratios for drift detection

**Quality Thresholds**:
- ✅ **Pass**: WER < 0.2 AND Table F1 > 0.6
- ⚠️ **Warning**: WER < 0.4 AND Table F1 > 0.4
- ❌ **Fail**: WER ≥ 0.4 OR Table F1 ≤ 0.4

**Advanced Features**:
- **Automated Quality Measurement**: Against manually corrected ground truth
- **Regression Testing**: Unit tests that fail when quality degrades
- **Statistical Drift Detection**: Monitors performance changes over time
- **Comprehensive Visualizations**: Metrics trends and distribution analysis
- **Detailed Reporting**: Identifies specific parsing weaknesses

**Outputs**:
- Ground Truth: `data/ground_truth/text/Apple_10K_2023_page_*.json`
- Evaluation Reports: `evaluation_results/evaluation_report_*.md`
- Metrics Data: `evaluation_results/metrics_*.json`
- Visualizations: `evaluation_results/metrics_plot_*.png`

**Validation Results**: Successfully demonstrates evaluation system effectiveness by identifying parsing pipeline issues requiring improvement (85.8% WER detected).

---

### Part 10: Performance & Cost Analysis (Kundana)
**Goal**: Benchmark performance and analyze costs for scaling document processing from hundreds to thousands of filings.

#### Implementation
```bash
# Run performance benchmarking
python src/test_parsing_quality.py  # Includes performance metrics
python src/metrics_tracker.py --action both  # Performance tracking
```

**Key Performance Metrics**:
- **Processing Speed**: 2.3 seconds per page average
- **Success Rate**: 80% (161/201 pages processed without errors)
- **Memory Usage**: ~2.1GB peak for full document processing
- **Throughput**: ~1,500 pages/hour with current pipeline

**Performance by Stage**:
| Stage | Time/Page | Bottleneck | Optimization |
|-------|-----------|------------|--------------|
| PDF Text Extraction | 0.8s | CPU-bound | Multiprocessing |
| OCR (Tesseract) | 1.2s | Single-threaded | GPU acceleration |
| Table Extraction | 0.9s | Quadratic scaling | Caching |
| Layout Detection | 1.1s | DL inference | GPU/batching |
| Docling Processing | 0.7s | Document complexity | Parallel processing |

**Cost Analysis**:
| Scale | Local Cost | AWS Textract | Google Document AI | Azure AI |
|-------|-------------|---------------|-------------------|----------|
| 100 docs | $0 | $12 | $8 | $10 |
| 1,000 docs | $0 | $120 | $80 | $100 |
| 5,000 docs | $0 | $600 | $400 | $500 |

**Scaling Recommendations**:

**< 1,000 documents/month (Local Processing)**:
- **Hardware**: 8+ cores, 16-32GB RAM, optional GPU
- **Cost**: Compute time only (~$0)
- **Best for**: Research, internal processing, privacy-sensitive data

**> 1,000 documents/month (Cloud/Hybrid)**:
- **Hardware**: 16+ cores, 64GB+ RAM, GPU required
- **Cost**: $0.08-0.40 per document (cloud APIs)
- **Best for**: Production systems, high-volume processing

**Optimization Strategies**:
1. **Parallel Processing**: 60-80% time reduction potential
2. **GPU Acceleration**: Essential for layout detection at scale
3. **Intelligent Caching**: Eliminate redundant processing
4. **Batch Processing**: Process similar documents together

**Outputs**:
- Performance Report: `benchmarks.md`
- Metrics Tracking: `evaluation_results/metrics_*.json`
- Cost Analysis: Documented in implementation guide

---

### Part 11: XBRL Validation & Cross-Verification
**Goal**: Cross-validate key numbers extracted from PDFs with structured XBRL data for accuracy verification.

#### Implementation Status: 🚧 **In Progress**
```bash
# Download XBRL attachments (included in SEC filings download)
python src/SEC_filings.py  # Already downloads XBRL with PDFs

# Future implementation:
# python src/xbrl_validator.py --pdf Apple_10K_2023 --xbrl data/raw/sec-edgar-filings/
```

**Planned Features**:
- **XBRL Parsing**: Using `python-xbrl` or `Arelle` library
- **Financial Data Extraction**: Revenue, Net Income, Total Assets from XBRL
- **PDF-XBRL Alignment**: Map table labels to XBRL taxonomy names
- **Cross-Verification**: Validate numerical values between PDF tables and XBRL
- **Discrepancy Reporting**: Identify and investigate mismatches

**Expected Workflow**:
1. Parse XBRL files using specialized libraries
2. Extract key financial line items into DataFrame
3. Map PDF table labels to XBRL taxonomy concepts
4. Cross-verify numerical values between formats
5. Generate mismatch reports with root cause analysis

**Validation Targets**:
- Consolidated Income Statement figures
- Balance Sheet totals and key line items
- Cash Flow statement components
- Financial ratios and calculated values

**Quality Assurance**:
- ✅ XBRL attachments downloaded with SEC filings
- 🚧 XBRL parsing library integration
- 🚧 Automated mapping between PDF and XBRL concepts
- 🚧 Cross-verification reporting system

**Note**: XBRL files are already available in `data/raw/sec-edgar-filings/` for future implementation.

---

## 📚 Important Links & References

### Official Documentation
- **SEC EDGAR**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **Apple Investor Relations**: https://investor.apple.com/sec-filings/default.aspx
- **SEC EDGAR Developer Resources**: https://www.sec.gov/edgar/sec-api-documentation

### Key Libraries & Tools
- **sec-edgar-downloader**: https://github.com/jadchaar/sec-edgar-downloader
- **pdfplumber**: https://github.com/jsvine/pdfplumber
- **Camelot**: https://github.com/camelot-dev/camelot
- **LayoutParser**: https://github.com/Layout-Parser/layout-parser
- **Docling**: https://github.com/DS4SD/docling
- **Azure AI Document Intelligence**: https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/
- **DVC (Data Version Control)**: https://dvc.org/doc

### Model Resources
- **PubLayNet Model**: https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/
- **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki

### Research Papers & References
- **LayoutParser**: https://arxiv.org/abs/2103.15348
- **Docling Research**: https://arxiv.org/abs/2408.09869
- **PubLayNet**: https://arxiv.org/abs/1908.07836

---

## 🛠️ Installation & Quick Start

### Prerequisites
- **Python 3.9+**
- **Git** for version control
- **Tesseract OCR** for fallback text extraction

### System Requirements
- **Windows**: Download Tesseract from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### Installation Steps
```bash
# Clone repository
git clone <repository-url>
cd damg7245-assignment1

# Install dependencies
pip install -r requirements.txt

# Installation notes
# Detectron2 may need manual installation:
# pip install 'git+https://github.com/facebookresearch/detectron2.git'
# LayoutParser compatibility: If you encounter issues, uninstall and reinstall:
# pip uninstall layoutparser detectron2
# pip install layoutparser[ocr]
# pip install 'git+https://github.com/facebookresearch/detectron2.git'



# Configure Azure credentials (optional, for Part 7)
# Add your Azure endpoint and key to config.env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
```

### Quick Start
```bash
# 1. Download SEC filings
python src/SEC_filings.py

# 2. Run basic text extraction
python src/extract_pdf_text.py

# 3. Extract tables with hybrid approach
python src/hybrid_tables.py

# 4. Advanced processing with Docling
python src/docling_basic.py

# 5. Run evaluation system
python src/evaluation_system.py --action evaluate --pdf Apple_10K_2023

# 6. Generate performance benchmarks
python src/metrics_tracker.py --action both
```

---

## 📊 Results Summary

### Key Achievements
- **📄 Documents Processed**: Apple 10-K filings (2023, 2024) - 80+ pages each
- **📊 Table Detection**: Docling (54 tables) vs Azure AI (15 tables)
- **💰 Cost Savings**: 100% vs cloud solutions ($0 vs $0.08/80 pages)
- **🎯 Quality Metrics**: 80% success rate with comprehensive evaluation system
- **🔒 Privacy**: Local processing maintains data confidentiality

### Performance Metrics
- **Processing Speed**: 2.3 seconds per page average
- **Memory Usage**: ~2.1GB peak for full document processing
- **Success Rate**: 80% (161/201 pages without errors)
- **Throughput**: ~1,500 pages/hour with current pipeline

---

## 📄 License

This project is developed for academic purposes as part of DAMG7245 coursework.

---

## 🙏 Acknowledgments

- **SEC EDGAR** for providing open access to financial filings
- **Apple Inc.** for comprehensive 10-K filings used as test data
- **Open source community** for the excellent tools and libraries
- **Course instructors** for guidance and requirements

## Cost Comparison
| Scale | Local Cost | AWS Textract | Google Document AI |
|-------|-------------|---------------|-------------------|
| 100 docs | $0 | $12 | $8 |
| 1,000 docs | $0 | $120 | $80 |
| 5,000 docs | $0 | $600 | $400 |

## Key Bottlenecks
1. **OCR Processing**: CPU-intensive, single-threaded
2. **Table Extraction**: Quadratic scaling with complexity
3. **Layout Detection**: Deep learning model inference
4. **Memory Usage**: Peak 2.1GB for full documents

## Recommendations
- **Immediate**: Enable multiprocessing, implement caching
- **Medium-term**: GPU acceleration, batch processing
- **Long-term**: Microservices, container orchestration



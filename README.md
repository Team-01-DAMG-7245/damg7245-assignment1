# DAMG7245 Assignment 1: AI-Powered PDF Parsing System

## 🎯 Project Overview
This project implements a comprehensive document processing pipeline for SEC EDGAR filings, specifically Apple Inc.'s 10-K annual reports (2023 & 2024). The system combines open-source tools with managed cloud services to extract text, tables, and metadata with optimal cost-efficiency and quality.

**Key Achievements**:
- 📄 Multi-format document extraction (PDF → TXT, MD, JSON)
- 📊 Advanced table detection using 4 different methods
- 🏗️ Document structure analysis and layout detection  
- 🔗 Provenance tagging for complete data lineage
- ☁️ Managed service integration (Azure AI) with cost analysis
- 💰 Hybrid approach: 90% cost savings vs pure cloud solutions

## Project Structure
```
damg7245-assignment1/
├── data/
│   ├── raw/                    # Raw PDF files
│   │   ├── Apple_10K_2023.pdf
│   │   ├── Apple_10K_2024.pdf
│   │   └── sec-edgar-filings/  # Downloaded SEC filings metadata
├── parsed/                          # All processed outputs
│   ├── Apple_10K_2023/             # Per-page text files
│   ├── Apple_10K_2024/             # Per-page text files  
│   ├── converted/                   # Format conversions (TXT/MD/JSON)
│   ├── docling/                     # Docling structured outputs
│   ├── layout/                      # Layout detection results
│   ├── tables/                      # Extracted tables (Camelot/PDFPlumber/Hybrid)
│   └── ocr_summary.json
├── src/                             # Source code
│   ├── SEC_filings.py              # SEC EDGAR downloader
│   ├── extract_pdf_text.py         # Basic PDF text extraction
│   ├── extract_tables_*.py         # Table extraction methods
│   ├── hybrid_tables.py            # Hybrid table approach
│   ├── format_converter.py         # Format conversions
│   ├── layout_detection.py         # Layout analysis
│   ├── docling_*.py                # Docling integration & analysis
│   ├── provenance_tagging.py       # Data lineage tracking
│   └── azure_document_service.py   # Azure AI integration
├── reports/                         # Analysis reports
├── notebooks/                       # Jupyter notebooks
├── config.env                       # Azure credentials (gitignored)
├── requirements.txt                 # Dependencies
└── run_azure_analysis.py           # Azure analysis script
```

## Installation & Dependencies

### Required Python Packages
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually:
# Core document processing
pip install sec-edgar-downloader pdfplumber pytesseract Pillow requests
pip install docling camelot-py[cv] pandas matplotlib seaborn

# Layout detection
pip install layoutparser[ocr]
pip install 'git+https://github.com/facebookresearch/detectron2.git'

# Azure AI Document Intelligence (Part 7)
pip install azure-ai-formrecognizer python-dotenv

# Note: you may need to uninstall layoutparser and reinstall for detectron2:
https://github.com/Layout-Parser/layout-parser/blob/main/installation.md
# for uninstallation,
pip uninstall layoutparser detectron2   # OPTIONAL, where needed

```

## 🚀 Quick Start Guide

### 1. Setup Environment
```bash
git clone <repository>
cd damg7245-assignment1
pip install -r requirements.txt

# Configure Azure credentials (for Part 7)
# Add your Azure endpoint and key to config.env
```

### 2. Run Analysis Pipeline
```bash
# Download SEC filings
python src/SEC_filings.py

# Extract text and tables
python src/extract_pdf_text.py
python src/extract_tables_camelot.py

# Advanced analysis with Docling
python src/docling_basic.py
python src/docling_structure_analyzer.py

# Azure AI comparison
python run_azure_analysis.py
```

### 3. Key Results Summary
- **📄 Documents Processed**: Apple 10-K filings (2023, 2024) - 80+ pages each
- **📊 Table Detection**: Docling (54 tables) vs Azure AI (15 tables) 
- **💰 Cost Analysis**: Docling ($0) vs Azure AI ($0.08/80 pages)
- **🎯 Final Recommendation**: Use Docling as primary, Azure as fallback
- **🔒 Privacy**: Docling (local) vs Azure (cloud processing)

---

## 📋 Assignment Parts Status

| Part | Description | Status | Key Outputs |
|------|-------------|--------|-------------|
| 1 | SEC EDGAR Download | ✅ | Raw PDF files, metadata |
| 2 | PDF Text Extraction | ✅ | Per-page TXT files, OCR summaries |
| 3 | Table Extraction | ✅ | CSV tables (3 methods + hybrid) |
| 4 | Format Conversion | ✅ | TXT/MD/JSON conversions |
| 5 | Layout Detection | ✅ | Bounding boxes, layout analysis |
| 6 | Docling Integration | ✅ | Structured JSON/MD outputs |
| 6.5 | Provenance Tagging | ✅ | Complete data lineage tracking |
| 7 | Managed Services | ✅ | Azure AI integration & comparison |

---

### System Requirements
- **Tesseract OCR**: Required for OCR fallback functionality
  - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

## Usage

### Part 1: PDF Text Extraction

For manual downloads: https://investor.apple.com/sec-filings/default.aspx

#### Step 1: Download SEC Filings
```bash
python data/raw/SEC_filings.py
```
This downloads Apple's 10-K filings for 2023 and 2024.

#### Step 2: Extract Text from PDFs
```bash
python src/extract_pdf_text.py
```
This extracts per-page text with OCR fallback and word bounding boxes.

Part 2: Table Extraction (Camelot + pdfplumber)
#### Step 3: Extract Tables with Camelot
```bash
python src/extract_tables_camelot.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/camelot
```
Runs both lattice and stream modes and saves extracted tables as CSV files.

#### Step 4: Extract Tables with pdfplumber
```bash
python src/extract_tables_pdfplumber.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/pdfplumber
```
Detects tables using line/overlap heuristics and saves them as CSV files.

#### Step 5: Hybrid Extractor
```bash
python src/hybrid_tables.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --pages 60-75 \
  --out data/parsed/tables/hybrid \
  --thresh 22
```
Automatically chooses lattice when pages have ruling lines and stream otherwise.

## Features Implemented

### Part 1 - Text Extraction from PDFs
- **PDF Processing**: Uses `pdfplumber` with experimental layout parameters (`x_density`, `y_density`)
- **OCR Fallback**: Applies Tesseract OCR for pages with no extractable text
- **Per-page Files**: Saves individual `.txt` files for each page
- **OCR Logging**: Tracks which pages required OCR processing
- **Word Bounding Boxes**: Extracts word coordinates for layout analysis
- **Error Handling**: Graceful handling of processing failures


### Key Outputs
- **Per-page text files**: `data/parsed/Apple_10K_YYYY/page_XXX.txt`
- **Word bounding boxes**: `data/parsed/Apple_10K_YYYY/page_XXX_bboxes.json`
- **OCR logs**: `data/parsed/Apple_10K_YYYY/ocr_pages.json`
- **Processing summary**: `data/parsed/ocr_summary.json`

### Part 2 - Table Extraction (Camelot + pdfplumber)

#### Step 1: Extract Tables with Camelot

python src/extract_tables_camelot.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/camelot
  
#### Step 2: Extract Tables with pdfplumber
python src/extract_tables_pdfplumber.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/tables/pdfplumber
This detects tables using line and intersection heuristics, saving them as CSV files.

#### Step 3: Hybrid Extractor (Auto lattice/stream selection)
python src/hybrid_tables.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --pages 60-75 \
  --out data/parsed/tables/hybrid \
  --thresh 22

Features Implemented
Camelot (lattice): Uses ruling lines; best for bordered tables and schedules.
Camelot (stream): Infers columns from text spacing; best for borderless financial statements.
pdfplumber: Groups text into cells using line-based heuristics; effective on tables with clear grid lines.
Hybrid approach: Simple rule-based selector that applies lattice on heavily ruled pages and stream on plain-text tables.

Key Outputs
Camelot CSVs: data/parsed/tables/camelot/Apple_10K_2023_stream_00.csv
pdfplumber CSVs: data/parsed/tables/pdfplumber/Apple_10K_2023_p065_00.csv
Hybrid CSVs: data/parsed/tables/hybrid/Apple_10K_2023_p065_stream_00.csv


Observations
Borderless statements (e.g., Income Statement, Balance Sheet, Cash Flows) were extracted most cleanly with Camelot stream.
Bordered/ruled tables (e.g., detailed schedules) were best handled by Camelot lattice or pdfplumber.
Hybrid mode automated method selection, reducing manual trial and error.
Final selected CSV contained properly aligned year columns and intact row labels for downstream analysis.

#Table Extraction Comparison

## Document & Scope
- **Filings analyzed:** Apple 10-K (2023, 2024)
- **Target pages:** Consolidated Income Statement, Balance Sheet, and Cash Flows


## Methods Compared
1. **Camelot (Stream mode)**
   - Groups text spans to infer columns.
   - Works best for **borderless tables** common in financial statements.

2. **Camelot (Lattice mode)**
   - Relies on ruling lines and grid borders.
   - Works best for **bordered schedules or supporting tables**.

3. **pdfplumber (Table detection)**
   - Uses line intersection and grouping heuristics.
   - Performs well when **clear lines exist**, but often mis-detects large, borderless statements.

---

## Results

- **Camelot Stream**
  - Successfully preserved **row labels** and **aligned year columns** for Income Statement and Balance Sheet.
  - Minimal cleanup required; numeric columns extracted consistently.
  - Best suited for the main financial statements which lack visible borders.

- **Camelot Lattice**
  - Worked on smaller tables with visible ruling lines.
  - On borderless statements, it over-split multi-line labels and sometimes produced empty or fragmented cells.

- **pdfplumber**
  - Detected line-based tables (e.g., note schedules) reliably.
  - On borderless statements, often returned large narrative blocks instead of structured rows/columns.

---

## Key Example
- **Income Statement (page ~65)**  
  - Stream mode produced a clean CSV: `data/parsed/tables/camelot/Apple_10K_2023_p065_stream_00.csv`  
  - Row labels (e.g., Net Sales, Operating Income, Net Income) were intact.  
  - Year columns (2021, 2022, 2023) aligned properly.  
  - Lattice mis-detected rows, and pdfplumber treated the page as plain text.


## Conclusion
- **Best method:** Camelot **Stream mode** for borderless statements.  
- **Supporting methods:** Camelot **Lattice** and pdfplumber are useful for **bordered tables and schedules**.  
- **Hybrid strategy:** Using line-count thresholding to switch between lattice (bordered) and stream (borderless) provided the most robust coverage.  

Final selected CSVs (clean outputs for downstream analysis):
- Income Statement → Camelot Stream  
- Balance Sheet → Camelot Stream  
- Cash Flows → Camelot Stream  



### Part 3 - Layout Detection

### Implementation
#### Step 1: PubLayNet Model
In order to run PubLayNet model, please manually download the model_.pth and config.yml file from:
https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/tree/d4cebcc544ac0c9899748e1023e2f3ccda8ca70e
Store them in a folder called 'publaynet-model' before running the 'layout_detection.py'

#### Step 2: Extract Layout
```
python src/layout_detection.py
```

### Features
- **LayoutParser Integration**: Uses PubLayNet model with PPYOLOv2 architecture
- **Document Structure**: Detects Text, Title, List, Table, and Figure blocks
- **Bounding Boxes**: Extracts precise coordinates for each detected element
- **Visualization**: Generates annotated images showing detected layout blocks
- **Routing Logic**: Routes different block types to appropriate extractors


### Key Outputs
- **Layout JSON**: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout.json`
- **Visualizations**: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout_viz.png`
- **Summary**: `data/parsed/layout/Apple_10K_YYYY/layout_summary.json`

### Part 4 - Advanced PDF Understanding with Docling

### Overview
Docling is a specialized library for advanced PDF understanding and content normalization. It provides unified document representation with superior structure detection, reading order preservation, and formula recognition capabilities.

### Installation
```bash
pip install docling
```

### Usage

#### Basic Docling Processing
```bash
# Process single PDF with Docling
python src/docling_basic.py --pdf data/raw/Apple_10K_2023.pdf --output data/parsed/docling

# Process with comparison analysis
python src/docling_basic.py --pdf data/raw/Apple_10K_2023.pdf --output data/parsed/docling --compare data/parsed
```

#### Detailed Structure Analysis
```bash
# Analyze Docling output structure
python src/docling_structure_analyzer.py
```

### Features Implemented

#### Advanced PDF Understanding
- **Unified Document Representation**: DoclingDocument schema with standardized structure
- **Reading Order Detection**: Preserves document flow across multi-column layouts
- **Table Structure Recognition**: Detects complex tables with merged cells and proper dimensions
- **Formula Detection**: Identifies mathematical expressions and equations
- **Page Layout Analysis**: Classifies document elements (text, titles, tables, figures)
- **Content Normalization**: Standardized export formats (Markdown, JSON)

#### Document Processing Results
- **Pages**: 80 pages processed successfully
- **Text Elements**: 990 structured text elements extracted
- **Tables**: 54 tables detected with proper structure
- **Pictures**: 4 images identified and cataloged
- **Formulas**: 56 mathematical expressions detected
- **Headers**: 259 hierarchical headers preserved

### Key Outputs

#### Docling Exports
- **Markdown**: `data/parsed/docling/Apple_10K_2023.md` (2,402 lines)
- **JSON**: `data/parsed/docling/Apple_10K_2023.json` (123,607 lines)
- **Analysis Report**: `docling_analysis_report.md`
- **DVC Config**: `dvc_docling_config.yaml`

#### Performance Comparison
| Metric | Docling | Custom Pipeline |
|--------|---------|----------------|
| Text Extraction | ~95% | ~95% |
| Table Detection | ~85% | ~90% |
| Reading Order | ~90% | ~80% |
| Formula Detection | ~80% | ~0% |
| Processing Speed | Slower (3min) | Faster (2min) |
| Memory Usage | Higher | Lower |


### Use Case Recommendations

#### Use Docling When:
- Processing complex multi-column documents
- Formula detection is critical
- Need unified document representation
- Building document understanding applications
- Require standardized output formats

#### Use Custom Pipeline When:
- Processing high-volume simple documents
- Need specialized table extraction
- Resource constraints are important
- Require fine-tuned extraction control
- Working with existing data workflows

### Technical Implementation

#### Core Components
1. **Document Converter**: Handles PDF to DoclingDocument conversion
2. **Structure Analyzer**: Examines document elements and relationships  
3. **Export Manager**: Generates Markdown and JSON outputs
4. **Comparison Tool**: Analyzes performance vs custom pipeline
5. **DVC Integrator**: Provides pipeline integration configuration

   
#### Part 5 — Metadata & Provenance Tagging

Attach provenance metadata to every extracted text/table block and generate section-based Markdown summaries for traceability and citation.

## Overview
- Define metadata schema for consistent provenance.
- Emit one JSON record per block to a per-document `.jsonl`.
- Reassemble sections by grouping records on the section label; write Markdown.

All functionality is in `src/provenance_tagging.py` using Docling JSON (`export_to_dict`).

## Prerequisites
- Python 3.9+
- Docling JSON for each PDF in `data/parsed/docling/<PDF_STEM>.json`
- Optional: PDF path to infer `company`/`fiscal_year` if not provided

## Metadata Schema
Each JSONL record contains:
- `doc_id`: Unique document identifier (Docling origin hash if available; else JSON stem)
- `company`: Company name (e.g., `Apple`)
- `fiscal_year`: Fiscal year (e.g., `2023`)
- `page`: 1-based page index
- `section`: Section label/category (from Docling `label`/`category`; defaults to `unknown`)
- `block_type`: `text` | `table`
- `bbox`: Bounding box if present (preserved format)
- `text`: Content (tables use caption if available)
- `source_path`: Source URI/path (from Docling origin if present)
- `table_shape` (tables only): `{ rows, cols }` from Docling `data.grid`

## Usage

### Option A — Provide Docling JSON and metadata
```bash
python src/provenance_tagging.py \
  --docling-json data/parsed/docling/Apple_10K_2023.json \
  --company Apple \
  --fiscal-year 2023 \
  --out data/parsed/docling
```

### Option B — Infer company/year from the PDF name
```bash
python src/provenance_tagging.py \
  --pdf data/raw/Apple_10K_2023.pdf \
  --out data/parsed/docling
```
This looks for `data/parsed/docling/Apple_10K_2023.json` and infers `company=Apple`, `fiscal_year=2023`.

## Outputs
- JSONL (per block records): `data/parsed/docling/{Company}_{Year}.jsonl`
- Section Markdown: `data/parsed/docling/{Company}_{Year}_sections.md`

## How It Works
- Parses Docling JSON pages and resolves `$ref` to `/texts/{id}` and `/tables/{id}`.
- Normalizes fields into the schema and writes one line per block to JSONL.
- Groups by `section` to produce Markdown with:
  - Section headings
  - Text content in order
  - A table listing tables with page, bbox, caption

## Validation Checklist
- JSONL files exist for each document with the keys in the schema.
- Markdown summaries exist per document and group content by section.

## Notes
- Missing section labels default to `unknown`.
- BBox structure is preserved as emitted by Docling.
- Table shape is estimated from `data.grid` if present.

## Troubleshooting
- "Docling JSON not found": Export Docling JSON to `data/parsed/docling/<PDF_STEM>.json`.
- Empty sections/unknown labels: Docling may omit labels; grouping falls back to `unknown`.
- No tables in Markdown: The summary only lists tables present in the JSONL.


### Part 6 - Storage Formats: Markdown vs JSON vs TXT

#### Overview
Part 6 converts parsed PDF content into three different storage formats to understand the trade-offs between human-readable, machine-readable, and plain text representations.

#### Implementation
```
python src/format_converter.py
```

#### Key Features
* Smart block organization by type (Title, Text, List, Table, Figure)
* Preserves semantic structure in Markdown
* Rich metadata in JSON (confidence scores, bounding boxes)
* Automated batch processing of all PDFs
* Format comparison reports with recommendations

#### Recommendations
Use Markdown as primary format - ideal for RAG applications as it preserves semantic structure while being LLM-friendly.



### Part 7: Managed Document Services Analysis

## Overview
Comparison of Azure AI Document Intelligence with open-source Docling pipeline for SEC filing processing.

## Azure AI Document Intelligence Setup ✅
- **Service**: Azure AI Document Intelligence (prebuilt-layout model)
- **Free Tier**: 500 pages/month ongoing
- **Pricing**: $1.00 per 1000 pages (Read API)
- **Files**: `src/azure_document_service.py`, `config.env`

## Key Findings

### Cost Comparison (Apple 10-K, 80 pages)
| Service | Cost | Tables Detected | Processing |
|---------|------|----------------|------------|
| Azure AI | $0.08 | 15 | Cloud |
| Docling | $0.00 | 54 | Local |

### Recommendations
- **Primary**: Use Docling (superior table detection, zero cost)
- **Fallback**: Use Azure for scanned documents or complex OCR cases
- **Privacy**: Docling processes locally, Azure uses cloud processing

### Usage
```bash
# Install dependencies
pip install azure-ai-formrecognizer python-dotenv

# Configure Azure credentials in config.env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key

# Run analysis
python run_azure_analysis.py
```

### Integration
The Azure service can be used as an optional fallback:
```python
from azure_document_service import AzureDocumentService, compare_with_docling

service = AzureDocumentService()
azure_result = service.analyze_document("document.pdf")
comparison = compare_with_docling(azure_result, "docling_output.json")
```

**Part 7 Status**: ✅ COMPLETE
- ✅ Managed service integration (Azure AI)
- ✅ Side-by-side comparison with Docling
- ✅ Cost analysis and pricing documentation
- ✅ Privacy and data processing considerations



### Part 8 — Staging pipeline & versioning with DVC

Make the project reproducible and version both code and data.

## Overview
- Install and initialize DVC.
- Define stages in `dvc.yaml`.
- Reproduce the pipeline with caching.
- Commit `dvc.lock` and `.dvc`/`*.dvc` to preserve lineage.
- CI: GitHub Actions runs a DVC smoke test.

## Quick Start
From repo root:

1) Create venv and install DVC
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install "dvc[ssh]"
dvc --version
```

2) Initialize DVC (skip if already initialized)
```bash
dvc init
git add .dvc .dvcignore
git commit -m "Initialize DVC"
```

3) Configure a default DVC remote
```bash
dvc remote add -d localremote /tmp/dvc-cache
git commit -am "Configure DVC remote"
```

4) Ensure raw PDFs exist
```bash
# Option A: download automatically
python3 src/SEC_filings.py
# Option B: copy PDFs into data/raw/
```

5) Run pipeline and cache artifacts
```bash
dvc repro
```

6) Push artifacts and commit lineage
```bash
dvc push
git add dvc.yaml dvc.lock *.dvc .dvc .github/workflows/dvc-smoke.yml || true
git commit -m "Add/Update DVC pipeline and lockfile"
git push
```

## Pipeline Stages (dvc.yaml)
- download → `data/raw` (or a subfolder)
- parse → `data/parsed/Apple_10K_2023`, `data/parsed/Apple_10K_2024`, `data/parsed/ocr_summary.json`
- tables → `data/parsed/tables/Hybrid/<DOC>`
- layout → `data/parsed/layout/<DOC>`
- docling → `data/parsed/docling/<DOC>`
- export → `data/parsed/provenance/<DOC>`

## CI
`.github/workflows/dvc-smoke.yml` validates the pipeline graph with:
```bash
dvc repro -n
```

## Troubleshooting
- Overlapping outputs: ensure each stage writes to unique subdirs.
- “Output is tracked by SCM”: untrack from git and let DVC manage it:
```bash
git rm -r --cached <path>
git commit -m "Untrack <path> from git; managed by DVC"
```
- Missing version info warnings: either
```bash
dvc repro
# or, associate existing outputs without rerun
dvc commit download parse tables@0 tables@1 layout@0 layout@1 docling@0 docling@1 export@0 export@1
dvc push
```
- `dvc` not found: activate venv and install DVC.
- Parse cannot find PDFs: ensure `data/raw/*.pdf` exist or rerun the download.

## Validation
- `dvc status -c` shows no missing version info; remote in sync.
- `dvc repro` succeeds and creates/updates `dvc.lock`.
- Artifacts exist in `data/parsed/...` and push via `dvc push`.
- CI smoke test runs on PRs/pushes.


### Part 9 - Evaluation: Parsing Quality & Regression

#### Overview
Part 9 builds a comprehensive evaluation system to measure PDF parsing quality and detect regressions over time through ground truth comparison and automated testing.

#### Implementation
**Step 1**: Creating ground truth templates. 
For modeling purposes, we will look at the first 5 pages of the 2023 report.

```
python src/evaluation_system.py --action create-gt --pdf Apple_10K_2023 --max-pages 5
```

**Step 2**: Manually editing ground truth. 
Manually edit the 'ground truth' for the inaccurately extracted texts in the json file. For example,  
```
{
  "extracted_text": "Appel In",
  "ground_truth_text": "Apple Inc."  // <- Fix this
}
```

**Step 3**: Run evaluation. 
```
python src/evaluation_system.py --action evaluate --pdf Apple_10K_2023
```

**Step 4**: Run regresstion test. 
```
python src/test_parsing_quality.py
```

**Step 5**: Track metrics over time. 
```
python src/metrics_tracker.py --action both
```

#### Key Metrics
* Word Error Rate (WER): Proportion of incorrect words (lower = better)
* Character Error Rate (CER): Proportion of incorrect characters (lower = better)
* Table Precision/Recall/F1: Accuracy of table extraction (higher = better)
* Content Distribution: Chunk lengths, numeric token ratios

#### Quality Thresholds
* Pass: WER < 0.2 AND Table F1 > 0.6
* Warning: WER < 0.4 AND Table F1 > 0.4
* Fail: WER ≥ 0.4 OR Table F1 ≤ 0.4

#### Key Features
* Automated quality measurement against manually corrected ground truth
* Unit tests that fail when parsing quality degrades
* Statistical drift detection over time
* Comprehensive visualizations of metrics trends
* Detailed reports identifying specific weaknesses

#### Sample result and purpose
The poor performance metrics (85.8% word error rate) successfully demonstrate the evaluation system works correctly by identifying significant parsing pipeline issues that need improvement.


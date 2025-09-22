# DAMG7245 Assignment 1 AI-Powered PDF Parsing System

## Project Overview
This project focuses on analyzing SEC EDGAR filings, specifically Apple Inc.'s 10-K annual reports for 2023 and 2024. The assignment involves downloading, parsing, and analyzing financial data from SEC filings using big data techniques.

## Project Structure
```
damg7245-assignment1/
├── data/
│   ├── raw/                    # Raw PDF files
│   │   ├── Apple_10K_2023.pdf
│   │   ├── Apple_10K_2024.pdf
│   │   └── sec-edgar-filings/  # Downloaded SEC filings metadata
├── parsed/                     # Processed text files
│   ├── Apple_10K_2023/        # Per-page text files
│   │   ├── page_001.txt
│   │   ├── page_001_bboxes.json
│   │   └── ...
│   ├── Apple_10K_2024/
│   └── ocr_summary.json
├── src/                       # Source code
│   └── extract_pdf_text.py   # PDF text extraction script
└── README.md
```

## Installation & Dependencies

### Required Python Packages
```bash
# Core dependencies
pip install sec-edgar-downloader pdfplumber pytesseract Pillow requests

# Individual installations (if needed)
pip install sec-edgar-downloader  # SEC filings download
pip install pdfplumber            # PDF text extraction
pip install pytesseract           # OCR functionality
pip install Pillow               # Image processing
pip install requests             # HTTP requests
pip install layoutparser[ocr]    # LayoutParser to detect document layout
pip install 'git+https://github.com/facebookresearch/detectron2.git'    # detectron2 which is needed along with LayoutParser
# note: you may need to uninstall layoutparser and reinstall in order to use detectron2, for installation guide:
https://github.com/Layout-Parser/layout-parser/blob/main/installation.md
# for uninstallation,
pip uninstall layoutparser detectron2   # OPTIONAL, where needed

```


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

#### Step 6: PubLayNet Model
In order to run PubLayNet model, please manually download the model_.pth and config.yml file from:
https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/tree/d4cebcc544ac0c9899748e1023e2f3ccda8ca70e
Store them in a folder called 'publaynet-model' before running the 'layout_detection.py'

#### Step 7: Extract Layout
```
python src/layout_detection.py
```

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

---

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

---

## Conclusion
- **Best method:** Camelot **Stream mode** for borderless statements.  
- **Supporting methods:** Camelot **Lattice** and pdfplumber are useful for **bordered tables and schedules**.  
- **Hybrid strategy:** Using line-count thresholding to switch between lattice (bordered) and stream (borderless) provided the most robust coverage.  

Final selected CSVs (clean outputs for downstream analysis):
- Income Statement → Camelot Stream  
- Balance Sheet → Camelot Stream  
- Cash Flows → Camelot Stream  



### Part 3 - Layout Detection
- **LayoutParser Integration**: Uses PubLayNet model with PPYOLOv2 architecture
- **Document Structure**: Detects Text, Title, List, Table, and Figure blocks
- **Bounding Boxes**: Extracts precise coordinates for each detected element
- **Visualization**: Generates annotated images showing detected layout blocks
- **Routing Logic**: Routes different block types to appropriate extractors


### Key Outputs
- **Layout JSON**: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout.json`
- **Visualizations**: `data/parsed/layout/Apple_10K_YYYY/page_XXX_layout_viz.png`
- **Summary**: `data/parsed/layout/Apple_10K_YYYY/layout_summary.json`

## Part 4 - Advanced PDF Understanding with Docling

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

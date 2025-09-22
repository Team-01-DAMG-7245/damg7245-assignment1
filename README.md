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

#### Step ?: PubLayNet Model
In order to run PubLayNet model, please manually download the model_.pth and config.yml file from:
https://huggingface.co/nlpconnect/PubLayNet-faster_rcnn_R_50_FPN_3x/tree/d4cebcc544ac0c9899748e1023e2f3ccda8ca70e
Store them in a folder called 'publaynet-model' before running the 'layout_detection.py'

#### Step ?: Extract Layout
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
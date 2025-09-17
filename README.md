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
```

### System Requirements
- **Tesseract OCR**: Required for OCR fallback functionality
  - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

## Usage

### Part 1: PDF Text Extraction

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

## Features Implemented

### ✅ Part 1 - Text Extraction from PDFs
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


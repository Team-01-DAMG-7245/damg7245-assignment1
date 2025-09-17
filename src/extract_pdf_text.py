"""
PDF Text Extraction - DAMG7245 Assignment 1 Part 1
Extract per-page text from PDFs using pdfplumber with OCR fallback
"""

import pdfplumber
import pytesseract
from pathlib import Path
import json

def extract_pdf_pages(pdf_path, output_dir="data/parsed"):
    """
    Extract text from each page of a PDF and save as individual .txt files
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save extracted text files
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    # Create output directory for this PDF
    pdf_output_dir = output_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    ocr_pages = []  # Track pages that needed OCR
    
    print(f"Processing PDF: {pdf_path.name}")
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}/{total_pages}", end=" ")
            
            # Extract text using pdfplumber with experimental layout parameters
            text = page.extract_text(
                x_density=2.0,  
                y_density=2.0   
            )
            
            # Check if text was extracted
            if text and text.strip():
                print("- Text extracted")
                extracted_text = text
            else:
                print("- No text found, applying OCR...")
                # Apply OCR fallback
                try:
                    # Convert page to image for OCR
                    img = page.to_image(resolution=300)
                    pil_image = img.original
                    
                    # Perform OCR using Tesseract
                    extracted_text = pytesseract.image_to_string(pil_image, config='--psm 6')
                    ocr_pages.append(page_num)
                    print("  OCR completed")
                except Exception as e:
                    print(f"  OCR failed: {e}")
                    extracted_text = ""
            
            # Extract word bounding boxes for layout analysis
            word_bboxes = []
            try:
                words = page.extract_words()
                word_bboxes = [
                    {
                        'text': word['text'],
                        'x0': word['x0'],
                        'y0': word['y0'], 
                        'x1': word['x1'],
                        'y1': word['y1'],
                        'fontname': word.get('fontname', ''),
                        'size': word.get('size', 0)
                    }
                    for word in words
                ]
            except Exception as e:
                print(f"  Warning: Could not extract word bboxes: {e}")
            
            # Save page text to individual .txt file
            page_filename = f"page_{page_num:03d}.txt"
            page_file_path = pdf_output_dir / page_filename
            
            with open(page_file_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            # Save word bounding boxes if available
            if word_bboxes:
                bbox_filename = f"page_{page_num:03d}_bboxes.json"
                bbox_file_path = pdf_output_dir / bbox_filename
                
                with open(bbox_file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'page_number': page_num,
                        'word_count': len(word_bboxes),
                        'words': word_bboxes
                    }, f, indent=2)
    
    # Log pages that required OCR
    if ocr_pages:
        ocr_log_file = pdf_output_dir / "ocr_pages.json"
        with open(ocr_log_file, 'w') as f:
            json.dump({
                "pdf_name": pdf_path.name,
                "pages_requiring_ocr": ocr_pages,
                "total_ocr_pages": len(ocr_pages)
            }, f, indent=2)
        
        print(f"OCR was applied to {len(ocr_pages)} pages: {ocr_pages}")
        print(f"OCR log saved to: {ocr_log_file}")
    
    print(f"All pages saved to: {pdf_output_dir}")
    return pdf_output_dir, ocr_pages

def process_all_pdfs(input_dir="data/raw", output_dir="data/parsed"):
    """
    Process all PDF files from raw folder and extract per-page text to parsed folder
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files in raw folder
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        print("Make sure to run SEC_filings.py first to download Apple 10-K PDFs")
        return
    
    print("DAMG7245 Assignment 1 - Part 1: PDF Text Extraction")
    print("=" * 55)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    print("=" * 55)
    
    all_ocr_info = {}
    
    for pdf_file in pdf_files:
        try:
            output_path, ocr_pages = extract_pdf_pages(pdf_file, output_dir)
            all_ocr_info[pdf_file.name] = ocr_pages
            print("-" * 50)
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
            continue
    
    # Save overall OCR summary
    summary_file = output_dir / "ocr_summary.json"
    total_ocr_pages = sum(len(pages) for pages in all_ocr_info.values())
    
    with open(summary_file, 'w') as f:
        json.dump({
            "processed_pdfs": list(all_ocr_info.keys()),
            "ocr_pages_by_pdf": all_ocr_info,
            "total_pdfs_processed": len(all_ocr_info),
            "total_pdfs_with_ocr": sum(1 for pages in all_ocr_info.values() if pages),
            "total_ocr_pages": total_ocr_pages
        }, f, indent=2)
    
    print("\n" + "=" * 55)
    print("✅ PDF TEXT EXTRACTION COMPLETE!")
    print("=" * 55)
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 PDFs processed: {len(all_ocr_info)}")
    print(f"🔍 Pages requiring OCR: {total_ocr_pages}")
    print(f"📊 OCR summary saved to: {summary_file}")
    print("\n📋 Checkpoints completed:")
    print("✅ Per-page .txt files created for each PDF")
    print("✅ OCR applied to pages with no text")
    print("✅ OCR pages logged and tracked")
    print("✅ Word bounding boxes extracted and saved")
    print("=" * 55)

if __name__ == "__main__":
    process_all_pdfs()

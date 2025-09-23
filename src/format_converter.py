#!/usr/bin/env python3
# complete_pdf_converter.py
# Complete solution to convert all processed PDFs to Markdown, JSON, and TXT formats

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import pdfplumber
from datetime import datetime


class CompletePDFConverter:
    """Complete converter for all processed PDFs to multiple formats"""
    
    def __init__(self, raw_dir="data/raw", layout_base_dir="data/parsed/layout", output_dir="data/converted"):
        self.raw_dir = Path(raw_dir)
        self.layout_base_dir = Path(layout_base_dir)
        
        # Create organized subdirectories
        self.reports_dir = Path("reports")  # Only comparison reports here
        self.parsed_converted_dir = Path("data/parsed/converted")  # All converted content here
        
        # Create all directories
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_converted_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each format in data/parsed/converted/
        self.markdown_dir = self.parsed_converted_dir / "markdown"
        self.json_dir = self.parsed_converted_dir / "json"
        self.txt_dir = self.parsed_converted_dir / "txt"
        
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.txt_dir.mkdir(parents=True, exist_ok=True)
        
    def find_processed_pdfs(self) -> List[tuple]:
        """Find all PDFs that have been processed with layout detection"""
        processed_pdfs = []
        
        for pdf_file in self.raw_dir.glob("*.pdf"):
            layout_dir = self.layout_base_dir / pdf_file.stem
            if layout_dir.exists() and (layout_dir / "layout_summary.json").exists():
                processed_pdfs.append((pdf_file, layout_dir))
        
        return processed_pdfs
    
    def extract_text_by_blocks(self, pdf_path: Path, layout_dir: Path) -> List[Dict]:
        """Extract text content organized by detected blocks"""
        # Load page layouts
        page_layouts = []
        layout_files = sorted(layout_dir.glob("page_*_layout.json"))
        
        for layout_file in layout_files:
            with open(layout_file, 'r') as f:
                page_layouts.append(json.load(f))
        
        extracted_pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page_layout in enumerate(page_layouts, 1):
                if page_num > len(pdf.pages):
                    break
                    
                page = pdf.pages[page_num - 1]
                
                page_content = {
                    "page_number": page_num,
                    "blocks": []
                }
                
                for block in page_layout["blocks"]:
                    bbox = block["bbox"]
                    
                    try:
                        # Crop page to block bounds
                        cropped_page = page.crop((bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]))
                        text = cropped_page.extract_text() or ""
                        text = self._clean_text(text)
                        
                        # For tables, try to extract structured data
                        table_data = None
                        if block["type"] == "Table":
                            table_data = self._extract_table_data(cropped_page)
                        
                        page_content["blocks"].append({
                            "block_id": block["block_id"],
                            "type": block["type"],
                            "confidence": block["confidence"],
                            "bbox": bbox,
                            "text": text,
                            "table_data": table_data
                        })
                        
                    except Exception as e:
                        print(f"    Warning: Error extracting block {block['block_id']} on page {page_num}: {e}")
                        continue
                
                extracted_pages.append(page_content)
        
        return extracted_pages
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        return '\n'.join(lines)
    
    def _extract_table_data(self, cropped_page) -> List[List[str]]:
        """Extract structured table data"""
        try:
            tables = cropped_page.find_tables()
            if tables:
                return tables[0].extract()
        except Exception:
            pass
        return None
    
    def convert_to_markdown(self, pdf_name: str, extracted_pages: List[Dict]) -> str:
        """Convert extracted content to Markdown format"""
        markdown_lines = [
            f"# {pdf_name}",
            "",
            f"*Converted from PDF on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Total pages: {len(extracted_pages)}*",
            "",
            "---",
            ""
        ]
        
        for page_content in extracted_pages:
            page_num = page_content["page_number"]
            markdown_lines.append(f"## Page {page_num}")
            markdown_lines.append("")
            
            # Group blocks by type for better organization
            blocks_by_type = self._group_blocks_by_type(page_content["blocks"])
            
            # Process in logical order
            for block_type in ["Title", "Text", "List", "Table", "Figure"]:
                if block_type in blocks_by_type:
                    for block in blocks_by_type[block_type]:
                        markdown_lines.extend(self._block_to_markdown(block))
            
            markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    def _group_blocks_by_type(self, blocks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group blocks by their type and sort by position"""
        grouped = {}
        for block in blocks:
            block_type = block["type"]
            if block_type not in grouped:
                grouped[block_type] = []
            grouped[block_type].append(block)
        
        # Sort blocks within each type by position (top to bottom, left to right)
        for block_type in grouped:
            grouped[block_type].sort(key=lambda b: (b["bbox"]["y1"], b["bbox"]["x1"]))
        
        return grouped
    
    def _block_to_markdown(self, block: Dict) -> List[str]:
        """Convert a single block to Markdown format"""
        lines = []
        text = block["text"]
        block_type = block["type"]
        
        if not text.strip():
            return lines
        
        if block_type == "Title":
            level = self._determine_heading_level(block)
            lines.extend([f"{'#' * level} {text}", ""])
            
        elif block_type == "Text":
            lines.extend([text, ""])
            
        elif block_type == "List":
            list_items = self._text_to_list_items(text)
            for item in list_items:
                lines.append(f"- {item}")
            lines.append("")
            
        elif block_type == "Table":
            if block["table_data"]:
                table_md = self._table_data_to_markdown(block["table_data"])
                lines.extend(table_md)
            else:
                lines.extend(["```", text, "```"])
            lines.append("")
            
        elif block_type == "Figure":
            lines.extend([f"*[Figure: {text or 'Image content'}]*", ""])
        
        return lines
    
    def _determine_heading_level(self, block: Dict) -> int:
        """Determine heading level based on text characteristics"""
        text = block["text"]
        if len(text) < 30 and text.isupper():
            return 2
        elif len(text) < 50:
            return 3
        else:
            return 4
    
    def _text_to_list_items(self, text: str) -> List[str]:
        """Convert text to list items"""
        lines = text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if line:
                line = line.lstrip('•-*1234567890.() ')
                if line:
                    items.append(line)
        
        return items
    
    def _table_data_to_markdown(self, table_data: List[List[str]]) -> List[str]:
        """Convert table data to Markdown table format"""
        if not table_data or len(table_data) < 2:
            return []
        
        lines = []
        header = table_data[0]
        lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        
        for row in table_data[1:]:
            padded_row = row + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(str(cell or "") for cell in padded_row[:len(header)]) + " |")
        
        return lines
    
    def convert_to_json(self, pdf_name: str, extracted_pages: List[Dict], layout_summary: Dict) -> Dict[str, Any]:
        """Convert extracted content to structured JSON format"""
        json_data = {
            "document": {
                "filename": pdf_name,
                "conversion_timestamp": datetime.now().isoformat(),
                "total_pages": len(extracted_pages),
                "layout_summary": layout_summary.get("overall_block_counts", {}),
            },
            "pages": []
        }
        
        for page_content in extracted_pages:
            page_data = {
                "page_number": page_content["page_number"],
                "content": {
                    "titles": [],
                    "text_blocks": [],
                    "lists": [],
                    "tables": [],
                    "figures": []
                },
                "layout_info": {
                    "total_blocks": len(page_content["blocks"]),
                    "block_types": {}
                }
            }
            
            for block in page_content["blocks"]:
                block_type = block["type"]
                content_item = {
                    "block_id": block["block_id"],
                    "confidence": block["confidence"],
                    "bbox": block["bbox"],
                    "text": block["text"]
                }
                
                if block_type == "Title":
                    content_item["heading_level"] = self._determine_heading_level(block)
                    page_data["content"]["titles"].append(content_item)
                elif block_type == "Text":
                    page_data["content"]["text_blocks"].append(content_item)
                elif block_type == "List":
                    content_item["items"] = self._text_to_list_items(block["text"])
                    page_data["content"]["lists"].append(content_item)
                elif block_type == "Table":
                    if block["table_data"]:
                        content_item["table_data"] = block["table_data"]
                        content_item["rows"] = len(block["table_data"])
                        content_item["columns"] = len(block["table_data"][0]) if block["table_data"] else 0
                    page_data["content"]["tables"].append(content_item)
                elif block_type == "Figure":
                    page_data["content"]["figures"].append(content_item)
                
                page_data["layout_info"]["block_types"][block_type] = \
                    page_data["layout_info"]["block_types"].get(block_type, 0) + 1
            
            json_data["pages"].append(page_data)
        
        return json_data
    
    def convert_to_txt(self, pdf_name: str, extracted_pages: List[Dict]) -> str:
        """Convert extracted content to plain text format"""
        txt_lines = [
            f"PLAIN TEXT VERSION: {pdf_name}",
            f"Converted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total pages: {len(extracted_pages)}",
            "",
            "=" * 50,
            ""
        ]
        
        for page_content in extracted_pages:
            page_num = page_content["page_number"]
            txt_lines.extend([f"PAGE {page_num}", "-" * 20, ""])
            
            blocks_sorted = sorted(page_content["blocks"], 
                                 key=lambda b: (b["bbox"]["y1"], b["bbox"]["x1"]))
            
            for block in blocks_sorted:
                if block["text"].strip():
                    txt_lines.extend([block["text"], ""])
            
            txt_lines.append("")
        
        return "\n".join(txt_lines)
    
    def generate_format_report(self, pdf_name: str, md_size: int, json_size: int, txt_size: int) -> str:
        """Generate a comparison report of the different formats"""
        return f"""# Format Comparison Report: {pdf_name}

## File Sizes
- **Markdown**: {md_size:,} characters
- **JSON**: {json_size:,} characters  
- **Plain Text**: {txt_size:,} characters

## Format Analysis

### 📝 Markdown (.md)
**Best for: RAG pipelines, LLM processing, human review**

**Advantages:**
- ✅ Preserves semantic structure (headings, lists, tables)
- ✅ Human-readable and editable
- ✅ Well-understood by LLMs
- ✅ Maintains document hierarchy
- ✅ Good balance of structure and readability

**Use cases:**
- RAG document ingestion
- LLM fine-tuning data
- Documentation generation
- Human review and editing

### 🔧 JSON (.json)
**Best for: APIs, databases, programmatic access**

**Advantages:**
- ✅ Fully structured and queryable
- ✅ Preserves metadata (confidence scores, bounding boxes)
- ✅ Easy programmatic access
- ✅ Can store complex nested data
- ✅ Ideal for search and filtering

**Use cases:**
- Document databases
- Search indexing
- Programmatic analysis
- Metadata-rich applications

### 📄 Plain Text (.txt)
**Best for: Simple text processing, baseline storage**

**Advantages:**
- ✅ Smallest file size
- ✅ Universal compatibility
- ✅ Simple processing

**Disadvantages:**
- ❌ **ALL STRUCTURE IS LOST**
- ❌ No semantic information
- ❌ No metadata preservation
- ❌ Difficult to reconstruct original layout

## 🎯 Recommendation for RAG Pipeline

**Primary format: Markdown**
- Perfect for RAG applications
- Preserves semantic structure needed for context
- LLM-friendly format
- Maintains document hierarchy for better retrieval

**Secondary format: JSON**  
- For applications requiring programmatic access
- When metadata (confidence, coordinates) is needed
- For building search indexes

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def convert_single_pdf(self, pdf_path: Path, layout_dir: Path) -> Dict[str, Path]:
        """Convert a single PDF to all formats"""
        pdf_name = pdf_path.stem
        
        print(f"  📄 Extracting text content...")
        extracted_pages = self.extract_text_by_blocks(pdf_path, layout_dir)
        
        if not extracted_pages:
            print(f"  ❌ No content extracted from {pdf_name}")
            return {}
        
        # Load layout summary
        summary_file = layout_dir / "layout_summary.json"
        layout_summary = {}
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                layout_summary = json.load(f)
        
        print(f"  📝 Converting to Markdown...")
        markdown_content = self.convert_to_markdown(pdf_name, extracted_pages)
        
        print(f"  🔧 Converting to JSON...")
        json_content = self.convert_to_json(pdf_name, extracted_pages, layout_summary)
        
        print(f"  📄 Converting to plain text...")
        txt_content = self.convert_to_txt(pdf_name, extracted_pages)
        
        # Save files to organized directories
        md_file = self.markdown_dir / f"{pdf_name}.md"
        json_file = self.json_dir / f"{pdf_name}.json"
        txt_file = self.txt_dir / f"{pdf_name}.txt"
        report_file = self.reports_dir / f"{pdf_name}_format_report.md"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        # Generate and save format report
        report_content = self.generate_format_report(
            pdf_name, len(markdown_content), len(json.dumps(json_content)), len(txt_content)
        )
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"  ✅ Files saved:")
        print(f"     - data/parsed/converted/markdown/{md_file.name}")
        print(f"     - data/parsed/converted/json/{json_file.name}")
        print(f"     - data/parsed/converted/txt/{txt_file.name}")
        print(f"     - reports/{report_file.name}")
        
        return {
            "markdown": md_file,
            "json": json_file,
            "txt": txt_file,
            "report": report_file
        }
    
    def convert_all_pdfs(self) -> Dict[str, Any]:
        """Convert all processed PDFs to multiple formats"""
        print("🔍 Finding processed PDFs...")
        processed_pdfs = self.find_processed_pdfs()
        
        if not processed_pdfs:
            print("❌ No processed PDFs found!")
            print(f"Looking for layout results in: {self.layout_base_dir}")
            print("Make sure you've run layout detection first!")
            return {"success": False, "results": []}
        
        print(f"Found {len(processed_pdfs)} processed PDFs:")
        for pdf_file, _ in processed_pdfs:
            print(f"  - {pdf_file.name}")
        
        print(f"\n🔄 Converting all PDFs to multiple formats...")
        print(f"Organized output directories created")
        
        results = []
        success_count = 0
        
        for pdf_file, layout_dir in processed_pdfs:
            try:
                print(f"\n{'='*60}")
                print(f"Converting: {pdf_file.name}")
                print(f"{'='*60}")
                
                files = self.convert_single_pdf(pdf_file, layout_dir)
                if files:
                    results.append({
                        "pdf_name": pdf_file.name,
                        "status": "success",
                        "files": files
                    })
                    success_count += 1
                else:
                    results.append({
                        "pdf_name": pdf_file.name,
                        "status": "failed",
                        "error": "No content extracted"
                    })
                
            except Exception as e:
                print(f"❌ Error converting {pdf_file.name}: {e}")
                results.append({
                    "pdf_name": pdf_file.name,
                    "status": "failed",
                    "error": str(e)
                })
                continue
        
        # Summary
        print(f"\n🎉 CONVERSION COMPLETE!")
        print(f"Successfully converted: {success_count}/{len(processed_pdfs)} PDFs")
        
        # Count files in their respective locations
        md_files = list(self.markdown_dir.glob("*.md"))
        json_files = list(self.json_dir.glob("*.json"))
        txt_files = list(self.txt_dir.glob("*.txt"))
        report_files = list(self.reports_dir.glob("*_format_report.md"))
        
        print(f"\n📁 Generated files in organized structure:")
        print(f"   📝 data/parsed/converted/markdown/ - {len(md_files)} Markdown files")
        print(f"   🔧 data/parsed/converted/json/     - {len(json_files)} JSON files")
        print(f"   📄 data/parsed/converted/txt/      - {len(txt_files)} Text files")
        print(f"   📊 reports/                        - {len(report_files)} Comparison reports")
        
        print(f"\n📂 Directory structure:")
        print(f"   data/parsed/converted/      🔄 All converted content")
        print(f"   ├── markdown/               📝 Markdown files (RAG-ready)")
        print(f"   │   └── *.md")
        print(f"   ├── json/                   🔧 Structured data")
        print(f"   │   └── *.json")
        print(f"   └── txt/                    📄 Plain text")
        print(f"       └── *.txt")
        print(f"   ")
        print(f"   reports/                    📊 Analysis reports")
        print(f"   └── *_format_report.md")
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Use files in data/parsed/converted/markdown/ for RAG pipelines")
        print(f"   Use files in data/parsed/converted/json/ for programmatic access")
        print(f"   Use files in data/parsed/converted/txt/ for plain text processing")
        print(f"   Read reports/ for format comparisons and analysis")
        
        return {
            "success": True,
            "total_processed": len(processed_pdfs),
            "successful_conversions": success_count,
            "results": results
        }


def main():
    parser = argparse.ArgumentParser(description="Convert all processed PDFs to multiple formats")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory containing raw PDFs")
    parser.add_argument("--layout-dir", default="data/parsed/layout", help="Base directory containing layout results")
    parser.add_argument("--output-dir", default="data/converted", help="Output directory for converted files")
    
    args = parser.parse_args()
    
    converter = CompletePDFConverter(args.raw_dir, args.layout_dir, args.output_dir)
    result = converter.convert_all_pdfs()
    
    if not result["success"]:
        exit(1)


if __name__ == "__main__":
    main()
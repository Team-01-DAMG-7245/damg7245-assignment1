#!/usr/bin/env python3
"""
Docling Structure Analysis - Detailed examination of parsed content
"""

import json
from pathlib import Path

def analyze_docling_structure(json_path):
    """Analyze the structure of Docling JSON output"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("DOCLING STRUCTURE ANALYSIS")
    print("=" * 40)
    
    # Basic document info
    print(f"Schema: {data.get('schema_name', 'Unknown')}")
    print(f"Version: {data.get('version', 'Unknown')}")
    print(f"Binary hash: {data.get('origin', {}).get('binary_hash', 'Unknown')}")
    
    # Content analysis
    pages = data.get('pages', [])
    texts = data.get('texts', [])
    tables = data.get('tables', [])
    pictures = data.get('pictures', [])
    
    print(f"\nCONTENT SUMMARY:")
    print(f"Pages: {len(pages)}")
    print(f"Text elements: {len(texts)}")
    print(f"Tables: {len(tables)}")
    print(f"Pictures: {len(pictures)}")
    
    # Reading order analysis
    print(f"\nREADING ORDER ANALYSIS:")
    if pages and len(pages) > 0:
        # Handle different page structure formats
        page_keys = list(pages.keys()) if isinstance(pages, dict) else range(len(pages))
        if page_keys:
            first_page_key = page_keys[0]
            first_page = pages[first_page_key] if isinstance(pages, dict) else pages[0]
            elements = first_page.get('children', [])
            print(f"First page elements: {len(elements)}")
            
            # Analyze element types
            element_types = {}
            for element_ref in elements[:10]:  # First 10 elements
                if isinstance(element_ref, dict):
                    ref_path = element_ref.get('$ref', '')
                    if '/texts/' in ref_path:
                        element_types['text'] = element_types.get('text', 0) + 1
                    elif '/tables/' in ref_path:
                        element_types['table'] = element_types.get('table', 0) + 1
                    elif '/pictures/' in ref_path:
                        element_types['picture'] = element_types.get('picture', 0) + 1
            
            print(f"Element types on first page: {element_types}")
    else:
        print("No pages found in document structure")
    
    # Table analysis
    print(f"\nTABLE ANALYSIS:")
    if tables:
        print(f"Total tables detected: {len(tables)}")
        
        # Analyze first table
        first_table = tables[0]
        table_data = first_table.get('data', {})
        if isinstance(table_data, dict):
            grid = table_data.get('grid', [])
            print(f"First table dimensions: {len(grid)} rows")
            if grid:
                print(f"First table columns: {len(grid[0])}")
        
        # Check for table captions
        captions = [t.get('caption', {}).get('text', '') for t in tables[:3] if t.get('caption')]
        if captions:
            print(f"Sample table captions: {captions}")
    
    # Text analysis
    print(f"\nTEXT ANALYSIS:")
    if texts:
        # Analyze text types/labels
        text_labels = {}
        for text in texts[:50]:  # First 50 text elements
            label = text.get('label', 'unknown')
            text_labels[label] = text_labels.get(label, 0) + 1
        
        print(f"Text element types: {dict(sorted(text_labels.items()))}")
        
        # Sample content
        sample_texts = [t.get('text', '')[:50] for t in texts[:3]]
        print(f"Sample text content:")
        for i, text in enumerate(sample_texts):
            print(f"  {i+1}: {text}...")
    
    # Formula detection
    print(f"\nFORMULA DETECTION:")
    formula_count = 0
    for text in texts:
        content = text.get('text', '')
        # Look for mathematical indicators
        if any(indicator in content for indicator in ['$', '=', '+', '-', '*', '/', '^', '%']):
            if len([c for c in content if c in '=+-*/%^']) > 2:
                formula_count += 1
    
    print(f"Potential formulas detected: {formula_count}")
    
    return {
        'pages': len(pages),
        'texts': len(texts),
        'tables': len(tables),
        'pictures': len(pictures),
        'formulas': formula_count
    }

def compare_markdown_output(md_path):
    """Analyze Markdown output structure"""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\nMARKDOWN ANALYSIS:")
    print("=" * 20)
    
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Count headers
    headers = [line for line in lines if line.startswith('#')]
    print(f"Headers: {len(headers)}")
    
    # Count tables
    table_lines = [line for line in lines if '|' in line and '---' not in line]
    print(f"Table rows: {len(table_lines)}")
    
    # Count images
    images = [line for line in lines if '<!-- image -->' in line or '![' in line]
    print(f"Images: {len(images)}")
    
    # Show structure sample
    print(f"\nDOCUMENT STRUCTURE (first 10 headers):")
    for header in headers[:10]:
        level = len(header.split()[0])
        title = header.replace('#', '').strip()
        print(f"  {'  ' * (level-1)}H{level}: {title[:60]}...")

if __name__ == "__main__":
    json_file = "data/parsed/docling/Apple_10K_2023.json"
    md_file = "data/parsed/docling/Apple_10K_2023.md"
    
    if Path(json_file).exists():
        stats = analyze_docling_structure(json_file)
        
        if Path(md_file).exists():
            compare_markdown_output(md_file)
        
        print(f"\n" + "="*50)
        print("SUMMARY STATISTICS:")
        for key, value in stats.items():
            print(f"{key.capitalize()}: {value}")
    else:
        print(f"JSON file not found: {json_file}")

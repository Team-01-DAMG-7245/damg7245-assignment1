#!/usr/bin/env python3
"""
Simple Azure Document Intelligence integration for document comparison
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

class AzureDocumentService:
    """Simple Azure Document Intelligence wrapper"""
    
    def __init__(self):
        if not AZURE_AVAILABLE:
            raise ImportError("Install azure-ai-formrecognizer: pip install azure-ai-formrecognizer")
        
        endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not endpoint or not key:
            raise ValueError("Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY in config.env")
        
        self.client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))
    
    def analyze_document(self, pdf_path: str) -> dict:
        """Analyze document with Azure Document Intelligence"""
        with open(pdf_path, 'rb') as f:
            poller = self.client.begin_analyze_document("prebuilt-layout", f)
            result = poller.result()
        
        # Extract key metrics
        tables = []
        for table in result.tables:
            table_data = []
            for cell in table.cells:
                if cell.row_index >= len(table_data):
                    table_data.extend([[] for _ in range(cell.row_index + 1 - len(table_data))])
                if cell.column_index >= len(table_data[cell.row_index]):
                    table_data[cell.row_index].extend([''] * (cell.column_index + 1 - len(table_data[cell.row_index])))
                table_data[cell.row_index][cell.column_index] = cell.content
            tables.append(table_data)
        
        return {
            'service': 'Azure Document Intelligence',
            'pages': len(result.pages),
            'tables': len(tables),
            'paragraphs': len(result.paragraphs),
            'cost_estimate': len(result.pages) * 0.001,  # $1 per 1000 pages
            'raw_tables': tables
        }

def compare_with_docling(azure_result: dict, docling_json_path: str) -> dict:
    """Simple comparison between Azure and Docling results"""
    try:
        with open(docling_json_path, 'r', encoding='utf-8') as f:
            docling_data = json.load(f)
    except UnicodeDecodeError:
        with open(docling_json_path, 'r', encoding='utf-8', errors='ignore') as f:
            docling_data = json.load(f)
    
    docling_stats = {
        'pages': len(docling_data.get('pages', {})),
        'tables': len(docling_data.get('tables', [])),
        'texts': len(docling_data.get('texts', []))
    }
    
    return {
        'azure': {
            'pages': azure_result['pages'],
            'tables': azure_result['tables'],
            'paragraphs': azure_result['paragraphs'],
            'cost': f"${azure_result['cost_estimate']:.3f}"
        },
        'docling': {
            'pages': docling_stats['pages'],
            'tables': docling_stats['tables'],
            'texts': docling_stats['texts'],
            'cost': '$0.000'
        },
        'difference': {
            'tables': azure_result['tables'] - docling_stats['tables'],
            'cost_savings_with_docling': f"${azure_result['cost_estimate']:.3f}"
        }
    }

if __name__ == "__main__":
    pdf_path = "data/raw/Apple_10K_2023.pdf"
    docling_json = "data/parsed/docling/Apple_10K_2023.json"
    
    if os.path.exists(pdf_path):
        service = AzureDocumentService()
        azure_result = service.analyze_document(pdf_path)
        
        print("Azure Document Intelligence Results:")
        print(f"Pages: {azure_result['pages']}")
        print(f"Tables: {azure_result['tables']}")
        print(f"Paragraphs: {azure_result['paragraphs']}")
        print(f"Cost: ${azure_result['cost_estimate']:.3f}")
        
        if os.path.exists(docling_json):
            comparison = compare_with_docling(azure_result, docling_json)
            print(f"\nComparison:")
            print(f"Azure tables: {comparison['azure']['tables']}")
            print(f"Docling tables: {comparison['docling']['tables']}")
            print(f"Difference: {comparison['difference']['tables']}")
            print(f"Cost savings with Docling: {comparison['difference']['cost_savings_with_docling']}")
    else:
        print(f"PDF not found: {pdf_path}")

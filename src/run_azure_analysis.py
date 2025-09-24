#!/usr/bin/env python3
"""
Simple script to run Azure Document Intelligence analysis
"""

import os
import sys
sys.path.append('src')

try:
    from azure_document_service import AzureDocumentService, compare_with_docling
    
    # File paths
    pdf_path = "data/raw/Apple_10K_2023.pdf"
    docling_json = "data/parsed/docling/Apple_10K_2023.json"
    
    print("=" * 50)
    print("AZURE DOCUMENT INTELLIGENCE ANALYSIS")
    print("=" * 50)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        exit(1)
    
    # Initialize Azure service
    print("🔄 Initializing Azure Document Intelligence...")
    service = AzureDocumentService()
    
    # Analyze document
    print("🔄 Analyzing document...")
    azure_result = service.analyze_document(pdf_path)
    
    # Display results
    print("\n✅ AZURE RESULTS:")
    print(f"📄 Pages: {azure_result['pages']}")
    print(f"📊 Tables: {azure_result['tables']}")
    print(f"📝 Paragraphs: {azure_result['paragraphs']}")
    print(f"💰 Cost: ${azure_result['cost_estimate']:.3f}")
    
    # Compare with Docling if available
    if os.path.exists(docling_json):
        print("\n🔄 Comparing with Docling...")
        comparison = compare_with_docling(azure_result, docling_json)
        
        print("\n📊 COMPARISON RESULTS:")
        print("Azure vs Docling:")
        print(f"  Tables: {comparison['azure']['tables']} vs {comparison['docling']['tables']}")
        print(f"  Pages: {comparison['azure']['pages']} vs {comparison['docling']['pages']}")
        print(f"  Cost: {comparison['azure']['cost']} vs {comparison['docling']['cost']}")
        
        table_diff = comparison['difference']['tables']
        if table_diff > 0:
            print(f"✅ Azure detected {table_diff} more tables")
        elif table_diff < 0:
            print(f"✅ Docling detected {abs(table_diff)} more tables")
        else:
            print("✅ Same number of tables detected")
        
        print(f"💰 Cost savings with Docling: {comparison['difference']['cost_savings_with_docling']}")
        
        # Recommendation
        print("\n🎯 RECOMMENDATION:")
        if table_diff > 0:
            print(f"Consider Azure for complex table extraction (+{table_diff} tables)")
            print("Use as fallback for table-heavy documents")
        else:
            print("Docling performs adequately for this document type")
            print("Azure adds cost with minimal benefit")
    else:
        print(f"\n⚠️ Docling results not found: {docling_json}")
        print("Run Docling analysis first for comparison")
    
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install azure-ai-formrecognizer python-dotenv")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Check your Azure credentials in config.env")

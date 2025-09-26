# Generate architecture diagram for Project LANTERN PDF parsing pipeline

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.storage import S3
from diagrams.aws.ml import Textract
from diagrams.gcp.ml import AIHub
from diagrams.azure.ai import CognitiveServices
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.compute import Server
from diagrams.onprem.analytics import Jupyter
from diagrams.onprem.vcs import Git
from diagrams.programming.flowchart import Document, StartEnd, Decision
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.programming.language import Python


def create_project_lantern_architecture():
    """Create comprehensive architecture diagram for Project LANTERN"""
    
    with Diagram("Project LANTERN: AI-Powered PDF Parsing Pipeline", 
                 show=False, 
                 direction="TB",
                 filename="project_lantern_architecture"):
        
        # Phase 1: Design & Ingestion (Parts 0-4)
        with Cluster("Phase 1: Design & Ingestion (Parts 0-4)"):
            
            # Part 0: Data Bootstrap
            with Cluster("Part 0: Bootstrap & SEC Download"):
                sec_edgar = Storage("SEC EDGAR\nFilings")
                downloader = Python("sec-edgar-\ndownloader")
                raw_storage = Storage("data/raw/\nPDFs + XBRL")
                
                sec_edgar >> downloader >> raw_storage
            
            # Part 1: Text Extraction
            with Cluster("Part 1: Text Extraction"):
                pdfplumber = Python("pdfplumber")
                tesseract = Python("Tesseract OCR")
                text_output = Document("Per-page\n.txt files")
                
                raw_storage >> pdfplumber >> text_output
                raw_storage >> tesseract >> text_output
            
            # Part 2: Table Extraction
            with Cluster("Part 2: Table Extraction"):
                camelot = Python("Camelot\n(lattice/stream)")
                pdf_tables = Python("pdfplumber\ntables")
                hybrid = Python("Hybrid\nExtractor")
                csv_output = Document("CSV Tables")
                
                raw_storage >> camelot >> hybrid >> csv_output
                raw_storage >> pdf_tables >> hybrid
            
            # Part 3: Layout Detection
            with Cluster("Part 3: Layout Detection"):
                layoutparser = Python("LayoutParser\n(Detectron2)")
                layout_viz = Document("Layout\nVisualization")
                bbox_data = SQL("Bounding Box\nMetadata")
                
                raw_storage >> layoutparser >> layout_viz
                layoutparser >> bbox_data
            
            # Part 4: Advanced Understanding
            with Cluster("Part 4: Advanced Processing"):
                docling = Python("Docling\nAdvanced PDF")
                docling_output = Document("DoclingDocument\nJSON/MD")
                
                raw_storage >> docling >> docling_output
        
        # Phase 2: Representation & Staging (Parts 5-8)
        with Cluster("Phase 2: Representation & Staging (Parts 5-8)"):
            
            # Part 5: Metadata & Provenance
            with Cluster("Part 5: Metadata Schema"):
                metadata_schema = SQL("Metadata\nSchema")
                jsonl_files = Document("JSONL\nProvenance")
                
                bbox_data >> metadata_schema >> jsonl_files
            
            # Part 6: Format Conversion
            with Cluster("Part 6: Multi-Format Output"):
                converter = Python("Format\nConverter")
                markdown_out = Document("Markdown\n(RAG-ready)")
                json_out = Document("JSON\n(Structured)")
                txt_out = Document("Plain Text\n(Baseline)")
                
                text_output >> converter >> markdown_out
                converter >> json_out
                converter >> txt_out
            
            # Part 7: Build vs Buy
            with Cluster("Part 7: Managed Services"):
                aws_textract = Textract("AWS\nTextract")
                google_ai = AIHub("Google\nDocument AI")
                azure_ai = CognitiveServices("Azure AI\nDocument Intelligence")
                comparison = Document("Service\nComparison")
                
                raw_storage >> aws_textract >> comparison
                raw_storage >> google_ai >> comparison
                raw_storage >> azure_ai >> comparison
            
            # Part 8: DVC Pipeline
            with Cluster("Part 8: DVC Orchestration"):
                dvc = Git("Data Version\nControl")
                pipeline = Server("Reproducible\nPipeline")
                
                [text_output, csv_output, markdown_out] >> dvc
                dvc >> pipeline
        
        # Phase 3: Evaluation & Validation (Parts 9-11)
        with Cluster("Phase 3: Evaluation & Validation (Parts 9-11)"):
            
            # Part 9: Quality Evaluation
            with Cluster("Part 9: Quality Assessment"):
                ground_truth = Document("Ground Truth\nDataset")
                metrics = Python("WER/CER\nCalculation")
                tests = Python("Regression\nTests")
                eval_report = Document("Quality\nReport")
                
                [markdown_out, ground_truth] >> metrics >> eval_report
                metrics >> tests
            
            # Part 10: Benchmarking
            with Cluster("Part 10: Performance"):
                benchmark = Rack("Performance\nBenchmarks")
                cost_analysis = Document("Cost &\nThroughput")
                
                pipeline >> benchmark >> cost_analysis
            
            # Part 11: XBRL Validation
            with Cluster("Part 11: XBRL Cross-Validation"):
                xbrl_parser = Python("XBRL Parser\n(Arelle)")
                validator = Python("PDF-XBRL\nValidator")
                validation_report = Document("Validation\nReport")
                
                raw_storage >> xbrl_parser >> validator
                [csv_output, json_out] >> validator >> validation_report
        
        # Final Outputs
        with Cluster("Final Deliverables"):
            corpus = Storage("Layout-aware\nXBRL-validated\nCorpus")
            jupyter_nb = Jupyter("Analysis\nNotebooks")
            final_reports = Document("Comprehensive\nReports")
            
            [markdown_out, validation_report, eval_report] >> corpus
            [corpus, cost_analysis] >> jupyter_nb
            [eval_report, validation_report, cost_analysis] >> final_reports


def create_detailed_pipeline_flow():
    """Create detailed pipeline flow diagram"""
    
    with Diagram("Detailed Pipeline Flow", 
                 show=False, 
                 direction="LR",
                 filename="pipeline_flow_detailed"):
        
        # Input
        input_pdfs = Document("SEC 10-K/10-Q\nPDFs")
        
        # Processing stages
        with Cluster("Text Processing"):
            text_extract = Python("pdfplumber +\nOCR fallback")
            layout_detect = Python("LayoutParser\nDetection")
        
        with Cluster("Table Processing"):
            table_extract = Python("Camelot +\npdfplumber")
            hybrid_tables = Python("Hybrid\nApproach")
        
        with Cluster("Advanced Processing"):
            docling_proc = Python("Docling\nAdvanced")
            metadata_tag = Python("Provenance\nTagging")
        
        with Cluster("Format Conversion"):
            multi_format = Python("Multi-format\nConverter")
            
        with Cluster("Quality Assurance"):
            evaluation = Python("Quality\nEvaluation")
            xbrl_validation = Python("XBRL\nValidation")
        
        with Cluster("Output Formats"):
            md_output = Document("Markdown")
            json_output = Document("JSON")
            txt_output = Document("TXT")
        
        # Data flow
        input_pdfs >> text_extract >> layout_detect
        input_pdfs >> table_extract >> hybrid_tables
        input_pdfs >> docling_proc
        
        [layout_detect, hybrid_tables, docling_proc] >> metadata_tag
        metadata_tag >> multi_format
        
        multi_format >> md_output
        multi_format >> json_output  
        multi_format >> txt_output
        
        [md_output, json_output, txt_output] >> evaluation
        [json_output, input_pdfs] >> xbrl_validation


def create_data_flow_diagram():
    """Create data flow and storage diagram"""
    
    with Diagram("Data Flow & Storage", 
                 show=False, 
                 direction="TB",
                 filename="data_flow_storage"):
        
        # Raw Data
        with Cluster("Raw Data (data/raw/)"):
            pdfs = Document("PDF Files")
            xbrl_files = Document("XBRL Files")
        
        # Parsed Data
        with Cluster("Parsed Data (data/parsed/)"):
            with Cluster("Layout Analysis"):
                layout_json = Document("Layout\nJSON")
                viz_images = Document("Visualization\nPNGs")
            
            with Cluster("Tables"):
                csv_tables = Document("CSV\nTables")
                table_metadata = Document("Table\nMetadata")
            
            with Cluster("Text"):
                page_text = Document("Per-page\nText")
                word_boxes = Document("Word\nBounding Boxes")
            
            with Cluster("Converted Formats"):
                markdown_files = Document("Markdown\nFiles")
                json_files = Document("JSON\nFiles")
                txt_files = Document("Text\nFiles")
        
        # Evaluation Data
        with Cluster("Evaluation (evaluation_results/)"):
            ground_truth = Document("Ground Truth\nDataset")
            metrics = Document("Quality\nMetrics")
            reports = Document("Evaluation\nReports")
        
        # XBRL Validation
        with Cluster("XBRL Validation (data/xbrl_validation/)"):
            parsed_xbrl = Document("Parsed XBRL\nData")
            validation_results = Document("Validation\nReports")
        
        # Connections
        pdfs >> [layout_json, csv_tables, page_text, markdown_files]
        xbrl_files >> parsed_xbrl
        [markdown_files, json_files] >> [metrics, validation_results]
        [csv_tables, parsed_xbrl] >> validation_results


#!/usr/bin/env python3
# architecture_diagram.py
# Generate single comprehensive architecture diagram for Project LANTERN

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.storage import S3
from diagrams.aws.ml import Textract
from diagrams.gcp.ml import AIHub
from diagrams.azure.ai import CognitiveServices
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.compute import Server
from diagrams.onprem.analytics import Jupyter
from diagrams.onprem.vcs import Git
from diagrams.programming.flowchart import Document, StartEnd, Decision
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.programming.language import Python


def create_single_architecture_diagram():
    """Create single comprehensive architecture diagram for Project LANTERN"""
    
    with Diagram("Project LANTERN: Complete AI-Powered PDF Parsing Pipeline", 
                 show=False, 
                 direction="TB",
                 filename="project_lantern_complete"):
        
        # Input
        sec_edgar = Storage("SEC EDGAR\n10-K/10-Q Filings")
        
        # Phase 1: Ingestion
        with Cluster("Phase 1: Ingestion & Parsing"):
            downloader = Python("SEC Downloader\n(Part 0)")
            
            with Cluster("Extraction Methods"):
                pdfplumber = Python("pdfplumber +\nTesseract OCR\n(Part 1)")
                camelot = Python("Camelot Tables\n+ Hybrid\n(Part 2)")
                layoutparser = Python("LayoutParser\nDetection\n(Part 3)")
                docling = Python("Docling\nAdvanced\n(Part 4)")
            
            raw_storage = Storage("data/raw/\nPDFs + XBRL")
        
        # Phase 2: Processing & Storage
        with Cluster("Phase 2: Processing & Storage"):
            metadata = SQL("Metadata &\nProvenance\n(Part 5)")
            
            converter = Python("Multi-format\nConverter\n(Part 6)")
            
            with Cluster("Build vs Buy (Part 7)"):
                aws_service = Textract("AWS")
                google_service = AIHub("Google")
                azure_service = CognitiveServices("Azure")
            
            dvc = Git("DVC Pipeline\nVersioning\n(Part 8)")
        
        # Phase 3: Validation
        with Cluster("Phase 3: Evaluation & Validation"):
            evaluation = Python("Quality\nEvaluation\n(Part 9)")
            benchmarks = Rack("Performance\nBenchmarks\n(Part 10)")
            xbrl_validator = Python("XBRL Cross-\nValidation\n(Part 11)")
        
        # Outputs
        with Cluster("Final Outputs"):
            markdown_corpus = Document("Markdown\nCorpus\n(RAG-ready)")
            json_corpus = Document("JSON\nCorpus\n(API-ready)")
            validation_reports = Document("Validation\nReports")
            notebooks = Jupyter("Analysis\nNotebooks")
        
        # Main flow
        sec_edgar >> downloader >> raw_storage
        
        raw_storage >> [pdfplumber, camelot, layoutparser, docling]
        
        [pdfplumber, camelot, layoutparser, docling] >> metadata
        metadata >> converter
        
        converter >> [markdown_corpus, json_corpus]
        
        raw_storage >> [aws_service, google_service, azure_service]
        [aws_service, google_service, azure_service] >> converter
        
        [converter, metadata] >> dvc
        
        [markdown_corpus, json_corpus] >> evaluation
        [markdown_corpus, json_corpus, raw_storage] >> xbrl_validator
        [converter, metadata] >> benchmarks
        
        [evaluation, xbrl_validator, benchmarks] >> validation_reports
        [markdown_corpus, json_corpus, validation_reports] >> notebooks


def main():
    """Generate single architecture diagram"""
    print("Generating Project LANTERN architecture diagram...")
    
    # Install required package if not already installed
    try:
        import diagrams
    except ImportError:
        print("Installing diagrams package...")
        import subprocess
        subprocess.check_call(["pip", "install", "diagrams"])
        import diagrams
    
    # Generate single comprehensive diagram
    create_single_architecture_diagram()
    
    print("Architecture diagram generated:")
    print("  - project_lantern_complete.png")
    
    print("\nThis diagram shows:")
    print("  - Complete pipeline from SEC filings to validated corpus")
    print("  - All 12 parts (0-11) integrated into cohesive system")
    print("  - Data flow through ingestion, processing, and validation phases")
    print("  - Final outputs ready for RAG and analysis")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
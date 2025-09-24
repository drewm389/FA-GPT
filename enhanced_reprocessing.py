#!/usr/bin/env python3
# enhanced_reprocessing.py - Reprocess all documents with Granite Docling + multimodal embeddings

import os
import sys
import time
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from granite_docling_extraction import granite_docling_parsing
from multimodal_embeddings import embed_for_rag
from simple_ingestion import store_in_pgvector_rag, extract_and_store_kg_qwen
from app.config import settings

def multimodal_process_and_ingest_document(pdf_path: str):
    """Multimodal ingestion pipeline using Granite Docling + unified PostgreSQL storage."""
    print(f"Starting multimodal PDF ingestion for: {pdf_path}")
    
    # 1. Parse with Granite Docling + multimodal pipeline
    doc_elements, image_elements = granite_docling_parsing(pdf_path)
    if not doc_elements and not image_elements:
        print(f"No content extracted from {pdf_path}")
        return
    
    print(f"Granite Docling extraction: {len(doc_elements)} text elements and {len(image_elements)} image elements")
    
    # 2. Generate multimodal embeddings (unified vector space for text+images)
    embeddings = embed_for_rag(doc_elements, image_elements)
    print("Multimodal embedding generation complete")
    
    # 3. Store in pgvector for text+image RAG
    store_in_pgvector_rag(doc_elements, image_elements, embeddings, os.path.basename(pdf_path))
    print("Stored in pgvector for multimodal RAG")
    
    # 4. Extract knowledge graph using Qwen 2.5
    extract_and_store_kg_qwen(doc_elements, os.path.basename(pdf_path))
    print("Knowledge graph extraction complete")
    
    print(f"Successfully ingested {pdf_path} for multimodal RAG")

def reprocess_all_documents_multimodal(limit=None, clear_existing=False):
    """Reprocess all documents with Granite Docling + multimodal embeddings."""
    
    if clear_existing:
        print("Clearing existing database entries...")
        try:
            from app.connectors import get_db_connection
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM fa_gpt_documents;")
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Database cleared")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
    
    # Get all PDFs
    pdf_files = []
    documents_dir = os.path.join(os.path.dirname(__file__), 'data', 'documents')
    for root, _, files in os.walk(documents_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    # Sort by file size (smaller first for better success rate)
    pdf_files.sort(key=lambda x: os.path.getsize(x))
    
    # Apply limit if specified
    if limit and len(pdf_files) > limit:
        pdf_files = pdf_files[:limit]
        print(f"Processing {limit} documents (smallest first)")
    else:
        print(f"Processing all {len(pdf_files)} documents with multimodal RAG")
    
    successful = 0
    failed = 0
    
    # Process each document
    for i, pdf_file in enumerate(pdf_files):
        doc_name = os.path.basename(pdf_file)
        size_mb = os.path.getsize(pdf_file) / (1024*1024)
        
        print(f"\n{'='*80}")
        print(f"Processing {i+1}/{len(pdf_files)}: {doc_name}")
        print(f"File size: {size_mb:.2f} MB")
        print(f"{'='*80}")
        
        start_time = time.time()
        try:
            multimodal_process_and_ingest_document(pdf_file)
            duration = time.time() - start_time
            print(f"✅ Successfully processed in {duration:.2f} seconds")
            successful += 1
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error processing document after {duration:.2f}s: {str(e)}")
            failed += 1
            
            # Continue with next document
            continue
    
    print(f"\n{'='*80}")
    print(f"MULTIMODAL REPROCESSING SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total processed: {successful + failed}")
    print(f"🎯 Success rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "N/A")

if __name__ == "__main__":
    # Parse command line arguments
    limit = None
    clear_db = False
    
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit = int(arg)
        elif arg == "--clear":
            clear_db = True
    
    if limit:
        print(f"Using document limit: {limit}")
    if clear_db:
        print("Will clear existing database entries")
    
    # Start multimodal reprocessing
    reprocess_all_documents_multimodal(limit=limit, clear_existing=clear_db)
#!/usr/bin/env python3
# retry_failed_ingestion.py - Retry ingestion for documents that failed embedding

import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from simple_ingestion import process_and_ingest_document
from app.connectors import get_db_connection

def find_failed_documents():
    """Find documents that were extracted but failed during embedding/storage."""
    
    # Get all PDFs
    pdf_files = []
    documents_dir = os.path.join(os.path.dirname(__file__), 'data', 'documents')
    for root, _, files in os.walk(documents_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    # Get successfully processed documents from database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT source_doc FROM fa_gpt_documents;")
        processed_docs = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")
        processed_docs = set()
    
    # Find failed documents
    failed_docs = []
    for pdf_path in pdf_files:
        doc_name = os.path.basename(pdf_path)
        if doc_name not in processed_docs:
            failed_docs.append(pdf_path)
    
    return failed_docs

def retry_failed_ingestion(limit=None):
    """Retry ingestion for failed documents with optimized memory usage."""
    
    failed_docs = find_failed_documents()
    
    if not failed_docs:
        print("No failed documents found - all PDFs have been processed!")
        return
    
    # Sort by file size (smallest first)
    failed_docs.sort(key=lambda x: os.path.getsize(x))
    
    if limit:
        failed_docs = failed_docs[:limit]
        print(f"Retrying {limit} failed documents (smallest first)")
    else:
        print(f"Retrying {len(failed_docs)} failed documents")
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(failed_docs):
        doc_name = os.path.basename(pdf_path)
        size_mb = os.path.getsize(pdf_path) / (1024*1024)
        
        print(f"\nRetrying {i+1}/{len(failed_docs)}: {doc_name}")
        print(f"File size: {size_mb:.2f} MB")
        
        try:
            process_and_ingest_document(pdf_path)
            print(f"✅ Successfully processed {doc_name}")
            successful += 1
        except Exception as e:
            print(f"❌ Failed to process {doc_name}: {str(e)}")
            failed += 1
    
    print(f"\nRetry Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total processed: {successful + failed}")

if __name__ == "__main__":
    # Get optional limit from command line
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("Invalid limit argument")
            sys.exit(1)
    
    retry_failed_ingestion(limit=limit)
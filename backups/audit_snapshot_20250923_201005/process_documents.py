#!/usr/bin/env python3
# process_documents.py - Batch Document Processing for FA-GPT
"""
Batch Document Processing Script for FA-GPT

This script processes all PDF documents in the data/documents directory
through the complete FA-GPT ingestion pipeline.

Features:
- Recursive PDF discovery in documents directory and subdirectories
- Size-based processing order (smallest files first for faster initial results)
- Optional document limit for testing or partial processing
- Progress tracking and error handling
- Integration with the same ingestion pipeline used by the web interface

Usage:
    python process_documents.py           # Process all documents
    python process_documents.py 5         # Process only 5 smallest documents
    python process_documents.py 10        # Process only 10 smallest documents

The script uses the same pipeline as the Streamlit interface:
1. IBM Granite-Docling-258M multimodal document parsing
2. Organized file output in data/extracted/
3. Multimodal vector embedding generation
4. PostgreSQL storage with pgvector for vector search
5. Knowledge graph extraction using Apache AGE in PostgreSQL

Prerequisites:
- FA-GPT system properly configured
- PostgreSQL running with pgvector and Apache AGE extensions
- Ollama server with required models
- PDF documents in data/documents/ directory
"""

import os
import sys
import time
from pathlib import Path

# Ensure project root is on PYTHONPATH so we can import the app package
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the ingestion function from the app package
from app.simple_ingestion import process_and_ingest_document

def process_all_documents(directory, limit=None):
    """
    Process all PDF documents in the given directory and its subdirectories.
    
    Discovers PDF files recursively, sorts by size for optimal processing order,
    and processes each through the complete FA-GPT ingestion pipeline.
    
    Args:
        directory (str): Root directory to search for PDF documents
        limit (int, optional): Maximum number of documents to process
                             If None, processes all discovered documents
    
    Processing Strategy:
        - Recursive discovery of all PDF files in directory tree
        - Size-based sorting (smallest files first) for faster initial results
        - Progress tracking with detailed timing information
        - Error handling with continued processing on failures
        - Integration with same pipeline used by web interface
        
    Benefits of Size-Based Processing:
        - Faster initial feedback and results
        - Better resource utilization
        - Easier debugging with smaller test cases
        - Progressive system validation
        
    Output:
        For each processed document:
        - Organized files in data/extracted/{publication}/
        - Vector embeddings stored in PostgreSQL
        - Knowledge graph entities and relationships in Neo4j
        - Progress and timing information printed to console
        
    Error Handling:
        - Individual document failures don't stop batch processing
        - Detailed error messages with document identification
        - Timing information for performance analysis
        - Final summary of processed vs. failed documents
    """
    print(f"Starting document processing in {directory}")
    
    # Get all PDFs in the directory and subdirectories
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    # Sort by file size (smaller first for faster processing)
    pdf_files.sort(key=lambda x: os.path.getsize(x))
    
    # Apply limit if specified
    if limit and len(pdf_files) > limit:
        pdf_files = pdf_files[:limit]
        print(f"Limiting to {limit} documents (smallest first)")
    
    print(f"Found {len(pdf_files)} PDF documents")
    
    # Process each document
    for i, pdf_file in enumerate(pdf_files):
        print(f"\nProcessing {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
        print(f"File size: {os.path.getsize(pdf_file) / (1024*1024):.2f} MB")
        
        start_time = time.time()
        try:
            process_and_ingest_document(pdf_file)
            duration = time.time() - start_time
            print(f"✅ Successfully processed in {duration:.2f} seconds")
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            
    print("\nDocument processing complete!")

if __name__ == "__main__":
    # Define the document directory
    document_dir = os.path.join(os.path.dirname(__file__), 'data', 'documents')
    
    # Get optional limit from command line args
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Using document limit: {limit}")
        except ValueError:
            print("Invalid limit argument, processing all documents")
    
    # Process all documents
    process_all_documents(document_dir, limit=limit)
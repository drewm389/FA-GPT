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
    python process_documents.py --input-dir data/documents --limit 5 --verbose
    python process_documents.py --clear-db --limit 10
    python process_documents.py --verbose

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

# Import the ingestion function and logging from the app package
from app.simple_ingestion import process_and_ingest_document, get_db_connection
from app.logging_config import get_logger

# Initialize structured logger
logger = get_logger("process-documents")

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
    logger.info(f"📁 Starting batch document processing in {directory}")
    
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
        logger.info(f"🔢 Limiting to {limit} documents (smallest first)")
    
    logger.info(f"🔍 Found {len(pdf_files)} PDF documents for processing")
    
    # Processing statistics
    processed_count = 0
    failed_count = 0
    total_processing_time = 0
    
    # Process each document
    for i, pdf_file in enumerate(pdf_files):
        file_size_mb = os.path.getsize(pdf_file) / (1024*1024)
        logger.info(f"📄 Processing {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)} ({file_size_mb:.2f} MB)")
        
        start_time = time.time()
        try:
            with logger.log_performance(f"Document processing: {os.path.basename(pdf_file)}"):
                process_and_ingest_document(pdf_file)
            
            duration = time.time() - start_time
            total_processing_time += duration
            processed_count += 1
            
            logger.info(f"✅ Successfully processed in {duration:.2f} seconds")
            
        except Exception as e:
            failed_count += 1
            logger.log_exception(e, f"Failed to process document: {os.path.basename(pdf_file)}")
    
    # Final processing summary
    logger.info("📊 Batch Processing Summary:")
    logger.info(f"   ✅ Successfully processed: {processed_count} documents")
    logger.info(f"   ❌ Failed processing: {failed_count} documents")
    logger.info(f"   ⏱️  Total processing time: {total_processing_time:.2f} seconds")
    if processed_count > 0:
        avg_time = total_processing_time / processed_count
        logger.info(f"   ⚡ Average time per document: {avg_time:.2f} seconds")
    
    logger.info("🏁 Batch document processing complete!")

def clear_database():
    """Clear existing database entries before processing."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        logger.info("🗑️  Clearing existing database entries...")
        
        # Clear pgvector tables
        cur.execute("DROP TABLE IF EXISTS fa_gpt_documents CASCADE;")
        
        # Clear AGE graph data (if exists)
        try:
            cur.execute("SELECT drop_graph('fa_gpt_kg', true);")
        except:
            pass  # Graph might not exist
            
        conn.commit()
        logger.info("✅ Database cleared successfully")
        
    except Exception as e:
        logger.log_exception(e, "Database clearing failed")
        raise
    finally:
        if conn:
            conn.close()

def parse_arguments():
    """Professional CLI interface for FA-GPT batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FA-GPT Batch Document Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input-dir data/documents --limit 5
  %(prog)s --clear-db --verbose
  %(prog)s --input-dir /path/to/pdfs --limit 10 --verbose
        """
    )
    
    parser.add_argument("--input-dir", type=str, default="data/documents",
                        help="Root directory containing documents (default: data/documents)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit the number of documents to process")
    parser.add_argument("--clear-db", action="store_true",
                        help="Clear existing database entries before processing")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging (DEBUG level)")
    
    # Legacy support for positional argument
    parser.add_argument("legacy_limit", nargs="?", type=int, default=None,
                        help=argparse.SUPPRESS)  # Hidden legacy support
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments and configure logging
    args = parse_arguments()
    
    # Configure logger with verbosity
    if args.verbose:
        logger = get_logger("process-documents", verbose=True)
        logger.info("🔍 Verbose logging enabled")
    
    # Legacy support - use positional argument if provided and no --limit
    if args.legacy_limit and args.limit is None:
        args.limit = args.legacy_limit
        logger.warning("⚠️  Using legacy positional argument for limit. Consider using --limit flag.")
    
    logger.info("🚀 FA-GPT Batch Document Processing Pipeline Starting...")
    logger.log_environment_info()
    
    try:
        # Clear database if requested
        if args.clear_db:
            clear_database()
        
        # Define the document directory
        document_dir = os.path.join(PROJECT_ROOT, args.input_dir) if not os.path.isabs(args.input_dir) else args.input_dir
        
        if not os.path.exists(document_dir):
            logger.error(f"❌ Document directory does not exist: {document_dir}")
            sys.exit(1)
        
        # Process all documents
        process_all_documents(document_dir, limit=args.limit)
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.log_exception(e, "Batch processing failed")
        sys.exit(1)
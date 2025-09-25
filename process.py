#!/usr/bin/env python3
# process.py - Unified Document Processing Script for FA-GPT
"""
Consolidated document processing script for FA-GPT that replaces:
- process_documents.py
- enhanced_reprocessing.py 
- retry_failed_ingestion.py

This unified script provides all document processing functionality through
command-line arguments, making the project structure cleaner and easier to maintain.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List
import logging

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.simple_ingestion import process_and_ingest_document
from app.connectors import get_db_connection
from app.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_pdfs(directory: Path) -> List[Path]:
    """
    Recursively finds all PDF files in a directory.
    
    Args:
        directory: Directory to search in
        
    Returns:
        List of PDF file paths
    """
    logger.info(f"Searching for PDFs in: {directory}")
    pdfs = list(directory.rglob("*.pdf"))
    logger.info(f"Found {len(pdfs)} PDF files")
    return pdfs

def clear_database():
    """
    Wipes the main documents table and knowledge graph.
    Use with caution - this will delete all processed documents!
    """
    logger.warning("🗑️ Clearing existing database entries...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Drop tables in correct order (considering foreign key constraints)
        tables_to_drop = [
            "document_embeddings",
            "document_chunks", 
            "fa_gpt_documents",
            "document_processing_log"
        ]
        
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            logger.info(f"Dropped table: {table}")
        
        # Recreate necessary tables (app will handle this on first run)
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("✅ Database cleared successfully.")
        
    except Exception as e:
        logger.error(f"❌ Database clearing failed: {e}")
        sys.exit(1)

def check_document_processed(pdf_path: str) -> bool:
    """
    Check if a document has already been processed.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        True if document is already processed, False otherwise
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if document exists in database
        cur.execute(
            "SELECT COUNT(*) FROM fa_gpt_documents WHERE file_path = %s",
            (pdf_path,)
        )
        count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return count > 0
        
    except Exception as e:
        logger.warning(f"Could not check document status: {e}")
        return False

def move_to_quarantine(pdf_path: Path, error: str):
    """
    Move failed document to quarantine directory with error log.
    
    Args:
        pdf_path: Path to the failed PDF
        error: Error message to log
    """
    try:
        quarantine_dir = settings.data_dir / "quarantine"
        quarantine_dir.mkdir(exist_ok=True)
        
        # Move file to quarantine
        quarantine_path = quarantine_dir / pdf_path.name
        pdf_path.rename(quarantine_path)
        
        # Create error log
        error_log_path = quarantine_dir / f"{pdf_path.stem}_error.log"
        with open(error_log_path, 'w') as f:
            f.write(f"Processing failed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Original path: {pdf_path}\n")
            f.write(f"Error: {error}\n")
        
        logger.warning(f"Moved {pdf_path.name} to quarantine")
        
    except Exception as move_error:
        logger.error(f"Failed to move {pdf_path.name} to quarantine: {move_error}")

def process_documents(args):
    """
    Main document processing function.
    
    Args:
        args: Parsed command line arguments
    """
    # Determine source directory
    if args.retry_failed:
        logger.info("--- Starting Run: Retry Failed Documents ---")
        process_dir = settings.data_dir / "quarantine"
        if not process_dir.exists():
            logger.error(f"❌ Quarantine directory not found: {process_dir}")
            return
    else:
        logger.info("--- Starting Run: Standard Document Processing ---")
        process_dir = Path(args.input_dir)

    if not process_dir.exists():
        logger.error(f"❌ Error: Directory not found -> {process_dir}")
        sys.exit(1)

    # Find documents to process
    pdfs_to_process = find_pdfs(process_dir)
    
    if not pdfs_to_process:
        logger.info("✅ No documents found to process in the specified directory.")
        return

    # Filter out already processed documents (unless reprocessing or retrying)
    if not args.reprocess_all and not args.retry_failed:
        logger.info("Filtering out already processed documents...")
        unprocessed_pdfs = []
        for pdf in pdfs_to_process:
            if not check_document_processed(str(pdf)):
                unprocessed_pdfs.append(pdf)
            else:
                logger.info(f"Skipping already processed: {pdf.name}")
        
        pdfs_to_process = unprocessed_pdfs
        logger.info(f"Found {len(pdfs_to_process)} unprocessed documents")

    # Sort by size (smallest first for faster feedback)
    pdfs_to_process.sort(key=lambda p: p.stat().st_size)
    
    # Apply limit if specified
    if args.limit:
        pdfs_to_process = pdfs_to_process[:args.limit]
        logger.info(f"Limited processing to {args.limit} documents")

    if not pdfs_to_process:
        logger.info("✅ All documents have already been processed.")
        return

    logger.info(f"Processing {len(pdfs_to_process)} documents...")
    
    # Process documents
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, doc_path in enumerate(pdfs_to_process, 1):
        try:
            logger.info(f"\n--- Processing {i}/{len(pdfs_to_process)}: {doc_path.name} ---")
            doc_start_time = time.time()
            
            # Process the document
            process_and_ingest_document(str(doc_path))
            
            processing_time = time.time() - doc_start_time
            successful += 1
            
            logger.info(f"✅ Successfully processed {doc_path.name} in {processing_time:.1f}s")
            
            # Brief pause to prevent overwhelming the system
            if args.delay:
                time.sleep(args.delay)
                
        except KeyboardInterrupt:
            logger.info(f"\n🛑 Processing interrupted by user after {successful} successful documents")
            break
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ FAILED to process {doc_path.name}. Reason: {error_msg}")
            failed += 1
            
            # Move failed document to quarantine (unless we're already processing quarantine)
            if not args.retry_failed:
                move_to_quarantine(doc_path, error_msg)
            
            # Continue with next document unless --stop-on-error is set
            if args.stop_on_error:
                logger.error("Stopping processing due to --stop-on-error flag")
                break

    # Print summary
    total_time = time.time() - start_time
    logger.info("\n" + "="*50)
    logger.info("--- PROCESSING SUMMARY ---")
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⏱️ Total time: {total_time:.1f} seconds")
    logger.info(f"📊 Average time per document: {total_time/(successful+failed):.1f}s")
    logger.info("="*50)

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="FA-GPT Unified Document Processing Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Process all new documents
  %(prog)s --limit 10                # Process only 10 documents  
  %(prog)s --retry-failed            # Retry documents in quarantine
  %(prog)s --reprocess-all           # Reprocess all documents
  %(prog)s --clear-db                # Clear database first
  %(prog)s --input-dir /path/to/pdfs # Use custom input directory
        """
    )
    
    # Input/output options
    parser.add_argument(
        '--input-dir',
        type=str,
        default=str(settings.documents_dir),
        help='Directory to search for PDF documents (default: %(default)s)'
    )
    
    # Processing modes
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Process only the documents in the quarantine directory'
    )
    
    parser.add_argument(
        '--reprocess-all',
        action='store_true',
        help='Force reprocessing of all documents in the input directory'
    )
    
    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear the database before starting any processing (DESTRUCTIVE!)'
    )
    
    # Processing limits and controls
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit the number of documents to process'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0,
        help='Delay in seconds between processing documents'
    )
    
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop processing if any document fails'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments
    if args.retry_failed and args.reprocess_all:
        parser.error("Cannot use --retry-failed and --reprocess-all together")
    
    if args.clear_db:
        confirm = input("⚠️  This will DELETE ALL processed documents from the database. Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("Database clear cancelled")
            return
        clear_database()
        
        # Brief pause to let database operations complete
        time.sleep(2)
    
    # Start processing
    try:
        process_documents(args)
    except KeyboardInterrupt:
        logger.info("\n🛑 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
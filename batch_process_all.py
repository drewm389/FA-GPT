#!/usr/bin/env python3
"""
Batch processing script for FA-GPT to process all PDF documents in data directories.
Uses the enhanced GPU-accelerated pipeline with MIOpen fixes.
"""

import os
import sys
import time
from pathlib import Path
from typing import List

# Add the app directory to path
app_dir = str(Path(__file__).parent / "app")
sys.path.insert(0, app_dir)

from logging_config import get_logger
import simple_ingestion

logger = get_logger("batch-processor", verbose=True)

def find_all_pdfs(base_dir: str) -> List[str]:
    """Find all PDF files in the data directory structure."""
    pdf_files = []
    base_path = Path(base_dir)
    
    for pdf_file in base_path.rglob("*.pdf"):
        # Skip quarantine directory
        if "quarantine" not in str(pdf_file):
            pdf_files.append(str(pdf_file))
    
    return sorted(pdf_files)

def batch_process_pdfs(pdf_files: List[str], start_from: int = 0, max_docs: int = None):
    """Process multiple PDF files with progress tracking."""
    total_files = len(pdf_files)
    processed = 0
    failed = 0
    
    if max_docs:
        pdf_files = pdf_files[:max_docs]
        total_files = min(total_files, max_docs)
    
    if start_from > 0:
        pdf_files = pdf_files[start_from:]
        logger.info(f"Starting from document #{start_from + 1}")
    
    logger.info(f"🚀 Starting batch processing of {len(pdf_files)} PDF documents")
    logger.info(f"📊 Progress: 0/{total_files} documents processed")
    
    start_time = time.time()
    
    for i, pdf_path in enumerate(pdf_files, start=start_from + 1):
        try:
            doc_name = Path(pdf_path).name
            logger.info(f"\n{'='*80}")
            logger.info(f"📄 Processing document {i}/{total_files}: {doc_name}")
            logger.info(f"📁 Path: {pdf_path}")
            logger.info(f"{'='*80}")
            
            doc_start_time = time.time()
            simple_ingestion.process_and_ingest_document(pdf_path)
            doc_duration = time.time() - doc_start_time
            
            processed += 1
            logger.info(f"✅ Successfully processed {doc_name} in {doc_duration:.2f}s")
            logger.info(f"📊 Progress: {processed}/{total_files} documents completed")
            
        except Exception as e:
            failed += 1
            logger.error(f"❌ Failed to process {Path(pdf_path).name}: {str(e)}")
            logger.info(f"📊 Progress: {processed}/{total_files} completed, {failed} failed")
            continue
    
    total_duration = time.time() - start_time
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🏁 BATCH PROCESSING COMPLETE!")
    logger.info(f"📊 Final Statistics:")
    logger.info(f"   ✅ Successfully processed: {processed} documents")
    logger.info(f"   ❌ Failed: {failed} documents")
    logger.info(f"   📈 Success rate: {(processed/total_files)*100:.1f}%")
    logger.info(f"   ⏱️  Total time: {total_duration:.2f}s")
    logger.info(f"   ⚡ Average time per document: {total_duration/total_files:.2f}s")
    logger.info(f"{'='*80}")

def main():
    """Main batch processing function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FA-GPT Batch Document Processor")
    parser.add_argument("--data-dir", default="data", help="Base data directory")
    parser.add_argument("--clear-db", action="store_true", help="Clear database before processing")
    parser.add_argument("--max-docs", type=int, help="Maximum number of documents to process")
    parser.add_argument("--start-from", type=int, default=0, help="Start from document number (0-based)")
    parser.add_argument("--dry-run", action="store_true", help="Show files to be processed without processing")
    
    args = parser.parse_args()
    
    logger.info("🎯 FA-GPT Batch Document Processing Pipeline Starting...")
    
    # Find all PDF files
    pdf_files = find_all_pdfs(args.data_dir)
    
    if not pdf_files:
        logger.error(f"❌ No PDF files found in {args.data_dir}")
        return 1
    
    logger.info(f"📋 Found {len(pdf_files)} PDF files:")
    for i, pdf_file in enumerate(pdf_files, 1):
        rel_path = os.path.relpath(pdf_file, args.data_dir)
        logger.info(f"   {i:2d}. {rel_path}")
    
    if args.dry_run:
        logger.info("🔍 Dry run complete - no processing performed")
        return 0
    
    # Clear database if requested
    if args.clear_db:
        logger.info("🗑️  Clearing database...")
        simple_ingestion.clear_database()
    
    # Start batch processing
    try:
        batch_process_pdfs(pdf_files, args.start_from, args.max_docs)
        return 0
    except KeyboardInterrupt:
        logger.info("\n⏹️  Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
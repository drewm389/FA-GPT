#!/usr/bin/env python3
"""
Simple PDF extraction test using PyMuPDF as fallback when Docling fails.
This provides a basic ingestion capability without GPU dependencies.
"""

import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_with_pymupdf(pdf_path: str):
    """
    Extract text and basic structure from PDF using PyMuPDF as a fallback.
    This is much simpler than Docling but still provides useful content.
    """
    logger.info(f"🔄 Extracting with PyMuPDF fallback: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        text_elements = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if text.strip():
                text_elements.append({
                    'page': page_num + 1,
                    'type': 'text',
                    'content': text.strip(),
                    'bbox': None,  # Could extract if needed
                    'confidence': 1.0
                })
        
        logger.info(f"✅ PyMuPDF extraction successful: {len(text_elements)} text blocks from {len(doc)} pages")
        doc.close()
        return text_elements, []  # No images for now
        
    except Exception as e:
        logger.error(f"❌ PyMuPDF extraction failed: {e}")
        return [], []

def test_pdf_extraction():
    """Test PDF extraction with available documents."""
    docs_dir = Path("data/documents/Original PDFS")
    
    if not docs_dir.exists():
        logger.error(f"Documents directory not found: {docs_dir}")
        return
    
    # Find a small PDF to test with
    pdf_files = list(docs_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in documents directory")
        return
    
    # Use a smaller document for testing
    test_pdf = pdf_files[0]  # Just use the first one
    logger.info(f"Testing with: {test_pdf}")
    
    # Test extraction
    text_elements, image_elements = extract_with_pymupdf(str(test_pdf))
    
    if text_elements:
        logger.info(f"✅ Extraction successful!")
        logger.info(f"📄 Found {len(text_elements)} text elements")
        
        # Show first few lines of content
        if text_elements:
            first_content = text_elements[0]['content'][:200] + "..." if len(text_elements[0]['content']) > 200 else text_elements[0]['content']
            logger.info(f"📖 Sample content: {first_content}")
            
        return True
    else:
        logger.error("❌ No content extracted")
        return False

if __name__ == "__main__":
    success = test_pdf_extraction()
    if success:
        print("\n✅ Simple PDF extraction test PASSED")
        print("This confirms basic PDF processing works when Docling fails")
    else:
        print("\n❌ Simple PDF extraction test FAILED")
        sys.exit(1)
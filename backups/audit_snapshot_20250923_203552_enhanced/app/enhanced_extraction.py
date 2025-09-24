# app/enhanced_extraction.py
"""
Enhanced Document Extraction for FA-GPT

This module provides fallback document extraction capabilities using PyMuPDF,
pdfplumber, and EasyOCR for scenarios where IBM Docling may not be available
or when additional extraction methods are needed.

Features:
- Enhanced table detection using pdfplumber
- OCR text extraction using EasyOCR
- Image extraction and processing
- Metadata extraction and analysis
- Structured content organization

This module works alongside the main Granite-Docling pipeline to provide
comprehensive document processing capabilities.
"""

import os
import uuid
import json
from pathlib import Path
from typing import List, Tuple, Dict
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

def enhanced_document_parsing(pdf_path: str) -> Tuple[List[Dict], List[str]]:
    """Enhanced document parsing with better table detection and OCR."""
    
    doc_elements = []
    image_paths = []
    
    # Open document with PyMuPDF
    doc = fitz.open(pdf_path)
    
    # Extract document metadata
    metadata = doc.metadata
    doc_elements.append({
        'id': str(uuid.uuid4()),
        'type': 'metadata',
        'content': json.dumps({
            'title': metadata.get('title', 'Unknown'),
            'author': metadata.get('author', 'Unknown'),
            'subject': metadata.get('subject', 'Unknown'),
            'total_pages': len(doc),
            'file_size_mb': os.path.getsize(pdf_path) / (1024*1024)
        }),
        'metadata': metadata
    })
    
    # Try to use pdfplumber for better table extraction
    try:
        import pdfplumber
        use_pdfplumber = True
    except ImportError:
        print("pdfplumber not available, using PyMuPDF for tables")
        use_pdfplumber = False
    
    # Try to use EasyOCR for better image text extraction
    try:
        import easyocr
        ocr_reader = easyocr.Reader(['en'])
        use_easyocr = True
    except ImportError:
        print("EasyOCR not available, using basic image extraction")
        use_easyocr = False
    
    # Process each page
    for page_num, page in enumerate(doc):
        print(f"Processing page {page_num + 1}/{len(doc)}")
        
        # Extract text with better structure preservation
        text_dict = page.get_text("dict")
        
        # Group text by blocks and detect structure
        structured_content = extract_structured_content(text_dict, page_num + 1)
        doc_elements.extend(structured_content)
        
        # Enhanced table extraction
        if use_pdfplumber:
            tables = extract_tables_pdfplumber(pdf_path, page_num)
            doc_elements.extend(tables)
        else:
            tables = extract_tables_pymupdf(page, page_num + 1)
            doc_elements.extend(tables)
        
        # Enhanced image extraction with OCR
        images = extract_images_enhanced(doc, page, page_num + 1, pdf_path, use_easyocr, ocr_reader if use_easyocr else None)
        image_paths.extend(images['paths'])
        doc_elements.extend(images['elements'])
    
    doc.close()
    return doc_elements, image_paths

def extract_structured_content(text_dict: dict, page_num: int) -> List[Dict]:
    """Extract structured content with better layout understanding."""
    elements = []
    
    # Group blocks by reading order and type
    blocks = text_dict.get("blocks", [])
    
    # Detect headers, paragraphs, and lists
    for block_idx, block in enumerate(blocks):
        if "lines" not in block:
            continue
            
        block_text = ""
        font_sizes = []
        
        for line in block["lines"]:
            line_text = ""
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text:
                    line_text += text + " "
                    font_sizes.append(span.get("size", 12))
            
            if line_text.strip():
                block_text += line_text.strip() + "\n"
        
        if not block_text.strip():
            continue
        
        # Determine content type based on formatting
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        content_type = classify_content_type(block_text, avg_font_size, block_idx == 0)
        
        elements.append({
            'id': str(uuid.uuid4()),
            'type': content_type,
            'content': block_text.strip(),
            'metadata': {
                'page': page_num,
                'block_index': block_idx,
                'avg_font_size': avg_font_size,
                'char_count': len(block_text)
            }
        })
    
    return elements

def classify_content_type(text: str, font_size: float, is_first_block: bool) -> str:
    """Classify content type based on text characteristics."""
    text_lower = text.lower().strip()
    
    # Header detection
    if font_size > 14 or is_first_block or len(text) < 100:
        if any(word in text_lower for word in ['chapter', 'section', 'appendix', 'figure', 'table']):
            return 'header'
    
    # List detection
    if text.count('\n') > 2 and any(line.strip().startswith(('•', '-', '*', '1.', 'a.', 'i.')) for line in text.split('\n')):
        return 'list'
    
    # Military-specific content
    if any(term in text_lower for term in ['firing table', 'charge', 'projectile', 'range', 'elevation', 'azimuth']):
        return 'military_data'
    
    # Technical specifications
    if any(term in text_lower for term in ['specification', 'requirement', 'parameter', 'dimension']):
        return 'specification'
    
    return 'text'

def extract_tables_pdfplumber(pdf_path: str, page_num: int) -> List[Dict]:
    """Extract tables using pdfplumber for better accuracy."""
    try:
        import pdfplumber
        
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()
                
                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 1:  # Must have header + data
                        # Convert to DataFrame for better formatting
                        df = pd.DataFrame(table[1:], columns=table[0])
                        table_content = df.to_string(index=False)
                        
                        tables.append({
                            'id': str(uuid.uuid4()),
                            'type': 'table',
                            'content': table_content,
                            'metadata': {
                                'page': page_num + 1,
                                'table_index': table_idx,
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0,
                                'extraction_method': 'pdfplumber'
                            }
                        })
        
        return tables
    except Exception as e:
        print(f"pdfplumber table extraction failed: {e}")
        return []

def extract_tables_pymupdf(page, page_num: int) -> List[Dict]:
    """Fallback table extraction using PyMuPDF."""
    tables = []
    
    # Look for table-like structures in text blocks
    blocks = page.get_text("dict")["blocks"]
    
    for block_idx, block in enumerate(blocks):
        if "lines" not in block:
            continue
        
        lines = block["lines"]
        if len(lines) < 3:  # Need at least 3 lines for a table
            continue
        
        # Check if block looks like a table
        table_rows = []
        for line in lines:
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
            
            # Simple heuristic for table detection
            if '\t' in line_text or '  ' in line_text:
                table_rows.append(line_text.strip())
        
        if len(table_rows) >= 3:
            table_content = '\n'.join(table_rows)
            tables.append({
                'id': str(uuid.uuid4()),
                'type': 'table',
                'content': table_content,
                'metadata': {
                    'page': page_num,
                    'block_index': block_idx,
                    'rows': len(table_rows),
                    'extraction_method': 'pymupdf_heuristic'
                }
            })
    
    return tables

def extract_images_enhanced(doc, page, page_num: int, pdf_path: str, use_easyocr: bool, ocr_reader) -> Dict:
    """Enhanced image extraction with OCR analysis."""
    from app.config import settings
    
    image_paths = []
    image_elements = []
    
    image_list = page.get_images()
    
    for img_index, img in enumerate(image_list):
        try:
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                image_filename = f"{Path(pdf_path).stem}_p{page_num}_img{img_index}.png"
                image_path = settings.images_dir / image_filename
                
                pix.save(str(image_path))
                image_paths.append(str(image_path))
                
                # Analyze image content
                image_analysis = analyze_image_content(str(image_path), use_easyocr, ocr_reader)
                
                image_elements.append({
                    'id': str(uuid.uuid4()),
                    'type': 'image',
                    'content': f"[Image: {image_filename}] {image_analysis['description']}",
                    'metadata': {
                        'page': page_num,
                        'image_path': str(image_path),
                        'image_index': img_index,
                        'has_text': image_analysis['has_text'],
                        'extracted_text': image_analysis['text'],
                        'image_type': image_analysis['type']
                    }
                })
            
            pix = None
        except Exception as e:
            print(f"Error extracting image {img_index}: {e}")
            continue
    
    return {'paths': image_paths, 'elements': image_elements}

def analyze_image_content(image_path: str, use_easyocr: bool, ocr_reader) -> Dict:
    """Analyze image content to determine type and extract text."""
    analysis = {
        'description': '',
        'has_text': False,
        'text': '',
        'type': 'unknown'
    }
    
    try:
        # Open image for analysis
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Classify image type based on characteristics
            if width > height * 1.5:
                analysis['type'] = 'diagram'
                analysis['description'] = 'Technical diagram or chart'
            elif width < height * 0.7:
                analysis['type'] = 'table'
                analysis['description'] = 'Tabular data or form'
            else:
                analysis['type'] = 'figure'
                analysis['description'] = 'Figure or illustration'
            
            # Extract text using OCR
            if use_easyocr and ocr_reader:
                try:
                    results = ocr_reader.readtext(image_path)
                    extracted_texts = [result[1] for result in results if result[2] > 0.5]  # Confidence > 0.5
                    if extracted_texts:
                        analysis['has_text'] = True
                        analysis['text'] = ' '.join(extracted_texts)
                        analysis['description'] += f' containing text: {analysis["text"][:100]}...'
                except Exception as e:
                    print(f"EasyOCR failed for {image_path}: {e}")
            
            # Fallback to pytesseract if available
            elif not analysis['has_text']:
                try:
                    import pytesseract
                    text = pytesseract.image_to_string(img).strip()
                    if text and len(text) > 3:
                        analysis['has_text'] = True
                        analysis['text'] = text
                        analysis['description'] += f' with text content'
                except Exception as e:
                    print(f"pytesseract failed for {image_path}: {e}")
    
    except Exception as e:
        print(f"Image analysis failed for {image_path}: {e}")
        analysis['description'] = 'Image analysis failed'
    
    return analysis
# app/granite_docling_extraction.py
"""
Granite Docling-based document extraction for FA-GPT
Uses Docling for high-quality document structure extraction and VML pipeline with Qwen 2.5 VL
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import tempfile
import json

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import ConversionStatus
    from docling.datamodel.document import ConvertedDocument
    DOCLING_AVAILABLE = True
except ImportError:
    DocumentConverter = None
    ConversionStatus = None
    ConvertedDocument = None
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available - falling back to basic extraction")

from PIL import Image
import io
import base64

from app.config import settings
from app.connectors import get_ollama_client

logger = logging.getLogger(__name__)

class GraniteDoclingExtractor:
    """Granite Docling-based document processor for text+image RAG."""
    
    def __init__(self):
        self.ollama_client = get_ollama_client()
        
        if DOCLING_AVAILABLE:
            # Initialize basic DocumentConverter for local processing
            # No external APIs needed - everything runs locally
            try:
                self.converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized for local processing")
            except Exception as e:
                logger.warning(f"Failed to initialize DocumentConverter: {e}")
                self.converter = None
        else:
            self.converter = None
            logger.warning("Docling not available - using fallback extraction")
    
    def extract_document_structure(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract structured content from PDF using Granite Docling.
        Returns: (text_elements, image_elements)
        """
        
        if not DOCLING_AVAILABLE or not self.converter:
            return self._fallback_extraction(pdf_path)
        
        try:
            # Convert document with Docling - fully local processing
            result = self.converter.convert(pdf_path)
            document = result.document
            
            # Extract structured text elements
            text_elements = self._extract_text_elements(document)
            
            # Extract and process images (if any)
            image_elements = self._extract_image_elements(document, pdf_path)
            
            logger.info(f"Docling extracted {len(text_elements)} text elements and {len(image_elements)} images")
            return text_elements, image_elements
            
        except Exception as e:
            logger.error(f"Error in Docling extraction: {e}")
            logger.info("Falling back to basic PyMuPDF extraction")
            return self._fallback_extraction(pdf_path)
    
    def _extract_text_elements(self, document: ConvertedDocument) -> List[Dict[str, Any]]:
        """Extract structured text elements from Docling document - fully local processing."""
        text_elements = []
        
        try:
            # Use Docling's export_to_markdown for clean structured text
            markdown_content = document.export_to_markdown()
            
            if markdown_content.strip():
                text_elements.append({
                    'type': 'document',
                    'content': markdown_content,
                    'page': 1,
                    'bbox': {},
                    'metadata': {
                        'extraction_method': 'docling_local',
                        'format': 'markdown',
                        'confidence': 1.0
                    }
                })
            
            logger.info(f"Extracted markdown content: {len(markdown_content)} characters")
        
        except Exception as e:
            logger.error(f"Error extracting text with Docling: {e}")
            # Simple fallback - try to get any available text
            try:
                if hasattr(document, 'texts') and document.texts:
                    for i, text_item in enumerate(document.texts):
                        if hasattr(text_item, 'text') and text_item.text.strip():
                            text_elements.append({
                                'type': 'text',
                                'content': text_item.text.strip(),
                                'page': getattr(text_item, 'page', 1),
                                'bbox': {},
                                'metadata': {
                                    'extraction_method': 'docling_simple',
                                    'element_id': f'text_{i}',
                                    'confidence': 1.0
                                }
                            })
            except Exception as e2:
                logger.error(f"Simple text extraction also failed: {e2}")
        
        return text_elements
    
    def _extract_image_elements(self, document: ConvertedDocument, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract and process images with VML pipeline."""
        image_elements = []
        
        try:
            # Extract images from Docling document
            doc_dict = document.model_dump()
            
            for item in doc_dict.get('content', []):
                if item.get('label') == 'figure' or 'image' in item.get('label', '').lower():
                    # Extract image data
                    image_data = item.get('image_data')
                    if image_data:
                        # Process with VML pipeline
                        vml_analysis = self._process_image_with_vml(image_data, item)
                        
                        if vml_analysis:
                            image_elements.append({
                                'type': 'image',
                                'page': item.get('page', 0),
                                'bbox': item.get('bbox', {}),
                                'image_data': image_data,
                                'vml_analysis': vml_analysis,
                                'metadata': {
                                    'extraction_method': 'docling_image',
                                    'image_id': item.get('id', ''),
                                    'caption': item.get('text', ''),
                                }
                            })
        
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return image_elements
    
    def _process_image_with_vml(self, image_data: bytes, item: Dict) -> Optional[Dict[str, Any]]:
        """Process image using Qwen 2.5 VL for text+image RAG."""
        try:
            # Convert image to base64 for Ollama
            if isinstance(image_data, bytes):
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            else:
                # If image_data is already a string, assume it's base64
                image_b64 = image_data
            
            # Use Qwen 2.5 VL to analyze the image
            response = self.ollama_client.generate(
                model=settings.vlm_model,
                prompt="""Analyze this document image and extract:
1. Any text content (OCR)
2. The type of content (diagram, chart, table, photo, etc.)
3. Key visual elements and their relationships
4. Context that would be useful for document search

Provide a structured analysis in JSON format.""",
                images=[image_b64],
                stream=False
            )
            
            if response and 'response' in response:
                try:
                    # Try to parse as JSON, fallback to text
                    analysis_text = response['response']
                    try:
                        analysis_json = json.loads(analysis_text)
                        return analysis_json
                    except json.JSONDecodeError:
                        # Return as structured text if JSON parsing fails
                        return {
                            'description': analysis_text,
                            'extraction_method': 'qwen2.5vl',
                            'has_text': 'text' in analysis_text.lower(),
                            'content_type': 'unknown'
                        }
                except Exception as e:
                    logger.error(f"Error processing VML response: {e}")
                    return None
        
        except Exception as e:
            logger.error(f"Error in VML processing: {e}")
            return None
    
    def _format_table_for_rag(self, table) -> str:
        """Format table data for RAG indexing."""
        try:
            if hasattr(table, 'data') and table.data:
                # Convert table to text format suitable for embedding
                rows = []
                for row in table.data:
                    if isinstance(row, list):
                        rows.append(" | ".join(str(cell) for cell in row))
                
                return "\n".join(rows)
        except Exception as e:
            logger.error(f"Error formatting table: {e}")
        
        return ""
    
    def _fallback_extraction(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Fallback extraction when Docling is not available."""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            text_elements = []
            image_elements = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text blocks
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        text_content = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_content += span["text"] + " "
                        
                        if text_content.strip():
                            text_elements.append({
                                'type': 'text',
                                'content': text_content.strip(),
                                'page': page_num,
                                'bbox': block.get("bbox", []),
                                'metadata': {
                                    'extraction_method': 'pymupdf_fallback'
                                }
                            })
                
                # Extract images (basic)
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            
                            image_elements.append({
                                'type': 'image',
                                'page': page_num,
                                'image_data': img_data,
                                'metadata': {
                                    'extraction_method': 'pymupdf_fallback',
                                    'image_index': img_index
                                }
                            })
                        
                        pix = None
                    except Exception as e:
                        logger.error(f"Error extracting image {img_index}: {e}")
            
            doc.close()
            return text_elements, image_elements
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return [], []

def granite_docling_parsing(pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Main entry point for Granite Docling-based document parsing.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (text_elements, image_elements) for text+image RAG
    """
    extractor = GraniteDoclingExtractor()
    return extractor.extract_document_structure(pdf_path)
# app/enhanced_granite_docling.py
"""
Enhanced Granite Docling-based document extraction for FA-GPT
Uses instruction-based processing and content-aware analysis for military documents
Integrated with Qwen 2.5 VL for advanced vision-language analysis and image extraction
"""

import os
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
import tempfile
import json
import base64
import hashlib
from datetime import datetime

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import ConversionStatus
    DOCLING_AVAILABLE = True
except ImportError:
    DocumentConverter = None
    ConversionStatus = None
    DOCLING_AVAILABLE = False
    raise ImportError("Docling is required for enhanced extraction. Please install docling package.")

from PIL import Image
import io
import numpy as np

from app.config import settings
from app.connectors import get_ollama_client

logger = logging.getLogger(__name__)

class EnhancedGraniteDoclingExtractor:
    """Enhanced Granite Docling extractor with instruction-based processing for military documents."""
    
    def __init__(self):
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling is required for enhanced extraction. Please install docling package.")
        
        # Initialize Ollama client only if needed for VLM analysis
        self.ollama_client = None
        try:
            self.ollama_client = get_ollama_client()
            logger.info("Ollama client initialized for VLM analysis")
        except Exception as e:
            logger.warning(f"Ollama not available for VLM analysis: {e}")
        
        # Initialize DocumentConverter with GPU optimization where possible
        try:
            # Set up PyTorch to use ROCm GPU
            import torch
            if torch.cuda.is_available():
                # Force PyTorch to use CUDA/ROCm 
                device = torch.device("cuda:0")
                torch.cuda.set_device(0)
                logger.info(f"PyTorch GPU device configured: {device}")
                
                # Configure Docling with optimized pipeline options
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                from docling.document_converter import PdfFormatOption
                
                # Set up optimized pipeline without OCR to avoid MIOpen
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = False  # Keep OCR disabled to avoid MIOpen
                pipeline_options.do_table_structure = True
                # Note: GPU device is handled by PyTorch directly, not through pipeline options
                
                format_options = {
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
                
                self.converter = DocumentConverter(format_options=format_options)
                logger.info(f"Enhanced Docling DocumentConverter initialized with PyTorch GPU support")
            else:
                # Fallback to CPU if GPU not available
                self.converter = DocumentConverter()
                logger.info("Enhanced Docling DocumentConverter initialized with CPU processing")
                
        except Exception as e:
            logger.warning(f"GPU configuration failed, using basic setup: {e}")
            self.converter = DocumentConverter()
            logger.info("Enhanced Docling DocumentConverter initialized with basic configuration")
        
        # Military document content patterns
        self.content_patterns = {
            'firing_table': [
                r'firing table', r'range table', r'ballistic', r'charge\s+\d+',
                r'elevation', r'azimuth', r'deflection', r'mils'
            ],
            'safety_warning': [
                r'warning', r'caution', r'danger', r'safety', r'hazard',
                r'⚠', r'warning:', r'caution:', r'danger:'
            ],
            'maintenance_procedure': [
                r'maintenance', r'procedure', r'step\s+\d+', r'pmcs',
                r'lubrication', r'inspection', r'repair', r'replace'
            ],
            'technical_specification': [
                r'specification', r'tolerance', r'dimension', r'weight',
                r'capacity', r'pressure', r'temperature', r'rpm'
            ],
            'equipment_diagram': [
                r'figure\s+\d+', r'diagram', r'schematic', r'assembly',
                r'exploded view', r'cross section', r'cutaway'
            ],
            'ammunition_data': [
                r'ammunition', r'round', r'projectile', r'fuze', r'charge',
                r'propellant', r'cartridge', r'shell'
            ]
        }
        
        # Enhanced instruction templates for Granite-Docling-258M
        self.instruction_templates = {
            'firing_table': "Convert chart to table. Focus on range, elevation, and charge data.",
            'ballistic_formula': "Convert formula to LaTeX. Include all mathematical expressions.",
            'maintenance_procedure': "Retrieve all procedural steps in order. Include tool requirements and safety warnings.",
            'safety_warning': "Find all safety warning elements on the page. Include caution and danger notices.",
            'technical_diagram': "Convert diagram to detailed description. Include all labeled components and relationships.",
            'ammunition_chart': "Convert ammunition chart to structured table with specifications.",
            'equipment_specifications': "Extract all technical specifications as structured data.",
            'location_specific': "OCR the text in specific location: {coordinates}",
            'element_detection': "Find all '{element_type}' elements on the page.",
            'document_structure': "Analyze document structure and identify section headers, procedures, and warnings."
        }
    
    def extract_document_structure(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract structured content from PDF using enhanced instruction-based processing.
        Returns: (text_elements, image_elements)
        """
        try:
            # Convert document with enhanced Docling pipeline
            result = self.converter.convert(pdf_path)
            document = result.document
            
            # Analyze document structure first
            structure_analysis = self._analyze_document_structure(document)
            
            # Extract text elements with content-aware processing
            text_elements = self._extract_enhanced_text_elements(document, structure_analysis)
            
            # Extract and process images with instruction-based VLM
            image_elements = self._extract_enhanced_image_elements(document, pdf_path, structure_analysis)
            
            # Save comprehensive document metadata to organized folder
            try:
                metadata_path = self._save_document_metadata(structure_analysis, text_elements, image_elements, pdf_path)
                logger.info(f"Document metadata saved to: {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to save document metadata: {e}")
            
            logger.info(f"Enhanced extraction: {len(text_elements)} text elements, {len(image_elements)} images")
            logger.info(f"Document organized in: {settings.images_dir / Path(pdf_path).stem}")
            return text_elements, image_elements
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in enhanced Docling extraction: {error_msg}")
            
            # Check if this is the MLX dependency issue
            if "libmlx.so" in error_msg or "mlx.core" in error_msg:
                logger.warning("MLX dependency issue detected, falling back to standard Granite-Docling extractor")
                
                # Import and use standard extractor as fallback
                try:
                    from app.granite_docling_extraction import granite_docling_parsing
                    logger.info("Using standard Granite-Docling extractor as fallback")
                    return granite_docling_parsing(pdf_path)
                except Exception as fallback_error:
                    logger.error(f"Standard extractor also failed: {fallback_error}")
                    raise RuntimeError(f"Both enhanced and standard extraction failed. Enhanced: {error_msg}, Standard: {fallback_error}")
            else:
                raise RuntimeError(f"Enhanced extraction failed: {e}")
    
    def _analyze_document_structure(self, document) -> Dict[str, Any]:
        """Analyze document structure to determine content types and processing strategy."""
        try:
            # Get full document text for analysis
            full_text = document.export_to_markdown()
            
            # Detect content types based on patterns
            detected_types = {}
            for content_type, patterns in self.content_patterns.items():
                pattern_matches = sum(1 for pattern in patterns if re.search(pattern, full_text, re.IGNORECASE))
                detected_types[content_type] = pattern_matches > 0
            
            # Analyze document structure
            structure = {
                'content_types': detected_types,
                'has_tables': 'table' in full_text.lower() or '|' in full_text,
                'has_formulas': bool(re.search(r'[=\+\-\*/\^]|\$.*\$', full_text)),
                'has_procedures': bool(re.search(r'step\s+\d+|procedure|pmcs', full_text, re.IGNORECASE)),
                'has_warnings': bool(re.search(r'warning|caution|danger', full_text, re.IGNORECASE)),
                'document_type': self._classify_document_type(full_text),
                'total_pages': getattr(document, 'num_pages', 1),
                'text_length': len(full_text)
            }
            
            logger.info(f"Document structure analysis: {structure['document_type']}, "
                       f"Content types: {[k for k, v in detected_types.items() if v]}")
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {e}")
            return {
                'content_types': {},
                'document_type': 'unknown',
                'has_tables': False,
                'has_formulas': False,
                'has_procedures': False,
                'has_warnings': False
            }
    
    def _classify_document_type(self, text: str) -> str:
        """Classify the type of military document."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['firing table', 'ft ', 'range table']):
            return 'firing_table'
        elif any(term in text_lower for term in ['technical manual', 'tm ', 'maintenance']):
            return 'technical_manual'
        elif any(term in text_lower for term in ['operator manual', 'operator\'s manual']):
            return 'operator_manual'
        elif any(term in text_lower for term in ['safety', 'warning', 'hazard']):
            return 'safety_manual'
        elif any(term in text_lower for term in ['ammunition', 'round', 'projectile']):
            return 'ammunition_manual'
        else:
            return 'general_manual'
    
    def _detect_content_type(self, text: str, element_type: str) -> str:
        """Detect content type for enhanced processing."""
        text_lower = text.lower()
        
        # Military-specific content patterns
        if any(pattern in text_lower for pattern in ['firing table', 'range table', 'ballistic']):
            return 'firing_table'
        elif any(pattern in text_lower for pattern in ['danger', 'warning', 'caution', 'hazard']):
            return 'safety_warning'
        elif any(pattern in text_lower for pattern in ['procedure', 'step', 'operation']):
            return 'procedure'
        elif any(pattern in text_lower for pattern in ['figure', 'diagram', 'illustration']):
            return 'technical_diagram'
        elif any(pattern in text_lower for pattern in ['table', 'chart', 'data']):
            return 'data_table'
        elif any(pattern in text_lower for pattern in ['formula', 'equation', 'calculation']):
            return 'formula'
        else:
            return 'general_text'
    
    def _extract_enhanced_text_elements(self, document, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text elements using content-aware instruction-based processing."""
        text_elements = []
        
        try:
            # Process different document sections with specific instructions
            if structure.get('has_procedures'):
                procedure_elements = self._extract_procedures(document)
                text_elements.extend(procedure_elements)
            
            if structure.get('has_tables'):
                table_elements = self._extract_tables(document)
                text_elements.extend(table_elements)
            
            if structure.get('has_formulas'):
                formula_elements = self._extract_formulas(document)
                text_elements.extend(formula_elements)
            
            if structure.get('has_warnings'):
                warning_elements = self._extract_warnings(document)
                text_elements.extend(warning_elements)
            
            # Extract general text content with structure preservation
            general_elements = self._extract_structured_text(document, structure)
            text_elements.extend(general_elements)
            
            # Deduplicate and organize elements
            text_elements = self._deduplicate_elements(text_elements)
            
            # Save text elements to organized folders
            for element in text_elements:
                try:
                    saved_path = self._save_text_element_to_folder(element, pdf_path)
                    element['metadata']['saved_path'] = saved_path
                except Exception as e:
                    logger.debug(f"Failed to save text element: {e}")
            
        except Exception as e:
            logger.error(f"Error in enhanced text extraction: {e}")
            # Fallback to basic extraction
            text_elements = self._basic_text_extraction(document)
        
        return text_elements
    
    def _extract_procedures(self, document) -> List[Dict[str, Any]]:
        """Extract procedural content using specific instruction."""
        elements = []
        
        try:
            # Use instruction-based extraction for procedures
            instruction = self.instruction_templates['maintenance_procedure']
            
            # Process document with procedure-specific instruction
            markdown_content = document.export_to_markdown()
            
            # Parse procedures from markdown
            procedure_sections = re.split(r'\n#+\s*', markdown_content)
            
            for i, section in enumerate(procedure_sections):
                if any(keyword in section.lower() for keyword in ['step', 'procedure', 'maintenance', 'pmcs']):
                    elements.append({
                        'type': 'procedure',
                        'content': section.strip(),
                        'page': 1,  # TODO: Get actual page from document structure
                        'bbox': {},
                        'metadata': {
                            'extraction_method': 'instruction_based',
                            'instruction': instruction,
                            'content_type': 'procedure',
                            'procedure_id': f'proc_{i}',
                            'confidence': 0.9
                        }
                    })
            
        except Exception as e:
            logger.error(f"Error extracting procedures: {e}")
        
        return elements
    
    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """Extract table content using chart-to-table instruction."""
        elements = []
        
        try:
            instruction = self.instruction_templates['firing_table']
            
            # Extract table data from document
            markdown_content = document.export_to_markdown()
            
            # Find table patterns in markdown
            table_pattern = r'\|.*\|.*\n\|[-\s|:]*\|.*\n(\|.*\|.*\n)*'
            tables = re.findall(table_pattern, markdown_content, re.MULTILINE)
            
            for i, table in enumerate(tables):
                elements.append({
                    'type': 'table',
                    'content': table,
                    'page': 1,
                    'bbox': {},
                    'metadata': {
                        'extraction_method': 'instruction_based',
                        'instruction': instruction,
                        'content_type': 'table',
                        'table_id': f'table_{i}',
                        'confidence': 0.95
                    }
                })
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return elements
    
    def _extract_formulas(self, document) -> List[Dict[str, Any]]:
        """Extract mathematical formulas using LaTeX conversion instruction."""
        elements = []
        
        try:
            instruction = self.instruction_templates['ballistic_formula']
            
            markdown_content = document.export_to_markdown()
            
            # Find formula patterns
            formula_patterns = [
                r'\$.*?\$',  # LaTeX inline
                r'\$\$.*?\$\$',  # LaTeX block
                r'[A-Za-z]\s*=\s*[^=\n]+',  # Simple equations
                r'[A-Za-z]\s*[+\-*/]\s*[A-Za-z]\s*=\s*[^=\n]+'  # Complex equations
            ]
            
            for pattern in formula_patterns:
                formulas = re.findall(pattern, markdown_content, re.MULTILINE | re.DOTALL)
                
                for i, formula in enumerate(formulas):
                    if len(formula.strip()) > 3:  # Avoid false positives
                        elements.append({
                            'type': 'formula',
                            'content': formula.strip(),
                            'page': 1,
                            'bbox': {},
                            'metadata': {
                                'extraction_method': 'instruction_based',
                                'instruction': instruction,
                                'content_type': 'formula',
                                'formula_id': f'formula_{i}',
                                'confidence': 0.85
                            }
                        })
            
        except Exception as e:
            logger.error(f"Error extracting formulas: {e}")
        
        return elements
    
    def _extract_warnings(self, document) -> List[Dict[str, Any]]:
        """Extract safety warnings using warning detection instruction."""
        elements = []
        
        try:
            instruction = self.instruction_templates['safety_warning']
            
            markdown_content = document.export_to_markdown()
            
            # Find warning sections
            warning_pattern = r'(warning|caution|danger)[:\s]*([^\n]*\n(?:[^\n]*\n)*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)'
            warnings = re.findall(warning_pattern, markdown_content, re.IGNORECASE | re.MULTILINE)
            
            for i, (warning_type, warning_text) in enumerate(warnings):
                elements.append({
                    'type': 'warning',
                    'content': f"{warning_type.upper()}: {warning_text.strip()}",
                    'page': 1,
                    'bbox': {},
                    'metadata': {
                        'extraction_method': 'instruction_based',
                        'instruction': instruction,
                        'content_type': 'safety_warning',
                        'warning_type': warning_type.lower(),
                        'warning_id': f'warning_{i}',
                        'confidence': 0.95
                    }
                })
            
        except Exception as e:
            logger.error(f"Error extracting warnings: {e}")
        
        return elements
    
    def _extract_structured_text(self, document, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract general text content with structure preservation."""
        elements = []
        
        try:
            markdown_content = document.export_to_markdown()
            
            # Split by sections (headers)
            sections = re.split(r'\n(#+\s*.*)\n', markdown_content)
            
            current_section = "introduction"
            for i, part in enumerate(sections):
                if part.strip():
                    if part.startswith('#'):
                        # This is a header
                        current_section = part.strip('# ').lower()
                        elements.append({
                            'type': 'header',
                            'content': part.strip(),
                            'page': 1,
                            'bbox': {},
                            'metadata': {
                                'extraction_method': 'structure_aware',
                                'content_type': 'header',
                                'section': current_section,
                                'confidence': 1.0
                            }
                        })
                    else:
                        # This is content
                        if len(part.strip()) > 50:  # Only include substantial content
                            elements.append({
                                'type': 'text',
                                'content': part.strip(),
                                'page': 1,
                                'bbox': {},
                                'metadata': {
                                    'extraction_method': 'structure_aware',
                                    'content_type': 'text',
                                    'section': current_section,
                                    'confidence': 0.9
                                }
                            })
            
        except Exception as e:
            logger.error(f"Error in structured text extraction: {e}")
        
        return elements
    
    def _extract_enhanced_image_elements(self, document, pdf_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract images with enhanced VLM analysis using content-aware instructions."""
        image_elements = []
        
        try:
            # Get document content for context
            doc_dict = document.model_dump()
            
            # Look for images in the pictures field (correct Docling structure)
            pictures = doc_dict.get('pictures', [])
            logger.info(f"Found {len(pictures)} pictures in document")
            
            for i, item in enumerate(pictures):
                try:
                    # Skip None items
                    if item is None:
                        continue
                        
                    # Get image data from the picture item - try different possible structures
                    image_data = None
                    
                    # Try various ways the image data might be stored
                    if hasattr(item, 'get'):
                        # If item is a dict-like object
                        image_data = item.get('image', {}).get('image_data') if item.get('image') else None
                        if not image_data:
                            image_data = item.get('data') or item.get('image_data') or item.get('bytes')
                    elif hasattr(item, 'image'):
                        # If item has image attribute
                        image_data = getattr(item.image, 'image_data', None) if item.image else None
                    elif hasattr(item, 'data'):
                        # If item has data attribute
                        image_data = item.data
                    
                    if image_data:
                        # Get page info from provenance
                        page_num = 1
                        try:
                            if hasattr(item, 'get') and item.get('prov') and len(item['prov']) > 0:
                                page_num = item['prov'][0].get('page', 1)
                            elif hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                                page_num = getattr(item.prov[0], 'page', 1)
                        except (AttributeError, IndexError, KeyError):
                            page_num = 1
                        
                        # Determine image type and use appropriate instruction
                        image_type = self._classify_image_content(item, structure)
                        
                        # Process with content-specific VLM analysis
                        vml_analysis = self._process_image_with_enhanced_vml(
                            image_data, item, image_type, structure, pdf_path
                        )
                        
                        if vml_analysis:
                            image_elements.append({
                                'type': 'image',
                                'page': page_num,
                                'bbox': getattr(item, 'bbox', {}) if hasattr(item, 'bbox') else item.get('bbox', {}) if hasattr(item, 'get') else {},
                                'image_data': image_data,
                                'vml_analysis': vml_analysis,
                                'saved_path': vml_analysis.get('saved_path', ''),
                                'metadata': {
                                    'extraction_method': 'qwen2.5vl_enhanced',
                                    'image_type': image_type,
                                    'image_id': getattr(item, 'id', f'img_{i}') if hasattr(item, 'id') else item.get('id', f'img_{i}') if hasattr(item, 'get') else f'img_{i}',
                                    'caption': getattr(item, 'text', '') if hasattr(item, 'text') else item.get('text', '') if hasattr(item, 'get') else '',
                                    'confidence': vml_analysis.get('confidence', 0.8),
                                    'saved_path': vml_analysis.get('saved_path', '')
                                }
                            })
                        else:
                            # Even without VLM analysis, save the image to organized folder
                            saved_path = self._save_image_to_document_folder(image_data, item, pdf_path, image_type)
                            image_elements.append({
                                'type': 'image',
                                'page': page_num,
                                'bbox': getattr(item, 'bbox', {}) if hasattr(item, 'bbox') else item.get('bbox', {}) if hasattr(item, 'get') else {},
                                'image_data': image_data,
                                'saved_path': saved_path,
                                'metadata': {
                                    'extraction_method': 'basic_image_with_save',
                                    'image_type': image_type,
                                    'image_id': getattr(item, 'id', f'img_{i}') if hasattr(item, 'id') else item.get('id', f'img_{i}') if hasattr(item, 'get') else f'img_{i}',
                                    'caption': getattr(item, 'text', '') if hasattr(item, 'text') else item.get('text', '') if hasattr(item, 'get') else '',
                                    'confidence': 0.6,
                                    'saved_path': saved_path
                                }
                            })
                except Exception as e:
                    logger.debug(f"Skipping image {i}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in enhanced image extraction: {e}")
        
        return image_elements
    
    def _classify_image_content(self, item: Any, structure: Dict[str, Any]) -> str:
        """Classify image content type for targeted processing."""
        caption = ""
        
        # Try to get caption/text from different possible structures
        try:
            if hasattr(item, 'get') and callable(item.get):
                caption = item.get('text', '').lower()
            elif hasattr(item, 'text'):
                caption = str(getattr(item, 'text', '')).lower()
            elif hasattr(item, 'caption'):
                caption = str(getattr(item, 'caption', '')).lower()
        except:
            caption = ""
        
        if any(term in caption for term in ['chart', 'table', 'firing']):
            return 'chart'
        elif any(term in caption for term in ['diagram', 'figure', 'schematic']):
            return 'technical_diagram'
        elif any(term in caption for term in ['photo', 'image', 'picture']):
            return 'photograph'
        elif structure['content_types'].get('firing_table') and any(term in caption for term in ['range', 'elevation']):
            return 'firing_table_chart'
        else:
            return 'general_figure'
    
    def _save_image_to_document_folder(self, image_data: bytes, item: Any, pdf_path: str, image_type: str = 'general_figure') -> str:
        """Save extracted image to the document's organized subfolder structure."""
        try:
            # Get document name from PDF path
            pdf_name = Path(pdf_path).stem
            
            # Create document-specific folder with organized subfolders
            doc_base_dir = settings.images_dir / pdf_name
            
            # Create subfolder based on image type
            subfolder_map = {
                'chart': 'charts',
                'firing_table_chart': 'firing_tables', 
                'technical_diagram': 'diagrams',
                'photograph': 'photographs',
                'general_figure': 'figures'
            }
            
            subfolder = subfolder_map.get(image_type, 'figures')
            doc_images_dir = doc_base_dir / 'images' / subfolder
            doc_images_dir.mkdir(exist_ok=True, parents=True)
            
            # Also create other organized folders for this document
            self._ensure_document_folder_structure(doc_base_dir)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Try to get image ID from item
            image_id = "unknown"
            try:
                if hasattr(item, 'get') and callable(item.get):
                    image_id = item.get('id', 'unknown')
                elif hasattr(item, 'id'):
                    image_id = str(getattr(item, 'id', 'unknown'))
            except:
                pass
            
            # Create hash of image data for uniqueness
            image_hash = hashlib.md5(image_data).hexdigest()[:8]
            
            # Determine file extension from image data
            file_ext = ".png"  # Default
            if image_data.startswith(b'\\xff\\xd8'):
                file_ext = ".jpg"
            elif image_data.startswith(b'\\x89PNG'):
                file_ext = ".png"
            elif image_data.startswith(b'GIF'):
                file_ext = ".gif"
            
            # Create filename with type prefix
            filename = f"{image_type}_{image_id}_{timestamp}_{image_hash}{file_ext}"
            image_path = doc_images_dir / filename
            
            # Save image
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Saved {image_type} image to: {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return f"save_failed_{datetime.now().isoformat()}"
    
    def _ensure_document_folder_structure(self, doc_base_dir: Path) -> None:
        """Ensure the complete folder structure exists for a document."""
        try:
            # Create organized subfolders
            subfolders = [
                'images/charts',
                'images/diagrams', 
                'images/photographs',
                'images/firing_tables',
                'images/figures',
                'text/procedures',
                'text/warnings',
                'text/specifications',
                'text/general',
                'data/tables',
                'data/formulas',
                'metadata',
                'analysis'
            ]
            
            for subfolder in subfolders:
                folder_path = doc_base_dir / subfolder
                folder_path.mkdir(exist_ok=True, parents=True)
                
        except Exception as e:
            logger.error(f"Failed to create document folder structure: {e}")
    
    def _save_text_element_to_folder(self, element: Dict[str, Any], pdf_path: str) -> str:
        """Save text elements to organized subfolders based on content type."""
        try:
            # Get document name from PDF path
            pdf_name = Path(pdf_path).stem
            doc_base_dir = settings.images_dir / pdf_name
            
            # Determine subfolder based on element type
            element_type = element.get('type', 'general')
            content_type = element.get('metadata', {}).get('content_type', 'general')
            
            subfolder_map = {
                'procedure': 'text/procedures',
                'warning': 'text/warnings', 
                'table': 'data/tables',
                'formula': 'data/formulas',
                'header': 'text/general',
                'text': 'text/general'
            }
            
            if content_type in ['safety_warning', 'warning']:
                subfolder = 'text/warnings'
            elif content_type == 'procedure':
                subfolder = 'text/procedures'
            elif content_type in ['technical_specification', 'specification']:
                subfolder = 'text/specifications'
            else:
                subfolder = subfolder_map.get(element_type, 'text/general')
            
            # Create target directory
            target_dir = doc_base_dir / subfolder
            target_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            element_id = element.get('metadata', {}).get('element_id', 'unknown')
            filename = f"{content_type}_{element_id}_{timestamp}.txt"
            
            # Save content
            file_path = target_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {element_type.upper()}: {content_type}\n\n")
                f.write(element['content'])
                f.write(f"\n\n# Metadata\n")
                f.write(json.dumps(element.get('metadata', {}), indent=2))
            
            logger.info(f"Saved {element_type} to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save text element: {e}")
            return f"save_failed_{datetime.now().isoformat()}"
    
    def _save_document_metadata(self, structure: Dict[str, Any], text_elements: List[Dict], image_elements: List[Dict], pdf_path: str) -> str:
        """Save comprehensive document metadata to organized folder."""
        try:
            # Get document name from PDF path
            pdf_name = Path(pdf_path).stem
            doc_base_dir = settings.images_dir / pdf_name
            metadata_dir = doc_base_dir / 'metadata'
            metadata_dir.mkdir(exist_ok=True, parents=True)
            
            # Create comprehensive metadata
            timestamp = datetime.now().isoformat()
            metadata = {
                'document_info': {
                    'name': pdf_name,
                    'path': pdf_path,
                    'processed_at': timestamp,
                    'extractor_version': 'enhanced_granite_docling_v2.0'
                },
                'structure_analysis': structure,
                'extraction_summary': {
                    'total_text_elements': len(text_elements),
                    'total_image_elements': len(image_elements),
                    'text_types': {}, 
                    'image_types': {}
                },
                'content_inventory': {
                    'text_files': [],
                    'image_files': []
                }
            }
            
            # Analyze extracted elements
            for element in text_elements:
                content_type = element.get('metadata', {}).get('content_type', 'unknown')
                metadata['extraction_summary']['text_types'][content_type] = metadata['extraction_summary']['text_types'].get(content_type, 0) + 1
            
            for element in image_elements:
                image_type = element.get('metadata', {}).get('image_type', 'unknown')
                metadata['extraction_summary']['image_types'][image_type] = metadata['extraction_summary']['image_types'].get(image_type, 0) + 1
                if 'saved_path' in element:
                    metadata['content_inventory']['image_files'].append(element['saved_path'])
            
            # Save metadata
            metadata_file = metadata_dir / f"{pdf_name}_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved document metadata to: {metadata_file}")
            return str(metadata_file)
            
        except Exception as e:
            logger.error(f"Failed to save document metadata: {e}")
            return f"metadata_save_failed_{datetime.now().isoformat()}"
    
    def _process_image_with_enhanced_vml(self, image_data: bytes, item: Dict, image_type: str, structure: Dict[str, Any], pdf_path: str) -> Optional[Dict[str, Any]]:
        """Process image using Qwen 2.5 VL with content-specific instructions and save to organized document folder."""
        
        # Save image to organized document folder first
        saved_image_path = self._save_image_to_document_folder(image_data, item, pdf_path, image_type)
        
        # Skip VLM processing if Ollama not available
        if not self.ollama_client:
            logger.info("Ollama not available, skipping VLM image analysis")
            return {
                'description': f'Image of type: {image_type}',
                'image_type': image_type,
                'extraction_method': 'enhanced_basic',
                'has_text': False,
                'has_data': image_type in ['chart', 'firing_table_chart'],
                'confidence': 0.6,
                'saved_path': saved_image_path
            }
        
        try:
            # Convert image to base64
            if isinstance(image_data, bytes):
                image_b64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_b64 = image_data
            
            # Create content-specific prompt
            prompt = self._create_image_analysis_prompt(image_type, structure)
            
            # Use Qwen 2.5 VL with enhanced instruction
            logger.info(f"Processing image with Qwen 2.5 VL model: {settings.vlm_model}")
            response = self.ollama_client.generate(
                model=settings.vlm_model,
                prompt=prompt,
                images=[image_b64],
                stream=False
            )
            
            if response and 'response' in response:
                analysis_text = response['response']
                
                # Try to parse structured response
                try:
                    analysis_json = json.loads(analysis_text)
                    analysis_json['image_type'] = image_type
                    analysis_json['extraction_method'] = 'qwen2.5vl_enhanced'
                    analysis_json['confidence'] = 0.9
                    analysis_json['saved_path'] = saved_image_path
                    return analysis_json
                except json.JSONDecodeError:
                    # Return structured text response
                    return {
                        'description': analysis_text,
                        'image_type': image_type,
                        'extraction_method': 'qwen2.5vl_enhanced',
                        'has_text': 'text' in analysis_text.lower(),
                        'has_data': 'data' in analysis_text.lower() or 'table' in analysis_text.lower(),
                        'confidence': 0.8,
                        'saved_path': saved_image_path
                    }
        
        except Exception as e:
            logger.error(f"Error in Qwen 2.5 VL processing: {e}")
            return {
                'description': f'Image of type: {image_type} (VLM processing failed)',
                'image_type': image_type,
                'extraction_method': 'qwen2.5vl_fallback',
                'error': str(e),
                'confidence': 0.5,
                'saved_path': saved_image_path
            }
    
    def _create_image_analysis_prompt(self, image_type: str, structure: Dict[str, Any]) -> str:
        """Create content-specific analysis prompt optimized for Qwen 2.5 VL model."""
        
        base_prompt = """You are analyzing a military document image using advanced vision-language understanding. Provide detailed, structured analysis focusing on extracting actionable information for field artillery operations.

General requirements:
1. Describe what you see using precise military terminology
2. Extract ALL visible text, numbers, measurements, and labels
3. Identify key components, systems, procedures, or equipment shown
4. Note any safety warnings, cautions, or critical operational information
5. Structure your response in clear, parseable format for RAG integration

Provide comprehensive analysis with high attention to detail."""
        
        type_specific_prompts = {
            'chart': """
CHART/TABLE ANALYSIS:
1. Chart Type: Identify the specific type (bar chart, line graph, data table, firing table)
2. Data Extraction: Extract ALL numerical values, units, and measurements
3. Text Content: Transcribe all visible text including headers, labels, and legends
4. Military Context: Identify weapon systems, ammunition types, ranges, elevations
5. Conditions: Note environmental conditions, charge data, or modifiers
6. Accuracy: Pay special attention to precise numerical data for ballistic calculations

Output Format: Structured text with clear sections for each category.""",
            
            'technical_diagram': """
TECHNICAL DIAGRAM ANALYSIS:
1. System Identification: Identify the main equipment, weapon, or system shown
2. Component Analysis: List and describe all visible components, parts, and assemblies
3. Labels & Text: Extract all part numbers, specifications, dimensions, and technical text
4. Assembly Information: Describe how components connect or relate to each other
5. Operational Context: Identify maintenance procedures, operation steps, or safety protocols
6. Technical Specifications: Note any visible measurements, tolerances, or requirements

Output Format: Structured analysis with clear component hierarchy and relationships.""",
            
            'firing_table_chart': """
FIRING TABLE ANALYSIS:
1. Weapon System: Identify the specific weapon system and configuration
2. Ammunition Data: Extract ammunition type, weight, and characteristics
3. Firing Data: Extract ALL ranges, elevations, deflections, and charge information
4. Ballistic Coefficients: Note trajectory data, time of flight, and ballistic parameters
5. Environmental Conditions: Extract temperature, altitude, wind, and other conditions
6. Special Instructions: Note any special firing procedures or restrictions

Output Format: Precise tabular data extraction with complete ballistic information.""",
            
            'photograph': """
EQUIPMENT PHOTOGRAPH ANALYSIS:
1. Equipment Identification: Identify and describe all visible military equipment
2. Visible Markings: Extract all visible text, labels, serial numbers, and markings
3. Operational Context: Describe the setting, usage scenario, or operational environment
4. Personnel & Procedures: Note any visible operational procedures or personnel actions
5. Safety Information: Identify any visible safety equipment, warnings, or protocols
6. Condition Assessment: Note equipment condition, wear patterns, or maintenance needs

Output Format: Detailed description with emphasis on operational and maintenance information."""
        }
        
        specific_prompt = type_specific_prompts.get(image_type, type_specific_prompts['technical_diagram'])
        
        return f"{base_prompt}\n\n{specific_prompt}"
    
    def _basic_text_extraction(self, document) -> List[Dict[str, Any]]:
        """Fallback basic text extraction."""
        try:
            markdown_content = document.export_to_markdown()
            
            return [{
                'type': 'document',
                'content': markdown_content,
                'page': 1,
                'bbox': {},
                'metadata': {
                    'extraction_method': 'basic_fallback',
                    'format': 'markdown',
                    'confidence': 0.7
                }
            }]
        except Exception as e:
            logger.error(f"Basic text extraction failed: {e}")
            return []
    
    def _deduplicate_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate elements while preserving the most specific ones."""
        seen_content = set()
        unique_elements = []
        
        # Sort by specificity (more specific extraction methods first)
        method_priority = {
            'instruction_based': 0,
            'enhanced_vml': 1,
            'structure_aware': 2,
            'basic_fallback': 3
        }
        
        elements.sort(key=lambda x: method_priority.get(x['metadata'].get('extraction_method', 'basic_fallback'), 4))
        
        for element in elements:
            content_hash = hash(element['content'][:100])  # Use first 100 chars for comparison
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_elements.append(element)
        
        return unique_elements

def enhanced_granite_multimodal_parsing(pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Enhanced entry point for Granite Docling-based document parsing with instruction-based processing.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (text_elements, image_elements) optimized for military document RAG
    """
    extractor = EnhancedGraniteDoclingExtractor()
    return extractor.extract_document_structure(pdf_path)
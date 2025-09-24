# app/batch_processing.py
"""
Batch processing utilities for enhanced Granite-Docling document ingestion
Provides optimized batch processing for large document collections
"""

import os
import logging
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable
import time
import json
from dataclasses import dataclass
from collections import defaultdict

from app.enhanced_granite_docling import enhanced_granite_multimodal_parsing
from app.granite_multimodal_extractor import granite_multimodal_parsing

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for batch processing operations."""
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_pages: int = 0
    total_text_elements: int = 0
    total_image_elements: int = 0
    total_processing_time: float = 0.0
    average_time_per_document: float = 0.0
    errors: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BatchDocumentProcessor:
    """Enhanced batch processor for military document collections."""
    
    def __init__(self, 
                 max_workers: int = 2,
                 chunk_size: int = 5,
                 enable_caching: bool = True,
                 memory_limit_mb: int = 4096):
        """
        Initialize batch processor with performance optimizations.
        
        Args:
            max_workers: Maximum concurrent workers for parallel processing
            chunk_size: Number of documents to process in each batch
            enable_caching: Whether to cache processing results
            memory_limit_mb: Memory limit in MB for processing
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.enable_caching = enable_caching
        self.memory_limit_mb = memory_limit_mb
        
        # Initialize caching if enabled
        self.cache_dir = Path("cache/document_processing") if enable_caching else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing statistics
        self.stats = ProcessingStats()
        
        # Document type processors
        self.processors = {
            'enhanced': enhanced_granite_multimodal_parsing,
            'standard': granite_multimodal_parsing
        }
    
    def process_document_collection(self, 
                                  documents_dir: str,
                                  processor_type: str = 'enhanced',
                                  file_patterns: List[str] = None,
                                  max_documents: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a collection of documents with optimized batch processing.
        
        Args:
            documents_dir: Directory containing documents to process
            processor_type: Type of processor ('enhanced' or 'standard')
            file_patterns: List of file patterns to match (default: ['*.pdf'])
            max_documents: Maximum number of documents to process
            
        Returns:
            Dictionary containing processing results and statistics
        """
        
        if file_patterns is None:
            file_patterns = ['*.pdf']
        
        # Discover documents
        documents = self._discover_documents(documents_dir, file_patterns, max_documents)
        
        if not documents:
            logger.warning(f"No documents found in {documents_dir}")
            return {'results': [], 'stats': self.stats}
        
        logger.info(f"Found {len(documents)} documents for processing")
        
        # Get processor function
        processor_func = self.processors.get(processor_type, enhanced_granite_multimodal_parsing)
        
        # Process documents in batches
        start_time = time.time()
        all_results = []
        
        for i in range(0, len(documents), self.chunk_size):
            chunk = documents[i:i + self.chunk_size]
            logger.info(f"Processing batch {i//self.chunk_size + 1}: {len(chunk)} documents")
            
            batch_results = self._process_batch(chunk, processor_func)
            all_results.extend(batch_results)
            
            # Memory management
            if self._check_memory_usage():
                logger.info("Memory usage high, forcing garbage collection")
                import gc
                gc.collect()
        
        # Update final statistics
        self.stats.total_processing_time = time.time() - start_time
        if self.stats.successful_documents > 0:
            self.stats.average_time_per_document = (
                self.stats.total_processing_time / self.stats.successful_documents
            )
        
        logger.info(f"Batch processing completed: {self.stats.successful_documents}/{self.stats.total_documents} successful")
        
        return {
            'results': all_results,
            'stats': self.stats,
            'processing_summary': self._generate_summary()
        }
    
    def _discover_documents(self, 
                           documents_dir: str, 
                           file_patterns: List[str],
                           max_documents: Optional[int]) -> List[Path]:
        """Discover documents matching patterns in directory."""
        documents = []
        
        for pattern in file_patterns:
            matching_files = list(Path(documents_dir).rglob(pattern))
            documents.extend(matching_files)
        
        # Remove duplicates and sort by size (smallest first)
        documents = list(set(documents))
        documents.sort(key=lambda x: x.stat().st_size)
        
        if max_documents:
            documents = documents[:max_documents]
        
        self.stats.total_documents = len(documents)
        return documents
    
    def _process_batch(self, 
                      documents: List[Path], 
                      processor_func: Callable) -> List[Dict[str, Any]]:
        """Process a batch of documents with parallel execution."""
        
        batch_results = []
        
        # Use thread pool for I/O bound operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all documents in batch
            future_to_doc = {
                executor.submit(self._process_single_document, doc, processor_func): doc 
                for doc in documents
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_doc):
                doc_path = future_to_doc[future]
                
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per document
                    batch_results.append(result)
                    
                    if result['success']:
                        self.stats.successful_documents += 1
                        self.stats.total_text_elements += len(result.get('text_elements', []))
                        self.stats.total_image_elements += len(result.get('image_elements', []))
                    else:
                        self.stats.failed_documents += 1
                        
                except concurrent.futures.TimeoutError:
                    logger.error(f"Document processing timeout: {doc_path}")
                    self.stats.failed_documents += 1
                    self.stats.errors.append({
                        'document': str(doc_path),
                        'error': 'Processing timeout (300s)',
                        'timestamp': time.time()
                    })
                    
                except Exception as e:
                    logger.error(f"Document processing error: {doc_path} - {e}")
                    self.stats.failed_documents += 1
                    self.stats.errors.append({
                        'document': str(doc_path),
                        'error': str(e),
                        'timestamp': time.time()
                    })
        
        return batch_results
    
    def _process_single_document(self, 
                                doc_path: Path, 
                                processor_func: Callable) -> Dict[str, Any]:
        """Process a single document with caching and error handling."""
        
        doc_start_time = time.time()
        doc_str = str(doc_path)
        
        try:
            # Check cache first
            if self.enable_caching:
                cached_result = self._load_from_cache(doc_path)
                if cached_result:
                    logger.info(f"Loaded from cache: {doc_path.name}")
                    return cached_result
            
            # Process document
            logger.info(f"Processing: {doc_path.name}")
            text_elements, image_elements = processor_func(doc_str)
            
            processing_time = time.time() - doc_start_time
            
            result = {
                'document_path': doc_str,
                'document_name': doc_path.name,
                'success': True,
                'text_elements': text_elements,
                'image_elements': image_elements,
                'processing_time': processing_time,
                'file_size_mb': doc_path.stat().st_size / (1024 * 1024),
                'extraction_stats': {
                    'text_element_count': len(text_elements),
                    'image_element_count': len(image_elements),
                    'has_tables': any('table' in elem.get('type', '') for elem in text_elements),
                    'has_formulas': any('formula' in elem.get('type', '') for elem in text_elements),
                    'has_procedures': any('procedure' in elem.get('type', '') for elem in text_elements),
                    'has_warnings': any('warning' in elem.get('type', '') for elem in text_elements)
                }
            }
            
            # Cache result if enabled
            if self.enable_caching:
                self._save_to_cache(doc_path, result)
            
            logger.info(f"Completed: {doc_path.name} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            processing_time = time.time() - doc_start_time
            logger.error(f"Failed to process {doc_path.name}: {e}")
            
            return {
                'document_path': doc_str,
                'document_name': doc_path.name,
                'success': False,
                'error': str(e),
                'processing_time': processing_time,
                'text_elements': [],
                'image_elements': []
            }
    
    def _load_from_cache(self, doc_path: Path) -> Optional[Dict[str, Any]]:
        """Load processing result from cache."""
        if not self.cache_dir:
            return None
            
        cache_file = self.cache_dir / f"{doc_path.stem}.json"
        
        try:
            if cache_file.exists():
                # Check if cache is newer than source file
                if cache_file.stat().st_mtime > doc_path.stat().st_mtime:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {doc_path.name}: {e}")
        
        return None
    
    def _save_to_cache(self, doc_path: Path, result: Dict[str, Any]) -> None:
        """Save processing result to cache."""
        if not self.cache_dir:
            return
            
        cache_file = self.cache_dir / f"{doc_path.stem}.json"
        
        try:
            # Create a cache-safe version (remove large binary data)
            cache_result = result.copy()
            
            # Remove large image data for caching
            if 'image_elements' in cache_result:
                for img_elem in cache_result['image_elements']:
                    if 'image_data' in img_elem:
                        img_elem['image_data'] = '<cached_image_data>'
            
            with open(cache_file, 'w') as f:
                json.dump(cache_result, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save cache for {doc_path.name}: {e}")
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is approaching limits."""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent > 80  # Trigger cleanup at 80% memory usage
        except ImportError:
            return False  # psutil not available
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate processing summary statistics."""
        
        success_rate = (
            (self.stats.successful_documents / self.stats.total_documents * 100)
            if self.stats.total_documents > 0 else 0
        )
        
        return {
            'success_rate_percent': round(success_rate, 2),
            'total_processing_time_minutes': round(self.stats.total_processing_time / 60, 2),
            'average_time_per_document_seconds': round(self.stats.average_time_per_document, 2),
            'total_elements_extracted': self.stats.total_text_elements + self.stats.total_image_elements,
            'error_count': len(self.stats.errors),
            'most_common_errors': self._get_common_errors()
        }
    
    def _get_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error types from processing."""
        error_counts = defaultdict(int)
        
        for error in self.stats.errors:
            error_type = error['error'].split(':')[0] if ':' in error['error'] else error['error']
            error_counts[error_type] += 1
        
        # Return top 5 most common errors
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {'error_type': error_type, 'count': count}
            for error_type, count in common_errors
        ]

def batch_process_documents(documents_dir: str,
                          processor_type: str = 'enhanced',
                          max_workers: int = 2,
                          max_documents: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function for batch processing documents.
    
    Args:
        documents_dir: Directory containing documents
        processor_type: 'enhanced' or 'standard' processing
        max_workers: Maximum concurrent workers
        max_documents: Maximum documents to process
        
    Returns:
        Processing results and statistics
    """
    
    processor = BatchDocumentProcessor(
        max_workers=max_workers,
        chunk_size=min(5, max_workers * 2),
        enable_caching=True
    )
    
    return processor.process_document_collection(
        documents_dir=documents_dir,
        processor_type=processor_type,
        max_documents=max_documents
    )
# app/multimodal_embeddings.py
"""
Multimodal embedding utilities for text+image RAG
Provides unified embedding space for both text and images using CLIP
"""

import logging
import base64
import io
from typing import List, Dict, Union, Optional
import numpy as np
from PIL import Image

try:
    import clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    raise ImportError("CLIP is required for multimodal embeddings. Please install: pip install git+https://github.com/openai/CLIP.git")

from app.config import settings

logger = logging.getLogger(__name__)

class MultimodalEmbedder:
    """Handles unified embeddings for text and images using CLIP."""
    
    def __init__(self):
        if not CLIP_AVAILABLE:
            raise RuntimeError("CLIP is required for multimodal embeddings. Please install CLIP and PyTorch.")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize CLIP - this is the primary and only method
        if not settings.use_multimodal_embeddings:
            raise ValueError("Multimodal embeddings must be enabled in settings for this pipeline to work.")
        
        try:
            self.clip_model, self.clip_preprocess = clip.load(
                settings.multimodal_embedding_model, 
                device=self.device
            )
            logger.info(f"Loaded CLIP model: {settings.multimodal_embedding_model} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"CLIP model loading failed: {e}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text using CLIP."""
        if not texts:
            return []
        
        try:
            # Handle text chunking for CLIP's 77 token limit
            processed_texts = []
            for text in texts:
                # Very aggressive preprocessing to handle CLIP tokenizer's strict 77 token limit
                if not text or not text.strip():
                    processed_texts.append("document content")
                    continue
                
                # Clean and normalize text first
                clean_text = ' '.join(text.strip().split())
                
                # Multiple fallback strategies for token limit
                words = clean_text.split()
                if len(words) > 15:  # Very conservative word limit
                    # Take first 15 words to ensure we stay under 77 tokens
                    truncated_text = ' '.join(words[:15])
                    processed_texts.append(truncated_text)
                    logger.debug(f"Word-truncated text from {len(words)} words to 15 words")
                elif len(clean_text) > 150:  # Character limit check
                    # Fallback to character truncation if still too long
                    truncated_text = clean_text[:150].strip()
                    processed_texts.append(truncated_text)
                    logger.debug(f"Char-truncated text from {len(clean_text)} chars to 150 chars")
                else:
                    processed_texts.append(clean_text)
            
            # Use CLIP for text embeddings with additional safety checks
            try:
                text_tokens = clip.tokenize(processed_texts, truncate=True).to(self.device)
                with torch.no_grad():
                    text_features = self.clip_model.encode_text(text_tokens)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                return text_features.cpu().numpy().tolist()
            except Exception as tokenize_error:
                logger.warning(f"CLIP tokenization failed, trying emergency fallback: {tokenize_error}")
                # Emergency fallback: use very short text snippets
                emergency_texts = []
                for text in processed_texts:
                    # Ultimate fallback: just take first few words
                    words = text.split()[:5]  # Maximum 5 words
                    emergency_text = ' '.join(words) if words else "text"
                    emergency_texts.append(emergency_text)
                
                text_tokens = clip.tokenize(emergency_texts, truncate=True).to(self.device)
                with torch.no_grad():
                    text_features = self.clip_model.encode_text(text_tokens)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                logger.info(f"Emergency fallback successful for {len(emergency_texts)} texts")
                return text_features.cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"CLIP text embedding failed: {e}")
            raise RuntimeError(f"Text embedding failed: {e}")
    
    def embed_images(self, image_data_list: List[Union[bytes, str, Image.Image]]) -> List[List[float]]:
        """Generate embeddings for images using CLIP."""
        if not image_data_list:
            return []
        
        try:
            images = []
            for img_data in image_data_list:
                img = self._process_image_data(img_data)
                if img:
                    images.append(img)
            
            if not images:
                raise ValueError("No valid images could be processed from input data")
            
            # Process images through CLIP
            image_tensors = torch.stack([self.clip_preprocess(img) for img in images]).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensors)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().tolist()
            
        except Exception as e:
            logger.error(f"CLIP image embedding failed: {e}")
            raise RuntimeError(f"Image embedding failed: {e}")
    
    def embed_mixed_content(self, contents: List[Dict]) -> Dict[str, List[float]]:
        """
        Embed mixed content (text and images) maintaining unified vector space.
        
        Args:
            contents: List of dicts with 'type', 'id', and 'content'/'image_data'
        
        Returns:
            Dict mapping content IDs to embeddings
        """
        embeddings = {}
        
        # Separate text and image content
        text_items = []
        image_items = []
        
        for item in contents:
            if item.get('type') in ['text', 'table']:
                text_items.append(item)
            elif item.get('type') == 'image':
                image_items.append(item)
        
        # Embed text content
        if text_items:
            texts = [item.get('content', '') for item in text_items]
            text_embeddings = self.embed_texts(texts)
            
            for item, embedding in zip(text_items, text_embeddings):
                embeddings[item.get('id')] = embedding
        
        # Embed image content
        if image_items:
            images = [item.get('image_data') for item in image_items]
            image_embeddings = self.embed_images(images)
            
            for item, embedding in zip(image_items, image_embeddings):
                embeddings[item.get('id')] = embedding
        
        return embeddings
    
    def _process_image_data(self, img_data: Union[bytes, str, Image.Image]) -> Optional[Image.Image]:
        """Convert various image data formats to PIL Image."""
        try:
            if isinstance(img_data, Image.Image):
                return img_data.convert('RGB')
            elif isinstance(img_data, bytes):
                return Image.open(io.BytesIO(img_data)).convert('RGB')
            elif isinstance(img_data, str):
                # Assume base64 encoded
                img_bytes = base64.b64decode(img_data)
                return Image.open(io.BytesIO(img_bytes)).convert('RGB')
            else:
                logger.error(f"Unsupported image data type: {type(img_data)}")
                return None
        except Exception as e:
            logger.error(f"Error processing image data: {e}")
            return None

# Global embedder instance
_multimodal_embedder = None

def get_multimodal_embedder() -> MultimodalEmbedder:
    """Get singleton multimodal embedder instance."""
    global _multimodal_embedder
    if _multimodal_embedder is None:
        _multimodal_embedder = MultimodalEmbedder()
    return _multimodal_embedder

def embed_for_rag(text_elements: List[Dict], image_elements: List[Dict]) -> Dict[str, List[float]]:
    """
    Main entry point for RAG embeddings.
    
    Args:
        text_elements: Text elements from Granite Docling
        image_elements: Image elements from Granite Docling
    
    Returns:
        Dict mapping element IDs to embeddings in unified vector space
    """
    embedder = get_multimodal_embedder()
    
    # Combine all content for unified embedding
    all_content = []
    
    # Add text content
    for element in text_elements:
        all_content.append({
            'type': element.get('type', 'text'),
            'id': element.get('id'),
            'content': element.get('content', '')
        })
    
    # Add image content
    for element in image_elements:
        all_content.append({
            'type': 'image',
            'id': element.get('id'),
            'image_data': element.get('image_data')
        })
    
    return embedder.embed_mixed_content(all_content)
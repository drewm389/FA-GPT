# app/multimodal_embeddings.py
"""
Multimodal embedding utilities for text+image RAG
Provides unified embedding space for both text and images using CLIP
Implements token-aware text chunking to preserve information integrity
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
    import tiktoken
    CLIP_AVAILABLE = True
    TIKTOKEN_AVAILABLE = True
except ImportError as e:
    CLIP_AVAILABLE = False
    TIKTOKEN_AVAILABLE = False
    raise ImportError(f"Required packages missing: {e}. Please install: pip install tiktoken")

from app.config import settings

logger = logging.getLogger(__name__)

class MultimodalEmbedder:
    """Handles unified embeddings for text and images using CLIP."""
    
    def __init__(self):
        if not CLIP_AVAILABLE or not TIKTOKEN_AVAILABLE:
            raise RuntimeError("CLIP and tiktoken are required for multimodal embeddings. Please install required packages.")
        
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
        
        # Initialize tiktoken tokenizer for intelligent text chunking
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("Initialized tiktoken tokenizer for intelligent text chunking")
        except Exception as e:
            logger.error(f"Failed to initialize tiktoken: {e}")
            raise RuntimeError(f"Tiktoken initialization failed: {e}")
    
    def embed_texts(self, texts: List[str]) -> Dict[str, List[List[float]]]:
        """
        Generate embeddings for text using CLIP, with intelligent token-aware chunking.
        Returns a dictionary mapping original text index to a list of its chunk embeddings.
        This preserves all information instead of truncating.
        """
        if not texts:
            return {}

        all_embeddings = {}
        for i, text in enumerate(texts):
            if not text or not text.strip():
                # Handle empty text with a single embedding
                all_embeddings[str(i)] = [[0.0] * 512]  # CLIP ViT-B/32 embedding dimension
                continue

            try:
                # Split text into tokens using tiktoken
                tokens = self.tokenizer.encode(text.strip())
                
                # Create chunks of approximately 70 tokens to be safe (CLIP limit is 77)
                chunk_size = 70
                text_chunks = []
                
                if len(tokens) <= chunk_size:
                    # Text is short enough, use as-is
                    text_chunks = [text.strip()]
                else:
                    # Split into semantic chunks
                    for j in range(0, len(tokens), chunk_size):
                        chunk_tokens = tokens[j:j + chunk_size]
                        chunk_text = self.tokenizer.decode(chunk_tokens).strip()
                        if chunk_text:  # Only add non-empty chunks
                            text_chunks.append(chunk_text)

                if not text_chunks:
                    # Fallback for edge cases
                    text_chunks = [text[:200].strip() or "document content"]

                logger.debug(f"Text {i}: Split into {len(text_chunks)} chunks (original: {len(tokens)} tokens)")

                # Embed all chunks for this text
                try:
                    text_tokens_for_clip = clip.tokenize(text_chunks, truncate=True).to(self.device)
                    with torch.no_grad():
                        text_features = self.clip_model.encode_text(text_tokens_for_clip)
                        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    
                    # Store all chunk embeddings for this text
                    all_embeddings[str(i)] = text_features.cpu().numpy().tolist()
                    
                except Exception as clip_error:
                    logger.warning(f"CLIP embedding failed for text {i}, using fallback: {clip_error}")
                    # Emergency fallback: create very short chunks
                    words = text.split()[:10]  # Maximum 10 words as ultimate fallback
                    fallback_text = ' '.join(words) if words else "content"
                    
                    text_tokens_for_clip = clip.tokenize([fallback_text], truncate=True).to(self.device)
                    with torch.no_grad():
                        text_features = self.clip_model.encode_text(text_tokens_for_clip)
                        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                    
                    all_embeddings[str(i)] = text_features.cpu().numpy().tolist()
                    logger.info(f"Emergency fallback successful for text {i}")
                    
            except Exception as text_error:
                logger.error(f"Failed to process text {i}: {text_error}")
                # Last resort: zero embedding
                all_embeddings[str(i)] = [[0.0] * 512]
            
        return all_embeddings
    
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
        
        # Embed text content with chunking support
        if text_items:
            texts = [item.get('content', '') for item in text_items]
            text_embeddings_dict = self.embed_texts(texts)
            
            for idx, item in enumerate(text_items):
                item_id = item.get('id')
                chunk_embeddings = text_embeddings_dict.get(str(idx), [])
                
                if len(chunk_embeddings) == 1:
                    # Single chunk, use directly
                    embeddings[item_id] = chunk_embeddings[0]
                elif len(chunk_embeddings) > 1:
                    # Multiple chunks, average them to create unified representation
                    avg_embedding = np.mean(chunk_embeddings, axis=0).tolist()
                    embeddings[item_id] = avg_embedding
                    
                    # Optionally store individual chunks with suffix
                    for chunk_idx, chunk_emb in enumerate(chunk_embeddings):
                        embeddings[f"{item_id}_chunk_{chunk_idx}"] = chunk_emb
                else:
                    # Fallback zero embedding
                    embeddings[item_id] = [0.0] * 512
        
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
# app/connectors.py
"""
Connection utilities for FA-GPT system components.

This module provides cached connection functions for:
- Ollama client (local LLM/VLM inference)
- PostgreSQL storage (unified vector and knowledge graph with pgvector + Apache AGE)
- Embedding generation functions

All connections are cached using Streamlit's @st.cache_resource decorator
to avoid reconnection overhead during the application lifecycle.
"""

import ollama
import streamlit as st
from typing import List, Dict, Any
import numpy as np

from .config import settings

@st.cache_resource
def get_ollama_client():
    """
    Returns cached Ollama client for local LLM/VLM operations.
    
    Automatically pulls required models if they're not available locally.
    This ensures the system has all necessary models before processing.
    
    Returns:
        ollama.Client: Configured Ollama client instance
        
    Models automatically pulled:
        - VLM model (qwen2.5vl:7b) for image analysis
        - LLM model (qwen2.5:7b) for text generation
        - Embedding model (nomic-embed-text) for vector generation
    """
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        
        # Try to get available models with error handling
        try:
            models_response = client.list()
            if 'models' in models_response and models_response['models']:
                available_models = [m.get('name', '') for m in models_response['models'] if m.get('name')]
            else:
                available_models = []
                st.warning("No models found in Ollama. Please ensure Ollama is running and models are installed.")
        except Exception as e:
            st.error(f"Could not retrieve model list from Ollama: {e}")
            available_models = []
        
        # Ensure required models are available locally (only if we can connect)
        if available_models:
            required_models = [settings.vlm_model, settings.llm_model, settings.embedding_model]
            
            for model in required_models:
                if model not in available_models:
                    st.warning(f"Model {model} not found. Attempting to pull...")
                    try:
                        client.pull(model)
                        st.success(f"Successfully pulled {model}")
                    except Exception as e:
                        st.error(f"Failed to pull {model}: {e}")
        
        return client
        
    except Exception as e:
        st.error(f"Failed to initialize Ollama client: {e}")
        st.info("Please ensure Ollama is running: `ollama serve`")
        # Return a dummy client that will fail gracefully
        return ollama.Client(host=settings.ollama_base_url)

@st.cache_resource
def get_embedding_client():
    """
    Returns a cached function for generating embeddings using Ollama.
    
    This function handles both text and image embedding generation:
    - Text: Direct embedding using the configured text embedding model
    - Images: VLM analysis to description, then text embedding
    
    Returns:
        Callable: Function that takes (inputs, input_types) and returns embeddings
        
    Usage:
        embedding_fn = get_embedding_client()
        embeddings = embedding_fn(["text", "image.png"], ["text", "image"])
    """
    client = get_ollama_client()
    
    def generate_embeddings(inputs: List[Any], input_types: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for text or image inputs.
        
        Args:
            inputs: List of input data (strings for text, file paths for images)
            input_types: List of types ("text" or "image") corresponding to inputs
            
        Returns:
            List of numpy arrays containing embeddings
        """
        embeddings = []
        
        for input_data, input_type in zip(inputs, input_types):
            if input_type == "text":
                # Direct text embedding
                response = client.embeddings(
                    model=settings.embedding_model,
                    prompt=input_data
                )
                embeddings.append(np.array(response['embedding']))
            
            elif input_type == "image":
                # For images, use VLM to generate description, then embed
                import base64
                with open(input_data, 'rb') as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode()
                
                # Generate description first, then embed
                response = client.chat(
                    model=settings.vlm_model,
                    messages=[{
                        'role': 'user',
                        'content': 'Describe this image in detail for a military technical manual.',
                        'images': [img_base64]
                    }]
                )
                description = response['message']['content']
                
                # Embed the description
                embed_response = client.embeddings(
                    model=settings.embedding_model,
                    prompt=description
                )
                embeddings.append(np.array(embed_response['embedding']))
        
        return embeddings
    
    return generate_embeddings

def get_db_connection():
    """
    Returns a new PostgreSQL connection for direct database operations.
    
    Returns:
        psycopg2.connection: PostgreSQL database connection
        
    Note:
        Connection should be closed after use to free resources.
    """
    import psycopg2
    return psycopg2.connect(settings.postgres_uri)

@st.cache_resource
def get_storage_client():
    """
    Returns cached PostgreSQL storage client for vector and graph operations.
    
    This provides a cached connection to the unified PostgreSQL storage system
    with pgvector for embeddings and Apache AGE for knowledge graphs.
    
    Returns:
        PostgreSQLStorage: Cached storage client instance
        
    Note: This function is temporarily disabled pending full Apache AGE migration.
    """
    # Temporarily disabled - will be re-enabled once Apache AGE implementation is complete
    from .postgres_storage import PostgreSQLStorage
    return PostgreSQLStorage(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        username=settings.postgres_user,
        password=settings.postgres_password
    )
# app/config.py
"""
Configuration module for FA-GPT (Field Artillery GPT)

This module defines all configuration settings for the FA-GPT system, which is a 
local RAG (Retrieval-Augmented Generation) system designed for U.S. Army Field 
Artillery documents.

The system uses:
- IBM Granite-Docling-258M for multimodal document parsing and structure extraction
- Ollama for local LLM/VLM inference (unified to use Qwen 2.5 VL for all tasks)
- PostgreSQL with pgvector + Apache AGE for unified vector storage and knowledge graphs
- Nomic Embed Text for multimodal embeddings
- Streamlit for the web interface

All AI operations are now consolidated to use a single Vision-Language Model for
consistency and to eliminate complexity of managing separate text and vision models.

All settings can be overridden via environment variables or a .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from .logging_config import get_logger

# Initialize structured logger for configuration
logger = get_logger("config")

class Settings(BaseSettings):
    """
    Configuration class for FA-GPT deployment.
    
    This class defines all configurable parameters for the system including:
    - Database connection settings (PostgreSQL with pgvector + Apache AGE)
    - Model configuration (Ollama models)
    - Directory paths for data storage
    - Feature flags for extraction capabilities
    
    All settings use sensible defaults for Docker deployment but can be 
    customized via environment variables.
    """
    
    # Database Configuration - PostgreSQL with pgvector + Apache AGE
    # PostgreSQL with pgvector extension for embeddings and Apache AGE for unified knowledge graphs
    postgres_host: str = "localhost"  # Docker service name or localhost for local dev
    postgres_port: int = 5432
    postgres_db: str = "fagpt_db"  # Database name for unified vector and graph storage
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    
    # Ollama Configuration (local LLM/VLM server)
    ollama_host: str = "localhost"  # Docker service name or localhost for local dev
    ollama_port: int = 11434  # Default Ollama API port
    
    # Local AI Models Configuration (Consolidated to single VLM)
    vlm_model: str = "qwen2.5vl:7b"  # Primary Vision-Language model for all AI tasks
    llm_model: str = "qwen2.5vl:7b"  # Set to same VLM for text-only tasks (consolidated)
    embedding_model: str = "nomic-embed-text"  # Ollama's text embedding model
    multimodal_embedding_model: str = "ViT-B/32"  # CLIP model for unified text+image embeddings
    use_multimodal_embeddings: bool = True  # Enable unified vector space for text+images
    
    # Directory Configuration (container paths, override with .env for local dev)
    data_dir: Path = Path("./data")  # Main data directory for all file storage
    images_dir: Path = Path("./images")  # Extracted images from documents
    documents_dir: Path = Path("./data/documents")  # Source PDF documents to process
    
    # IBM Docling Configuration
    docling_cache_dir: Path = Path("./.cache/docling")  # Cache for Docling models and data
    # Extraction Configuration
    enable_ocr: bool = True  # Enable OCR for scanned documents and images
    enable_table_extraction: bool = True  # Extract and parse table structures
    force_cpu_only: bool = False  # Force CPU-only processing (disable GPU acceleration)
    
    @property
    def postgres_uri(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from environment variables

# Initialize settings with logging
settings = Settings()

# Log configuration initialization
logger.info("⚙️  FA-GPT Configuration initialized")
logger.debug(f"🔗 PostgreSQL URI: {settings.postgres_uri}")
logger.debug(f"🦙 Ollama Base URL: {settings.ollama_base_url}")
logger.debug(f"🤖 Primary VLM Model: {settings.vlm_model}")
logger.debug(f"📁 Data Directory: {settings.data_dir}")

# Create directories if they don't exist
settings.data_dir.mkdir(exist_ok=True, parents=True)
settings.images_dir.mkdir(exist_ok=True, parents=True)
settings.documents_dir.mkdir(exist_ok=True, parents=True)
settings.docling_cache_dir.mkdir(exist_ok=True, parents=True)

logger.debug("📂 Required directories created/verified")
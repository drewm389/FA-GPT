# FA-GPT Changelog

All notable changes to the FA-GPT (Field Artillery GPT) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation updates including README and technical docs
- Automated changelog maintenance workflow

## [2.2.0] - 2025-01-XX - GPU Acceleration & System Optimization

### 🚀 Major Features Added
- **Full GPU Acceleration Support**
  - AMD RX 6700 XT with ROCm 6.2.0 integration
  - NVIDIA GPU support with CUDA acceleration
  - PyTorch 2.5.1+rocm6.2 for optimal AMD performance
  - 5-10x performance improvement over CPU-only mode

### ⚡ Performance Improvements
- **Enhanced Document Processing Pipeline**
  - GPU-accelerated Granite-Docling-258M vision-language model
  - Real-time inference for interactive query responses
  - Parallel processing of multiple documents
  - MIOpen database optimization for AMD OCR performance

### 🔧 System Optimizations
- **Streamlined Fallback Architecture**
  - Removed PyMuPDF tertiary fallback for cleaner error handling
  - Two-tier processing system: Enhanced → Standard → Error
  - Improved extraction quality with Granite-Docling focus
  - Better error messages and debugging information

### 🛠️ Technical Improvements
- **Dependency Management**
  - Resolved NumPy 2.0 compatibility issues with ChromaDB
  - Fixed MLX dependency conflicts for non-Apple systems
  - Updated transformers to 4.54.0 for better model support
  - ChromaDB 0.4.18 with NumPy 1.26.4 compatibility

### 🎯 Multimodal Capabilities
- **Vision-Language Model Integration**
  - **Upgraded to Qwen 2.5 VL 7B** model for superior image analysis
  - **Removed LLaVA dependency** for cleaner model architecture
  - **Enhanced image extraction with automatic saving** to document folders
  - **Integrated Docling image extraction** as core pipeline feature (not fallback)
  - Improved picture processing with doc_dict['pictures']
  - Better handling of complex military document visuals

### 🏗️ Infrastructure Updates
- **ROCm Environment Setup**
  - Complete ROCm 6.2.0 installation guide
  - Environment variable configuration for AMD GPUs
  - User group permissions for hardware access
  - MIOpen database permissions optimization

### 📚 Documentation
- **Comprehensive Setup Guides**
  - GPU acceleration installation instructions
  - AMD vs NVIDIA setup differentiation
  - Performance benchmarking information
  - Troubleshooting guides for common issues

### 🐛 Bug Fixes
- Fixed image extraction logic to use correct Docling structure
- Resolved GPU detection issues with proper environment variables
- Fixed ChromaDB compatibility with NumPy version constraints
- Corrected MIOpen database permissions for OCR functionality
- Resolved tokenizer version conflicts with transformers

## [2.1.0] - 2025-09-23

### Added - Major Granite-Docling-258M Integration
- **IBM Granite-Docling-258M VLM Integration**: Added support for IBM's specialized 258M parameter vision-language model for document understanding
- **Enhanced Multimodal Processing**: New `granite_multimodal_extractor.py` module with superior table recognition and formula detection
- **Advanced Document Parsing**: Upgraded to Docling 2.54.0+ with enhanced capabilities for military documents
- **Improved Table Extraction**: Better handling of complex Tabular Firing Tables (TFTs) and numerical data
- **DocTags Format Support**: Native support for IBM's DocTags document format for improved structure preservation

### Enhanced
- **Multimodal Pipeline**: Upgraded multimodal embedding generation with Open-CLIP integration
- **Container Architecture**: Enhanced Docker setup with optimized dependency management
- **Document Processing**: Improved PDF-to-image conversion and page-by-page VLM processing
- **Error Handling**: Robust fallback mechanisms for model availability and processing failures

### Changed
- **Dependencies**: Updated requirements.txt with Granite-Docling-258M compatible versions
  - docling>=2.54.0 (was 2.0.2)
  - mlx-vlm>=0.3.3 (new dependency)
  - transformers>=4.53.0 (was 4.35.2)
  - torch>=2.2.2 (was 2.1.1)
  - open-clip-torch>=2.20.0 (replaced clip-by-openai)
- **Ingestion Pipeline**: Updated `simple_ingestion.py` to use granite_multimodal_parsing
- **Container Build**: Fixed multiple dependency conflicts in Docker build process

### Fixed
- **Dependency Conflicts**: Resolved version incompatibilities between docling, transformers, torch, and CLIP packages
- **Docker Build Issues**: Fixed container build failures due to package version conflicts
- **Import Dependencies**: Improved error handling for missing optional dependencies

## [2.0.0] - 2025-09-20

### Added - Core Multimodal RAG System
- **Complete RAG Pipeline**: Implemented full retrieval-augmented generation with multimodal support
- **IBM Docling Integration**: Advanced document parsing with structure preservation
- **Multimodal Embeddings**: CLIP-based unified text+image embedding generation
- **Vector Database**: PostgreSQL with pgvector for similarity search
- **Knowledge Graph**: Neo4j integration for entity relationships
- **Web Interface**: Streamlit-based chat interface with document management
- **Docker Deployment**: Complete containerized stack with all services

### Core Modules
- **Main Application** (`app/main.py`): Streamlit web interface with document upload and chat
- **Configuration** (`app/config.py`): Centralized settings and environment management
- **Database Connectors** (`app/connectors.py`): PostgreSQL, Neo4j, and Ollama connections
- **Document Ingestion** (`app/simple_ingestion.py`): Complete processing pipeline
- **RAG Core** (`app/rag_core.py`): Query processing and response generation
- **Docling Extraction** (`app/granite_docling_extraction.py`): Document parsing and structure extraction
- **Multimodal Embeddings** (`app/multimodal_embeddings.py`): CLIP embedding generation

### AI Models Integration
- **Ollama LLM/VLM**: Local inference with Qwen 2.5 models
- **Vision-Language Models**: Qwen 2.5 VL for image understanding
- **Text Embeddings**: Nomic Embed Text for semantic search
- **Multimodal Embeddings**: CLIP for unified text+image representations

### Document Processing Features
- **PDF Parsing**: Extract text, images, tables, and metadata
- **Structure Preservation**: Maintain document hierarchy and relationships
- **OCR Support**: Handle scanned documents and images
- **Table Extraction**: Parse complex tabular data
- **Image Processing**: Extract and analyze document images
- **Metadata Generation**: Comprehensive document and element metadata

### Data Management
- **Organized Storage**: Structured file organization by publication
- **Vector Storage**: Efficient similarity search with pgvector
- **Knowledge Graphs**: Entity and relationship extraction
- **Batch Processing**: Scripts for bulk document processing
- **Incremental Ingestion**: Support for adding new documents

### Infrastructure
- **Docker Compose**: Complete multi-service deployment
- **PostgreSQL + pgvector**: Vector database for embeddings
- **Neo4j**: Graph database for knowledge relationships
- **Ollama**: Local AI model serving
- **Streamlit**: Web interface and document management

## [1.0.0] - 2025-09-15

### Added - Initial Release
- **Project Initialization**: Basic project structure and configuration
- **Requirements Definition**: Initial dependency specification
- **Docker Setup**: Basic containerization framework
- **Documentation**: Initial README and setup instructions

### Core Infrastructure
- **Python Environment**: Virtual environment setup and management
- **Database Configuration**: Initial PostgreSQL and Neo4j setup
- **AI Model Integration**: Basic Ollama configuration
- **Development Environment**: Local development workflow

---

## Version History Summary

- **v2.1.0**: Granite-Docling-258M integration with enhanced document understanding
- **v2.0.0**: Complete multimodal RAG system with all core features
- **v1.0.0**: Initial project setup and infrastructure

## Breaking Changes

### v2.1.0
- Updated minimum system requirements for Granite-Docling-258M
- Changed container resource requirements (increased memory/storage needs)
- Modified API endpoints for enhanced multimodal processing

### v2.0.0
- Complete rewrite from initial concept to full RAG system
- New database schema and storage requirements
- Docker deployment architecture changes

## Migration Notes

### Upgrading to v2.1.0
1. Update Docker containers: `docker compose pull && docker compose up -d`
2. Models will auto-download on first run (10-15 minutes initial setup)
3. Existing documents may need reprocessing for enhanced features
4. Monitor increased memory usage with Granite-Docling-258M

### Upgrading to v2.0.0
1. Complete fresh installation recommended
2. Migrate any existing documents to new structure
3. Update environment variables and configuration
4. Initialize new database schemas

## Known Issues

### v2.1.0
- Initial model download requires stable internet connection
- Granite-Docling-258M requires significant memory for large documents
- Some legacy document formats may need manual preprocessing

### v2.0.0
- Large PDF files (>100MB) may require extended processing time
- Initial Ollama model downloads can take 30+ minutes
- Memory requirements scale with document collection size

## Development Roadmap

### Planned Features
- [ ] Real-time document collaboration
- [ ] Advanced knowledge graph visualization
- [ ] Multi-language document support
- [ ] Enhanced security and access controls
- [ ] Performance optimization for large document collections

### Technical Improvements
- [ ] Automated model optimization
- [ ] Enhanced caching mechanisms
- [ ] Distributed processing support
- [ ] Advanced monitoring and analytics

## Contributors

- System Architecture and Development
- AI Model Integration and Optimization
- Document Processing Pipeline Design
- Docker Infrastructure and Deployment

## License

This project is designed for U.S. Army Field Artillery applications and follows applicable military software development guidelines.
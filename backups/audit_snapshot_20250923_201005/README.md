# FA-GPT: Field Artillery GPT System 🚀

A state-of-the-art local Retrieval-Augmented Generation (RAG) system specifically designed for Field Artillery technical documents. FA-GPT uses IBM's cutting-edge Granite-Docling-258M vision-language model and advanced multimodal processing to provide intelligent question-answering capabilities over military technical manuals.

## 🎯 System Overview

FA-GPT combines multiple advanced technologies to create a comprehensive multimodal document intelligence system:

## ⚡ GPU Acceleration 

FA-GPT now features **full GPU acceleration** with support for:

- **AMD RX 6700 XT**: Complete ROCm 6.2.0 support with 12GB VRAM utilization
- **NVIDIA GPUs**: CUDA acceleration for enhanced performance
- **PyTorch 2.5.1+rocm6.2**: Optimized for AMD graphics cards
- **Enhanced Processing**: GPU-accelerated document analysis with Granite-Docling-258M
- **MIOpen Database**: Optimized OCR performance for AMD hardware

Performance improvements:
- **5-10x faster** document processing compared to CPU-only mode
- **Real-time inference** for interactive query responses
- **Parallel processing** of multiple documents simultaneously
- **Advanced image analysis** with Vision-Language Models (VLM)

## 📄 Document Processing

### Supported Document Types

- **PDF Military Technical Manuals**: Field Manuals (FMs), Technical Manuals (TMs)
- **Tabular Firing Tables (TFTs)**: Complex numerical tables with ballistic data
- **Army Regulations (ARs)**: Policy and procedural documents
- **Training Materials**: SOPs, lesson plans, and procedural guides
- **Equipment Manuals**: Maintenance guides and technical specifications

### Enhanced Processing Pipeline with Granite-Docling-258M

1. **Multimodal Document Parsing** (IBM Granite-Docling-258M)
   - 258M parameter vision-language model specialized for documents
   - Superior table recognition and formula detection
   - Advanced layout understanding with DocTags format
   - Handles complex military document structures
   - OCR for scanned documents with high accuracy

2. **Intelligent Content Extraction**
   - Text blocks with semantic understanding
   - Images with contextual relationships
   - Tables preserved with full structure and data types
   - Mathematical formulas and equations
   - Document hierarchy and cross-references

3. **Multimodal Embedding Generation**
   - CLIP/Open-CLIP for unified text+image embeddings
   - Specialized military domain vocabulary
   - Cross-modal semantic understanding
   - Vector representations for similarity search

4. **Knowledge Graph Construction**
   - Entity extraction (weapons, procedures, personnel)
   - Relationship mapping between concepts
   - Cross-document reference linking
   - Hierarchical knowledge organization

5. **Unified Storage**
   - PostgreSQL with pgvector for fast vector similarity search
   - Apache AGE for complex knowledge graph queries within PostgreSQL
   - Single database for both embeddings and entity relationships
   - Organized file structure for manual access
   - Metadata preservation for traceability

- **IBM Granite-Docling-258M**: State-of-the-art 258M parameter vision-language model for document understanding
- **Enhanced Docling 2.54.0+**: Superior document parsing with table and formula recognition
- **Ollama**: Local LLM/VLM inference (Qwen 2.5 models)
- **PostgreSQL with pgvector + Apache AGE**: Unified vector storage and knowledge graphs
- **Nomic Embed Text**: Multimodal text and image embeddings
- **Streamlit**: Interactive web interface
- **Docker**: Complete containerized deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   PDF Documents │ -> │ Granite-Docling-258M │ -> │ Organized Files │
│  (TFTs, FMs,    │    │   VLM Processing     │    │ (Text, Images,  │
│   Regulations)  │    │                      │    │  Tables, Meta)  │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                                │
                                v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│PostgreSQL w/    │ <- │ Multimodal RAG   │ <- │  PostgreSQL     │
│ Apache AGE      │    │    Pipeline      │    │  + pgvector     │
│Knowledge Graphs │    │ Nomic Embeddings │    │Vector Database  │
│Entities & Rels  │    │  Qwen 2.5 VL     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                v
                    ┌──────────────────┐
                    │  Streamlit UI    │
                    │ (Chat Interface) │
                    │  Docker Deploy   │
                    └──────────────────┘
```

## 📁 Project Structure

```
FA-GPT/
├── app/                                   # Main application code
│   ├── main.py                            # Streamlit web interface
│   ├── config.py                          # Configuration settings
│   ├── connectors.py                      # Database and AI model connections
│   ├── simple_ingestion.py                # Document processing pipeline
│   ├── rag_core.py                        # RAG query processing
│   ├── granite_multimodal_extractor.py    # Granite-Docling-258M integration
│   ├── granite_docling_extraction.py      # Enhanced Docling parsing
│   ├── multimodal_embeddings.py           # CLIP embedding generation
│   └── enhanced_extraction.py             # Advanced extraction utilities
├── data/
│   ├── documents/                         # Source PDF files
│   │   ├── Original PDFs/                 # Original military documents
│   │   ├── TFTs/                          # Tabular Firing Tables
│   │   └── Field Manuals/                 # Army Field Manuals
│   └── extracted/                         # Processed document outputs
│       └── {publication}/                 # Per-document organized content
│           ├── text/                      # Text elements (.txt)
│           ├── images/                    # Extracted images (.png)
│           ├── tables/                    # Table data (.json)
│           └── metadata/                  # Element metadata (.json)
├── images/                                # Document image cache
├── process_documents.py                   # Batch processing script
├── enhanced_reprocessing.py               # Granite-enhanced reprocessing
├── docker-compose.yml                     # Docker services configuration
├── Dockerfile.streamlit                   # Streamlit container
├── requirements.txt                       # Python dependencies
├── CHANGELOG.md                           # Version history
└── README.md                              # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop with GPU support (recommended)
- 16GB+ RAM recommended for optimal performance
- 50GB+ disk space for models and processed documents
- AMD RX 6000+ or NVIDIA RTX 3000+ GPU (optional but recommended)

### Option 1: Docker Deployment (Recommended)

1. **Clone and navigate to the repository**
   ```bash
   git clone <repository-url>
   cd FA-GPT
   ```

2. **Start the complete stack**
   ```bash
   # Start all services (PostgreSQL with pgvector + Apache AGE, Ollama, Streamlit)
   docker compose up -d
   
   # Check service status
   docker compose ps
   ```

3. **Initialize AI models** (automatic on first run)
   ```bash
   # Models will auto-download: Qwen 2.5, CLIP, Granite-Docling-258M
   # Initial setup takes 10-15 minutes depending on internet speed
   ```

4. **Access the web interface**
   - Open http://localhost:8501 in your browser
   - Upload PDFs through the sidebar interface
   - Start processing and querying documents!

### Option 2: Local Development

1. **Install Python dependencies**
   ```bash
   python -m venv fagpt_env
   source fagpt_env/bin/activate  # On Windows: fagpt_env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **GPU Setup (Optional but Recommended)**
   
   **For AMD Graphics Cards (RX 6700 XT, etc.):**
   ```bash
   # Install ROCm 6.2.0 for AMD GPU acceleration
   wget https://repo.radeon.com/amdgpu-install/6.2/ubuntu/jammy/amdgpu-install_6.2.60200-1_all.deb
   sudo dpkg -i amdgpu-install_6.2.60200-1_all.deb
   sudo amdgpu-install --usecase=rocm
   
   # Install PyTorch with ROCm support
   pip install torch==2.5.1+rocm6.2 torchvision==0.20.1+rocm6.2 torchaudio==2.5.1+rocm6.2 \
       --index-url https://download.pytorch.org/whl/rocm6.2
   
   # Add user to render group
   sudo usermod -a -G render $USER
   # Logout and login to apply group changes
   
   # Set environment variables
   export HSA_OVERRIDE_GFX_VERSION=10.3.0
   export HIP_VISIBLE_DEVICES=0
   export PYTORCH_ROCM_ARCH=gfx1030
   ```
   
   **For NVIDIA Graphics Cards:**
   ```bash
   # Install CUDA-enabled PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Set up local services**
   ```bash
   # Install and start PostgreSQL with pgvector and Apache AGE extensions
   # Install and start Ollama
   ollama pull qwen2.5:14b
   ollama pull qwen2.5vl:7b  # For multimodal image analysis
   ollama pull nomic-embed-text
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local database credentials
   ```

5. **Run the application**
   ```bash
   streamlit run app/main.py
   ```

## 📚 Document Processing

### Supported Document Types

- PDF military technical manuals
- Field Artillery firing tables (TFTs)
- Training materials and procedures
- Equipment manuals and specifications

### Processing Pipeline

1. **Document Parsing** (IBM Docling)
   - Extracts text, images, tables, and structure
   - Preserves document hierarchy and relationships
   - Handles both text and scanned documents (OCR)

2. **Content Organization**
   - Saves extracted content in publication-specific folders
   - Organizes by content type (text, images, tables, metadata)
   - Maintains source document references

3. **Embedding Generation**
   - Creates unified vector representations for text and images
   - Uses CLIP for multimodal embeddings
   - Enables semantic similarity search

4. **Database Storage**
   - PostgreSQL: Vector embeddings and content for RAG
   - Neo4j: Knowledge graph of entities and relationships

5. **Knowledge Extraction**
   - Identifies military entities (weapons, ammunition, procedures)
   - Extracts relationships between entities
   - Creates queryable knowledge graph

### Batch Processing

Process multiple documents using the command-line script:

```bash
# Process all documents
python process_documents.py

# Process only 5 smallest documents (for testing)
python process_documents.py 5

# Process 10 documents
python process_documents.py 10
```

## 💬 Using the Chat Interface

### Query Types

The system handles various types of questions:

- **Factual**: "What is the range of the M777 howitzer?"
- **Procedural**: "How do I perform preventive maintenance on the M109?"
- **Visual**: "Show me the firing table for M795 projectiles"
- **Comparative**: "What's the difference between M549 and M795 rounds?"

### Features

- **Multimodal Responses**: Text answers with supporting images
- **Source Citations**: References to specific documents and pages
- **Metadata Display**: Confidence scores and retrieval information
- **Visual Context**: Relevant diagrams and technical illustrations

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vectordb
NEO4J_HOST=localhost
NEO4J_PORT=7687

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# AI Models
VLM_MODEL=qwen2.5vl:7b
LLM_MODEL=qwen2.5:7b
EMBEDDING_MODEL=nomic-embed-text

# Directories
DATA_DIR=/app/data
DOCUMENTS_DIR=/app/data/documents
IMAGES_DIR=/app/images
```

### Model Configuration

The system uses local AI models via Ollama:

- **qwen2.5vl:7b**: Vision-Language model for image analysis
- **qwen2.5:7b**: Text-only LLM for generation and analysis
- **nomic-embed-text**: Text embedding model
- **clip-ViT-B-32**: Multimodal embedding model (via Python)

## 🔧 Development

### Adding New Features

1. **Document Processors**: Extend `granite_docling_extraction.py`
2. **Embedding Methods**: Modify `multimodal_embeddings.py`
3. **RAG Pipeline**: Update `rag_core.py`
4. **Web Interface**: Enhance `main.py`

### Database Schema

#### PostgreSQL (fa_gpt_documents)
```sql
CREATE TABLE fa_gpt_documents (
    id UUID PRIMARY KEY,
    source_doc VARCHAR(255),
    element_type VARCHAR(50),
    content TEXT,
    page INTEGER,
    bbox JSONB,
    image_data BYTEA,
    vml_analysis JSONB,
    metadata JSONB,
    embedding VECTOR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Neo4j Knowledge Graph
- **Nodes**: WeaponSystem, Ammunition, Component, Procedure, Specification, SafetyWarning
- **Relationships**: USES, REQUIRES, PART_OF, PRECEDED_BY, HAS_SPECIFICATION, HAS_WARNING, COMPATIBLE_WITH

## 🐛 Troubleshooting

### Common Issues

1. **Models not downloading**
   - Check Ollama service status
   - Verify internet connection for initial model pull
   - Check disk space (models are 3-7GB each)

2. **Database connection errors**
   - Verify PostgreSQL and Neo4j are running
   - Check connection credentials in `.env`
   - Ensure pgvector extension is installed

3. **Document processing failures**
   - Check PDF file integrity
   - Verify Docling dependencies
   - Review logs for specific error messages

4. **Out of memory errors**
   - Reduce batch size in processing
   - Process smaller documents first
   - Increase Docker memory limits

### Performance Optimization

- **GPU Acceleration**: Configure CUDA for faster model inference
- **Batch Processing**: Process multiple documents efficiently
- **Index Optimization**: Tune PostgreSQL vector indexes
- **Caching**: Use model and connection caching

## 📊 System Requirements

### Minimum Requirements
- 8GB RAM
- 4 CPU cores
- 20GB disk space
- GPU optional (CPU inference supported)

### Recommended Requirements
- 16GB+ RAM
- 8+ CPU cores
- 50GB+ disk space
- NVIDIA GPU with 8GB+ VRAM

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is intended for U.S. Army use and educational purposes. See LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the troubleshooting section
2. Review logs in the web interface
3. Create an issue with detailed information
4. Include system specifications and error messages

## 🔄 Version History

- **v2.0**: Current version with Docling integration and multimodal RAG
- **v1.0**: Initial version with basic PDF processing

---

**FA-GPT: Empowering Field Artillery with AI-driven document intelligence**
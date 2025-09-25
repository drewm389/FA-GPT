[![CI](https://github.com/drewm389/FA-GPT/actions/workflows/ci.yml/badge.svg)](https://github.com/drewm389/FA-GPT/actions/workflows/ci.yml)
# FA-GPT: Field Artillery GPT
# FA-GPT: Field Artillery GPT System 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) A state-of-the-art local Retrieval-Augmented Generation (RAG) system specifically designed for Field Artillery technical documents. FA-GPT uses IBM's cutting-edge Granite-Docling-258M vision-language model and advanced multimodal processing to provide intelligent question-answering capabilities over military technical manuals.



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)A state-of-the-art local Retrieval-Augmented Generation (RAG) system specifically designed for Field Artillery technical documents. FA-GPT uses IBM's cutting-edge Granite-Docling-258M vision-language model and advanced multimodal processing to provide intelligent question-answering capabilities over military technical manuals.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[![GPU: AMD ROCm](https://img.shields.io/badge/GPU-AMD%20ROCm-red.svg)](https://rocm.docs.amd.com/)## 🎯 System Overview

[![AI: Local](https://img.shields.io/badge/AI-100%25%20Local-green.svg)](https://ollama.ai/)

FA-GPT combines multiple advanced technologies to create a comprehensive multimodal document intelligence system:

> **Production-ready Retrieval-Augmented Generation (RAG) system for U.S. Army Field Artillery documents with GPU acceleration, professional logging, and enterprise-grade operational capabilities.**

## 🔄 Recent Architecture Improvements

FA-GPT has been refactored for better maintainability and cleaner separation of concerns:

### **New Application Architecture**
- **`app/state.py`**: Centralized state management with `AppState` dataclass replacing scattered session variables
- **`app/military_ui.py`**: Clean UI rendering class (`MilitaryUI`) separating interface logic from business logic
- **`app/main.py`**: Simplified controller coordinating state and UI components

### **Unified Processing Scripts**
- **`process.py`**: Single consolidated script replacing multiple processing utilities
  - Replaces: `process_documents.py`, `enhanced_reprocessing.py`, `retry_failed_ingestion.py`
  - Supports: batch processing, failed document retry, database clearing, custom limits
  - Command-line interface: `python process.py --help` for all options

### **Benefits of Refactoring**
- **Cleaner Architecture**: Separation of concerns with state, UI, and business logic
- **Easier Maintenance**: Single processing script instead of multiple redundant tools
- **Better Testing**: Modular components allow for targeted unit testing
- **Improved Documentation**: Centralized logic makes codebase easier to understand

## ⚡ GPU Acceleration 

## 🎯 Overview

FA-GPT now features **full GPU acceleration** with support for:

FA-GPT is a sophisticated, locally-deployed RAG system specifically designed for processing and querying U.S. Army Field Artillery documentation. Built with enterprise-grade reliability, the system provides intelligent document analysis, semantic search, and AI-powered question answering while maintaining complete data sovereignty through local processing.

- **AMD RX 6700 XT**: Complete ROCm 6.2.0 support with 12GB VRAM utilization

### ✨ Key Features- **NVIDIA GPUs**: CUDA acceleration for enhanced performance

- **PyTorch 2.5.1+rocm6.2**: Optimized for AMD graphics cards

- **🤖 Advanced Document Processing**: IBM Granite + Docling with RT-DETR v2 for multimodal document parsing- **Enhanced Processing**: GPU-accelerated document analysis with Granite-Docling-258M

- **🚀 GPU Acceleration**: Optimized for AMD RX 6700 XT with ROCm 6.2.0 + PyTorch 2.5.1+rocm6.2- **MIOpen Database**: Optimized OCR performance for AMD hardware

- **🧠 Unified AI Stack**: Ollama with `qwen2.5vl:7b` vision-language model for all AI tasks

- **🗄️ Hybrid Storage**: PostgreSQL + pgvector + Apache AGE for vector search and knowledge graphsPerformance improvements:

- **🔒 Complete Privacy**: 100% local processing, no external API dependencies- **5-10x faster** document processing compared to CPU-only mode

- **📊 Production Ready**: Professional logging, monitoring, diagnostics, and unified CLI interfaces- **Real-time inference** for interactive query responses

- **Parallel processing** of multiple documents simultaneously

### 🏗️ Architecture- **Advanced image analysis** with Vision-Language Models (VLM)



```mermaid## 📄 Document Processing

graph TB

    A[PDF Documents] --> B[Docling + Granite-258M]### Supported Document Types

    B --> C[Content Extraction]

    C --> D[Qwen2.5VL:7b Processing]- **PDF Military Technical Manuals**: Field Manuals (FMs), Technical Manuals (TMs)

    D --> E[Vector Embeddings]- **Tabular Firing Tables (TFTs)**: Complex numerical tables with ballistic data

    D --> F[Knowledge Graph]- **Army Regulations (ARs)**: Policy and procedural documents

    E --> G[PostgreSQL + pgvector]- **Training Materials**: SOPs, lesson plans, and procedural guides

    F --> H[Apache AGE]- **Equipment Manuals**: Maintenance guides and technical specifications

    G --> I[Semantic Search]

    H --> I### Enhanced Processing Pipeline with Granite-Docling-258M

    I --> J[RAG Response]

```1. **Multimodal Document Parsing** (IBM Granite-Docling-258M)

   - 258M parameter vision-language model specialized for documents

## 🚀 Quick Start   - Superior table recognition and formula detection

   - Advanced layout understanding with DocTags format

### Prerequisites   - Handles complex military document structures

   - OCR for scanned documents with high accuracy

- **Operating System**: Linux (Ubuntu 20.04+ recommended)

- **GPU**: AMD RX 6000+ series with ROCm 6.2.0+2. **Intelligent Content Extraction**

- **Memory**: 16GB+ RAM, 8GB+ VRAM   - Text blocks with semantic understanding

- **Storage**: 50GB+ free space   - Images with contextual relationships

- **Python**: 3.8+ with virtual environment support   - Tables preserved with full structure and data types

   - Mathematical formulas and equations

### Installation   - Document hierarchy and cross-references



1. **Clone the repository**:3. **Multimodal Embedding Generation**

   ```bash   - CLIP/Open-CLIP for unified text+image embeddings

   git clone https://github.com/yourusername/FA-GPT.git   - Specialized military domain vocabulary

   cd FA-GPT   - Cross-modal semantic understanding

   ```   - Vector representations for similarity search



2. **Set up Python environment**:4. **Knowledge Graph Construction**

   ```bash   - Entity extraction (weapons, procedures, personnel)

   python -m venv fagpt_env   - Relationship mapping between concepts

   source fagpt_env/bin/activate   - Cross-document reference linking

   pip install -r requirements.txt   - Hierarchical knowledge organization

   ```

5. **Unified Storage**

3. **Start the system**:   - PostgreSQL with pgvector for fast vector similarity search

   ```bash   - Apache AGE for complex knowledge graph queries within PostgreSQL

   ./start.sh   - Single database for both embeddings and entity relationships

   ```   - Organized file structure for manual access

   - Metadata preservation for traceability

4. **Verify installation**:

   ```bash- **IBM Granite-Docling-258M**: State-of-the-art 258M parameter vision-language model for document understanding

   python system_status.py --detailed- **Enhanced Docling 2.54.0+**: Superior document parsing with table and formula recognition

   ```- **Ollama**: Local LLM/VLM inference (Qwen 2.5 models)

- **PostgreSQL with pgvector + Apache AGE**: Unified vector storage and knowledge graphs

### First Document Processing- **Nomic Embed Text**: Multimodal text and image embeddings

- **Streamlit**: Interactive web interface

```bash- **Docker**: Complete containerized deployment

# Place PDF documents in the documents directory

cp your_pdfs/*.pdf data/documents/## 🏗️ Architecture



# Process documents with verbose output```

python process.py --input-dir data/documents --limit 5┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐

│   PDF Documents │ -> │ Granite-Docling-258M │ -> │ Organized Files │

# Access web interface│  (TFTs, FMs,    │    │   VLM Processing     │    │ (Text, Images,  │

streamlit run app/main.py│   Regulations)  │    │                      │    │  Tables, Meta)  │

# Navigate to: http://localhost:8501└─────────────────┘    └──────────────────────┘    └─────────────────┘

```                                │

                                v

## 📖 Documentation┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐

│PostgreSQL w/    │ <- │ Multimodal RAG   │ <- │  PostgreSQL     │

- **[🏗️ Architecture Guide](ARCHITECTURE.md)**: Complete technical architecture and troubleshooting│ Apache AGE      │    │    Pipeline      │    │  + pgvector     │

- **[⚙️ Operations Manual](OPERATIONS.md)**: Daily operations, commands, and maintenance procedures  │Knowledge Graphs │    │ Nomic Embeddings │    │Vector Database  │

- **[🚀 Setup Guide](SETUP_COMPLETE.md)**: Quick start and system overview│Entities & Rels  │    │  Qwen 2.5 VL     │    │                 │

└─────────────────┘    └──────────────────┘    └─────────────────┘

## 🛠️ Usage                                │

                                v

### Command Line Interface                    ┌──────────────────┐

                    │  Streamlit UI    │

**Single Document Processing**:                    │ (Chat Interface) │

```bash                    │  Docker Deploy   │

python -m app.simple_ingestion --file /path/to/document.pdf --verbose

# Or use the unified processing script for single files
python process.py --input-dir /path/containing/single/file --limit 1                    └──────────────────┘

``````



**Batch Processing**:## 📁 Project Structure

```bash

python process.py --input-dir data/documents --limit 10```

```FA-GPT/

├── app/                                   # Main application code

**System Monitoring**:│   ├── main.py                            # Streamlit web interface

```bash│   ├── config.py                          # Configuration settings

python system_status.py --detailed --verbose│   ├── connectors.py                      # Database and AI model connections

```│   ├── simple_ingestion.py                # Document processing pipeline

│   ├── rag_core.py                        # RAG query processing

### Web Interface│   ├── granite_multimodal_extractor.py    # Granite-Docling-258M integration

│   ├── granite_docling_extraction.py      # Enhanced Docling parsing

Start the Streamlit interface for interactive document processing:│   ├── multimodal_embeddings.py           # CLIP embedding generation

│   └── enhanced_extraction.py             # Advanced extraction utilities

```bash├── data/

streamlit run app/main.py│   ├── documents/                         # Source PDF files

```│   │   ├── Original PDFs/                 # Original military documents

│   │   ├── TFTs/                          # Tabular Firing Tables

Features:│   │   └── Field Manuals/                 # Army Field Manuals

- 📤 Drag-and-drop PDF upload│   └── extracted/                         # Processed document outputs

- 🔍 Real-time processing progress│       └── {publication}/                 # Per-document organized content

- 💬 Natural language querying│           ├── text/                      # Text elements (.txt)

- 📊 Document insights and analytics│           ├── images/                    # Extracted images (.png)

- 🖼️ Extracted images and tables│           ├── tables/                    # Table data (.json)

│           └── metadata/                  # Element metadata (.json)

### API Integration├── images/                                # Document image cache

├── process.py                             # Unified document processing script

```python

from app.simple_ingestion import process_and_ingest_document├── docker-compose.yml                     # Docker services configuration

from app.rag_core import query_documents├── Dockerfile.streamlit                   # Streamlit container

├── requirements.txt                       # Python dependencies

# Process a document├── CHANGELOG.md                           # Version history

process_and_ingest_document("/path/to/document.pdf")└── README.md                              # This file

```

# Query the knowledge base

response = query_documents("What are the firing procedures for M777 howitzer?")## 🚀 Quick Start

print(response)

```### Prerequisites



## 🔧 Configuration- Docker Desktop with GPU support (recommended)

- 16GB+ RAM recommended for optimal performance

### Environment Variables- 50GB+ disk space for models and processed documents

- AMD RX 6000+ or NVIDIA RTX 3000+ GPU (optional but recommended)

Create a `.env` file for custom configuration:

### Option 1: Docker Deployment (Recommended)

```bash

# Database Configuration1. **Clone and navigate to the repository**

POSTGRES_HOST=localhost   ```bash

POSTGRES_PORT=5432   git clone <repository-url>

POSTGRES_DB=vectordb   cd FA-GPT

POSTGRES_USER=postgres   ```

POSTGRES_PASSWORD=your_password

2. **Start the complete stack**

# Ollama Configuration     ```bash

OLLAMA_HOST=localhost   # Start all services (PostgreSQL with pgvector + Apache AGE, Ollama, Streamlit)

OLLAMA_PORT=11434   docker compose up -d

   

# GPU Configuration   # Check service status

ROCM_PATH=/opt/rocm   docker compose ps

HIP_VISIBLE_DEVICES=0   ```

```

3. **Initialize AI models** (automatic on first run)

### GPU Optimization   ```bash

   # Models will auto-download: Qwen 2.5, CLIP, Granite-Docling-258M

The system includes comprehensive MIOpen configuration for stable GPU processing:   # Initial setup takes 10-15 minutes depending on internet speed

   ```

```bash

# Automatically configured by start.sh4. **Access the web interface**

export MIOPEN_ENABLE_SQLITE_KERNDB=0   - Open http://localhost:8501 in your browser

export MIOPEN_ENABLE_SQLITE_PERFDB=0   - Upload PDFs through the sidebar interface

export MIOPEN_USER_DB_PATH=/tmp/miopen_cache_text   - Start processing and querying documents!

```

### Option 2: Local Development

## 📊 Performance

1. **Install Python dependencies**

### Processing Benchmarks   ```bash

   python -m venv fagpt_env

| Document Size | Processing Time | GPU Utilization |   source fagpt_env/bin/activate  # On Windows: fagpt_env\Scripts\activate

|---------------|-----------------|-----------------|   pip install -r requirements.txt

| Small (< 1MB) | 2-5 seconds | 60-80% |   ```

| Medium (1-10MB) | 10-30 seconds | 80-95% |

| Large (> 10MB) | 30-120 seconds | 90-100% |2. **GPU Setup (Optional but Recommended)**

   

### Throughput Metrics   **For AMD Graphics Cards (RX 6700 XT, etc.):**

   ```bash

- **Document Processing**: 5-15 pages/minute   # Install ROCm 6.2.0 for AMD GPU acceleration

- **Vector Search**: < 100ms for 10k+ documents   wget https://repo.radeon.com/amdgpu-install/6.2/ubuntu/jammy/amdgpu-install_6.2.60200-1_all.deb

- **Knowledge Graph Queries**: < 200ms average response time   sudo dpkg -i amdgpu-install_6.2.60200-1_all.deb

   sudo amdgpu-install --usecase=rocm

## 🔍 Monitoring & Logging   

   # Install PyTorch with ROCm support

### Structured Logging   pip install torch==2.5.1+rocm6.2 torchvision==0.20.1+rocm6.2 torchaudio==2.5.1+rocm6.2 \

       --index-url https://download.pytorch.org/whl/rocm6.2

Professional logging system with rotation and performance tracking:   

   # Add user to render group

```bash   sudo usermod -a -G render $USER

# View real-time logs   # Logout and login to apply group changes

tail -f logs/fa-gpt-system.log   

   # Set environment variables

# Monitor errors   export HSA_OVERRIDE_GFX_VERSION=10.3.0

grep "ERROR\|EXCEPTION" logs/fa-gpt-system.log   export HIP_VISIBLE_DEVICES=0

   export PYTORCH_ROCM_ARCH=gfx1030

# Performance analysis   ```

grep "Performance\|⏱️" logs/fa-gpt-system.log   

```   **For NVIDIA Graphics Cards:**

   ```bash

### System Health   # Install CUDA-enabled PyTorch

   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

```bash   ```

# Quick status check

python system_status.py3. **Set up local services**

   ```bash

# Detailed diagnostics   # Install and start PostgreSQL with pgvector and Apache AGE extensions

python system_status.py --detailed --verbose   # Install and start Ollama

   ollama pull qwen2.5:14b

# Service-only monitoring (for CI/CD)   ollama pull qwen2.5vl:7b  # For multimodal image analysis

python system_status.py --services-only   ollama pull nomic-embed-text

```   ```



## 🛡️ Security & Privacy4. **Configure environment**

   ```bash

- **🔒 Air-Gapped Operation**: Complete offline capability   cp .env.example .env

- **🏠 Local Processing**: All data remains on your infrastructure   # Edit .env with your local database credentials

- **🔐 No External APIs**: Zero dependency on cloud services   ```

- **📁 Secure Storage**: PostgreSQL with standard security practices

- **🚫 No Telemetry**: No usage data collection or external communication5. **Run the application**

   ```bash

## 🚧 Troubleshooting   streamlit run app/main.py

   ```

### Common Issues

## 📚 Document Processing

**GPU Processing Crashes**:

```bash### Supported Document Types

# Restart with proper MIOpen configuration

./stop.sh && ./start.sh- PDF military technical manuals

- Field Artillery firing tables (TFTs)

# Verify GPU status- Training materials and procedures

rocm-smi- Equipment manuals and specifications

```

### Processing Pipeline

**Database Connection Issues**:

```bash1. **Document Parsing** (IBM Docling)

# Check PostgreSQL service   - Extracts text, images, tables, and structure

python system_status.py --services-only   - Preserves document hierarchy and relationships

   - Handles both text and scanned documents (OCR)

# Restart database

docker-compose restart postgres2. **Content Organization**

```   - Saves extracted content in publication-specific folders

   - Organizes by content type (text, images, tables, metadata)

**Document Processing Failures**:   - Maintains source document references

```bash

# Enable verbose diagnostics3. **Embedding Generation**

python -m app.simple_ingestion --file problematic.pdf --verbose   - Creates unified vector representations for text and images

   - Uses CLIP for multimodal embeddings

# Check PDF diagnostics   - Enables semantic similarity search

python -c "

from app.enhanced_granite_docling import Enhanced_Granite_Docling_Processor4. **Database Storage**

processor = Enhanced_Granite_Docling_Processor()   - PostgreSQL: Vector embeddings and content for RAG

print(processor._extract_pdf_diagnostics('problematic.pdf'))   - Neo4j: Knowledge graph of entities and relationships

"

```5. **Knowledge Extraction**

   - Identifies military entities (weapons, ammunition, procedures)

## 🤝 Contributing   - Extracts relationships between entities

   - Creates queryable knowledge graph

1. Fork the repository

2. Create a feature branch (`git checkout -b feature/amazing-feature`)### Batch Processing

3. Commit your changes (`git commit -m 'Add amazing feature'`)

4. Push to the branch (`git push origin feature/amazing-feature`)Process multiple documents using the command-line script:

5. Open a Pull Request

```bash

### Development Setup# Process all documents

python process_documents.py

```bash

# Install development dependencies# Process only 5 smallest documents (for testing)

pip install -r requirements-dev.txtpython process_documents.py 5



# Run tests# Process 10 documents

python -m pytest tests/python process_documents.py 10

```

# Code formatting

black app/ *.py## 💬 Using the Chat Interface



# Type checking### Query Types

mypy app/

```The system handles various types of questions:



## 📋 Roadmap- **Factual**: "What is the range of the M777 howitzer?"

- **Procedural**: "How do I perform preventive maintenance on the M109?"

- [ ] **Multi-GPU Support**: Distributed processing across multiple GPUs- **Visual**: "Show me the firing table for M795 projectiles"

- [ ] **API Server**: RESTful API for external integrations- **Comparative**: "What's the difference between M549 and M795 rounds?"

- [ ] **Advanced Analytics**: Document relationship analysis and insights

- [ ] **Model Fine-tuning**: Domain-specific model optimization### Features

- [ ] **Kubernetes Support**: Cloud-native deployment options

- **Multimodal Responses**: Text answers with supporting images

## 📄 License- **Source Citations**: References to specific documents and pages

- **Metadata Display**: Confidence scores and retrieval information

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.- **Visual Context**: Relevant diagrams and technical illustrations



## 🙏 Acknowledgments## ⚙️ Configuration



- **IBM Research**: Granite + Docling document processing models### Environment Variables

- **Ollama Team**: Local LLM inference framework

- **PostgreSQL Community**: pgvector and Apache AGE extensionsKey configuration options in `.env`:

- **AMD**: ROCm GPU computing platform

- **U.S. Army**: Field Artillery documentation standards and requirements```bash

# Database Configuration

## 📞 SupportPOSTGRES_HOST=localhost

POSTGRES_PORT=5432

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) and [OPERATIONS.md](OPERATIONS.md)POSTGRES_DB=vectordb

- **Issues**: Open a GitHub issue for bug reports or feature requestsNEO4J_HOST=localhost

- **Discussions**: Use GitHub Discussions for questions and community supportNEO4J_PORT=7687



---# Ollama Configuration

OLLAMA_HOST=localhost

**FA-GPT**: Bringing AI-powered document intelligence to the modern battlefield while maintaining complete operational security and data sovereignty.OLLAMA_PORT=11434



*Built with ❤️ for the U.S. Army Field Artillery community*# AI Models
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
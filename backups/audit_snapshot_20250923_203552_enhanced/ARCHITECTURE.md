# FA-GPT System Architecture Documentation

## Overview

FA-GPT (Field Artillery GPT) is a production-ready Retrieval-Augmented Generation (RAG) system designed specifically for U.S. Army Field Artillery documents. The system leverages state-of-the-art AI models and enterprise-grade infrastructure for robust document processing, semantic search, and intelligent query response.

## System Architecture

### Core Components

#### 1. Document Processing Pipeline
- **Docling + IBM Granite-258M**: Multimodal document parsing with table extraction and OCR
- **RT-DETR v2**: Advanced object detection for document structure analysis
- **GPU-Accelerated Processing**: AMD RX 6700 XT (gfx1030) with ROCm 6.2.0 support

#### 2. AI/ML Stack
- **Ollama**: Local LLM/VLM inference server
- **Primary Model**: `qwen2.5vl:7b` (unified vision-language model)
- **Embeddings**: `nomic-embed-text` for semantic vector generation
- **Multimodal Embeddings**: CLIP ViT-B/32 for unified text+image vectors

#### 3. Data Storage
- **PostgreSQL**: Primary database with extensions:
  - **pgvector**: High-performance vector similarity search
  - **Apache AGE**: Knowledge graph storage and graph queries
- **File System**: Organized document extraction and image storage

#### 4. Runtime Environment
- **GPU Environment**: ROCm 6.2.0 + PyTorch 2.5.1+rocm6.2
- **MIOpen Configuration**: Separate SQLite/text backends for stability
- **Container Support**: Docker Compose orchestration

## Technical Implementation

### GPU Processing Configuration

The system implements comprehensive MIOpen configuration to prevent GPU processing crashes:

```bash
# MIOpen Backend Separation (prevents SQLite/text mixing)
export MIOPEN_ENABLE_SQLITE_KERNDB=0     # Disable SQLite for kernel database
export MIOPEN_ENABLE_SQLITE_PERFDB=0     # Disable SQLite for performance database
export MIOPEN_USER_DB_PATH="/tmp/miopen_cache_text"  # Text-based cache path
export MIOPEN_FIND_ENFORCE=SEARCH        # Enforce search mode
export MIOPEN_USE_GEMM=1                 # Enable optimized GEMM operations
export MIOPEN_DEBUG_DISABLE_MLIR=1       # Disable MLIR for stability
```

**Technical Rationale**: The root cause of GPU crashes was identified as MIOpen backend mixing between SQLite and text databases. This configuration ensures consistent text-based caching and prevents database path conflicts.

### Structured Logging System

#### Logging Framework Architecture

The system implements a centralized `FAGPTLogger` class with enterprise-grade features:

```python
# app/logging_config.py
class FAGPTLogger:
    - File rotation: 10MB max size, 5 backup files
    - Dual output: File + console logging
    - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Error tracking: Exception logging with stack traces
    - Performance timing: Context manager for operation timing
    - Environment logging: System configuration details
```

#### Component-Specific Loggers

Each system component uses structured logging:

- `enhanced-granite-docling`: GPU extraction operations
- `simple-ingestion`: Document processing pipeline
- `process-documents`: Batch processing operations
- `system-status`: System monitoring and health checks
- `config`: Configuration initialization and validation

#### Log File Organization

```
logs/
├── fa-gpt-system.log      # Current log file
├── fa-gpt-system.log.1    # First backup
├── fa-gpt-system.log.2    # Second backup
├── ...
└── fa-gpt-system.log.5    # Fifth backup (oldest)
```

### Command Line Interface (CLI)

#### Unified CLI Standards

All system scripts implement consistent CLI interfaces with professional argument parsing:

**Common Options**:
- `--verbose`: Enable DEBUG-level logging
- `--clear-db`: Clear database before processing
- `--limit N`: Limit processing to N documents
- `--input-dir PATH`: Specify input directory

**Script-Specific Options**:

**simple_ingestion.py**:
```bash
python -m app.simple_ingestion --file /path/to/document.pdf
python -m app.simple_ingestion --input-dir data/documents --test-single file.pdf --verbose
python -m app.simple_ingestion --input-dir data/documents --limit 5 --clear-db
```

**process_documents.py**:
```bash
python process_documents.py --input-dir data/documents --limit 5 --verbose
python process_documents.py --clear-db --verbose
```

**system_status.py**:
```bash
python system_status.py --detailed --verbose
python system_status.py --services-only
```

### Diagnostic Capabilities

#### PDF Diagnostic Metadata

The system provides comprehensive PDF analysis through `_extract_pdf_diagnostics()`:

```python
def _extract_pdf_diagnostics(pdf_path: str) -> dict:
    """Extract comprehensive PDF metadata for troubleshooting."""
    return {
        "file_size_mb": float,      # File size in megabytes
        "page_count": int,          # Total number of pages
        "is_encrypted": bool,       # Encryption status
        "has_text": bool,           # Text content presence
        "has_images": bool,         # Image content presence
        "creation_date": str,       # Document creation timestamp
        "modification_date": str,   # Last modification timestamp
        "producer": str,            # PDF producer software
        "creator": str              # Original creation software
    }
```

This diagnostic information aids in:
- Troubleshooting extraction failures
- Identifying problematic document formats
- Performance optimization based on document characteristics
- Quality assessment of processing results

### Performance Optimizations

#### Memory Management
- **Page-batch processing**: Process large documents in manageable chunks
- **GPU memory monitoring**: Track VRAM usage and prevent OOM errors
- **Cache management**: Efficient MIOpen cache organization

#### Processing Efficiency
- **Size-based ordering**: Process smallest documents first for faster feedback
- **Parallel embeddings**: Concurrent vector generation when possible
- **Incremental processing**: Skip already-processed documents

## Database Schema

### PostgreSQL Tables

#### Vector Storage (pgvector)
```sql
-- fa_gpt_documents table
CREATE TABLE fa_gpt_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content TEXT,
    embedding vector(768),  -- Nomic Embed Text dimensions
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector similarity index
CREATE INDEX ON fa_gpt_documents USING ivfflat (embedding vector_cosine_ops);
```

#### Knowledge Graph (Apache AGE)
```sql
-- Create graph for FA-GPT knowledge
SELECT create_graph('fa_gpt_kg');

-- Entities and relationships stored as graph nodes and edges
-- Accessible via Cypher queries through AGE extension
```

## Operational Procedures

### System Startup

1. **Environment Setup**:
   ```bash
   ./start.sh  # Comprehensive MIOpen + service startup
   ```

2. **Service Verification**:
   ```bash
   python system_status.py --detailed --verbose
   ```

3. **Document Processing**:
   ```bash
   python process_documents.py --input-dir data/documents --limit 5 --verbose
   ```

### Monitoring and Maintenance

#### Health Checks
- **Service Status**: PostgreSQL, Ollama, GPU availability
- **Model Status**: Verify Qwen2.5VL:7b and nomic-embed-text
- **Storage Status**: Database connections, disk space
- **GPU Status**: ROCm driver, MIOpen configuration

#### Log Monitoring
```bash
# Real-time log monitoring
tail -f logs/fa-gpt-system.log

# Error pattern analysis
grep "ERROR\|EXCEPTION" logs/fa-gpt-system.log

# Performance analysis
grep "Performance\|⏱️" logs/fa-gpt-system.log
```

#### Database Maintenance
```bash
# Clear database for fresh start
python process_documents.py --clear-db

# Database connection testing
python system_status.py --services-only
```

## Troubleshooting Guide

### GPU Processing Issues

**Problem**: GPU crashes with MIOpen database errors
**Solution**: Verify MIOpen configuration in start.sh
```bash
# Check MIOpen environment
echo $MIOPEN_ENABLE_SQLITE_KERNDB  # Should be 0
echo $MIOPEN_USER_DB_PATH          # Should point to text cache
```

**Problem**: ROCm driver issues
**Solution**: Verify ROCm installation and GPU recognition
```bash
rocm-smi                           # Check GPU status
pytorch version check              # Verify ROCm PyTorch build
```

### Document Processing Failures

**Problem**: PDF extraction fails silently
**Solution**: Enable diagnostic logging
```bash
python -m app.simple_ingestion --file problem.pdf --verbose
```

**Problem**: Large documents cause OOM errors
**Solution**: Implement memory-optimized processing
- Process documents in page batches
- Monitor GPU memory usage
- Use document size limits for testing

### Service Connectivity Issues

**Problem**: PostgreSQL connection failures
**Solution**: Verify database service and credentials
```bash
python system_status.py --services-only
docker-compose ps postgres  # If using Docker
```

**Problem**: Ollama model unavailable
**Solution**: Check model installation and service status
```bash
ollama list                  # Verify installed models
ollama pull qwen2.5vl:7b    # Download missing model
```

## Performance Benchmarks

### Processing Speed
- **Small PDFs** (< 1MB): ~2-5 seconds
- **Medium PDFs** (1-10MB): ~10-30 seconds  
- **Large PDFs** (> 10MB): ~30-120 seconds

### GPU Utilization
- **Optimal VRAM usage**: 8-12GB for RX 6700 XT
- **Processing throughput**: ~5-15 pages/minute
- **Batch efficiency**: 20-40% faster than individual processing

### Storage Requirements
- **Extracted content**: ~2-5x original PDF size
- **Vector embeddings**: ~3KB per 512-token chunk
- **Images**: Variable (depends on PDF content)

## Security Considerations

### Data Protection
- **Local Processing**: All data remains on local infrastructure
- **No External APIs**: Complete air-gapped operation capability
- **Secure Storage**: PostgreSQL with standard security practices

### Access Control
- **Database Authentication**: PostgreSQL user credentials
- **File Permissions**: Proper Unix permissions for data directories
- **Container Security**: Docker security best practices

## Development and Deployment

### Local Development Setup
1. Clone repository and setup virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env`
4. Initialize database with extensions
5. Start services: `./start.sh`

### Production Deployment
1. Use Docker Compose for service orchestration
2. Configure persistent volumes for data
3. Set appropriate resource limits
4. Implement backup strategies for database
5. Monitor system health and performance

### Testing Procedures
1. **Unit Tests**: Component-level functionality
2. **Integration Tests**: End-to-end pipeline testing  
3. **Performance Tests**: GPU processing benchmarks
4. **Stress Tests**: High-volume document processing

This documentation provides a comprehensive guide for understanding, operating, and maintaining the FA-GPT system in production environments.
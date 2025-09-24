# FA-GPT Technical Documentation

This document provides comprehensive technical details about the FA-GPT (Field Artillery GPT) system architecture, implementation, and deployment with the latest Granite-Docling-258M integration.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Granite-Docling-258M Integration](#granite-docling-258m-integration)
3. [Multimodal Processing Pipeline](#multimodal-processing-pipeline)
4. [Database Schema](#database-schema)
5. [AI Models and Configuration](#ai-models-and-configuration)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

## System Architecture

### Overview

FA-GPT implements a microservices architecture using Docker containers with advanced document processing capabilities:

```
┌─────────────────────────────────────────────────────────────────┐
│                     FA-GPT System v2.1                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Streamlit UI  │  Document       │   RAG Engine    │  AI Models│
│   (Port 8501)   │  Processing     │                 │  (Ollama) │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ - User Interface│ - Granite VLM   │ - Query Process │ - Qwen 2.5│
│ - Chat Interface│ - Enhanced Doc  │ - Vector Search │ - CLIP    │
│ - Doc Management│ - Content Org   │ - KG Retrieval  │ - Granite │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
         │                 │                 │                │
         └─────────────────┼─────────────────┼────────────────┘
                           │                 │
         ┌─────────────────┼─────────────────┼────────────────┐
         │              Enhanced Data Layer                   │
         ├─────────────────┬─────────────────┬────────────────┤
         │  PostgreSQL     │     Neo4j       │   File System  │
         │  + pgvector     │                 │                │
         ├─────────────────┼─────────────────┼────────────────┤
         │ - Vector Store  │ - Knowledge     │ - Document     │
         │ - Embeddings    │   Graph         │   Storage      │
         │ - Metadata      │ - Entities      │ - Images       │
         │ - Full Text     │ - Relationships │ - Extracted    │
         └─────────────────┴─────────────────┴────────────────┘
```

## Granite-Docling-258M Integration

### Model Specifications

**IBM Granite-Docling-258M** is a specialized 258M parameter vision-language model designed for document understanding:

- **Architecture**: Transformer-based with optimized vision and language components
- **Specialization**: Tables, formulas, layout understanding, military documents
- **Input Format**: PDF pages as images + structured prompts
- **Output Format**: DocTags structured format preserving document layout
- **Performance**: 90%+ accuracy on structured document elements

### Technical Implementation

#### Model Loading and Initialization

```python
from mlx_vlm import load, stream_generate
from mlx_vlm.prompt_utils import apply_chat_template

class GraniteMultimodalExtractor:
    def __init__(self):
        self.model_path = "ibm-granite/granite-docling-258M-mlx"
        self.granite_model, self.granite_processor = load(self.model_path)
        self.granite_config = load_config(self.model_path)
```

#### Enhanced Document Processing Pipeline

1. **PDF to High-Resolution Images**: Convert PDF pages to 300 DPI images
2. **Page-by-Page VLM Analysis**: Process each page with Granite-Docling-258M
3. **DocTags Generation**: Create structured format preserving layout
4. **Element Extraction**: Parse DocTags into typed elements with metadata
5. **Fallback Handling**: Use standard Docling if VLM unavailable

### Performance Characteristics

- **Memory Usage**: 2-4GB for model, scales with document complexity
- **Processing Speed**: 10-30 seconds per page (GPU accelerated)
- **Accuracy Metrics**:
  - Text extraction: 95%+
  - Table recognition: 90%+ (major improvement over standard OCR)
  - Formula detection: 85%+
  - Layout preservation: 95%+
```

**Stage 2: Multimodal Retrieval**
```python
def retrieve_multimodal_content(query: str, intent: Dict) -> List[Dict]:
    # Vector similarity search against document embeddings
    # Filters by content type based on query intent
    # Returns top candidates with similarity scores
```

**Stage 3: AI-Powered Reranking**
```python
def rerank_with_local_vlm(query: str, results: List[Dict], client) -> List[Dict]:
    # Uses VLM to analyze image relevance
    # LLM evaluation of text content relevance
    # Combines similarity scores with AI analysis
```

**Stage 4: Knowledge Graph Augmentation**
```python
def get_kg_context(query: str) -> List[Dict]:
    # Searches Neo4j for relevant entities and relationships
    # Adds structured knowledge to context
    # Provides entity connections and properties
```

**Stage 5: Response Generation**
```python
def generate_vlm_response(query: str, contexts: List[Dict], kg_context: List[Dict], client) -> Tuple[str, List[Dict]]:
    # Combines retrieved content with KG context
    # Uses VLM for image-aware response generation
    # Provides citations and source references
```

#### 3. Multimodal Embeddings (`app/multimodal_embeddings.py`)

Handles unified embedding generation for text and images:

**Text Embeddings**
- Primary: CLIP text encoder for multimodal alignment
- Fallback: Ollama text embeddings via nomic-embed-text
- Final fallback: Sentence transformers

**Image Embeddings**
- CLIP image encoder for visual content
- Fallback: VLM description → text embedding
- Preserves visual-semantic relationships

**Unified Vector Space**
- Enables text-image similarity comparison
- Supports multimodal retrieval queries
- Maintains semantic coherence across modalities

#### 4. Database Connections (`app/connectors.py`)

Manages all external service connections:

**Ollama Client**
- Cached connection to local AI inference server
- Automatic model pulling and validation
- Handles both LLM and VLM requests

**PostgreSQL Connection**
- Vector database for embedding storage
- pgvector extension for similarity operations
- Optimized indexes for fast retrieval

**Neo4j Driver**
- Knowledge graph database connection
- Cypher query execution
- Entity and relationship management

### Data Flow Diagram

```
PDF Document
     │
     ▼
IBM Docling Parser
     │
     ├─ Text Elements ────────┐
     ├─ Image Elements ───────┤
     ├─ Table Elements ───────┤
     └─ Metadata ─────────────┤
                              │
                              ▼
                    Embedding Generation
                    (CLIP + Text Models)
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    File Storage        Vector DB           Knowledge Graph
  (Organized Folders)  (PostgreSQL)           (Neo4j)
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                         RAG Pipeline
                              │
                              ▼
                        User Interface
                        (Streamlit)
```

### Database Schemas

#### PostgreSQL Vector Storage

```sql
CREATE TABLE fa_gpt_documents (
    id UUID PRIMARY KEY,                    -- Unique element identifier
    source_doc VARCHAR(255),                -- Source document filename
    element_type VARCHAR(50),               -- text, image, table, title, etc.
    content TEXT,                           -- Text content (NULL for images)
    page INTEGER,                           -- Page number in source document
    bbox JSONB,                            -- Bounding box coordinates
    image_data BYTEA,                       -- Binary image data (NULL for text)
    vml_analysis JSONB,                     -- VLM analysis results
    metadata JSONB,                         -- Additional element metadata
    embedding VECTOR(512),                  -- 512-dimensional embedding vector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimized indexes for fast retrieval
CREATE INDEX idx_element_type ON fa_gpt_documents(element_type);
CREATE INDEX idx_source_doc ON fa_gpt_documents(source_doc);
CREATE INDEX idx_page ON fa_gpt_documents(page);
CREATE INDEX idx_embedding_cosine ON fa_gpt_documents 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### Neo4j Knowledge Graph

**Node Types:**
- `WeaponSystem`: Artillery pieces, mortars, launchers
- `Ammunition`: Projectiles, charges, fuzes
- `Component`: Parts, subsystems, assemblies
- `Procedure`: Firing procedures, maintenance steps
- `Specification`: Technical specs, ranges, capabilities
- `SafetyWarning`: Safety protocols, warnings

**Relationship Types:**
- `USES`: Entity uses another entity
- `REQUIRES`: Entity requires another entity for operation
- `PART_OF`: Entity is a component of another entity
- `PRECEDED_BY`: Procedure follows another procedure
- `HAS_SPECIFICATION`: Entity has technical specification
- `HAS_WARNING`: Entity has associated safety warning
- `COMPATIBLE_WITH`: Entity works with another entity

### Configuration Management

#### Settings Hierarchy

1. **Default Values**: Defined in `app/config.py`
2. **Environment Variables**: Override defaults
3. **`.env` File**: Override for local development
4. **Docker Environment**: Override for container deployment

#### Key Configuration Categories

**Database Settings**
```python
postgres_host: str = "postgres"      # Container name or localhost
postgres_port: int = 5432
postgres_db: str = "vectordb"
neo4j_host: str = "neo4j"
neo4j_port: int = 7687
```

**AI Model Settings**
```python
vlm_model: str = "qwen2.5vl:7b"     # Vision-Language model
llm_model: str = "qwen2.5:7b"       # Text-only LLM
embedding_model: str = "nomic-embed-text"  # Text embeddings
```

**Processing Settings**
```python
enable_ocr: bool = True              # OCR for scanned documents
enable_table_extraction: bool = True # Table structure parsing
use_multimodal_embeddings: bool = True  # Unified text+image vectors
```

### API Reference

#### Main Processing Function

```python
def process_and_ingest_document(pdf_path: str) -> None:
    """
    Complete document ingestion pipeline.
    
    Args:
        pdf_path: Path to PDF document to process
        
    Outputs:
        - Organized files in data/extracted/{publication}/
        - Vector embeddings in PostgreSQL
        - Knowledge graph in Neo4j
        
    Raises:
        Exception: If parsing or processing fails
    """
```

#### RAG Query Function

```python
def get_rag_response(query: str) -> Tuple[str, List[str], Dict]:
    """
    Process query through complete RAG pipeline.
    
    Args:
        query: User question about documents
        
    Returns:
        - Generated response with citations
        - List of base64-encoded supporting images
        - Metadata about retrieval and generation
    """
```

### Performance Optimization

#### Vector Search Optimization

1. **Index Configuration**
   ```sql
   -- Adjust lists parameter based on data size
   CREATE INDEX idx_embedding_cosine ON fa_gpt_documents 
       USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```

2. **Query Optimization**
   - Limit retrieval candidates (e.g., top 30)
   - Filter by element type when possible
   - Use reranking for final selection

#### Memory Management

1. **Model Caching**
   - Use `@st.cache_resource` for model connections
   - Avoid reloading heavy models
   - Cache embedding functions

2. **Batch Processing**
   - Process documents in size order (smallest first)
   - Limit concurrent processing
   - Use streaming for large documents

#### GPU Acceleration

1. **CUDA Configuration**
   ```python
   device = "cuda" if torch.cuda.is_available() else "cpu"
   model.to(device)
   ```

2. **Memory Management**
   - Clear GPU cache between large operations
   - Use mixed precision when supported
   - Monitor GPU memory usage

### Error Handling and Logging

#### Common Error Patterns

1. **Document Processing Errors**
   ```python
   try:
       doc_elements, image_elements = granite_docling_parsing(pdf_path)
   except Exception as e:
       logger.error(f"Docling parsing failed: {e}")
       return fallback_processing(pdf_path)
   ```

2. **Model Inference Errors**
   ```python
   try:
       response = client.chat(model=model, messages=messages)
   except Exception as e:
       logger.warning(f"Model inference failed, using fallback: {e}")
       return fallback_response()
   ```

3. **Database Connection Errors**
   ```python
   try:
       conn = get_db_connection()
   except Exception as e:
       logger.error(f"Database connection failed: {e}")
       raise ConnectionError("Vector database unavailable")
   ```

#### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fa_gpt.log'),
        logging.StreamHandler()
    ]
)
```

### Testing Strategy

#### Unit Tests

1. **Document Processing**
   - Test Docling integration
   - Validate element extraction
   - Check metadata preservation

2. **Embedding Generation**
   - Test text embedding quality
   - Validate image embedding generation
   - Check vector dimensions

3. **Database Operations**
   - Test vector storage and retrieval
   - Validate knowledge graph operations
   - Check index performance

#### Integration Tests

1. **End-to-End Pipeline**
   - Full document processing test
   - RAG query response test
   - Performance benchmarks

2. **Model Integration**
   - Ollama connection test
   - Model inference validation
   - Error handling verification

#### Performance Tests

1. **Throughput Testing**
   - Documents processed per hour
   - Query response times
   - Memory usage patterns

2. **Scale Testing**
   - Large document handling
   - Concurrent user support
   - Database performance under load

### Deployment Considerations

#### Docker Deployment

1. **Resource Allocation**
   ```yaml
   services:
     ollama:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

2. **Volume Mapping**
   ```yaml
   volumes:
     - ./data:/app/data
     - ./images:/app/images
     - ollama_data:/root/.ollama
   ```

#### Production Setup

1. **Security Considerations**
   - Database access controls
   - API authentication
   - File system permissions

2. **Monitoring**
   - Model inference metrics
   - Database performance
   - System resource usage

3. **Backup Strategy**
   - Database backups
   - Model checkpoint preservation
   - Document archive management

### Extension Points

#### Adding New Document Types

1. **Extend Docling Integration**
   ```python
   def handle_new_document_type(doc_path: str) -> Tuple[List[Dict], List[Dict]]:
       # Custom parsing logic
       # Return text_elements, image_elements
   ```

2. **Update Schema**
   ```sql
   ALTER TABLE fa_gpt_documents ADD COLUMN document_type VARCHAR(50);
   CREATE INDEX idx_document_type ON fa_gpt_documents(document_type);
   ```

#### Adding New AI Models

1. **Model Configuration**
   ```python
   class Settings(BaseSettings):
       new_model: str = "custom-model:latest"
   ```

2. **Integration Logic**
   ```python
   def get_new_model_client():
       # Custom model initialization
       # Return model interface
   ```

#### Custom Embedding Methods

1. **Embedding Interface**
   ```python
   class CustomEmbedder:
       def embed_texts(self, texts: List[str]) -> List[List[float]]:
           # Custom text embedding logic
           
       def embed_images(self, images: List[bytes]) -> List[List[float]]:
           # Custom image embedding logic
   ```

---

This technical documentation provides the detailed implementation guidance needed for developers working with the FA-GPT system. For user-facing documentation, refer to the main README.md file.
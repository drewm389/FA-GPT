# FA-GPT API Documentation

## Overview

FA-GPT provides several programmatic interfaces for document processing and query handling. This documentation covers the main API functions and their usage patterns.

## Core APIs

### Document Processing API

#### `process_and_ingest_document(pdf_path: str) -> None`

**Module:** `app.simple_ingestion`

**Description:** Complete document ingestion pipeline using IBM Docling and local AI models.

**Parameters:**
- `pdf_path` (str): Absolute path to the PDF document to process

**Returns:** None

**Side Effects:**
- Creates organized files in `data/extracted/{publication}/`
- Stores vector embeddings in PostgreSQL `fa_gpt_documents` table
- Extracts knowledge graph to Neo4j database
- Prints progress information to console

**Example:**
```python
from app.simple_ingestion import process_and_ingest_document

pdf_path = "/path/to/document.pdf"
process_and_ingest_document(pdf_path)
```

**Error Handling:**
- Raises `Exception` if document parsing fails
- Prints warning messages for non-critical failures
- Continues processing even if some steps fail

#### `process_all_documents(directory: str, limit: int = None) -> None`

**Module:** `process_documents`

**Description:** Batch process all PDF documents in a directory tree.

**Parameters:**
- `directory` (str): Root directory to search for PDF files
- `limit` (int, optional): Maximum number of documents to process

**Returns:** None

**Example:**
```python
from process_documents import process_all_documents

# Process all documents
process_all_documents("/path/to/documents")

# Process only 5 smallest documents
process_all_documents("/path/to/documents", limit=5)
```

### Query Processing API

#### `get_rag_response(query: str) -> Tuple[str, List[str], Dict]`

**Module:** `app.rag_core`

**Description:** Process user query through complete RAG pipeline.

**Parameters:**
- `query` (str): User question about Field Artillery documents

**Returns:**
- `str`: Generated response with citations and analysis
- `List[str]`: Base64-encoded images that support the answer
- `Dict`: Metadata about retrieval and generation process

**Example:**
```python
from app.rag_core import get_rag_response

query = "What is the maximum range of the M777 howitzer?"
response, images, metadata = get_rag_response(query)

print(f"Response: {response}")
print(f"Supporting images: {len(images)}")
print(f"Retrieved documents: {metadata['retrieved_count']}")
```

**Metadata Structure:**
```python
{
    "query_intent": {
        "type": "factual",  # factual, procedural, visual, comparative
        "needs_kg": True,   # whether knowledge graph was used
        "needs_images": True,  # whether images were requested
        "key_entities": ["M777", "howitzer", "range"]
    },
    "retrieved_count": 15,  # number of documents retrieved
    "kg_nodes": 3          # number of knowledge graph nodes used
}
```

### Connection APIs

#### `get_ollama_client() -> ollama.Client`

**Module:** `app.connectors`

**Description:** Get cached Ollama client for AI model operations.

**Returns:** Configured Ollama client instance

**Features:**
- Automatic model downloading if not available
- Connection caching via Streamlit
- Model validation and status checking

**Example:**
```python
from app.connectors import get_ollama_client

client = get_ollama_client()
response = client.chat(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

#### `get_embedding_client() -> Callable`

**Module:** `app.connectors`

**Description:** Get function for generating embeddings.

**Returns:** Function that generates embeddings for text and images

**Usage:**
```python
from app.connectors import get_embedding_client

embedding_fn = get_embedding_client()
embeddings = embedding_fn(
    inputs=["sample text", "/path/to/image.png"],
    input_types=["text", "image"]
)
```

#### `get_db_connection() -> psycopg2.connection`

**Module:** `app.connectors`

**Description:** Get PostgreSQL database connection.

**Returns:** Database connection object

**Example:**
```python
from app.connectors import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM fa_gpt_documents")
count = cur.fetchone()[0]
conn.close()
```

#### `get_neo4j_driver() -> neo4j.Driver`

**Module:** `app.connectors`

**Description:** Get Neo4j database driver.

**Returns:** Neo4j driver instance

**Example:**
```python
from app.connectors import get_neo4j_driver

driver = get_neo4j_driver()
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as total")
    total_nodes = result.single()["total"]
driver.close()
```

### Configuration API

#### `Settings` Class

**Module:** `app.config`

**Description:** Configuration management using Pydantic settings.

**Key Properties:**
```python
from app.config import settings

# Database connections
postgres_uri = settings.postgres_uri
neo4j_uri = settings.neo4j_uri

# AI model configuration
vlm_model = settings.vlm_model          # "qwen2.5vl:7b"
llm_model = settings.llm_model          # "qwen2.5:7b"
embedding_model = settings.embedding_model  # "nomic-embed-text"

# Directory paths
data_dir = settings.data_dir            # Path("/app/data")
documents_dir = settings.documents_dir  # Path("/app/data/documents")

# Feature flags
enable_ocr = settings.enable_ocr        # True
enable_table_extraction = settings.enable_table_extraction  # True
```

## Advanced Usage Patterns

### Custom Document Processing

```python
from app.simple_ingestion import (
    granite_docling_parsing,
    embed_for_rag,
    store_in_pgvector_rag,
    extract_and_store_kg_qwen
)

def custom_process_document(pdf_path: str):
    # Step 1: Parse document
    doc_elements, image_elements = granite_docling_parsing(pdf_path)
    
    # Step 2: Custom processing
    filtered_elements = [
        elem for elem in doc_elements 
        if len(elem.get('content', '')) > 100
    ]
    
    # Step 3: Generate embeddings
    embeddings = embed_for_rag(filtered_elements, image_elements)
    
    # Step 4: Store results
    doc_name = os.path.basename(pdf_path)
    store_in_pgvector_rag(filtered_elements, image_elements, embeddings, doc_name)
    extract_and_store_kg_qwen(filtered_elements, doc_name)
```

### Custom RAG Pipeline

```python
from app.rag_core import (
    analyze_query_intent,
    retrieve_multimodal_content,
    rerank_with_local_vlm,
    get_kg_context,
    generate_vlm_response
)
from app.connectors import get_ollama_client

def custom_rag_query(query: str, use_reranking: bool = True):
    client = get_ollama_client()
    
    # Analyze query
    intent = analyze_query_intent(query, client)
    
    # Retrieve content
    retrieved = retrieve_multimodal_content(query, intent)
    
    # Optional reranking
    if use_reranking:
        reranked = rerank_with_local_vlm(query, retrieved, client)
    else:
        reranked = retrieved
    
    # Get knowledge graph context
    kg_context = get_kg_context(query) if intent.get('needs_kg') else []
    
    # Generate response
    response, sources = generate_vlm_response(
        query, reranked[:3], kg_context, client
    )
    
    return {
        "response": response,
        "sources": sources,
        "intent": intent,
        "kg_entities": len(kg_context)
    }
```

### Database Query Patterns

#### Vector Similarity Search

```python
import numpy as np
from app.connectors import get_db_connection, get_embedding_client

def similarity_search(query_text: str, limit: int = 10):
    # Generate query embedding
    embedding_fn = get_embedding_client()
    query_embedding = embedding_fn([query_text], ['text'])[0]
    
    # Search database
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, source_doc, content, element_type,
               1 - (embedding <=> %s) as similarity
        FROM fa_gpt_documents
        WHERE element_type IN ('text', 'table', 'title')
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (query_embedding.tolist(), query_embedding.tolist(), limit))
    
    results = cur.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "source_doc": row[1], 
            "content": row[2],
            "element_type": row[3],
            "similarity": row[4]
        }
        for row in results
    ]
```

#### Knowledge Graph Queries

```python
from app.connectors import get_neo4j_driver

def find_related_entities(entity_name: str):
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        result = session.run("""
            MATCH (n {id: $entity_name})-[r]-(connected)
            RETURN n, type(r) as relationship, connected
            ORDER BY relationship
        """, entity_name=entity_name)
        
        relationships = []
        for record in result:
            relationships.append({
                "source": dict(record["n"]),
                "relationship": record["relationship"],
                "target": dict(record["connected"])
            })
    
    driver.close()
    return relationships

def get_weapon_systems():
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        result = session.run("""
            MATCH (w:WeaponSystem)
            RETURN w.id as name, w.caliber as caliber, 
                   w.range as range, w.source_doc as source
            ORDER BY w.id
        """)
        
        weapons = [dict(record) for record in result]
    
    driver.close()
    return weapons
```

## Error Handling Patterns

### Graceful Degradation

```python
from app.rag_core import get_rag_response

def safe_rag_query(query: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response, images, metadata = get_rag_response(query)
            return {
                "success": True,
                "response": response,
                "images": images,
                "metadata": metadata
            }
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "error": str(e),
                    "response": "I'm sorry, I encountered an error processing your question. Please try again or rephrase your query."
                }
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Database Connection Handling

```python
from contextlib import contextmanager
from app.connectors import get_db_connection

@contextmanager
def database_transaction():
    conn = None
    try:
        conn = get_db_connection()
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Usage
with database_transaction() as conn:
    cur = conn.cursor()
    cur.execute("INSERT INTO fa_gpt_documents (...) VALUES (...)")
    # Transaction automatically committed or rolled back
```

## Performance Optimization

### Batch Processing

```python
def batch_embed_documents(doc_elements: List[Dict], batch_size: int = 10):
    """Process documents in batches to optimize memory usage."""
    from app.multimodal_embeddings import embed_for_rag
    
    all_embeddings = {}
    
    for i in range(0, len(doc_elements), batch_size):
        batch = doc_elements[i:i + batch_size]
        batch_embeddings = embed_for_rag(batch, [])
        all_embeddings.update(batch_embeddings)
        
        # Optional: Clear GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    return all_embeddings
```

### Connection Pooling

```python
from psycopg2 import pool
from threading import Lock

class DatabasePool:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._pool = pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=10,
                        dsn=settings.postgres_uri
                    )
        return cls._instance
    
    def get_connection(self):
        return self._pool.getconn()
    
    def put_connection(self, conn):
        self._pool.putconn(conn)

# Usage
db_pool = DatabasePool()
conn = db_pool.get_connection()
try:
    # Use connection
    pass
finally:
    db_pool.put_connection(conn)
```

## Integration Examples

### Flask API Wrapper

```python
from flask import Flask, request, jsonify
from app.rag_core import get_rag_response
from app.simple_ingestion import process_and_ingest_document

app = Flask(__name__)

@app.route('/api/query', methods=['POST'])
def query_documents():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        response, images, metadata = get_rag_response(query)
        return jsonify({
            "response": response,
            "image_count": len(images),
            "metadata": metadata
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest_document():
    data = request.get_json()
    pdf_path = data.get('pdf_path', '')
    
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Valid PDF path is required"}), 400
    
    try:
        process_and_ingest_document(pdf_path)
        return jsonify({"message": "Document ingested successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Jupyter Notebook Integration

```python
# Cell 1: Setup
import sys
sys.path.append('/path/to/FA-GPT')

from app.rag_core import get_rag_response
from app.simple_ingestion import process_and_ingest_document
import base64
from IPython.display import Image, display

# Cell 2: Process Document
pdf_path = "/path/to/manual.pdf"
process_and_ingest_document(pdf_path)

# Cell 3: Query and Display Results
query = "Show me the firing table for M795 projectiles"
response, images, metadata = get_rag_response(query)

print("Response:", response)
print("\\nMetadata:", metadata)

# Display images
for i, img_b64 in enumerate(images):
    print(f"\\nImage {i+1}:")
    img_data = base64.b64decode(img_b64)
    display(Image(data=img_data))
```

---

This API documentation provides comprehensive guidance for integrating with and extending the FA-GPT system programmatically.
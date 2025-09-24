"""
PostgreSQL Storage Module for FA-GPT
Unified storage interface for vector search and knowledge graphs
Replaces ChromaDB with PostgreSQL + pgvector + Apache AGE
"""

import json
import logging
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Document chunk with vector embedding"""
    id: Optional[int] = None
    document_id: str = ""
    chunk_index: int = 0
    content: str = ""
    content_type: str = "text"
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None

@dataclass
class ImageEmbedding:
    """Image with vector embedding"""
    id: Optional[int] = None
    document_id: str = ""
    image_path: str = ""
    image_description: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None

@dataclass
class Document:
    """Document metadata"""
    id: str = ""
    filename: str = ""
    file_path: str = ""
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    processing_status: str = "pending"
    extraction_method: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PostgreSQLStorage:
    """Unified PostgreSQL storage with vector search and knowledge graphs"""
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 database: str = "fagpt_db", username: str = "fagpt_user", 
                 password: str = "fagpt_secure_2024"):
        """Initialize PostgreSQL connection"""
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': username,
            'password': password
        }
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            self.connection.autocommit = True
            logger.info("Connected to PostgreSQL database")
            
            # Set search path for AGE
            with self.connection.cursor() as cursor:
                cursor.execute("SET search_path = ag_catalog, public")
                
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure active database connection"""
        if self.connection is None or self.connection.closed:
            self._connect()
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("PostgreSQL connection closed")
    
    # Document Management
    def add_document(self, document: Document) -> str:
        """Add or update document metadata"""
        self._ensure_connection()
        
        # Generate ID if not provided
        if not document.id:
            document.id = str(uuid.uuid4())
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO documents (id, filename, file_path, file_type, file_size, 
                                         page_count, processing_status, extraction_method, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        file_path = EXCLUDED.file_path,
                        file_type = EXCLUDED.file_type,
                        file_size = EXCLUDED.file_size,
                        page_count = EXCLUDED.page_count,
                        processing_status = EXCLUDED.processing_status,
                        extraction_method = EXCLUDED.extraction_method,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    document.id, document.filename, document.file_path,
                    document.file_type, document.file_size, document.page_count,
                    document.processing_status, document.extraction_method,
                    json.dumps(document.metadata or {})
                ))
            
            logger.info(f"Document {document.id} stored successfully")
            return document.id
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document by ID"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
                row = cursor.fetchone()
                
                if row:
                    return Document(
                        id=row['id'],
                        filename=row['filename'],
                        file_path=row['file_path'],
                        file_type=row['file_type'],
                        file_size=row['file_size'],
                        page_count=row['page_count'],
                        processing_status=row['processing_status'],
                        extraction_method=row['extraction_method'],
                        metadata=row['metadata'] or {},
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            raise
    
    def update_document_status(self, document_id: str, status: str):
        """Update document processing status"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE documents 
                    SET processing_status = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (status, document_id))
            
            logger.info(f"Document {document_id} status updated to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            raise
    
    # Vector Storage and Search
    def add_document_chunks(self, chunks: List[DocumentChunk]) -> List[int]:
        """Add document chunks with embeddings"""
        self._ensure_connection()
        chunk_ids = []
        
        try:
            with self.connection.cursor() as cursor:
                for chunk in chunks:
                    # Convert numpy array to list for PostgreSQL
                    embedding_list = chunk.embedding.tolist() if chunk.embedding is not None else None
                    
                    cursor.execute("""
                        INSERT INTO document_chunks (document_id, chunk_index, content, 
                                                   content_type, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        chunk.document_id, chunk.chunk_index, chunk.content,
                        chunk.content_type, embedding_list,
                        json.dumps(chunk.metadata or {})
                    ))
                    
                    chunk_id = cursor.fetchone()[0]
                    chunk_ids.append(chunk_id)
            
            logger.info(f"Added {len(chunk_ids)} document chunks")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Failed to add document chunks: {e}")
            raise
    
    def add_image_embeddings(self, images: List[ImageEmbedding]) -> List[int]:
        """Add image embeddings"""
        self._ensure_connection()
        image_ids = []
        
        try:
            with self.connection.cursor() as cursor:
                for image in images:
                    # Convert numpy array to list for PostgreSQL
                    embedding_list = image.embedding.tolist() if image.embedding is not None else None
                    
                    cursor.execute("""
                        INSERT INTO image_embeddings (document_id, image_path, image_description, 
                                                    embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        image.document_id, image.image_path, image.image_description,
                        embedding_list, json.dumps(image.metadata or {})
                    ))
                    
                    image_id = cursor.fetchone()[0]
                    image_ids.append(image_id)
            
            logger.info(f"Added {len(image_ids)} image embeddings")
            return image_ids
            
        except Exception as e:
            logger.error(f"Failed to add image embeddings: {e}")
            raise
    
    def semantic_search(self, query_embedding: np.ndarray, 
                       match_count: int = 10, 
                       similarity_threshold: float = 0.7,
                       content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on document chunks"""
        self._ensure_connection()
        
        try:
            embedding_list = query_embedding.tolist()
            
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                if content_type:
                    cursor.execute("""
                        SELECT dc.document_id, dc.id as chunk_id, dc.content, dc.content_type,
                               1 - (dc.embedding <=> %s::vector) as similarity, dc.metadata,
                               d.filename
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE dc.content_type = %s 
                        AND 1 - (dc.embedding <=> %s::vector) > %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """, (embedding_list, content_type, embedding_list, 
                         similarity_threshold, embedding_list, match_count))
                else:
                    cursor.execute("""
                        SELECT dc.document_id, dc.id as chunk_id, dc.content, dc.content_type,
                               1 - (dc.embedding <=> %s::vector) as similarity, dc.metadata,
                               d.filename
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE 1 - (dc.embedding <=> %s::vector) > %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """, (embedding_list, embedding_list, similarity_threshold, 
                         embedding_list, match_count))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'document_id': row['document_id'],
                        'chunk_id': row['chunk_id'],
                        'content': row['content'],
                        'content_type': row['content_type'],
                        'similarity': float(row['similarity']),
                        'metadata': row['metadata'],
                        'filename': row['filename']
                    })
                
                logger.info(f"Found {len(results)} similar chunks")
                return results
                
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    def multimodal_search(self, query_embedding: np.ndarray, 
                         match_count: int = 10, 
                         similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform multimodal search across text and images"""
        self._ensure_connection()
        
        try:
            embedding_list = query_embedding.tolist()
            
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM search_multimodal(%s::vector, %s, %s)
                """, (embedding_list, match_count, similarity_threshold))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'document_id': row['document_id'],
                        'content_type': row['content_type'],
                        'content_id': row['id'],
                        'content': row['content'],
                        'similarity': float(row['similarity_score']),
                        'metadata': row['metadata'],
                        'image_path': row['image_path'],
                        'image_description': row['image_description']
                    })
                
                logger.info(f"Found {len(results)} multimodal results")
                return results
                
        except Exception as e:
            logger.error(f"Multimodal search failed: {e}")
            raise
    
    # Knowledge Graph Operations
    def create_knowledge_relationship(self, subject: str, predicate: str, object_: str, 
                                    properties: Optional[Dict[str, Any]] = None) -> bool:
        """Create knowledge graph relationship using Apache AGE wrapper functions"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                # Use the wrapper function that has SECURITY DEFINER
                cursor.execute("""
                    SELECT create_cypher_relationship(%s, %s, %s, %s, %s)
                """, (
                    'fagpt_knowledge',
                    subject,
                    predicate,
                    object_,
                    json.dumps(properties or {})
                ))
                
                result = cursor.fetchone()
                success = result[0] if result else False
                
                if success:
                    logger.info(f"Created knowledge relationship: {subject} -[{predicate}]-> {object_}")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to create knowledge relationship: {e}")
            return False
    
    def query_knowledge_graph(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query on knowledge graph using wrapper function"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                # Use the wrapper function
                cursor.execute("""
                    SELECT query_cypher_graph(%s, %s)
                """, ('fagpt_knowledge', cypher_query))
                
                results = []
                result_row = cursor.fetchone()
                if result_row and result_row[0]:
                    for result_data in result_row[0]:  # result_row[0] is the text array
                        results.append({'result': result_data})
                
                logger.info(f"Knowledge graph query returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            return []
    
    # Utility Methods
    def get_document_summary(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get summary of all documents"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM document_summary 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get document summary: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document and all associated data"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                # Delete in reverse dependency order
                cursor.execute("DELETE FROM image_embeddings WHERE document_id = %s", (document_id,))
                cursor.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
                cursor.execute("DELETE FROM documents WHERE id = %s", (document_id,))
                
                logger.info(f"Deleted document {document_id} and all associated data")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        self._ensure_connection()
        
        try:
            with self.connection.cursor() as cursor:
                stats = {}
                
                # Document counts
                cursor.execute("SELECT COUNT(*) FROM documents")
                stats['document_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM document_chunks")
                stats['chunk_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM image_embeddings")
                stats['image_count'] = cursor.fetchone()[0]
                
                # Processing status breakdown
                cursor.execute("""
                    SELECT processing_status, COUNT(*) 
                    FROM documents 
                    GROUP BY processing_status
                """)
                stats['status_breakdown'] = dict(cursor.fetchall())
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise

# Convenience functions for backward compatibility
def create_storage_client(host: str = "localhost", port: int = 5432, 
                         database: str = "fagpt_db", username: str = "fagpt_user", 
                         password: str = "fagpt_secure_2024") -> PostgreSQLStorage:
    """Create PostgreSQL storage client"""
    return PostgreSQLStorage(host, port, database, username, password)

def test_connection() -> bool:
    """Test PostgreSQL connection"""
    try:
        client = create_storage_client()
        stats = client.get_stats()
        client.close()
        logger.info(f"Connection test successful. Database stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    print("Testing PostgreSQL connection...")
    if test_connection():
        print("✓ PostgreSQL storage module working correctly!")
    else:
        print("✗ PostgreSQL connection failed")
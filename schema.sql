-- FA-GPT PostgreSQL Schema with pgvector and Apache AGE
-- Initialize extensions and schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, '$user', public;

-- Create age graph for knowledge relationships
SELECT create_graph('fagpt_knowledge');

-- Document chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Image embeddings table for multimodal search
CREATE TABLE IF NOT EXISTS image_embeddings (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    image_description TEXT,
    embedding vector(1536), -- Multimodal embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document metadata table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    page_count INTEGER,
    processing_status VARCHAR(50) DEFAULT 'pending',
    extraction_method VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Create indexes for efficient vector similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_image_embeddings_embedding 
ON image_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Traditional indexes for metadata queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_type ON document_chunks(content_type);
CREATE INDEX IF NOT EXISTS idx_image_embeddings_document_id ON image_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);

-- GIN indexes for JSONB metadata search
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_image_embeddings_metadata ON image_embeddings USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

-- Create views for common queries
CREATE OR REPLACE VIEW document_summary AS
SELECT 
    d.id,
    d.filename,
    d.file_type,
    d.processing_status,
    COUNT(DISTINCT dc.id) as chunk_count,
    COUNT(DISTINCT ie.id) as image_count,
    d.created_at,
    d.updated_at
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN image_embeddings ie ON d.id = ie.document_id
GROUP BY d.id, d.filename, d.file_type, d.processing_status, d.created_at, d.updated_at;

-- Function for semantic search across document chunks
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE (
    document_id VARCHAR(255),
    chunk_id INTEGER,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) 
LANGUAGE sql
AS $$
    SELECT 
        dc.document_id,
        dc.id as chunk_id,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity,
        dc.metadata
    FROM document_chunks dc
    WHERE 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Function for multimodal search (text + images)
CREATE OR REPLACE FUNCTION search_multimodal(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE (
    document_id VARCHAR(255),
    content_type VARCHAR(50),
    content_id INTEGER,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) 
LANGUAGE sql
AS $$
    (
        SELECT 
            dc.document_id,
            'text' as content_type,
            dc.id as content_id,
            dc.content,
            1 - (dc.embedding <=> query_embedding) as similarity,
            dc.metadata
        FROM document_chunks dc
        WHERE 1 - (dc.embedding <=> query_embedding) > similarity_threshold
    )
    UNION ALL
    (
        SELECT 
            ie.document_id,
            'image' as content_type,
            ie.id as content_id,
            COALESCE(ie.image_description, ie.image_path) as content,
            1 - (ie.embedding <=> query_embedding) as similarity,
            ie.metadata
        FROM image_embeddings ie
        WHERE 1 - (ie.embedding <=> query_embedding) > similarity_threshold
    )
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- Grant permissions to fagpt_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO fagpt_user;
GRANT USAGE ON SCHEMA ag_catalog TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ag_catalog TO fagpt_user;

-- Initialize search_path for age graph operations
ALTER DATABASE fagpt_db SET search_path = ag_catalog, public;
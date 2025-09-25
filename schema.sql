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

-- Artillery-specific tables for fire support operations
-- =====================================================

-- Weapon systems and capabilities
CREATE TABLE IF NOT EXISTS weapon_systems (
    id SERIAL PRIMARY KEY,
    designation VARCHAR(100) NOT NULL UNIQUE, -- e.g., "M777A2", "M109A6"
    system_type VARCHAR(50) NOT NULL, -- "towed", "self-propelled", "mortar"
    caliber_mm INTEGER NOT NULL,
    min_range_meters INTEGER DEFAULT 0,
    max_range_meters INTEGER NOT NULL,
    crew_size INTEGER,
    ammunition_types JSONB DEFAULT '[]', -- Supported ammunition types
    firing_rates JSONB DEFAULT '{}', -- Max/sustained rates of fire
    deployment_time_minutes INTEGER, -- Time to emplace/displace
    mobility VARCHAR(50), -- "towed", "tracked", "wheeled"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Ammunition types and characteristics
CREATE TABLE IF NOT EXISTS ammunition_types (
    id SERIAL PRIMARY KEY,
    designation VARCHAR(100) NOT NULL UNIQUE, -- e.g., "M107 HE", "M825 Smoke"
    ammunition_type VARCHAR(50) NOT NULL, -- "HE", "SMOKE", "ILLUM", etc.
    caliber_mm INTEGER NOT NULL,
    weight_kg DECIMAL(6,2),
    max_range_meters INTEGER,
    lethal_radius_meters INTEGER,
    suppression_radius_meters INTEGER,
    fuze_types JSONB DEFAULT '[]', -- Available fuze options
    storage_temperature_range JSONB DEFAULT '{}',
    shelf_life_months INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Firing tables and ballistic data
CREATE TABLE IF NOT EXISTS firing_tables (
    id SERIAL PRIMARY KEY,
    weapon_system_id INTEGER REFERENCES weapon_systems(id),
    ammunition_type_id INTEGER REFERENCES ammunition_types(id),
    charge VARCHAR(10) NOT NULL, -- "1", "2", "GB", "WB", etc.
    range_meters INTEGER NOT NULL,
    elevation_mils INTEGER NOT NULL,
    azimuth_mils INTEGER NOT NULL,
    time_of_flight_seconds DECIMAL(5,2),
    muzzle_velocity_mps INTEGER,
    drift_mils INTEGER DEFAULT 0,
    meteorological_corrections JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(weapon_system_id, ammunition_type_id, charge, range_meters)
);

-- Military units and organizational structure
CREATE TABLE IF NOT EXISTS military_units (
    id SERIAL PRIMARY KEY,
    unit_designation VARCHAR(100) NOT NULL, -- "A/1-77 FA", "1st BCT"
    unit_type VARCHAR(50) NOT NULL, -- "battery", "battalion", "brigade"
    parent_unit_id INTEGER REFERENCES military_units(id),
    call_sign VARCHAR(50),
    grid_coordinates VARCHAR(20), -- MGRS coordinates
    elevation_meters INTEGER,
    unit_status VARCHAR(50) DEFAULT 'operational', -- operational, maintenance, displaced
    weapon_systems JSONB DEFAULT '[]', -- Array of weapon system assignments
    personnel_count INTEGER,
    ammunition_status JSONB DEFAULT '{}', -- Current ammunition holdings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Fire missions and orders tracking
CREATE TABLE IF NOT EXISTS fire_missions (
    id SERIAL PRIMARY KEY,
    mission_id VARCHAR(50) NOT NULL UNIQUE,
    target_designation VARCHAR(100) NOT NULL,
    target_grid VARCHAR(20) NOT NULL,
    target_elevation_meters INTEGER,
    target_description TEXT,
    firing_unit_id INTEGER REFERENCES military_units(id),
    mission_type VARCHAR(50) NOT NULL, -- "DESTROY", "SUPPRESS", "NEUTRALIZE"
    priority VARCHAR(20) NOT NULL, -- "IMMEDIATE", "PRIORITY", "ROUTINE"
    observer VARCHAR(50),
    ammunition_type VARCHAR(100),
    charge VARCHAR(10),
    rounds_fired INTEGER DEFAULT 0,
    rounds_requested INTEGER,
    azimuth_mils INTEGER,
    elevation_mils INTEGER,
    range_meters INTEGER,
    time_of_flight_seconds DECIMAL(5,2),
    method_of_fire VARCHAR(50), -- "AT MY COMMAND", "WHEN READY"
    mission_status VARCHAR(50) DEFAULT 'planned', -- planned, executing, complete, cancelled
    fire_order_text TEXT, -- Complete formatted fire order
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Tactical entities extracted from documents
CREATE TABLE IF NOT EXISTS tactical_entities (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) REFERENCES documents(id),
    entity_type VARCHAR(100) NOT NULL, -- "target", "unit", "procedure", "equipment"
    entity_subtype VARCHAR(100), -- "howitzer", "fire_mission", "gunnery_procedure"
    designation VARCHAR(200), -- Official designation or name
    description TEXT,
    grid_coordinates VARCHAR(20), -- If applicable
    elevation_meters INTEGER, -- If applicable
    parent_entity_id INTEGER REFERENCES tactical_entities(id),
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- AI extraction confidence
    extraction_method VARCHAR(100), -- "granite_docling", "qwen_vision", "manual"
    page_number INTEGER,
    bounding_box JSONB, -- Image coordinates if extracted from image
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Fire support coordination measures
CREATE TABLE IF NOT EXISTS coordination_measures (
    id SERIAL PRIMARY KEY,
    measure_type VARCHAR(100) NOT NULL, -- "no_fire_area", "restricted_fire_area", "fscl"
    designation VARCHAR(100) NOT NULL,
    coordinates JSONB NOT NULL, -- Polygon or line coordinates
    elevation_floor_meters INTEGER,
    elevation_ceiling_meters INTEGER,
    effective_time TIMESTAMP,
    expiry_time TIMESTAMP,
    controlling_unit VARCHAR(100),
    restrictions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Artillery-specific indexes
CREATE INDEX IF NOT EXISTS idx_weapon_systems_designation ON weapon_systems(designation);
CREATE INDEX IF NOT EXISTS idx_ammunition_types_designation ON ammunition_types(designation);
CREATE INDEX IF NOT EXISTS idx_firing_tables_weapon_ammo ON firing_tables(weapon_system_id, ammunition_type_id);
CREATE INDEX IF NOT EXISTS idx_military_units_designation ON military_units(unit_designation);
CREATE INDEX IF NOT EXISTS idx_fire_missions_mission_id ON fire_missions(mission_id);
CREATE INDEX IF NOT EXISTS idx_fire_missions_status ON fire_missions(mission_status);
CREATE INDEX IF NOT EXISTS idx_tactical_entities_type ON tactical_entities(entity_type, entity_subtype);
CREATE INDEX IF NOT EXISTS idx_tactical_entities_document ON tactical_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_coordination_measures_type ON coordination_measures(measure_type);

-- GIN indexes for artillery JSONB fields
CREATE INDEX IF NOT EXISTS idx_weapon_systems_metadata ON weapon_systems USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_military_units_metadata ON military_units USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_fire_missions_metadata ON fire_missions USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_tactical_entities_metadata ON tactical_entities USING GIN(metadata);

-- Artillery-specific search functions
CREATE OR REPLACE FUNCTION search_firing_solutions(
    target_range_min INTEGER DEFAULT 0,
    target_range_max INTEGER DEFAULT 50000,
    weapon_system_filter VARCHAR DEFAULT NULL,
    ammunition_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    weapon_designation VARCHAR,
    ammunition_designation VARCHAR,
    charge VARCHAR,
    max_range_meters INTEGER,
    elevation_mils INTEGER,
    time_of_flight_seconds DECIMAL
) 
LANGUAGE sql
AS $$
    SELECT 
        ws.designation as weapon_designation,
        at.designation as ammunition_designation,
        ft.charge,
        MAX(ft.range_meters) as max_range_meters,
        ft.elevation_mils,
        ft.time_of_flight_seconds
    FROM firing_tables ft
    JOIN weapon_systems ws ON ft.weapon_system_id = ws.id
    JOIN ammunition_types at ON ft.ammunition_type_id = at.id
    WHERE ft.range_meters BETWEEN target_range_min AND target_range_max
    AND (weapon_system_filter IS NULL OR ws.designation ILIKE '%' || weapon_system_filter || '%')
    AND (ammunition_filter IS NULL OR at.ammunition_type = ammunition_filter)
    GROUP BY ws.designation, at.designation, ft.charge, ft.elevation_mils, ft.time_of_flight_seconds
    ORDER BY max_range_meters;
$$;

-- Function to find tactical entities by type and location
CREATE OR REPLACE FUNCTION search_tactical_entities(
    entity_type_filter VARCHAR DEFAULT NULL,
    grid_area VARCHAR DEFAULT NULL,
    confidence_threshold DECIMAL DEFAULT 0.5
)
RETURNS TABLE (
    entity_id INTEGER,
    entity_type VARCHAR,
    designation VARCHAR,
    description TEXT,
    grid_coordinates VARCHAR,
    document_filename VARCHAR,
    confidence_score DECIMAL
) 
LANGUAGE sql
AS $$
    SELECT 
        te.id as entity_id,
        te.entity_type,
        te.designation,
        te.description,
        te.grid_coordinates,
        d.filename as document_filename,
        te.confidence_score
    FROM tactical_entities te
    JOIN documents d ON te.document_id = d.id
    WHERE (entity_type_filter IS NULL OR te.entity_type = entity_type_filter)
    AND (grid_area IS NULL OR te.grid_coordinates LIKE grid_area || '%')
    AND te.confidence_score >= confidence_threshold
    ORDER BY te.confidence_score DESC, te.created_at DESC;
$$;

-- Insert standard weapon systems data
INSERT INTO weapon_systems (designation, system_type, caliber_mm, min_range_meters, max_range_meters, crew_size, ammunition_types, firing_rates, deployment_time_minutes, mobility, metadata) VALUES
('M777A2', 'towed', 155, 200, 30000, 8, '["HE", "SMOKE", "ILLUM", "WP", "DPICM", "EXCALIBUR"]', '{"max_rpm": 4, "sustained_rpm": 2}', 15, 'towed', '{"country": "USA", "manufacturer": "BAE Systems"}'),
('M109A6', 'self-propelled', 155, 200, 30000, 6, '["HE", "SMOKE", "ILLUM", "WP", "DPICM", "EXCALIBUR"]', '{"max_rpm": 4, "sustained_rpm": 1}', 5, 'tracked', '{"country": "USA", "manufacturer": "BAE Systems"}'),
('M119A3', 'towed', 105, 200, 11500, 6, '["HE", "SMOKE", "ILLUM", "WP"]', '{"max_rpm": 8, "sustained_rpm": 3}', 10, 'towed', '{"country": "USA", "manufacturer": "General Dynamics"}'),
('M252', 'mortar', 81, 70, 5650, 3, '["HE", "SMOKE", "ILLUM", "WP"]', '{"max_rpm": 30, "sustained_rpm": 15}', 2, 'portable', '{"country": "USA", "manufacturer": "General Dynamics"}'
)
ON CONFLICT (designation) DO NOTHING;

-- Insert standard ammunition types
INSERT INTO ammunition_types (designation, ammunition_type, caliber_mm, weight_kg, max_range_meters, lethal_radius_meters, suppression_radius_meters, fuze_types, metadata) VALUES
('M107 HE', 'HE', 155, 43.2, 30000, 50, 300, '["PD", "VT", "DELAY"]', '{"country": "USA", "explosive_weight_kg": 6.6}'),
('M825 Smoke', 'SMOKE', 155, 46.7, 22500, 0, 200, '["TIME", "PD"]', '{"country": "USA", "screening_time_minutes": 15}'),
('M982 Excalibur', 'EXCALIBUR', 155, 48.0, 40000, 75, 200, '["PD", "DELAY"]', '{"country": "USA", "guidance": "GPS", "cep_meters": 4}'),
('M1 HE', 'HE', 105, 15.0, 11500, 30, 200, '["PD", "VT", "DELAY"]', '{"country": "USA", "explosive_weight_kg": 2.18}'),
('M60 HE', 'HE', 81, 4.2, 5650, 15, 100, '["PD", "VT"]', '{"country": "USA", "explosive_weight_kg": 0.68}'
)
ON CONFLICT (designation) DO NOTHING;

-- Grant permissions to fagpt_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO fagpt_user;
GRANT USAGE ON SCHEMA ag_catalog TO fagpt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ag_catalog TO fagpt_user;

-- Initialize search_path for age graph operations
ALTER DATABASE fagpt_db SET search_path = ag_catalog, public;
# app/simple_ingestion.py
"""
Document Ingestion Pipeline for FA-GPT

This module handles the complete document processing pipeline using the primary
and most advanced extraction method: `enhanced_granite_multimodal_parsing`.

This pipeline does NOT have a fallback mechanism. If the primary extraction
method fails, the ingestion process will stop and raise an error. This ensure    except Exception as e:
        logger.log_exception(e, "Single document ingestion failed")
        sys.exit(2)hat only the highest quality data is ingested.
"""

import os
import uuid
import json
import time
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Dict
import base64
import shutil

from .config import settings
from .connectors import get_ollama_client, get_db_connection
from .multimodal_embeddings import embed_for_rag
from .logging_config import get_logger

# --- Primary and ONLY Parser Import ---
# If this import fails, the entire system will stop, as requested.
from .enhanced_granite_docling import enhanced_granite_multimodal_parsing

logger = get_logger("simple-ingestion")
logger.info("🔒 Ingestion pipeline is locked to: Enhanced Granite Docling Parser")

def quarantine_document(pdf_path: str, reason: str):
    """Moves a failed document to the quarantine directory."""
    try:
        quarantine_dir = settings.data_dir / "quarantine"
        quarantine_dir.mkdir(exist_ok=True)
        shutil.move(pdf_path, quarantine_dir / Path(pdf_path).name)
        logger.warning(f"Moved document {pdf_path} to quarantine. Reason: {reason}")
    except Exception as e:
        logger.error(f"Failed to move {pdf_path} to quarantine: {e}")

def process_and_ingest_document(pdf_path: str):
    """
    Complete document ingestion pipeline using the enhanced Granite-Docling extractor.
    This process will fail if the primary extractor is not operational.
    """
    start_time = time.time()
    logger.info(f"🚀 Starting HIGH-QUALITY ingestion for: {pdf_path}")
    
    try:
        # Log environment for diagnostics
        logger.log_environment_info()
        
        # 1. Parse with the enhanced multimodal pipeline. No fallback.
        # This will raise an exception if it fails, stopping the process.
        doc_elements, image_elements = enhanced_granite_multimodal_parsing(pdf_path)
        
        if not doc_elements and not image_elements:
            logger.warning(f"⚠️  No content was extracted from {pdf_path}. Check the document and logs.")
            return
        
        logger.info(f"✅ Extracted {len(doc_elements)} text elements and {len(image_elements)} image elements.")

        # 2. Generate multimodal embeddings for unified search
        logger.info("🧠 Generating multimodal embeddings...")
        embeddings = embed_for_rag(doc_elements, image_elements)
        logger.info("✅ Multimodal embedding generation complete.")
        
        # 3. Store in PostgreSQL with pgvector for RAG
        logger.info("💾 Storing content and embeddings in PostgreSQL...")
        store_in_pgvector_rag(doc_elements, image_elements, embeddings, os.path.basename(pdf_path))
        logger.info("✅ Stored in pgvector for RAG.")
        
        # 4. Extract knowledge graph using the consolidated Qwen 2.5 VL model
        logger.info("🕸️  Extracting knowledge graph with Qwen 2.5 VL...")
        extract_and_store_kg_qwen(doc_elements, os.path.basename(pdf_path))
        logger.info("✅ Knowledge graph extraction complete.")
        
        duration = time.time() - start_time
        logger.log_performance(f"Complete ingestion for {os.path.basename(pdf_path)}", duration)
        logger.info(f"🎉 Successfully ingested {pdf_path} using the primary pipeline")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.log_exception(e, f"Ingestion failed for {pdf_path} after {duration:.2f}s")
        quarantine_document(pdf_path, str(e))
        raise


def store_in_pgvector_rag(doc_elements: List[Dict], image_elements: List[Dict], embeddings: Dict, doc_source: str):
    """
    Store Docling-parsed content with embeddings in PostgreSQL for multimodal RAG.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS fa_gpt_documents (
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
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_element_type ON fa_gpt_documents(element_type);
        CREATE INDEX IF NOT EXISTS idx_source_doc ON fa_gpt_documents(source_doc);
        CREATE INDEX IF NOT EXISTS idx_page ON fa_gpt_documents(page);
        CREATE INDEX IF NOT EXISTS idx_embedding_cosine ON fa_gpt_documents 
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    """)
    conn.commit()
    
    # Store text elements
    for element in doc_elements:
        element_id = element.get('id', str(uuid.uuid4()))
        if element_id in embeddings:
            cur.execute("""
                INSERT INTO fa_gpt_documents 
                (id, source_doc, element_type, content, page, bbox, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                element_id,
                doc_source,
                element.get('type', 'text'),
                element.get('content', ''),
                element.get('page', 0),
                json.dumps(element.get('bbox', {})),
                json.dumps(element.get('metadata', {})),
                embeddings[element_id]
            ))
    
    # Store image elements
    for img_element in image_elements:
        img_id = img_element.get('id', str(uuid.uuid4()))
        if img_id in embeddings:
            image_data = img_element.get('image_data')
            if isinstance(image_data, str):
                try:
                    image_data = base64.b64decode(image_data)
                except:
                    image_data = None
            
            cur.execute("""
                INSERT INTO fa_gpt_documents 
                (id, source_doc, element_type, page, bbox, image_data, vml_analysis, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                img_id,
                doc_source,
                'image',
                img_element.get('page', 0),
                json.dumps(img_element.get('bbox', {})),
                image_data,
                json.dumps(img_element.get('vml_analysis', {})),
                json.dumps(img_element.get('metadata', {})),
                embeddings[img_id]
            ))
    
    conn.commit()
    cur.close()
    conn.close()

def extract_and_store_kg_qwen(doc_elements: List[Dict], doc_source: str):
    """
    Extract knowledge graph using Qwen 2.5 LLM and store in PostgreSQL with Apache AGE.
    """
    client = get_ollama_client()
    conn = None
    
    # --- Start of New Enhanced Prompt ---
    kg_prompt = """You are an expert military analyst creating a unified knowledge graph from U.S. Army doctrine, including Field Manuals (FM), Army Techniques Publications (ATP), and Tabular Firing Tables (TFTs). Your task is to extract and structure information related to both tactical gunnery and the operational planning process.

Focus on these entity types:
- MDMP_Step: A step in the Military Decision Making Process (e.g., "Mission Analysis," "COA Development").
- Planning_Product: An artifact of the planning process (e.g., "Course of Action," "Commander's Critical Information Requirements," "Decision Support Matrix").
- Staff_Section: A staff element within a headquarters (e.g., "S3," "G2," "Fire Support Cell").
- Command_Post_Function: A key activity or cell within a command post (e.g., "Current Operations," "Plans Cell," "Battle Rhythm").
- GunneryTask: A specific action or step in a gunnery procedure (e.g., "Lay for Direction," "Apply Deflection").
- SafetyProcedure: A critical safety check or warning (e.g., "Verify Boresight," "Check for Misfire").
- BallisticData: A complete row from a firing table, representing a firing solution.
- BallisticVariable: A factor that affects the projectile's trajectory (e.g., "Muzzle Velocity," "Air Density," "Projectile Weight").
- WeaponSystem: A cannon or howitzer (e.g., "M777A1," "M109A6").
- Ammunition: A type of projectile or charge (e.g., "M795 HE," "MACS Charge 3").
- Publication: A referenced manual or document (e.g., "TC 3-09.81," "FM 5-0").

Relationship types:
- PRECEDES, PART_OF: To show procedural and hierarchical flow in MDMP and Gunnery.
- PRODUCES: Linking an MDMP_Step to a Planning_Product.
- RESPONSIBLE_FOR: Linking a Staff_Section to a Planning_Product or Command_Post_Function.
- INFORMS: Linking a Planning_Product to an MDMP_Step or a decision.
- REQUIRES_SAFETY_CHECK: Linking a GunneryTask to a mandatory SafetyProcedure.
- HAS_BALLISTIC_DATA: Linking a WeaponSystem/Ammunition combination to its BallisticData.
- AFFECTS_TRAJECTORY: Linking a BallisticVariable to BallisticData.
- REFERENCES_PUBLICATION: Linking a procedure or concept to another manual.

Content to analyze: {content}

Return valid JSON only. For TFT data, create one `BallisticData` entity per row with all columns as properties. For MDMP steps, detail their inputs and outputs.
{{"entities": [{{"id": "Mission_Analysis", "type": "MDMP_Step", "properties": {{"description": "An iterative planning methodology to understand the situation and mission."}}}}, {{"id": "COA_Sketch", "type": "Planning_Product", "properties": {{"purpose": "A visual representation of a potential solution."}}}}, {{"id": "Determine_Firing_Data", "type": "GunneryTask", "properties": {{"description": "The process of calculating all data required to fire the weapon."}}}}, {{"id": "Misfire_Procedures", "type": "SafetyProcedure", "properties": {{"priority": "High"}}}}],
"relationships": [{{"source": "Mission_Analysis", "target": "COA_Sketch", "type": "PRODUCES"}}, {{"source": "Determine_Firing_Data", "target": "Misfire_Procedures", "type": "REQUIRES_SAFETY_CHECK"}}]}}
"""
    # --- End of New Enhanced Prompt ---
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Setup Apache AGE if not already done
        cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
        cur.execute("LOAD 'age';")
        cur.execute("SET search_path = ag_catalog, '$user', public;")
        
        graph_name = 'fagpt_graph'
        try:
            cur.execute(f"SELECT create_graph('{graph_name}');")
        except Exception:
            pass  # Graph already exists
        conn.commit()

        for element in doc_elements:
            content = element.get('content', '')
            if element.get('type') in ['text', 'table'] and len(content) > 100:
                try:
                    response = client.chat(
                        model=settings.llm_model,
                        messages=[{'role': 'user', 'content': kg_prompt.format(content=content[:2000])}],
                        format='json',
                        options={'temperature': 0.1}
                    )
                    kg_data = json.loads(response.get('message', {}).get('content', ''))

                    # Store entities (vertices)
                    for entity in kg_data.get('entities', []):
                        props = entity.get('properties', {})
                        props['source_doc'] = doc_source
                        props['page'] = element.get('page', 0)
                        
                        cypher_query = f"""
                        SELECT * FROM cypher('{graph_name}', $$
                            MERGE (v:{entity['type']} {{id: $id}})
                            SET v += $properties
                        $$, %s) AS (v agtype);
                        """
                        cur.execute(cypher_query, (json.dumps({'id': entity['id'], 'properties': props}),))

                    # Store relationships (edges)
                    for rel in kg_data.get('relationships', []):
                        cypher_query = f"""
                        SELECT * FROM cypher('{graph_name}', $$
                            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                            MERGE (a)-[r:{rel['type']}]->(b)
                            SET r.source_doc = $doc, r.page = $page
                        $$, %s) AS (r agtype);
                        """
                        cur.execute(cypher_query, (json.dumps({
                            'source_id': rel['source'], 
                            'target_id': rel['target'],
                            'doc': doc_source,
                            'page': element.get('page', 0)
                        }),))
                    
                    conn.commit()
                except Exception as e:
                    logger.error(f"KG element extraction failed: {str(e)}")
                    conn.rollback()
                    continue
    except Exception as e:
        logger.error(f"Database connection for KG failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    def parse_arguments():
        """Professional CLI interface for FA-GPT ingestion."""
        parser = argparse.ArgumentParser(
            description="FA-GPT Document Processing Pipeline",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --file /path/to/document.pdf
  %(prog)s --input-dir data/documents --test-single file.pdf
  %(prog)s --input-dir data/documents --limit 5 --verbose
  %(prog)s --input-dir data/documents --clear-db
            """
        )
        
        parser.add_argument("--input-dir", type=str, default="data/documents",
                            help="Root directory containing documents (default: data/documents)")
        parser.add_argument("--test-single", type=str, default=None,
                            help="Single filename within --input-dir to process (e.g., file.pdf)")
        parser.add_argument("--file", type=str, default=None,
                            help="Absolute path to a single PDF to process")
        parser.add_argument("--limit", type=int, default=None,
                            help="Limit the number of documents to process")
        parser.add_argument("--clear-db", action="store_true",
                            help="Clear existing database entries before processing")
        parser.add_argument("--verbose", action="store_true",
                            help="Enable verbose logging (DEBUG level)")
        
        return parser.parse_args()

    def clear_database():
        """Clear existing database entries."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            logger.info("🗑️  Clearing existing database entries...")
            
            # Clear pgvector tables
            cur.execute("DROP TABLE IF EXISTS fa_gpt_documents CASCADE;")
            
            # Clear AGE graph data (if exists)
            try:
                cur.execute("SELECT drop_graph('fa_gpt_kg', true);")
            except:
                pass  # Graph might not exist
                
            conn.commit()
            logger.info("✅ Database cleared successfully")
            
        except Exception as e:
            logger.log_exception(e, "Database clearing failed")
            raise
        finally:
            if conn:
                conn.close()

    # Parse arguments and configure logging
    args = parse_arguments()
    
    # Configure logger with verbosity
    if args.verbose:
        logger = get_logger("simple-ingestion", verbose=True)
        logger.info("🔍 Verbose logging enabled")
    
    logger.info("🎯 FA-GPT Document Processing Pipeline Starting...")
    logger.log_environment_info()

    try:
        # Clear database if requested
        if args.clear_db:
            clear_database()
        
        if args.file:
            pdf_path = args.file
        elif args.test_single:
            pdf_path = str(Path(args.input_dir) / args.test_single)
        else:
            print("No --file or --test-single provided; nothing to do.")
            sys.exit(0)

        if not Path(pdf_path).exists():
            print(f"❌ PDF not found: {pdf_path}")
            sys.exit(1)

        logger.info(f"Running ingestion for single document: {pdf_path}")
        process_and_ingest_document(pdf_path)
        logger.info("Single document ingestion completed successfully")
    except Exception as e:
        logger.log_exception(e, "Single document ingestion failed")
        sys.exit(2)
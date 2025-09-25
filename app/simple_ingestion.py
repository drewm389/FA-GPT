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
import traceback
from pathlib import Path
from typing import List, Tuple, Dict
import base64
import shutil

from .config import settings
from .connectors import get_ollama_client, get_db_connection
from .multimodal_embeddings import embed_for_rag
from .logging_config import get_logger
# NEW: Import the enhanced prompt
from .prompts import KG_EXTRACTION_PROMPT_ENHANCED

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
                    # MODIFIED: Use the imported KG_EXTRACTION_PROMPT_ENHANCED
                    prompt = KG_EXTRACTION_PROMPT_ENHANCED + "\n\n" + content[:2000]
                    
                    response = client.chat(
                        model=settings.llm_model,
                        messages=[{'role': 'user', 'content': prompt}],
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
  %(prog)s --batch-all --clear-db --verbose
  %(prog)s --batch-all
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
        parser.add_argument("--batch-all", action="store_true",
                            help="Process all PDF files in data directory")
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
        
        if args.batch_all:
            # Find all PDF files in data directory
            data_path = Path("data")
            pdf_files = []
            for pdf_file in data_path.rglob("*.pdf"):
                if "quarantine" not in str(pdf_file):
                    pdf_files.append(str(pdf_file))
            
            pdf_files = sorted(pdf_files)
            
            if not pdf_files:
                logger.error("❌ No PDF files found in data directory")
                sys.exit(1)
            
            logger.info(f"🚀 Found {len(pdf_files)} PDF files to process")
            processed = 0
            failed = 0
            
            start_time = time.time()
            
            for i, pdf_path in enumerate(pdf_files, 1):
                try:
                    doc_name = Path(pdf_path).name
                    logger.info(f"\n{'='*80}")
                    logger.info(f"📄 Processing document {i}/{len(pdf_files)}: {doc_name}")
                    logger.info(f"📁 Path: {pdf_path}")
                    logger.info(f"{'='*80}")
                    
                    doc_start_time = time.time()
                    process_and_ingest_document(pdf_path)
                    doc_duration = time.time() - doc_start_time
                    
                    processed += 1
                    logger.info(f"✅ Successfully processed {doc_name} in {doc_duration:.2f}s")
                    logger.info(f"📊 Progress: {processed}/{len(pdf_files)} documents completed")
                    
                except KeyboardInterrupt:
                    logger.warning(f"⏹️  Processing interrupted by user at document {i}/{len(pdf_files)}")
                    logger.info(f"📊 Current Progress: {processed} completed, {failed} failed")
                    break
                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    # Truncate very long error messages
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200] + "..."
                    
                    logger.error(f"❌ Failed to process {Path(pdf_path).name}: {error_msg}")
                    logger.error(f"Full traceback for {Path(pdf_path).name}: {traceback.format_exc()}")
                    logger.info(f"📊 Progress: {processed}/{len(pdf_files)} completed, {failed} failed")
                    
                    # Continue processing other documents
                    continue
            
            total_duration = time.time() - start_time
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🏁 BATCH PROCESSING COMPLETE!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   ✅ Successfully processed: {processed} documents")
            logger.info(f"   ❌ Failed: {failed} documents")
            logger.info(f"   📈 Success rate: {(processed/len(pdf_files))*100:.1f}%")
            logger.info(f"   ⏱️  Total time: {total_duration:.2f}s")
            logger.info(f"   ⚡ Average time per document: {total_duration/len(pdf_files):.2f}s")
            logger.info(f"{'='*80}")
            
        elif args.file:
            pdf_path = args.file
            if not Path(pdf_path).exists():
                print(f"❌ PDF not found: {pdf_path}")
                sys.exit(1)
            logger.info(f"Running ingestion for single document: {pdf_path}")
            process_and_ingest_document(pdf_path)
            logger.info("Single document ingestion completed successfully")
            
        elif args.test_single:
            pdf_path = str(Path(args.input_dir) / args.test_single)
            if not Path(pdf_path).exists():
                print(f"❌ PDF not found: {pdf_path}")
                sys.exit(1)
            logger.info(f"Running ingestion for single document: {pdf_path}")
            process_and_ingest_document(pdf_path)
            logger.info("Single document ingestion completed successfully")
            
        else:
            print("No --file, --test-single, or --batch-all provided; nothing to do.")
            sys.exit(0)
    except Exception as e:
        logger.log_exception(e, "Single document ingestion failed")
        sys.exit(2)
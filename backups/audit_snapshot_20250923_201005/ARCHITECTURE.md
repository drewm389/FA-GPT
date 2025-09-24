# FA-GPT Architecture Overview

## Goals
- GPU-accelerated, document-centric RAG with knowledge graph extraction
- Deterministic ingestion flow with resumability and auditability

## High-Level Flow
1. Ingestion entry (CLI): `app/simple_ingestion.py` or `process_documents.py`
2. Parsing & structure: `app/enhanced_granite_docling.py` (Docling + Granite)
3. Chunking & embeddings: `app/rag_core.py`, `app/multimodal_embeddings.py`
4. Storage: PostgreSQL + pgvector (RAG), Apache AGE (KG)
5. KG extraction: `app/connectors.py` (Ollama client) with `qwen2.5vl` via `app/simple_ingestion.py`
6. Serving / status: Streamlit app `app/main.py`, helpers `system_status.py`

## Key Components
- `app/config.py`: central settings
- `app/connectors.py`: DB + Ollama clients
- `app/enhanced_granite_docling.py`: GPU-enabled Docling pipeline wrapper
- `app/ingestion.py` / `app/simple_ingestion.py`: orchestrate end-to-end ingest
- `app/rag_core.py`: chunking, embeddings, retrieval
- `app/multimodal_embeddings.py`: image-aware embeddings
- `enhanced_reprocessing.py`, `retry_failed_ingestion.py`: ops tooling

## Data Model
- RAG: documents, chunks, embeddings (pgvector)
- KG: nodes and relationships (AGE), extracted from clean text

## GPU Notes (ROCm)
- PyTorch ROCm; Granite’s RT-DETR v2 for layout
- MIOpen cache configuration required on some setups

## Running
- Single doc: `python -m app.simple_ingestion --file <path>`
- Batch: `python process_documents.py --input-dir data/documents`
- Streamlit: `streamlit run app/main.py`

## Security & Secrets
- Secrets are not included; configure via environment or .env (excluded from snapshot)


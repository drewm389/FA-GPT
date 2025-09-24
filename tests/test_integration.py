# tests/test_integration.py
import os
import time
import pytest
from app.simple_ingestion import process_and_ingest_document
from app.rag_core import get_rag_response

@pytest.mark.integration
def test_full_pipeline():
    """
    Tests the full ingestion and RAG pipeline.
    """
    # Path to the test document inside the Docker container
    test_doc_path = "/app/data/documents/test.pdf"

    # 1. Ingestion
    try:
        process_and_ingest_document(test_doc_path)
    except Exception as e:
        pytest.fail(f"Ingestion failed with error: {e}")

    # Give the system a moment to process
    time.sleep(5)

    # 2. RAG Query
    query = "What is in the test document?"
    try:
        response, _, _ = get_rag_response(query)
        assert "test" in response.lower()
    except Exception as e:
        pytest.fail(f"RAG query failed with error: {e}")
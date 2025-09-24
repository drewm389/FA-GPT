# app/main.py
"""
Streamlit Web Interface for FA-GPT (Field Artillery GPT)

This is the main user interface for the FA-GPT system, providing:
1. Document management and ingestion controls
2. Multi-modal chat interface for querying documents
3. Visual display of retrieved images and metadata
4. Model status and system information

The interface allows users to:
- Upload and process PDF documents using IBM Docling
- Ask questions about processed documents
- View relevant images and context from the knowledge base
- Monitor system status and available models

The system runs entirely locally using:
- Ollama for LLM/VLM inference
- PostgreSQL with pgvector for vector storage and Apache AGE for knowledge graphs
- IBM Granite-Docling-258M for multimodal document extraction
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.simple_ingestion import process_and_ingest_document
from app.rag_core import get_rag_response
from system_status import check_database, check_ollama_models

# Page config
st.set_page_config(
    page_title="FA-GPT: Field Artillery Assistant",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for military styling
st.markdown("""
<style>
    .main {background-color: #f5f5f0;}
    .stAlert {background-color: #e8f5e9;}
    h1 {color: #2e7d32;}
    .metadata-box {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎖️ FA-GPT: Field Artillery RAG System")
st.caption("Powered by IBM Docling & Local VLM")

# Sidebar
with st.sidebar:
    st.header("📚 Document Management")

    # System Status
    with st.expander("🩺 System Status", expanded=True):
        db_ok, db_msg = check_database()
        ollama_ok, ollama_models = check_ollama_models()
        if db_ok:
            st.success("PostgreSQL: Connected")
        else:
            st.error(f"PostgreSQL: {db_msg}")
        if ollama_ok:
            st.success(f"Ollama: Connected ({len(ollama_models)} models)")
        else:
            st.error("Ollama: Not responding")

    
    # Model status
    with st.expander("🤖 Model Status", expanded=False):
        st.info(f"VLM: {settings.vlm_model}")
        st.info(f"LLM: {settings.llm_model}")
        st.info(f"Embedder: {settings.embedding_model}")
    
    st.divider()
    
    # Document listing
    try:
        doc_files = sorted([
            f for f in os.listdir(settings.documents_dir) 
            if f.endswith(('.pdf', '.PDF'))
        ])
    except FileNotFoundError:
        st.error("Documents directory not found!")
        doc_files = []
    
    if doc_files:
        st.success(f"📁 {len(doc_files)} document(s) available")
        with st.expander("View Documents"):
            for doc in doc_files:
                st.text(f"• {doc}")
    else:
        st.warning("No PDF documents found")
        st.info("Add PDFs to ./data/documents/")
    
    st.divider()
    
    # Ingestion controls
    st.subheader("🔄 Document Ingestion")
    selected_doc = st.selectbox(
        "Select document to ingest:",
        options=[""] + doc_files,
        help="Choose a PDF to process with IBM Docling"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        ingest_btn = st.button(
            "🚀 Ingest", 
            type="primary",
            disabled=not selected_doc
        )
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    if ingest_btn and selected_doc:
        doc_path = settings.documents_dir / selected_doc
        with st.spinner(f"Processing with Docling... This may take several minutes."):
            progress = st.progress(0)
            status = st.empty()
            
            try:
                status.text("Initializing Docling...")
                progress.progress(10)
                
                status.text("Parsing document structure...")
                progress.progress(30)
                
                process_and_ingest_document(str(doc_path))
                
                progress.progress(100)
                st.success(f"✅ Successfully ingested: {selected_doc}")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Ingestion failed: {str(e)}")
                st.exception(e)

# Main chat interface
st.header("💬 Multi-Modal Chat Interface")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "metadata" not in st.session_state:
    st.session_state.metadata = []

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display images if present
        if message.get("images"):
            cols = st.columns(min(len(message["images"]), 3))
            for idx, img_data in enumerate(message["images"]):
                with cols[idx % 3]:
                    st.image(img_data, caption=f"Source {idx+1}")
        
        # Display metadata if present
        if message["role"] == "assistant" and i < len(st.session_state.metadata):
            with st.expander("🔍 Response Metadata", expanded=False):
                metadata = st.session_state.metadata[i]
                st.json(metadata)

# Chat input
if prompt := st.chat_input("Ask about your Field Artillery documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Processing with local VLM..."):
            # Call RAG pipeline
            response, images, metadata = get_rag_response(prompt)
            
            # Display response
            st.markdown(response)
            
            # Display source images
            if images:
                st.divider()
                st.caption("📸 Retrieved Visual Context:")
                cols = st.columns(min(len(images), 3))
                for idx, img_data in enumerate(images):
                    with cols[idx % 3]:
                        st.image(img_data, caption=f"Source {idx+1}")
            
            # Store in session
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "images": images
            })
            st.session_state.metadata.append(metadata)

# Footer
st.divider()
st.caption("FA-GPT v2.0 | IBM Docling + Local VLM | Running 100% Locally")
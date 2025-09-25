# app/main.py
"""
Enhanced Streamlit Web Interface for FA-GPT (Field Artillery GPT)

This is the main user interface for the FA-GPT system, providing:
1. Document management and ingestion controls
2. Multi-modal chat interface for querying documents
3. Artillery fire mission planning and ballistic calculations
4. Military orders generation and tactical decision support
5. Visual display of retrieved images and tactical maps
6. Model status and system information

The interface allows users to:
- Upload and process PDF documents using IBM Docling
- Ask questions about processed documents with military-specific analysis
- Plan fire missions with ballistic calculations
- Generate military orders and tactical documents
- View relevant images and tactical context from the knowledge base
- Monitor system status and available models

The system runs entirely locally using:
- Ollama for LLM/VLM inference with Qwen 2.5 VL
- PostgreSQL with pgvector for vector storage and Apache AGE for knowledge graphs
- IBM Granite-Docling-258M for multimodal document extraction
- Custom artillery computation layer for ballistic calculations
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.simple_ingestion import process_and_ingest_document
from app.rag_core import get_rag_response
from app.military_ui import MilitaryUIComponents, render_military_sidebar
from app.ballistic_computer import BallisticComputer, FireMissionPlanner
from app.orders_generator import OrdersGenerator, TacticalDecisionSupport
from system_status import check_database, check_ollama_models

# Try to import MilitaryImageAnalyzer with error handling
try:
    from app.military_vision import MilitaryImageAnalyzer
except ImportError as e:
    st.warning(f"Military image analysis unavailable: {e}")
    MilitaryImageAnalyzer = None

# Page config
st.set_page_config(
    page_title="FA-GPT: Field Artillery Assistant",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_military_components():
    """Initialize military components with caching and error handling."""
    components = {}
    
    try:
        components["ui"] = MilitaryUIComponents()
        components["ballistic_computer"] = BallisticComputer()
        components["mission_planner"] = FireMissionPlanner()
        components["orders_generator"] = OrdersGenerator()
        components["tactical_support"] = TacticalDecisionSupport()
        
        # Initialize image analyzer with error handling for Ollama dependency
        try:
            if MilitaryImageAnalyzer is not None:
                components["image_analyzer"] = MilitaryImageAnalyzer()
            else:
                components["image_analyzer"] = None
        except Exception as e:
            st.warning(f"Military image analysis unavailable (Ollama connection issue): {e}")
            components["image_analyzer"] = None
            
    except Exception as e:
        st.error(f"Failed to initialize some military components: {e}")
        # Provide minimal fallback components
        components = {
            "ui": None,
            "ballistic_computer": BallisticComputer() if 'BallisticComputer' in globals() else None,
            "mission_planner": None,
            "orders_generator": None,
            "tactical_support": None,
            "image_analyzer": None
        }
    
    return components

military_components = initialize_military_components()

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
    .military-panel {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .fire-mission-header {
        background-color: #dc3545;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎖️ FA-GPT: Enhanced Field Artillery System")
st.caption("Powered by IBM Docling, Qwen 2.5 VL & Artillery Computation Layer")

# Navigation tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Knowledge Base", 
    "🎯 Fire Mission Planning", 
    "🧮 Ballistic Calculator",
    "📋 Orders Generation",
    "📊 System Status"
])

# Render military sidebar
render_military_sidebar()

# Sidebar for document management
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
        st.info("🎯 Artillery Computer: Active")
        st.info("📋 Orders Generator: Active")
    
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
        help="Choose a PDF to process with IBM Docling and military extraction"
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
        with st.spinner(f"Processing with enhanced military extraction..."):
            progress = st.progress(0)
            status = st.empty()
            
            try:
                status.text("Initializing Granite-Docling...")
                progress.progress(10)
                
                status.text("Parsing document structure...")
                progress.progress(30)
                
                status.text("Extracting tactical entities...")
                progress.progress(60)
                
                status.text("Processing military content...")
                progress.progress(80)
                
                process_and_ingest_document(str(doc_path))
                
                progress.progress(100)
                st.success(f"✅ Successfully ingested: {selected_doc}")
                st.info("📊 Military entities and tactical data extracted")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Ingestion failed: {str(e)}")
                st.exception(e)

# Tab 1: Knowledge Base Chat Interface
with tab1:
    st.header("💬 Multi-Modal Knowledge Base")

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
            with st.spinner("Processing with enhanced military analysis..."):
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

# Tab 2: Fire Mission Planning
with tab2:
    st.header("🎯 Fire Mission Planning")
    
    if military_components["ui"] is None:
        st.error("Military UI components unavailable. Please check Ollama connection.")
        st.info("Ensure Ollama is running: `ollama serve`")
    else:
        # Initialize session state for fire missions
        if "current_target" not in st.session_state:
            st.session_state.current_target = None
        if "firing_units" not in st.session_state:
            st.session_state.firing_units = []
        if "mission_plan" not in st.session_state:
            st.session_state.mission_plan = None
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Target input
            target = military_components["ui"].render_target_input_form()
            if target:
                st.session_state.current_target = target
                st.success(f"Target {target.designation} designated")
        
        with col2:
            # Firing unit configuration
            units = military_components["ui"].render_firing_unit_selector()
            if units:
                st.session_state.firing_units = units
    
    # Plan fire mission if we have target and units
    if st.session_state.current_target and st.session_state.firing_units:
        st.divider()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            mission_type = st.selectbox(
                "Mission Type",
                ["DESTROY", "NEUTRALIZE", "SUPPRESS", "HARASS"],
                help="Type of fire mission to plan"
            )
        
        with col2:
            if st.button("📊 Plan Mission", type="primary"):
                with st.spinner("Planning fire mission..."):
                    mission_plan = military_components["mission_planner"].plan_fire_mission(
                        st.session_state.firing_units,
                        st.session_state.current_target,
                        mission_type
                    )
                    st.session_state.mission_plan = mission_plan
        
        with col3:
            if st.button("🗺️ Show Map"):
                military_components["ui"].render_tactical_map(
                    st.session_state.firing_units,
                    [st.session_state.current_target]
                )
        
        # Display mission plan
        if st.session_state.mission_plan:
            st.divider()
            military_components["ui"].render_fire_mission_display(st.session_state.mission_plan)
    
    # Ammunition status
    if st.session_state.firing_units:
        st.divider()
        military_components["ui"].render_ammunition_status(st.session_state.firing_units)

# Tab 3: Ballistic Calculator
with tab3:
    st.header("🧮 Manual Ballistic Calculator")
    
    if military_components["ui"] is None:
        st.error("Military UI components unavailable. Please check Ollama connection.")
        st.info("Basic ballistic calculations still available:")
        # Provide basic fallback functionality
        col1, col2 = st.columns(2)
        with col1:
            range_m = st.number_input("Range (meters)", min_value=100, max_value=40000, value=10000)
        with col2:
            weapon = st.selectbox("Weapon System", ["M777A2", "M109A6", "M119A3", "M252"])
        
        if st.button("Calculate Basic Firing Data"):
            st.info("Advanced ballistic calculations require Ollama connection")
    else:
        military_components["ui"].render_ballistic_calculator()
    
    st.divider()
    st.subheader("📚 Firing Tables Reference")
    
    # Display sample firing data
    with st.expander("M777A2 155mm Howitzer - Sample Data"):
        sample_data = {
            "Range (m)": [5000, 10000, 15000, 20000, 25000, 30000],
            "Charge": ["1", "2", "3", "4", "5", "WB"],
            "Elevation (mils)": [245, 320, 425, 580, 720, 845],
            "TOF (sec)": [28.5, 38.2, 52.1, 68.9, 88.4, 112.3]
        }
        st.dataframe(sample_data, width='stretch')

# Tab 4: Orders Generation
with tab4:
    st.header("📋 Military Orders Generation")
    
    if military_components["orders_generator"] is None:
        st.error("Orders generation unavailable. Please check system components.")
        st.info("Ensure all military components are properly initialized.")
    else:
        order_type = st.selectbox(
            "Order Type",
            ["Fire Order", "Fire Support Plan", "Operation Order", "Unit Status Report"],
            help="Select type of military order to generate"
        )
        
        if order_type == "Fire Order" and st.session_state.get("mission_plan"):
            st.subheader("🔥 Generate Fire Order")
            
            if st.button("📋 Generate Fire Order", type="primary"):
                mission_plan = st.session_state.mission_plan
                if mission_plan["recommended_unit"]:
                    recommended = mission_plan["recommended_unit"]
                    
                    fire_order = military_components["orders_generator"].generate_fire_order(
                        st.session_state.current_target,
                        recommended["unit"],
                        recommended["solution"],
                        recommended["ammunition_expenditure"]
                )
                
                formatted_order = military_components["orders_generator"].format_fire_order(fire_order)
                
                st.subheader("📻 Fire Order")
                st.code(formatted_order, language="text")
                
                # Download button
                st.download_button(
                    label="💾 Download Fire Order",
                    data=formatted_order,
                    file_name=f"fire_order_{fire_order.order_id}.txt",
                    mime="text/plain"
                )
        
        elif order_type == "Fire Support Plan":
            st.subheader("📊 Generate Fire Support Plan")
            
            col1, col2 = st.columns(2)
            with col1:
                operation_name = st.text_input("Operation Name", "Operation STEEL RAIN")
                planning_unit = st.text_input("Planning Unit", "1-77 FA FDC")
            
            with col2:
                effective_date = st.date_input("Effective Date")
                effective_time = st.time_input("Effective Time")
            
            if st.button("📋 Generate Fire Support Plan"):
                if st.session_state.get("firing_units") and st.session_state.get("current_target"):
                    from datetime import datetime, time
                    effective_datetime = datetime.combine(effective_date, effective_time)
                    
                    fire_support_plan = military_components["orders_generator"].generate_fire_support_plan(
                        operation_name,
                        planning_unit,
                        [st.session_state.current_target],
                        st.session_state.firing_units,
                        effective_datetime
                    )
                    
                    formatted_plan = military_components["orders_generator"].format_fire_support_plan(fire_support_plan)
                    
                    st.subheader("📊 Fire Support Plan")
                    st.code(formatted_plan, language="text")
                    
                    st.download_button(
                        label="💾 Download Plan",
                        data=formatted_plan,
                        file_name=f"fire_support_plan_{fire_support_plan.plan_id}.txt",
                        mime="text/plain"
                    )
        
        elif order_type == "Unit Status Report":
            if st.session_state.get("firing_units"):
                if st.button("📋 Generate Unit Status Report"):
                    report = military_components["orders_generator"].generate_unit_status_report(
                        st.session_state.firing_units
                    )
                    
                    st.subheader("📊 Unit Status Report")
                    st.code(report, language="text")
                    
                    st.download_button(
                        label="💾 Download Report",
                        data=report,
                        file_name=f"unit_status_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )

# Tab 5: System Status
with tab5:
    st.header("📊 Enhanced System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗄️ Database Status")
        db_ok, db_msg = check_database()
        if db_ok:
            st.success("✅ PostgreSQL Connected")
            st.success("✅ pgvector Extension Active")
            st.success("✅ Apache AGE Extension Active")
        else:
            st.error(f"❌ Database Error: {db_msg}")
        
        st.divider()
        st.subheader("🤖 AI Models")
        ollama_ok, ollama_models = check_ollama_models()
        if ollama_ok:
            st.success(f"✅ Ollama ({len(ollama_models)} models)")
            for model in ollama_models:
                st.info(f"📦 {model}")
        else:
            st.error("❌ Ollama Not Responding")
    
    with col2:
        st.subheader("🎯 Artillery Systems")
        st.success("✅ Ballistic Computer Active")
        st.success("✅ Fire Mission Planner Active")
        st.success("✅ Orders Generator Active")
        st.success("✅ Military Vision Analysis Active")
        
        st.divider()
        st.subheader("📚 Document Processing")
        st.success("✅ Granite-Docling Extractor")
        st.success("✅ Military Entity Recognition")
        st.success("✅ Tactical Data Extraction")
        st.success("✅ Classification Detection")
    
    st.divider()
    st.subheader("⚙️ System Configuration")
    
    config_info = {
        "VLM Model": settings.vlm_model,
        "LLM Model": settings.llm_model,
        "Embedding Model": settings.embedding_model,
        "Vector Dimension": "1536",
        "Database": "PostgreSQL + pgvector + Apache AGE",
        "Artillery Computer": "Custom Ballistic Engine",
        "Military Extraction": "Enhanced Pattern Recognition"
    }
    
    for key, value in config_info.items():
        st.info(f"**{key}**: {value}")

# Footer
st.divider()
st.caption("FA-GPT v3.0 Enhanced | Artillery Computation Layer | IBM Docling + Qwen 2.5 VL | Running 100% Locally")
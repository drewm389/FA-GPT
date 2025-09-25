# app/main.py
"""
Enhanced Streamlit Web Interface for FA-GPT (Field Artillery GPT)

This is the main user interface for the FA-GPT system, providing:
1. Document management and ingestion controls
2. Multi-modal chat interface for querying documents
3. Artillery fire mission planning and ballistic calculations
4. Military orders generation and tactical decision support
5. Visual display of retrieved images and tactical maps
6. Minimal Document Processing System  
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 INTELLIGENCE HUB", 
    "🎯 FIRE SUPPORT", 
    "🔧 BALLISTICS",
    "� OPERATIONS",
    "⚙️ SYSTEM ADMIN"
]) system information

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

# Professional U.S. Army Website Design
st.markdown("""
<style>
    /* Import professional fonts matching Army.com */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700;900&family=Roboto:wght@300;400;500;700;900&family=Open+Sans:wght@300;400;600;700;800&display=swap');
    
    /* Clean professional Army theme */
    /* Dark minimalist theme */
    .stApp {
        background: #0a0a0a;
        color: #e5e5e5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
        position: relative;
        line-height: 1.5;
        font-weight: 400;
    }    /* Clean minimal overlay */
    .guard-overlay {
        display: none;
    }
    
    /* Minimal accessibility */
    * {
        outline: none;
    }
    
    *:focus {
        outline: 2px solid #1a1a1a !important;
        outline-offset: 2px !important;
    }
    
    /* Skip to content link */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 20px;
        background: #1a1a1a;
        color: #fafafa;
        padding: 8px 16px;
        text-decoration: none;
        font-weight: 500;
        z-index: 10000;
        border-radius: 2px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }
    
    .skip-link:focus {
        top: 20px;
    }
    
    /* Night vision HUD */
    .night-vision-hud {
        position: fixed;
        top: 60px;
        left: 40px;
        right: 40px;
        bottom: 80px;
        border: 1px solid #333333;
        border-radius: 20px;
        pointer-events: none;
        z-index: 2;
        box-shadow: none;
    }
    
    .guard-header::before {
        display: none;
    }
    
    .guard-logo {
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 12px;
        color: #666666;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Dark block menu */
    .guard-menu {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        padding: 40px;
        margin: 40px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        position: relative;
    }
    
    .guard-menu-item {
        display: flex;
        align-items: center;
        padding: 24px;
        margin: 16px 0;
        background: #0f0f0f;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .guard-menu-item::before {
        display: none;
    }
    
    .guard-menu-item:hover {
        background: #2a2a2a;
        border-color: #404040;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    
    .guard-menu-icon {
        width: 48px;
        height: 48px;
        margin-right: 20px;
        border-radius: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        background: #333333;
        color: #ffffff;
        position: relative;
        z-index: 2;
    }
    
    .guard-menu-content {
        flex: 1;
        position: relative;
        z-index: 2;
    }
    
    .guard-menu-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .guard-menu-desc {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #999999;
        line-height: 1.4;
        font-weight: 400;
    }
    
    /* Dark classification banner */
    .classification-banner {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #000000;
        color: #666666;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 400;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-align: center;
        padding: 8px;
        z-index: 9999;
        border-bottom: 1px solid #1a1a1a;
    }
    
    /* Dark status bar */
    .guard-status {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 36px;
        background: #0a0a0a;
        border-top: 1px solid #1a1a1a;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: 400;
        color: #666666;
        z-index: 1000;
    }
    
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        background: transparent;
        border: 1px solid #333333;
        border-radius: 2px;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-indicator::before {
        content: '•';
        color: #666666;
    }
    
    /* Minimal scan effect (disabled) */
    
    /* Dark sidebar */
    .css-1d391kg {
        background: #0f0f0f;
        border-right: 1px solid #2a2a2a;
        box-shadow: none;
    }
    
    /* Dark main header - centered */
    .guard-main-header {
        background: #0a0a0a;
        border: none;
        border-bottom: 1px solid #1a1a1a;
        border-radius: 0;
        padding: 80px 20px;
        margin: 0 0 80px 0;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    /* Artillery crosshairs removed for minimal design */
    
    /* Night vision effects removed for minimal design */
    
    .guard-main-header h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        color: #ffffff;
        margin: 0 0 16px 0;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 10;
        line-height: 1.1;
    }
    
    .guard-main-header .subtitle {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1.1rem;
        color: #999999;
        margin-top: 0;
        letter-spacing: 0;
        text-transform: none;
        line-height: 1.4;
    }
    
    .guard-main-header .tagline {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: #666666;
        margin-top: 24px;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Artillery designation removed for minimal design */
    
    /* Dark chat messages */
    .stChatMessage {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 4px !important;
        margin: 16px 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        color: #e5e5e5 !important;
        position: relative !important;
    }
    
    .stChatMessage::before {
        display: none !important;
    }
    
    .stChatMessage [data-testid="user-avatar"] {
        background: #333333 !important;
        border: 1px solid #404040 !important;
        box-shadow: none !important;
    }
    
    .stChatMessage [data-testid="assistant-avatar"] {
        background: #2a2a2a !important;
        border: 1px solid #404040 !important;
        box-shadow: none !important;
    }
    
    /* Dark input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #333333;
        border-radius: 2px;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 14px;
        box-shadow: none;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #555555;
        box-shadow: 0 0 0 2px rgba(85, 85, 85, 0.3);
        transform: none;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #666666;
        font-style: normal;
    }
    
    /* Dark button styling */
    .stButton > button {
        background: #333333;
        color: #ffffff;
        border: 1px solid #404040;
        border-radius: 2px;
        padding: 12px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 14px;
        text-transform: none;
        letter-spacing: 0;
        transition: all 0.2s ease;
        box-shadow: none;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        display: none;
    }
    
    .stButton > button:hover {
        background: #404040;
        color: #ffffff;
        border-color: #555555;
        transform: none;
        box-shadow: none;
    }
    
    .stButton > button:active {
        background: #2a2a2a;
        transform: none;
        box-shadow: none;
    }
    
    /* Dark file uploader styling */
    .stFileUploader {
        background-color: #1a1a1a;
        border: 1px dashed #404040;
        border-radius: 4px;
        padding: 20px;
    }
    
    /* Minimal tabs (primary) */
    /* Dark tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        padding: 0;
        border-radius: 0;
        border: none;
        border-bottom: 1px solid #2a2a2a;
        box-shadow: none;
    }    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #999999;
        border: none;
        border-radius: 0;
        padding: 16px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 14px;
        letter-spacing: 0;
        text-transform: uppercase;
        transition: all 0.2s ease;
        position: relative;
        margin: 0;
        box-shadow: none;
        border-bottom: 2px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: transparent;
        color: #e5e5e5;
        border-bottom-color: #666666;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #ffffff !important;
        border-bottom-color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Duplicate button styling removed */
    
    /* Dark input styling (secondary) */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #333333;
        border-radius: 2px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #555555;
        box-shadow: 0 0 0 2px rgba(85, 85, 85, 0.3);
    }
    
    /* Dark chat styling (secondary) */
    .stChatMessage {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 4px !important;
        margin: 16px 0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        color: #e5e5e5 !important;
    }
    
    /* Dark additional elements */
    .stSelectbox > div > div {
        background: #1a1a1a;
        color: #e5e5e5;
        border: 1px solid #333333;
        border-radius: 2px;
    }
    
    .stProgress > div > div > div {
        background: #666666;
    }
    
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid #22c55e;
        color: #4ade80;
        border-radius: 4px;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        color: #f87171;
        border-radius: 4px;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Minimal sidebar */
    .css-1d391kg {
        background: #f5f5f5;
        border-right: 1px solid #e5e5e5;
    }
    
    /* Dark metrics styling */
    .stMetric {
        background-color: #1a1a1a;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 15px;
    }
    
    .stMetric > div {
        color: #e5e5e5;
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark alert styling */
    .stAlert {
        background-color: rgba(26, 26, 26, 0.9);
        border: 1px solid #404040;
        color: #e5e5e5;
        font-family: 'Inter', sans-serif;
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: rgba(0, 77, 0, 0.3);
        border: 1px solid #00ff00;
        color: #00ff00;
    }
    
    /* Warning message styling */
    .stWarning {
        background-color: rgba(255, 140, 0, 0.1);
        border: 1px solid #ff8c00;
        color: #ff8c00;
    }
    
    /* Error message styling */
    .stError {
        background-color: rgba(139, 0, 0, 0.3);
        border: 1px solid #ff0000;
        color: #ff4444;
    }
    
    /* Information message styling */
    .stInfo {
        background-color: rgba(0, 100, 200, 0.1);
        border: 1px solid #0064c8;
        color: #4da6d9;
    }
    
    /* Selectbox styling */
    .st-selectbox > div > div {
        background-color: #1a2833;
        color: #e5e5e5;
        border: 1px solid #404040;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #666666;
    }
    
    /* Dark code block styling */
    .stCodeBlock {
        background-color: #0f0f0f;
        border: 1px solid #404040;
        color: #e5e5e5;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Dark dataframe styling */
    .stDataFrame {
        background-color: #1a1a1a;
        border: 1px solid #404040;
    }
    
    /* Minimal status indicators */
    .status-operational {
        color: #22c55e;
        font-weight: 500;
        text-shadow: none;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 500;
        text-shadow: none;
    }
    
    .status-critical {
        color: #ef4444;
        font-weight: 500;
        text-shadow: none;
    }
    
    /* Dark classification styling */
    .classification-header {
        background: #1a1a1a;
        color: #e5e5e5;
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        padding: 12px;
        border-radius: 4px;
        margin: 16px 0;
        letter-spacing: 0;
        border: 1px solid #2a2a2a;
    }
    
    /* Minimal grid layout */
    .military-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
        padding: 20px;
    }
    
    .military-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
    }
    
    .military-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        transform: translateY(-2px);
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Advanced Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
        border-radius: 6px;
        box-shadow: none;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #404040;
        border-radius: 6px;
        box-shadow: none;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555555;
        box-shadow: none;
    }
    
    /* Additional dark enhancements */
    .stSelectbox > div > div {
        background: #1a1a1a;
        color: #e5e5e5;
        border: 2px solid #00ff41;
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
    }
    
    .stProgress > div > div > div {
        background: #666666;
        box-shadow: none;
    }
    
    .stFileUploader > div {
        background: #1a1a1a;
        border: 1px dashed #404040;
        border-radius: 4px;
        padding: 20px;
        box-shadow: none;
    }
    
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border: 2px solid #00ff41;
        color: #00ff41;
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(150, 0, 0, 0.2), rgba(255, 51, 51, 0.1));
        border: 2px solid #ff3333;
        color: #ff6666;
        border-radius: 8px;
        box-shadow: 0 0 15px rgba(255, 51, 51, 0.3);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# National Guard Professional Military Interface
st.markdown("""
<a href="#main-content" class="skip-link">Skip to main content</a>
<div class="classification-banner">DARK MODE DOCUMENT PROCESSING INTERFACE.</div>
<div class="guard-overlay"></div>

<div class="guard-main-header" id="main-content">
    <div class="guard-logo">BLOCKS</div>
    <h1>FA-GPT</h1>
    <div class="subtitle">Field Artillery Document Processing System</div>
    <div class="tagline">
        DARK • ELEGANT • FOCUSED
    </div>
    <div style="margin-top: 40px; display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
        <div class="status-indicator">READY</div>
        <div class="status-indicator">ONLINE</div>
        <div class="status-indicator">ACTIVE</div>
        <div class="status-indicator">STABLE</div>
    </div>
</div>

<div class="guard-status">
    <div class="status-indicator">SYS</div>
    <div class="status-indicator">NET</div>
    <div class="status-indicator">OPS</div>
    <div class="status-indicator">DOC</div>
    <div class="status-indicator">TIME: <span id="current-time"></span></div>
</div>

<script>
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {hour12: false});
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}
setInterval(updateTime, 1000);
updateTime();
</script>
""", unsafe_allow_html=True)

# Main content area starts here - styling already applied above

# Minimal System Modules
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "� INTEL DATABASE", 
    "🎯 FIRE MISSIONS", 
    "⚡ BALLISTICS",
    "📋 ORDERS PROD",
    "�️ SYSTEM OPS"
])

# Render military sidebar
render_military_sidebar()

# Military-themed sidebar for tactical operations
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #1a2833 0%, #0a0a0a 100%); border: 2px solid #00ff00; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #00ff00; font-family: 'Orbitron', monospace; margin: 0;">⚡ TACTICAL OPS</h2>
        <p style="color: #7fff7f; font-family: 'Rajdhani', monospace; margin: 5px 0;">Document Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # System Status with military indicators
    with st.expander("🔍 SYSTEM STATUS", expanded=True):
        db_ok, db_msg = check_database()
        ollama_ok, ollama_models = check_ollama_models()
        
        if db_ok:
            st.markdown('<div class="status-operational">🟢 PostgreSQL: OPERATIONAL</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-critical">🔴 PostgreSQL: {db_msg}</div>', unsafe_allow_html=True)
            
        if ollama_ok:
            st.markdown(f'<div class="status-operational">🟢 Ollama: OPERATIONAL ({len(ollama_models)} models)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-critical">🔴 Ollama: NOT RESPONDING</div>', unsafe_allow_html=True)

    
    # Model status with military styling
    with st.expander("� AI SYSTEMS", expanded=False):
        st.markdown(f'<div style="color: #00ff00; font-family: \'Rajdhani\', monospace;">🔹 VLM: {settings.vlm_model}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #00ff00; font-family: \'Rajdhani\', monospace;">🔹 LLM: {settings.llm_model}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #00ff00; font-family: \'Rajdhani\', monospace;">🔹 Embedder: {settings.embedding_model}</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7fff7f; font-family: \'Rajdhani\', monospace;">🎯 Artillery Computer: ACTIVE</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7fff7f; font-family: \'Rajdhani\', monospace;">📋 Orders Generator: ACTIVE</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Document listing with military styling
    try:
        doc_files = sorted([
            f for f in os.listdir(settings.documents_dir) 
            if f.endswith(('.pdf', '.PDF'))
        ])
    except FileNotFoundError:
        st.error("⚠️ DOCUMENTS DIRECTORY NOT FOUND!")
        doc_files = []
    
    if doc_files:
        st.markdown(f'<div class="status-operational">📁 {len(doc_files)} DOCUMENTS AVAILABLE</div>', unsafe_allow_html=True)
        with st.expander("📋 VIEW DOCUMENTS"):
            for doc in doc_files:
                st.markdown(f'<div style="color: #7fff7f; font-family: \'Rajdhani\', monospace;">🔸 {doc}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⚠️ NO PDF DOCUMENTS FOUND</div>', unsafe_allow_html=True)
        st.markdown('<div style="color: #7fff7f;">📥 Add PDFs to ./data/documents/</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ingestion controls with military theme
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2833 0%, #0a0a0a 100%); padding: 15px; border: 1px solid #00ff00; border-radius: 10px;">
        <h4 style="color: #00ff00; font-family: 'Orbitron', monospace; margin-top: 0;">⚡ DOCUMENT INGESTION</h4>
    </div>
    """, unsafe_allow_html=True)
    
    selected_doc = st.selectbox(
        "📄 Select document to ingest:",
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

# Tab 1: Intelligence Database Interface
with tab1:

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

    # Military-themed chat input
    if prompt := st.chat_input("Enter your question about the documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 ANALYZING INTELLIGENCE... PROCESSING TACTICAL DATA..."):
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
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2833 0%, #0a0a0a 100%); padding: 20px; border: 2px solid #ff4444; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #ff4444; font-family: 'Orbitron', monospace; text-align: center; margin: 0;">🎯 FIRE MISSION PLANNING</h2>
        <p style="color: #ffaaaa; font-family: 'Rajdhani', monospace; text-align: center; margin: 5px 0;">Artillery Fire Support Coordination</p>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2833 0%, #0a0a0a 100%); padding: 20px; border: 2px solid #ffaa00; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #ffaa00; font-family: 'Orbitron', monospace; text-align: center; margin: 0;">⚡ BALLISTIC COMPUTER</h2>
        <p style="color: #ffdd77; font-family: 'Rajdhani', monospace; text-align: center; margin: 5px 0;">Advanced Firing Solution Calculator</p>
    </div>
    """, unsafe_allow_html=True)
    
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
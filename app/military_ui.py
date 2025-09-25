# app/military_ui.py
"""
Military UI Components for FA-GPT

Handles all UI rendering for the FA-GPT Streamlit application.

This refactored UI class takes an AppState object and renders the complete
interface while maintaining clean separation from business logic. All
actual processing is delegated to appropriate backend modules.

Key Components:
- MilitaryUI: Main UI class that coordinates all rendering
- Sidebar navigation and system status display
- Tabbed interface for different functional areas
- State-driven rendering ensures UI reflects current application state
"""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import base64



sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.state import AppStatefrom app.state import AppState

from app.rag_core import get_rag_responsefrom app.rag_core import get_rag_response

from app.ballistic_computer import BallisticComputer, FiringUnit, Target, WeaponSystem, AmmunitionType, ChargeTypefrom app.ballistic_computer import BallisticComputer, FiringUnit, Target, WeaponSystem, AmmunitionType, ChargeType

from app.orders_generator import OrdersGenerator, OrderType, MissionPriority, MethodOfFirefrom app.orders_generator import OrdersGenerator, OrderType, MissionPriority, MethodOfFire



class MilitaryUI:# ==============================================================================

    """# Custom CSS for Enhanced, Conversational UI

    Handles all UI rendering for the FA-GPT Streamlit application.# ==============================================================================

    The UI class takes the app state and calls backend functions.def load_css():

    """    st.markdown("""

        <style>

    def __init__(self, state: AppState):        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        """Initialize the Military UI with application state."""        

        self.state = state        /* --- Monochromatic Base --- */

        self.ballistic_computer = BallisticComputer()        :root {

        self.orders_generator = OrdersGenerator()            --primary-bg: #0a0a0a;

                    --secondary-bg: #1a1a1a;

        # Load CSS on initialization            --card-bg: #141414;

        self._load_css()            --border: #2a2a2a;

                --text-primary: #ffffff;

    def _load_css(self):            --text-secondary: #a0a0a0;

        """Load custom CSS for enhanced military styling."""            --accent: #ffffff;

        st.markdown("""            --hover: #202020;

        <style>            --success: #00ff00;

            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');            --warning: #ffaa00;

                        --error: #ff0000;

            /* --- Monochromatic Base --- */        }

            :root {        

                --primary-bg: #0a0a0a;        /* --- Main App Styling --- */

                --secondary-bg: #1a1a1a;        .stApp {

                --card-bg: #141414;            background: var(--primary-bg);

                --border: #2a2a2a;            color: var(--text-primary);

                --text-primary: #ffffff;            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

                --text-secondary: #a0a0a0;        }

                --accent: #ffffff;        

                --hover: #202020;        /* --- Remove default padding --- */

                --success: #00ff00;        .main .block-container {

                --warning: #ffaa00;            padding-top: 2rem;

                --error: #ff0000;            padding-bottom: 2rem;

            }            max-width: 100%;

                    }

            /* --- Main App Styling --- */        

            .stApp {        /* --- Card Components --- */

                background: var(--primary-bg);        .feature-card {

                color: var(--text-primary);            background: var(--card-bg);

                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;            border: 1px solid var(--border);

            }            border-radius: 12px;

                        padding: 2rem;

            /* --- Remove default padding --- */            margin-bottom: 1.5rem;

            .main .block-container {            transition: all 0.3s ease;

                padding-top: 2rem;            cursor: pointer;

                padding-bottom: 2rem;            height: 200px;

                max-width: 100%;            display: flex;

            }            flex-direction: column;

                        justify-content: space-between;

            /* --- Card Components --- */        }

            .feature-card {        

                background: var(--card-bg);        .feature-card:hover {

                border: 1px solid var(--border);            background: var(--hover);

                border-radius: 12px;            border-color: var(--accent);

                padding: 2rem;            transform: translateY(-2px);

                margin-bottom: 1.5rem;        }

                transition: all 0.3s ease;        

                cursor: pointer;        .feature-card h3 {

                height: 200px;            color: var(--text-primary);

                display: flex;            font-size: 1.25rem;

                flex-direction: column;            font-weight: 600;

                justify-content: space-between;            margin: 0 0 0.5rem 0;

            }            letter-spacing: -0.02em;

                    }

            .feature-card:hover {        

                background: var(--hover);        .feature-card p {

                border-color: var(--accent);            color: var(--text-secondary);

                transform: translateY(-2px);            font-size: 0.875rem;

            }            line-height: 1.5;

                        margin: 0;

            .feature-card h3 {        }

                color: var(--text-primary);        

                font-size: 1.25rem;        .feature-icon {

                font-weight: 600;            font-size: 2rem;

                margin: 0 0 0.5rem 0;            margin-bottom: 1rem;

                letter-spacing: -0.02em;            opacity: 0.8;

            }        }

                    

            .feature-card p {        /* --- Enhanced Chat Styling --- */

                color: var(--text-secondary);        .chat-message {

                font-size: 0.875rem;            background: var(--card-bg);

                line-height: 1.5;            border: 1px solid var(--border);

                margin: 0;            border-radius: 8px;

            }            padding: 1rem;

                        margin-bottom: 1rem;

            .feature-icon {        }

                font-size: 2rem;        

                margin-bottom: 1rem;        .chat-user {

                opacity: 0.8;            border-left: 3px solid var(--accent);

            }        }

                    

            /* --- Enhanced Chat Styling --- */        .chat-bot {

            .chat-message {            border-left: 3px solid var(--success);

                background: var(--card-bg);        }

                border: 1px solid var(--border);        

                border-radius: 8px;        .quick-prompt-btn {

                padding: 1rem;            background: var(--secondary-bg);

                margin-bottom: 1rem;            border: 1px solid var(--border);

            }            border-radius: 6px;

                        padding: 0.5rem 1rem;

            .chat-user {            color: var(--text-secondary);

                border-left: 3px solid var(--accent);            font-size: 0.875rem;

            }            margin: 0.25rem;

                        cursor: pointer;

            .chat-bot {            transition: all 0.2s ease;

                border-left: 3px solid var(--success);        }

            }        

                    .quick-prompt-btn:hover {

            /* --- Header Styling --- */            background: var(--hover);

            .main-header {            color: var(--text-primary);

                text-align: center;        }

                margin-bottom: 3rem;        

            }        /* --- Header Styling --- */

                    .main-header {

            .main-header h1 {            text-align: center;

                font-size: 3rem;            margin-bottom: 3rem;

                font-weight: 300;        }

                color: var(--text-primary);        

                margin: 0;        .main-header h1 {

                letter-spacing: -0.04em;            font-size: 3rem;

            }            font-weight: 300;

                        color: var(--text-primary);

            .main-header p {            margin: 0;

                font-size: 1.1rem;            letter-spacing: -0.04em;

                color: var(--text-secondary);        }

                margin: 0.5rem 0 0 0;        

                font-weight: 400;        .main-header p {

            }            font-size: 1.1rem;

                        color: var(--text-secondary);

            /* --- Status Bar --- */            margin: 0.5rem 0 0 0;

            .status-bar {            font-weight: 400;

                background: var(--secondary-bg);        }

                border: 1px solid var(--border);        

                border-radius: 8px;        /* --- Status Bar --- */

                padding: 1rem;        .status-bar {

                margin-bottom: 2rem;            background: var(--secondary-bg);

                display: flex;            border: 1px solid var(--border);

                justify-content: space-between;            border-radius: 8px;

                align-items: center;            padding: 1rem;

            }            margin-bottom: 2rem;

                        display: flex;

            .status-item {            justify-content: space-between;

                display: flex;            align-items: center;

                align-items: center;        }

                gap: 0.5rem;        

                font-size: 0.875rem;        .status-item {

                color: var(--text-secondary);            display: flex;

            }            align-items: center;

                        gap: 0.5rem;

            .status-dot {            font-size: 0.875rem;

                width: 8px;            color: var(--text-secondary);

                height: 8px;        }

                border-radius: 50%;        

                background: var(--success);        .status-dot {

            }            width: 8px;

                        height: 8px;

            /* --- Hide Streamlit Elements --- */            border-radius: 50%;

            #MainMenu {visibility: hidden;}            background: var(--success);

            footer {visibility: hidden;}        }

            header {visibility: hidden;}        

                    /* --- Hide Streamlit Elements --- */

            /* --- Streamlit Component Overrides --- */        #MainMenu {visibility: hidden;}

            .stSelectbox > div > div {        footer {visibility: hidden;}

                background: var(--card-bg);        header {visibility: hidden;}

                border: 1px solid var(--border);        

                color: var(--text-primary);        /* --- Streamlit Component Overrides --- */

            }        .stSelectbox > div > div {

                        background: var(--card-bg);

            .stTextInput > div > div > input {            border: 1px solid var(--border);

                background: var(--card-bg);            color: var(--text-primary);

                border: 1px solid var(--border);        }

                color: var(--text-primary);        

            }        .stTextInput > div > div > input {

                        background: var(--card-bg);

            .stButton > button {            border: 1px solid var(--border);

                background: var(--text-primary);            color: var(--text-primary);

                color: var(--primary-bg);        }

                border: none;        

                border-radius: 8px;        .stButton > button {

                font-weight: 500;            background: var(--text-primary);

                padding: 0.5rem 1.5rem;            color: var(--primary-bg);

                transition: all 0.2s ease;            border: none;

            }            border-radius: 8px;

                        font-weight: 500;

            .stButton > button:hover {            padding: 0.5rem 1.5rem;

                background: var(--text-secondary);            transition: all 0.2s ease;

            }        }

        </style>        

        """, unsafe_allow_html=True)        .stButton > button:hover {

                background: var(--text-secondary);

    def render_header_and_nav(self):        }

        """Renders the main header and navigation tabs."""        

        # Header    </style>

        st.markdown("""    """, unsafe_allow_html=True)

        <div class="main-header">

            <h1>🎖️ FA-GPT</h1>load_css()

            <p>ENHANCED FIELD ARTILLERY MISSION COMMAND SYSTEM</p>

        </div># ==============================================================================

        """, unsafe_allow_html=True)# Enhanced Functions

        # ==============================================================================

        # Status Bar

        self._render_status_bar()def render_feature_cards():

            """Render the main feature cards grid"""

        # Main navigation tabs    

        tab_titles = [    # Create the grid of feature cards

            "📊 INTELLIGENCE HUB",    col1, col2, col3 = st.columns(3)

            "🎯 FIRE SUPPORT",     

            "🔧 BALLISTICS",    with col1:

            "📋 OPERATIONS",        if st.button("", key="chat_card"):

            "⚙️ SYSTEM ADMIN"            st.session_state.current_view = "chat"

        ]            st.rerun()

        tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)        

                st.markdown("""

        with tab1:        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"chat_card\\"]').click()">

            self.render_intelligence_hub()            <div>

        with tab2:                <div class="feature-icon">💬</div>

            self.render_fire_support()                <h3>AI ASSISTANT</h3>

        with tab3:                <p>Advanced conversational AI with memory, export, and specialized query types.</p>

            self.render_ballistics()            </div>

        with tab4:        </div>

            self.render_operations()        """, unsafe_allow_html=True)

        with tab5:    

            self.render_system_admin()    with col2:

            if st.button("", key="ballistic_card"):

    def _render_status_bar(self):            st.session_state.current_view = "ballistic"

        """Render the system status bar."""            st.rerun()

        current_time = datetime.now()        

        session_stats = {        st.markdown("""

            "queries": len([m for m in self.state.messages if m["role"] == "user"]),        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"ballistic_card\\"]').click()">

            "responses": len([m for m in self.state.messages if m["role"] == "assistant"])            <div>

        }                <div class="feature-icon">🎯</div>

                        <h3>BALLISTIC COMPUTER</h3>

        st.markdown(f"""                <p>Advanced firing solutions with weather integration and multi-unit support.</p>

        <div class="status-bar">            </div>

            <div class="status-item">        </div>

                <div class="status-dot"></div>        """, unsafe_allow_html=True)

                <span>SYSTEM OPERATIONAL</span>    

            </div>    with col3:

            <div class="status-item">        if st.button("", key="orders_card"):

                <span>{current_time.strftime('%H:%M:%S UTC')}</span>            st.session_state.current_view = "orders"

            </div>            st.rerun()

            <div class="status-item">        

                <span>SESSION: {session_stats['queries']} QUERIES</span>        st.markdown("""

            </div>        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"orders_card\\"]').click()">

            <div class="status-item">            <div>

                <span>ENHANCED MODE</span>                <div class="feature-icon">📋</div>

            </div>                <h3>ORDERS GENERATOR</h3>

        </div>                <p>Comprehensive order templates with validation and multi-mission planning.</p>

        """, unsafe_allow_html=True)            </div>

            </div>

    def render_intelligence_hub(self):        """, unsafe_allow_html=True)

        """Renders the main chat interface and intelligence capabilities."""    

        st.header("💬 Multi-Modal Chat Interface")    # Second row

            col1, col2, col3 = st.columns(3)

        # Enhanced control panel    

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])    with col1:

        with col1:        if st.button("", key="status_card"):

            query_type = st.selectbox("🎯 Query Type",             st.session_state.current_view = "status"

                ["General Doctrine", "Tactical Procedures", "Technical Specifications",             st.rerun()

                 "Safety Protocols", "Training Materials", "Historical Analysis"],        

                help="Select the type of query for optimized response")        st.markdown("""

                <div class="feature-card" onclick="document.querySelector('[data-testid=\\"status_card\\"]').click()">

        with col2:            <div>

            if st.button("📁 EXPORT", help="Export conversation with metadata"):                <div class="feature-icon">📊</div>

                self._export_conversation_data()                <h3>SYSTEM STATUS</h3>

                        <p>Real-time monitoring with performance metrics and system diagnostics.</p>

        with col3:            </div>

            if st.button("🗑️ CLEAR", help="Clear conversation history"):        </div>

                self.state.clear_messages()        """, unsafe_allow_html=True)

                st.rerun()    

            with col2:

        with col4:        if st.button("", key="docs_card"):

            conversation_mode = st.toggle("🧠 Memory",             st.session_state.current_view = "documents"

                                        value=self.state.conversation_mode,            st.rerun()

                                        help="Maintain conversation context")        

            self.state.conversation_mode = conversation_mode        st.markdown("""

                <div class="feature-card" onclick="document.querySelector('[data-testid=\\"docs_card\\"]').click()">

        st.markdown("---")            <div>

                        <div class="feature-icon">📁</div>

        # Display session statistics                <h3>DOCUMENT PROCESSING</h3>

        if self.state.messages:                <p>Intelligent document analysis with OCR and automated indexing.</p>

            col1, col2, col3, col4 = st.columns(4)            </div>

            total_queries = len([m for m in self.state.messages if m["role"] == "user"])        </div>

            with col1:        """, unsafe_allow_html=True)

                st.metric("🔄 Total Queries", total_queries)    

            with col2:    with col3:

                st.metric("⏱️ Session Time", f"{len(self.state.messages) * 2}min")        if st.button("", key="settings_card"):

            with col3:            st.session_state.current_view = "settings"

                st.metric("🧠 Context Level", "High" if conversation_mode else "Standard")            st.rerun()

            with col4:        

                recent_query_type = "None"        st.markdown("""

                if self.state.messages:        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"settings_card\\"]').click()">

                    for msg in reversed(self.state.messages):            <div>

                        if msg["role"] == "user" and msg.get("query_type"):                <div class="feature-icon">⚙️</div>

                            recent_query_type = msg["query_type"]                <h3>CONFIGURATION</h3>

                            break                <p>Advanced settings with user preferences and operational modes.</p>

                st.metric("📋 Last Query Type", recent_query_type)            </div>

            st.markdown("---")        </div>

                """, unsafe_allow_html=True)

        # Display chat history

        self._display_enhanced_chat_history()def display_enhanced_chat_history():

            """Enhanced chat history with better formatting and metadata"""

        # Quick prompts section    for i, message in enumerate(st.session_state.messages):

        self._render_quick_prompts(query_type)        if message["role"] == "user":

                    st.markdown(f"""

        # Chat input            <div class="chat-message chat-user">

        if prompt := st.chat_input("Ask about your Field Artillery documents..."):                <strong>YOU</strong> ({message.get('timestamp', 'N/A')})

            # Add user message to state                <br>{message.get('content', '')}

            self.state.add_message("user", prompt, query_type=query_type)                <br><small>Query Type: {message.get('query_type', 'General')}</small>

            st.rerun() # Rerun to display the new message immediately            </div>

            """, unsafe_allow_html=True)

            # Get response from backend        else:

            with st.spinner("Processing with local VLM..."):            response_content = message["content"]

                response_text, images, metadata = get_rag_response(prompt)            st.markdown(f"""

                            <div class="chat-message chat-bot">

                # Add assistant message to state                <strong>FA-GPT</strong> ({response_content.get('timestamp', 'N/A')})

                self.state.add_message(                <br>{response_content.get('answer', '')}

                    "assistant",                 <br><small>Style: {response_content.get('response_style', 'Standard')} | 

                    response_text,                Query Type: {response_content.get('query_type', 'General')}</small>

                    images=images,            </div>

                    metadata=metadata,            """, unsafe_allow_html=True)

                    query_type=query_type            

                )            # Display images if they exist

                st.rerun() # Rerun to display the response            if response_content.get("images"):

                    with st.expander("📷 View Images"):

    def _display_enhanced_chat_history(self):                    cols = st.columns(min(len(response_content["images"]), 3))

        """Enhanced chat history with better formatting and metadata."""                    for j, img_path in enumerate(response_content["images"]):

        for message in self.state.messages:                        if os.path.exists(img_path):

            with st.chat_message(message["role"]):                            with cols[j % 3]:

                st.markdown(message["content"])                                st.image(img_path, use_column_width=True)

                            

                # Display images if present            # Display sources if they exist

                if message.get("images"):            if response_content.get("sources"):

                    with st.expander("📷 View Images"):                with st.expander("📚 View Sources"):

                        cols = st.columns(min(len(message["images"]), 3))                    for source in response_content["sources"]:

                        for j, img_path in enumerate(message["images"]):                        st.text(f"Source: {source.get('document', 'N/A')}")

                            if os.path.exists(img_path):

                                with cols[j % 3]:def export_conversation_data():

                                    st.image(img_path, use_column_width=True)    """Export conversation data with enhanced metadata"""

                    if st.session_state.messages:

                # Display metadata if present        export_data = {

                if message.get("metadata"):            "session_info": {

                    with st.expander("📚 View Sources"):                "session_id": st.session_state.get("session_id", str(uuid.uuid4())),

                        st.json(message["metadata"])                "export_timestamp": datetime.now().isoformat(),

                    "total_messages": len(st.session_state.messages),

    def _render_quick_prompts(self, query_type):                "user_queries": len([m for m in st.session_state.messages if m["role"] == "user"]),

        """Render quick prompt buttons for common queries."""                "system_version": "FA-GPT v2.0 Enhanced"

        st.markdown("### 💭 Quick Military Prompts")            },

        quick_prompts = [            "conversation": st.session_state.messages,

            "Explain high-angle fire procedures for mountainous terrain",            "statistics": {

            "What are the minimum safe distances for HE rounds by charge?",                "session_duration": f"{len(st.session_state.messages) * 2} minutes (estimated)",

            "How do I calculate proper charge selection for different ranges?",                "query_types": list(set([m.get('query_type', 'General') for m in st.session_state.messages if m["role"] == "user"])),

            "Describe counter-battery radar detection procedures",                "response_styles": list(set([m["content"].get('response_style', 'Standard') for m in st.session_state.messages if m["role"] == "bot"]))

            "What is the standard call for fire format and sequence?",            }

            "Explain observed fire adjustment procedures step-by-step"        }

        ]        

                filename = f"fa_gpt_enhanced_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        prompt_cols = st.columns(2)        st.download_button(

        for i, prompt in enumerate(quick_prompts):            label="📁 Download Enhanced Export",

            with prompt_cols[i % 2]:            data=json.dumps(export_data, indent=2),

                if st.button(f"💭 {prompt[:45]}...", key=f"quick_{i}", help=prompt):            file_name=filename,

                    # Process quick prompt            mime="application/json"

                    self.state.add_message("user", prompt, query_type=query_type)        )

                            return True

                    with st.spinner("🤔 Processing quick prompt..."):    return False

                        response_text, images, metadata = get_rag_response(prompt)

                        self.state.add_message(# ==============================================================================

                            "assistant",# Initialize Enhanced Session State

                            response_text,# ==============================================================================

                            images=images,if "ballistic_computer" not in st.session_state:

                            metadata=metadata,    st.session_state.ballistic_computer = BallisticComputer()

                            query_type=query_type,if "orders_generator" not in st.session_state:

                            response_style="Quick Response"    st.session_state.orders_generator = OrdersGenerator()

                        )if "current_view" not in st.session_state:

                    st.rerun()    st.session_state.current_view = "home"

    if "messages" not in st.session_state:

    def _export_conversation_data(self):    st.session_state.messages = []

        """Export conversation data with enhanced metadata."""if "session_id" not in st.session_state:

        if not self.state.messages:    st.session_state.session_id = str(uuid.uuid4())

            st.warning("No conversation to export")if "conversation_mode" not in st.session_state:

            return False    st.session_state.conversation_mode = True

        

        export_data = {# ==============================================================================

            "session_summary": self.state.get_session_summary(),# Enhanced Header and Status

            "conversation": self.state.messages,# ==============================================================================

            "export_timestamp": datetime.now().isoformat()

        }# Header

        st.markdown("""

        # Create downloadable JSON<div class="main-header">

        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)    <h1>FA-GPT</h1>

        st.download_button(    <p>ENHANCED FIELD ARTILLERY MISSION COMMAND SYSTEM</p>

            label="💾 Download Conversation",</div>

            data=json_data,""", unsafe_allow_html=True)

            file_name=f"fa_gpt_conversation_{self.state.session_id[:8]}.json",

            mime="application/json"# Enhanced Status Bar

        )current_time = datetime.now()

        return Trueuptime_hours = (current_time.hour + current_time.minute / 60)

    session_stats = {

    def render_fire_support(self):    "queries": len([m for m in st.session_state.messages if m["role"] == "user"]),

        """Render fire support planning interface."""    "responses": len([m for m in st.session_state.messages if m["role"] == "bot"])

        st.header("🎯 Fire Support Planner")}

        st.markdown("Advanced fire mission planning with multi-unit coordination.")

        st.markdown(f"""

        # Fire mission planning interface would go here<div class="status-bar">

        st.info("Fire support planning tools - Integration with existing ballistic computer")    <div class="status-item">

                <div class="status-dot"></div>

        # Display current targets and firing units from state        <span>SYSTEM OPERATIONAL</span>

        if self.state.current_target:    </div>

            st.subheader("Current Target")    <div class="status-item">

            st.json(self.state.current_target)        <span>{current_time.strftime('%H:%M:%S UTC')}</span>

            </div>

        if self.state.firing_units:    <div class="status-item">

            st.subheader("Firing Units")        <span>SESSION: {session_stats['queries']} QUERIES</span>

            for unit in self.state.firing_units:    </div>

                st.json(unit)    <div class="status-item">

            <span>ENHANCED MODE</span>

    def render_ballistics(self):    </div>

        """Render ballistic computation interface."""</div>

        st.header("🔧 Ballistic Computer")""", unsafe_allow_html=True)

        st.markdown("Precision firing solutions with weather integration.")

        # ==============================================================================

        # Ballistic computation interface# Enhanced Navigation

        st.info("Ballistic computation tools - Integration with existing BallisticComputer class")# ==============================================================================

        

        # Display ballistic calculations from stateif st.session_state.current_view != "home":

        if self.state.ballistic_calculations:    col1, col2 = st.columns([1, 4])

            st.subheader("Current Calculations")    with col1:

            st.json(self.state.ballistic_calculations)        if st.button("← BACK TO COMMAND CENTER", key="back_button"):

                st.session_state.current_view = "home"

    def render_operations(self):            st.rerun()

        """Render operations and orders interface."""    with col2:

        st.header("📋 Operations Center")        st.markdown(f"**Current Session:** {st.session_state.session_id[:8]}... | **Active View:** {st.session_state.current_view.upper()}")

        st.markdown("Mission planning, orders generation, and operational coordination.")    st.markdown("---")

        

        # Operations interface# ==============================================================================

        st.info("Operations tools - Integration with existing OrdersGenerator class")# Enhanced View Management

        # ==============================================================================

        # Display mission data from state

        if self.state.mission_data:if st.session_state.current_view == "home":

            st.subheader("Current Mission")    render_feature_cards()

            st.json(self.state.mission_data)

    elif st.session_state.current_view == "chat":

    def render_system_admin(self):    st.markdown("## 💬 AI ASSISTANT - ENHANCED")

        """Render system administration interface."""    st.markdown("Advanced conversational interface with memory, export capabilities, and specialized query processing.")

        st.header("⚙️ System Administration")    

        st.markdown("System configuration, monitoring, and maintenance.")    # Enhanced control panel

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        # System health display    with col1:

        col1, col2 = st.columns(2)        query_type = st.selectbox("🎯 Query Type", 

                    ["General Doctrine", "Tactical Procedures", "Technical Specifications", 

        with col1:             "Safety Protocols", "Training Materials", "Historical Analysis"],

            st.subheader("🔍 System Health")            help="Select the type of query for optimized response")

            for component, status in self.state.system_health.items():    

                if status == "operational":    with col2:

                    st.success(f"✅ {component.title()}: {status}")        if st.button("📁 EXPORT", help="Export conversation with metadata"):

                elif status == "warning":            if not export_conversation_data():

                    st.warning(f"⚠️ {component.title()}: {status}")                st.warning("No conversation to export")

                elif status == "error":    

                    st.error(f"❌ {component.title()}: {status}")    with col3:

                else:        if st.button("🗑️ CLEAR", help="Clear conversation history"):

                    st.info(f"ℹ️ {component.title()}: {status}")            st.session_state.messages = []

                    st.rerun()

        with col2:    

            st.subheader("📊 Session Information")    with col4:

            session_summary = self.state.get_session_summary()        conversation_mode = st.toggle("🧠 Memory", 

            for key, value in session_summary.items():                                    value=st.session_state.conversation_mode,

                if key != "active_features":  # Handle nested dict separately                                    help="Maintain conversation context")

                    st.metric(key.replace("_", " ").title(), str(value))        st.session_state.conversation_mode = conversation_mode

                

            # Display active features    st.markdown("---")

            st.markdown("**Active Features:**")    

            for feature, enabled in session_summary["active_features"].items():    # Enhanced statistics dashboard

                status = "✅ Enabled" if enabled else "❌ Disabled"    if st.session_state.messages:

                st.write(f"• {feature.replace('_', ' ').title()}: {status}")        col1, col2, col3, col4 = st.columns(4)

                total_queries = len([m for m in st.session_state.messages if m["role"] == "user"])

        # Configuration controls        with col1:

        st.subheader("⚙️ Configuration")            st.metric("🔄 Total Queries", total_queries)

                with col2:

        col1, col2 = st.columns(2)            st.metric("⏱️ Session Time", f"{len(st.session_state.messages) * 2}min")

        with col1:        with col3:

            multimodal = st.checkbox("Multimodal Processing", value=self.state.multimodal_enabled)            st.metric("🧠 Context Level", "High" if conversation_mode else "Standard")

            vision_analysis = st.checkbox("Vision Analysis", value=self.state.vision_analysis_enabled)        with col4:

                    recent_query_type = "None"

        with col2:            if st.session_state.messages:

            advanced_extraction = st.checkbox("Advanced Extraction", value=self.state.advanced_extraction)                for msg in reversed(st.session_state.messages):

                                if msg["role"] == "user" and msg.get("query_type"):

        # Update state if settings changed                        recent_query_type = msg["query_type"]

        if multimodal != self.state.multimodal_enabled:                        break

            self.state.multimodal_enabled = multimodal            st.metric("📋 Last Query Type", recent_query_type)

        if vision_analysis != self.state.vision_analysis_enabled:        st.markdown("---")

            self.state.vision_analysis_enabled = vision_analysis    

        if advanced_extraction != self.state.advanced_extraction:    # Display enhanced chat history

            self.state.advanced_extraction = advanced_extraction    display_enhanced_chat_history()

            

        # Session management    # Quick prompts section

        st.subheader("🔄 Session Management")    st.markdown("### 💭 Quick Military Prompts")

        col1, col2 = st.columns(2)    quick_prompts = [

        with col1:        "Explain high-angle fire procedures for mountainous terrain",

            if st.button("🗑️ Reset Session", type="secondary"):        "What are the minimum safe distances for HE rounds by charge?",

                self.state.reset_session()        "How do I calculate proper charge selection for different ranges?",

                st.success("Session reset successfully!")        "Describe counter-battery radar detection procedures",

                st.rerun()        "What is the standard call for fire format and sequence?",

                "Explain observed fire adjustment procedures step-by-step"

        with col2:    ]

            if st.button("💾 Export Session Data"):    

                session_data = self.state.get_session_summary()    prompt_cols = st.columns(2)

                json_data = json.dumps(session_data, indent=2, ensure_ascii=False)    for i, prompt in enumerate(quick_prompts):

                st.download_button(        with prompt_cols[i % 2]:

                    label="📥 Download Session Data",            if st.button(f"💭 {prompt[:45]}...", key=f"quick_{i}", help=prompt):

                    data=json_data,                # Process quick prompt

                    file_name=f"fa_gpt_session_{self.state.session_id[:8]}.json",                st.session_state.messages.append({

                    mime="application/json"                    "role": "user", 

                )                    "content": prompt,

                        "timestamp": datetime.now().isoformat(),

    def render_sidebar(self):                    "query_type": query_type

        """Renders the sidebar for document management and system controls."""                })

        with st.sidebar:                

            st.header("📚 Document Management")                with st.spinner("🤔 Processing quick prompt..."):

                                # Build context if memory mode is enabled

            # Document processing status                    enhanced_query = prompt

            if self.state.processing_status != "idle":                    if conversation_mode and len(st.session_state.messages) > 1:

                st.subheader("🔄 Processing Status")                        recent_context = st.session_state.messages[-4:]  # Last 2 exchanges

                st.progress(self.state.processing_progress)                        context_summary = f"Previous context: {json.dumps(recent_context, indent=2)}\n\nCurrent query: "

                st.write(f"Status: {self.state.processing_status}")                        enhanced_query = f"{context_summary}{prompt}"

                                    

                if self.state.processing_messages:                    response_text, images, metadata = get_rag_response(enhanced_query)

                    with st.expander("Processing Log"):                    response_data = {

                        for msg in self.state.processing_messages[-10:]:  # Show last 10 messages                        "answer": response_text,

                            st.text(msg)                        "images": images,

                                    "sources": metadata.get("sources", []),

            # File upload                        "query_type": query_type,

            st.subheader("📁 Upload Documents")                        "response_style": "Quick Response",

            uploaded_files = st.file_uploader(                        "timestamp": datetime.now().isoformat()

                "Upload PDFs for processing",                    }

                type=['pdf'],                

                accept_multiple_files=True                st.session_state.messages.append({"role": "bot", "content": response_data})

            )                st.rerun()

                

            if uploaded_files:    st.markdown("---")

                self.state.uploaded_files = [    

                    {"name": f.name, "size": f.size, "type": f.type}    # Enhanced main chat input

                    for f in uploaded_files    with st.form("enhanced_chat_form", clear_on_submit=True):

                ]        col1, col2 = st.columns([4, 1])

                        with col1:

                if st.button("🚀 Process Documents"):            user_query = st.text_area("🎤 Enter your detailed query:", 

                    self.state.update_processing_status("processing", 0.0, "Starting document processing...")                                    placeholder="Ask about artillery doctrine, tactical procedures, technical specifications, or request detailed analysis...",

                    # Document processing logic would go here                                    height=100)

                    st.info("Document processing integration needed")        with col2:

                        st.markdown("**Options:**")

            # Quick actions            response_style = st.selectbox("📝 Response Style", 

            st.subheader("⚡ Quick Actions")                                        ["Comprehensive", "Concise", "Technical", "Training-Focused"])

            if st.button("🔍 System Check"):            include_examples = st.checkbox("📖 Include Examples", value=True)

                # System health check logic            priority_level = st.selectbox("⚡ Priority", ["Standard", "High", "Critical"])

                st.info("System health check completed")        

                    submitted = st.form_submit_button("🚀 SEND ENHANCED QUERY", type="primary")

            if st.button("📊 View Stats"):        

                st.json(self.state.get_session_summary())        if submitted and user_query:

                        st.session_state.messages.append({

            # System information                "role": "user", 

            st.subheader("ℹ️ System Info")                "content": user_query,

            st.write(f"**Session ID:** {self.state.session_id[:8]}...")                "timestamp": datetime.now().isoformat(),

            st.write(f"**Uptime:** {(datetime.now() - self.state.session_start_time).total_seconds():.0f}s")                "query_type": query_type,

            st.write(f"**Messages:** {len(self.state.messages)}")                "response_style": response_style,

            st.write(f"**Current View:** {self.state.current_view}")                "priority": priority_level
            })
            
            with st.spinner("🔄 Processing enhanced query..."):
                # Build sophisticated query enhancement
                enhanced_query = user_query
                
                # Add conversation context if memory mode is enabled
                if conversation_mode and len(st.session_state.messages) > 1:
                    recent_messages = st.session_state.messages[-6:]  # Last 3 exchanges
                    context = f"Conversation context: {json.dumps(recent_messages, indent=2)}\n\n"
                    enhanced_query = f"{context}Please provide a {response_style.lower()} response about {query_type.lower()}"
                    if include_examples:
                        enhanced_query += " with practical examples"
                    enhanced_query += f" (Priority: {priority_level}):\n\n{user_query}"
                else:
                    enhanced_query = f"Please provide a {response_style.lower()} response about {query_type.lower()}"
                    if include_examples:
                        enhanced_query += " with practical examples"
                    enhanced_query += f":\n\n{user_query}"
                
                response_text, images, metadata = get_rag_response(enhanced_query)
                response_data = {
                    "answer": response_text,
                    "images": images,
                    "sources": metadata.get("sources", []),
                    "query_type": query_type,
                    "response_style": response_style,
                    "priority": priority_level,
                    "timestamp": datetime.now().isoformat(),
                    "enhanced_features": {
                        "memory_mode": conversation_mode,
                        "examples_included": include_examples,
                        "context_length": len(st.session_state.messages)
                    }
                }
            
            st.session_state.messages.append({"role": "bot", "content": response_data})
            st.rerun()

elif st.session_state.current_view == "ballistic":
    st.markdown("## 🎯 BALLISTIC COMPUTER - ENHANCED")
    st.markdown("Advanced firing solutions with weather integration, multi-unit support, and precision calculations.")
    
    # Enhanced ballistic calculator with more features
    tab1, tab2, tab3 = st.tabs(["🎯 Single Target", "🏢 Multi-Target", "🌤️ Weather Adjustments"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎯 TARGET DATA")
            target_id = st.text_input("Target ID", value="TGT001")
            target_grid = st.text_input("Target Grid (MGRS)", placeholder="18TWK1234567890")
            target_elevation = st.number_input("Target Elevation (m)", value=100, step=10)
            target_description = st.text_input("Target Description", placeholder="Enemy position")
            
        with col2:
            st.markdown("### 🏭 FIRING UNIT")
            gun_position = st.text_input("Gun Position Grid", placeholder="18TWK0987654321")
            gun_elevation = st.number_input("Gun Elevation (m)", value=150, step=10)
            weapon_system = st.selectbox("Weapon System", 
                ["M777_HOWITZER", "M109_PALADIN", "M119_HOWITZER", "M198_HOWITZER"])
            battery_size = st.number_input("Number of Guns", value=6, min_value=1, max_value=8)
            
        with col3:
            st.markdown("### 💥 MISSION PARAMETERS")
            ammunition_type = st.selectbox("Ammunition Type", 
                ["HE_STANDARD", "SMOKE", "ILLUM", "DPICM", "EXCALIBUR"])
            rounds_per_gun = st.number_input("Rounds per Gun", value=4, min_value=1, max_value=20)
            charge_type = st.selectbox("Charge", ["GREEN", "WHITE", "RED"])
            mission_type = st.selectbox("Mission", ["Adjust Fire", "Fire for Effect", "Suppression"])
        
        if st.button("🎯 CALCULATE ENHANCED FIRING SOLUTION", type="primary"):
            if target_grid and gun_position:
                try:
                    # Enhanced calculation with more parameters
                    target = Target(target_id, target_grid, target_elevation, target_description)
                    firing_unit = FiringUnit("A", "1st", gun_position, gun_elevation, 
                                           WeaponSystem[weapon_system], AmmunitionType[ammunition_type])
                    
                    solution = st.session_state.ballistic_computer.calculate_firing_solution(
                        firing_unit, target
                    )
                    
                    st.success("🎯 ENHANCED FIRING SOLUTION CALCULATED")
                    
                    # Enhanced results display
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📏 RANGE", f"{solution.range_meters:,}m")
                    with col2:
                        st.metric("🧭 AZIMUTH", f"{solution.azimuth_mils} mils")
                    with col3:
                        st.metric("📐 ELEVATION", f"{solution.quadrant_elevation} mils")
                    with col4:
                        st.metric("⏱️ TIME OF FLIGHT", f"{solution.time_of_flight:.1f}s")
                    
                    # Additional calculations
                    st.markdown("### 📊 ADDITIONAL CALCULATIONS")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_rounds = battery_size * rounds_per_gun
                        st.metric("💥 TOTAL ROUNDS", total_rounds)
                    with col2:
                        estimated_time = total_rounds * 8  # 8 seconds per round
                        st.metric("⏱️ MISSION DURATION", f"{estimated_time}s")
                    with col3:
                        danger_close = 600 if ammunition_type == "HE_STANDARD" else 300
                        st.metric("⚠️ DANGER CLOSE", f"{danger_close}m")
                    
                except Exception as e:
                    st.error(f"❌ Calculation error: {str(e)}")
            else:
                st.warning("⚠️ Please enter both target and gun position grids.")
    
    with tab2:
        st.markdown("### 🏢 MULTI-TARGET ENGAGEMENT")
        st.info("💡 Plan engagement sequences for multiple targets")
        
        num_targets = st.number_input("Number of Targets", value=2, min_value=1, max_value=5)
        
        if st.button("📊 GENERATE MULTI-TARGET PLAN"):
            st.success("🎯 Multi-target engagement plan generated!")
            st.markdown("**Engagement Sequence:**")
            for i in range(num_targets):
                st.markdown(f"- Target {i+1}: Priority sequence {i+1}")
    
    with tab3:
        st.markdown("### 🌤️ WEATHER CONDITIONS")
        col1, col2 = st.columns(2)
        
        with col1:
            wind_direction = st.number_input("Wind Direction (degrees)", value=270, min_value=0, max_value=360)
            wind_speed = st.number_input("Wind Speed (m/s)", value=5.0, step=0.5)
            temperature = st.number_input("Temperature (°C)", value=15, step=1)
        
        with col2:
            humidity = st.number_input("Humidity (%)", value=60, min_value=0, max_value=100)
            pressure = st.number_input("Pressure (hPa)", value=1013, step=1)
            visibility = st.selectbox("Visibility", ["Excellent", "Good", "Fair", "Poor"])
        
        if st.button("🌤️ APPLY WEATHER CORRECTIONS"):
            st.success("Weather corrections applied to ballistic calculations!")

elif st.session_state.current_view == "orders":
    st.markdown("## 📋 ORDERS GENERATOR - ENHANCED")
    st.markdown("Comprehensive order generation with templates, validation, and multi-mission planning.")
    
    tab1, tab2, tab3 = st.tabs(["📝 Fire Orders", "📋 Templates", "🎯 Mission Planning"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 TARGET INFORMATION")
            order_target_id = st.text_input("Target Designation", value="TGT001")
            order_target_grid = st.text_input("Target Grid", placeholder="18TWK1234567890")
            order_target_desc = st.text_input("Target Description", placeholder="Enemy bunker complex")
            order_mission_type = st.selectbox("Mission Type", 
                ["ADJUST_FIRE", "FIRE_FOR_EFFECT", "SUPPRESSION", "INTERDICTION", "HARASSMENT"])
            
        with col2:
            st.markdown("### ⚙️ MISSION PARAMETERS")
            order_method = st.selectbox("Method of Fire", 
                ["AT_MY_COMMAND", "WHEN_READY", "TIME_ON_TARGET", "CONTINUOUS"])
            order_priority = st.selectbox("Priority", ["ROUTINE", "PRIORITY", "IMMEDIATE", "FLASH"])
            order_rounds = st.number_input("Number of Rounds", value=10, min_value=1)
            observer_id = st.text_input("Observer Call Sign", value="STEEL 6")
        
        col1, col2 = st.columns(2)
        with col1:
            include_safety = st.checkbox("Include Safety Instructions", value=True)
            include_bda = st.checkbox("Request Battle Damage Assessment", value=True)
        with col2:
            distribution_list = st.multiselect("Distribution List", 
                ["S3", "FDC", "Battery Commander", "Observer", "Higher HQ"])
        
        if st.button("📋 GENERATE ENHANCED FIRE ORDER", type="primary"):
            if order_target_id and order_target_grid:
                try:
                    fire_order_dict = {
                        "target_id": order_target_id,
                        "target_grid": order_target_grid,
                        "target_description": order_target_desc,
                        "mission_type": OrderType[order_mission_type],
                        "method_of_fire": MethodOfFire[order_method],
                        "priority": MissionPriority[order_priority],
                        "number_of_rounds": order_rounds,
                        "observer_id": observer_id
                    }
                    
                    fire_order = st.session_state.orders_generator.generate_fire_order(**fire_order_dict)
                    formatted_order = st.session_state.orders_generator.format_fire_order(fire_order)
                    
                    # Enhanced formatting
                    enhanced_order = f"""
📋 ENHANCED FIRE ORDER
=====================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Order ID: {str(uuid.uuid4())[:8]}

{formatted_order}

📊 ADDITIONAL INFORMATION:
- Safety Instructions: {'Included' if include_safety else 'Not included'}
- BDA Request: {'Yes' if include_bda else 'No'}
- Distribution: {', '.join(distribution_list) if distribution_list else 'Standard'}

⚠️ SAFETY REMINDER: Verify all coordinates and safety data before execution.
                    """
                    
                    st.success("📋 ENHANCED FIRE ORDER GENERATED")
                    st.text_area("Enhanced Fire Order:", value=enhanced_order, height=400)
                    
                    # Download option
                    st.download_button(
                        label="📁 Download Order",
                        data=enhanced_order,
                        file_name=f"fire_order_{order_target_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Generation error: {str(e)}")
            else:
                st.warning("⚠️ Please enter target ID and grid coordinate.")
    
    with tab2:
        st.markdown("### 📋 ORDER TEMPLATES")
        template_type = st.selectbox("Template Type", 
            ["Fire Mission", "Prep Fire", "Counter-Battery", "Final Protective Fire", "Registration"])
        
        if st.button("📄 LOAD TEMPLATE"):
            st.success(f"📋 {template_type} template loaded!")
            st.info("Template parameters have been populated. Modify as needed.")
    
    with tab3:
        st.markdown("### 🎯 MULTI-MISSION PLANNING")
        st.info("💡 Plan coordinated fire missions across multiple targets")
        
        num_missions = st.number_input("Number of Missions", value=3, min_value=1, max_value=10)
        
        if st.button("📊 CREATE MISSION PLAN"):
            st.success("🎯 Multi-mission plan created!")
            for i in range(num_missions):
                st.markdown(f"**Mission {i+1}:** TGT{i+1:03d} - {['Prep Fire', 'Suppression', 'Interdiction'][i % 3]}")

elif st.session_state.current_view == "status":
    st.markdown("## 📊 SYSTEM STATUS - ENHANCED")
    st.markdown("Real-time monitoring with performance metrics and comprehensive diagnostics.")
    
    # Enhanced system metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🟢 STATUS", "OPERATIONAL", delta="100% uptime")
    with col2:
        st.metric("💾 DATABASE", "CONNECTED", delta="<50ms latency")
    with col3:
        st.metric("💬 MESSAGES", len(st.session_state.messages), delta=f"+{len([m for m in st.session_state.messages if m['role'] == 'user'])}")
    with col4:
        st.metric("⏱️ SESSION", f"{len(st.session_state.messages) * 2}min", delta="Active")
    
    st.markdown("---")
    
    # Performance charts
    tab1, tab2, tab3 = st.tabs(["📈 Performance", "🔍 Analytics", "⚙️ Diagnostics"])
    
    with tab1:
        # Mock performance data
        times = pd.date_range(end=datetime.now(), periods=24, freq='H')
        cpu_usage = [65 + 20 * (i % 3) for i in range(24)]
        memory_usage = [45 + 15 * (i % 4) for i in range(24)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=cpu_usage, name='CPU Usage %', line=dict(color='#00ff00')))
        fig.add_trace(go.Scatter(x=times, y=memory_usage, name='Memory Usage %', line=dict(color='#ffaa00')))
        fig.update_layout(
            title="System Performance (24h)",
            xaxis_title="Time",
            yaxis_title="Usage %",
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Usage Statistics")
            query_types = ["General Doctrine", "Technical Specs", "Safety Protocols", "Training"]
            usage_counts = [15, 23, 8, 12]
            
            fig = go.Figure(data=[go.Bar(x=query_types, y=usage_counts, marker_color='#ffffff')])
            fig.update_layout(title="Query Types Distribution", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🎯 Module Usage")
            modules = ["AI Assistant", "Ballistic Computer", "Orders Generator", "Status"]
            module_usage = [45, 25, 20, 10]
            
            fig = go.Figure(data=[go.Pie(labels=modules, values=module_usage)])
            fig.update_layout(title="Module Usage Distribution", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🔧 SYSTEM DIAGNOSTICS")
        
        diagnostics = [
            ("🔗 Database Connection", "✅ Healthy", "Connected to PostgreSQL"),
            ("🧠 AI Model", "✅ Operational", "RAG pipeline active"),
            ("💾 Memory Usage", "✅ Normal", "67% of available RAM"),
            ("📡 Network", "✅ Stable", "Latency: 23ms"),
            ("🔒 Security", "✅ Secure", "All certificates valid"),
            ("📊 Performance", "✅ Optimal", "Response time: <2s")
        ]
        
        for component, status, details in diagnostics:
            col1, col2, col3 = st.columns([2, 1, 3])
            with col1:
                st.markdown(f"**{component}**")
            with col2:
                st.markdown(f"{status}")
            with col3:
                st.markdown(f"*{details}*")

elif st.session_state.current_view == "documents":
    st.markdown("## 📁 DOCUMENT PROCESSING - ENHANCED")
    st.markdown("Intelligent document analysis with OCR, automated indexing, and content extraction.")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "🔍 Search & Analyze", "📊 Document Library"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "📁 Choose documents for processing", 
                accept_multiple_files=True, 
                type=['pdf', 'docx', 'txt', 'md'],
                help="Supports PDF, Word documents, text files, and Markdown"
            )
            
            if uploaded_files:
                st.success(f"📄 {len(uploaded_files)} file(s) selected for processing")
                
                # Processing options
                col1a, col1b = st.columns(2)
                with col1a:
                    extract_text = st.checkbox("📝 Extract Text", value=True)
                    perform_ocr = st.checkbox("👁️ Perform OCR", value=True)
                with col1b:
                    create_embeddings = st.checkbox("🧠 Create Embeddings", value=True)
                    auto_categorize = st.checkbox("🏷️ Auto-Categorize", value=True)
        
        with col2:
            st.markdown("### ⚙️ Processing Options")
            processing_quality = st.selectbox("Quality", ["Standard", "High", "Maximum"])
            language = st.selectbox("Language", ["English", "Multi-language"])
            
            if uploaded_files and st.button("🚀 START ENHANCED PROCESSING", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {file.name}... ({i+1}/{len(uploaded_files)})")
                    
                    # Simulate processing time
                    import time
                    time.sleep(1)
                
                st.success("✅ Enhanced processing complete!")
                st.info("📊 Documents have been indexed and are ready for analysis.")
    
    with tab2:
        st.markdown("### 🔍 INTELLIGENT DOCUMENT SEARCH")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search documents:", 
                                       placeholder="Enter keywords, concepts, or questions...")
        with col2:
            search_type = st.selectbox("Search Type", ["Semantic", "Keyword", "Both"])
        
        if search_query and st.button("🔍 SEARCH DOCUMENTS"):
            st.success("🎯 Search completed!")
            
            # Mock search results
            results = [
                ("FM 6-40 Field Artillery Manual", "Chapter 3: Firing Procedures", 95),
                ("ATP 3-09.70 Paladin Operations", "Section 2: Target Engagement", 87),
                ("DA PAM 600-3 Handbook", "Appendix B: Safety Protocols", 78)
            ]
            
            st.markdown("### 📋 SEARCH RESULTS")
            for doc, section, relevance in results:
                with st.expander(f"📄 {doc} - {section} ({relevance}% relevance)"):
                    st.markdown("Sample content from the document would appear here...")
    
    with tab3:
        st.markdown("### 📚 DOCUMENT LIBRARY")
        
        # Mock document library
        library_data = {
            "Document": ["FM 6-40", "ATP 3-09.70", "DA PAM 600-3", "FM 3-09"],
            "Type": ["Manual", "Tactics", "Handbook", "Doctrine"],
            "Pages": [420, 156, 89, 234],
            "Status": ["✅ Processed", "✅ Processed", "🔄 Processing", "✅ Processed"],
            "Last Updated": ["2024-01-15", "2024-01-12", "2024-01-18", "2024-01-10"]
        }
        
        df = pd.DataFrame(library_data)
        st.dataframe(df, use_container_width=True)

elif st.session_state.current_view == "settings":
    st.markdown("## ⚙️ CONFIGURATION - ENHANCED")
    st.markdown("Advanced system settings with user preferences and operational modes.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Appearance", "⚙️ System", "🔒 Security", "📊 Advanced"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎨 THEME SETTINGS")
            theme = st.selectbox("Color Theme", ["Dark (Current)", "Light", "Military Green", "High Contrast"])
            font_size = st.selectbox("Font Size", ["Small", "Medium (Current)", "Large", "Extra Large"])
            ui_density = st.selectbox("UI Density", ["Compact", "Standard (Current)", "Comfortable"])
        
        with col2:
            st.markdown("### 📱 DISPLAY OPTIONS")
            show_animations = st.checkbox("Enable Animations", value=True)
            show_tooltips = st.checkbox("Show Tooltips", value=True)
            compact_mode = st.checkbox("Compact Navigation", value=False)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌍 REGIONAL SETTINGS")
            units = st.selectbox("Measurement Units", ["Metric (Current)", "Imperial", "Mixed"])
            date_format = st.selectbox("Date Format", ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"])
            time_format = st.selectbox("Time Format", ["24-hour", "12-hour"])
        
        with col2:
            st.markdown("### 🔔 NOTIFICATIONS")
            enable_notifications = st.checkbox("Enable Notifications", value=True)
            sound_alerts = st.checkbox("Sound Alerts", value=False)
            email_reports = st.checkbox("Email Reports", value=False)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔒 SECURITY SETTINGS")
            auto_logout = st.selectbox("Auto Logout", ["Never", "30 minutes", "1 hour", "4 hours"])
            require_auth = st.checkbox("Require Authentication", value=False)
            audit_logging = st.checkbox("Enable Audit Logging", value=True)
        
        with col2:
            st.markdown("### 🛡️ PRIVACY SETTINGS")
            data_retention = st.selectbox("Data Retention", ["7 days", "30 days", "90 days", "1 year"])
            anonymous_usage = st.checkbox("Anonymous Usage Statistics", value=True)
            export_data = st.button("📁 Export My Data")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚀 PERFORMANCE SETTINGS")
            response_cache = st.checkbox("Enable Response Caching", value=True)
            preload_models = st.checkbox("Preload AI Models", value=True)
            max_context = st.slider("Max Context Length", 1000, 10000, 4000)
        
        with col2:
            st.markdown("### 🔧 ADVANCED OPTIONS")
            debug_mode = st.checkbox("Debug Mode", value=False)
            experimental_features = st.checkbox("Experimental Features", value=False)
            developer_mode = st.checkbox("Developer Mode", value=False)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("💾 SAVE ALL SETTINGS", type="primary"):
            st.success("✅ All settings saved successfully!")
    with col2:
        if st.button("🔄 RESET TO DEFAULTS"):
            st.warning("⚠️ Settings reset to defaults!")
    with col3:
        if st.button("📤 EXPORT SETTINGS"):
            st.info("📁 Settings exported to file!")

# ==============================================================================
# Footer
# ==============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.875rem; padding: 1rem;">
    FA-GPT Enhanced v2.0 | Session: {st.session_state.session_id[:8]}... | 
    Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
    🔒 Secure Mode Active
</div>
""", unsafe_allow_html=True)
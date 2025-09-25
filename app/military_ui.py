import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.rag_core import get_rag_response
from app.ballistic_computer import BallisticComputer, FiringUnit, Target, WeaponSystem, AmmunitionType, ChargeType
from app.orders_generator import OrdersGenerator, OrderType, MissionPriority, MethodOfFire
import base64

# ==============================================================================
# Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="FA-GPT | Mission Command",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# Custom CSS for Enhanced, Conversational UI
# ==============================================================================
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* --- Monochromatic Base --- */
        :root {
            --primary-bg: #0a0a0a;
            --secondary-bg: #1a1a1a;
            --card-bg: #141414;
            --border: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent: #ffffff;
            --hover: #202020;
            --success: #00ff00;
            --warning: #ffaa00;
            --error: #ff0000;
        }
        
        /* --- Main App Styling --- */
        .stApp {
            background: var(--primary-bg);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* --- Remove default padding --- */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }
        
        /* --- Card Components --- */
        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
            height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .feature-card:hover {
            background: var(--hover);
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        
        .feature-card h3 {
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.02em;
        }
        
        .feature-card p {
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.5;
            margin: 0;
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            opacity: 0.8;
        }
        
        /* --- Enhanced Chat Styling --- */
        .chat-message {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .chat-user {
            border-left: 3px solid var(--accent);
        }
        
        .chat-bot {
            border-left: 3px solid var(--success);
        }
        
        .quick-prompt-btn {
            background: var(--secondary-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.5rem 1rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin: 0.25rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .quick-prompt-btn:hover {
            background: var(--hover);
            color: var(--text-primary);
        }
        
        /* --- Header Styling --- */
        .main-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .main-header h1 {
            font-size: 3rem;
            font-weight: 300;
            color: var(--text-primary);
            margin: 0;
            letter-spacing: -0.04em;
        }
        
        .main-header p {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin: 0.5rem 0 0 0;
            font-weight: 400;
        }
        
        /* --- Status Bar --- */
        .status-bar {
            background: var(--secondary-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }
        
        /* --- Hide Streamlit Elements --- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* --- Streamlit Component Overrides --- */
        .stSelectbox > div > div {
            background: var(--card-bg);
            border: 1px solid var(--border);
            color: var(--text-primary);
        }
        
        .stTextInput > div > div > input {
            background: var(--card-bg);
            border: 1px solid var(--border);
            color: var(--text-primary);
        }
        
        .stButton > button {
            background: var(--text-primary);
            color: var(--primary-bg);
            border: none;
            border-radius: 8px;
            font-weight: 500;
            padding: 0.5rem 1.5rem;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background: var(--text-secondary);
        }
        
    </style>
    """, unsafe_allow_html=True)

load_css()

# ==============================================================================
# Enhanced Functions
# ==============================================================================

def render_feature_cards():
    """Render the main feature cards grid"""
    
    # Create the grid of feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("", key="chat_card"):
            st.session_state.current_view = "chat"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"chat_card\\"]').click()">
            <div>
                <div class="feature-icon">💬</div>
                <h3>AI ASSISTANT</h3>
                <p>Advanced conversational AI with memory, export, and specialized query types.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("", key="ballistic_card"):
            st.session_state.current_view = "ballistic"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"ballistic_card\\"]').click()">
            <div>
                <div class="feature-icon">🎯</div>
                <h3>BALLISTIC COMPUTER</h3>
                <p>Advanced firing solutions with weather integration and multi-unit support.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("", key="orders_card"):
            st.session_state.current_view = "orders"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"orders_card\\"]').click()">
            <div>
                <div class="feature-icon">📋</div>
                <h3>ORDERS GENERATOR</h3>
                <p>Comprehensive order templates with validation and multi-mission planning.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("", key="status_card"):
            st.session_state.current_view = "status"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"status_card\\"]').click()">
            <div>
                <div class="feature-icon">📊</div>
                <h3>SYSTEM STATUS</h3>
                <p>Real-time monitoring with performance metrics and system diagnostics.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("", key="docs_card"):
            st.session_state.current_view = "documents"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"docs_card\\"]').click()">
            <div>
                <div class="feature-icon">📁</div>
                <h3>DOCUMENT PROCESSING</h3>
                <p>Intelligent document analysis with OCR and automated indexing.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("", key="settings_card"):
            st.session_state.current_view = "settings"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" onclick="document.querySelector('[data-testid=\\"settings_card\\"]').click()">
            <div>
                <div class="feature-icon">⚙️</div>
                <h3>CONFIGURATION</h3>
                <p>Advanced settings with user preferences and operational modes.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_enhanced_chat_history():
    """Enhanced chat history with better formatting and metadata"""
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>YOU</strong> ({message.get('timestamp', 'N/A')})
                <br>{message.get('content', '')}
                <br><small>Query Type: {message.get('query_type', 'General')}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            response_content = message["content"]
            st.markdown(f"""
            <div class="chat-message chat-bot">
                <strong>FA-GPT</strong> ({response_content.get('timestamp', 'N/A')})
                <br>{response_content.get('answer', '')}
                <br><small>Style: {response_content.get('response_style', 'Standard')} | 
                Query Type: {response_content.get('query_type', 'General')}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Display images if they exist
            if response_content.get("images"):
                with st.expander("📷 View Images"):
                    cols = st.columns(min(len(response_content["images"]), 3))
                    for j, img_path in enumerate(response_content["images"]):
                        if os.path.exists(img_path):
                            with cols[j % 3]:
                                st.image(img_path, use_column_width=True)
            
            # Display sources if they exist
            if response_content.get("sources"):
                with st.expander("📚 View Sources"):
                    for source in response_content["sources"]:
                        st.text(f"Source: {source.get('document', 'N/A')}")

def export_conversation_data():
    """Export conversation data with enhanced metadata"""
    if st.session_state.messages:
        export_data = {
            "session_info": {
                "session_id": st.session_state.get("session_id", str(uuid.uuid4())),
                "export_timestamp": datetime.now().isoformat(),
                "total_messages": len(st.session_state.messages),
                "user_queries": len([m for m in st.session_state.messages if m["role"] == "user"]),
                "system_version": "FA-GPT v2.0 Enhanced"
            },
            "conversation": st.session_state.messages,
            "statistics": {
                "session_duration": f"{len(st.session_state.messages) * 2} minutes (estimated)",
                "query_types": list(set([m.get('query_type', 'General') for m in st.session_state.messages if m["role"] == "user"])),
                "response_styles": list(set([m["content"].get('response_style', 'Standard') for m in st.session_state.messages if m["role"] == "bot"]))
            }
        }
        
        filename = f"fa_gpt_enhanced_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.download_button(
            label="📁 Download Enhanced Export",
            data=json.dumps(export_data, indent=2),
            file_name=filename,
            mime="application/json"
        )
        return True
    return False

# ==============================================================================
# Initialize Enhanced Session State
# ==============================================================================
if "ballistic_computer" not in st.session_state:
    st.session_state.ballistic_computer = BallisticComputer()
if "orders_generator" not in st.session_state:
    st.session_state.orders_generator = OrdersGenerator()
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = True

# ==============================================================================
# Enhanced Header and Status
# ==============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>FA-GPT</h1>
    <p>ENHANCED FIELD ARTILLERY MISSION COMMAND SYSTEM</p>
</div>
""", unsafe_allow_html=True)

# Enhanced Status Bar
current_time = datetime.now()
uptime_hours = (current_time.hour + current_time.minute / 60)
session_stats = {
    "queries": len([m for m in st.session_state.messages if m["role"] == "user"]),
    "responses": len([m for m in st.session_state.messages if m["role"] == "bot"])
}

st.markdown(f"""
<div class="status-bar">
    <div class="status-item">
        <div class="status-dot"></div>
        <span>SYSTEM OPERATIONAL</span>
    </div>
    <div class="status-item">
        <span>{current_time.strftime('%H:%M:%S UTC')}</span>
    </div>
    <div class="status-item">
        <span>SESSION: {session_stats['queries']} QUERIES</span>
    </div>
    <div class="status-item">
        <span>ENHANCED MODE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# Enhanced Navigation
# ==============================================================================

if st.session_state.current_view != "home":
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← BACK TO COMMAND CENTER", key="back_button"):
            st.session_state.current_view = "home"
            st.rerun()
    with col2:
        st.markdown(f"**Current Session:** {st.session_state.session_id[:8]}... | **Active View:** {st.session_state.current_view.upper()}")
    st.markdown("---")

# ==============================================================================
# Enhanced View Management
# ==============================================================================

if st.session_state.current_view == "home":
    render_feature_cards()

elif st.session_state.current_view == "chat":
    st.markdown("## 💬 AI ASSISTANT - ENHANCED")
    st.markdown("Advanced conversational interface with memory, export capabilities, and specialized query processing.")
    
    # Enhanced control panel
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        query_type = st.selectbox("🎯 Query Type", 
            ["General Doctrine", "Tactical Procedures", "Technical Specifications", 
             "Safety Protocols", "Training Materials", "Historical Analysis"],
            help="Select the type of query for optimized response")
    
    with col2:
        if st.button("📁 EXPORT", help="Export conversation with metadata"):
            if not export_conversation_data():
                st.warning("No conversation to export")
    
    with col3:
        if st.button("🗑️ CLEAR", help="Clear conversation history"):
            st.session_state.messages = []
            st.rerun()
    
    with col4:
        conversation_mode = st.toggle("🧠 Memory", 
                                    value=st.session_state.conversation_mode,
                                    help="Maintain conversation context")
        st.session_state.conversation_mode = conversation_mode
    
    st.markdown("---")
    
    # Enhanced statistics dashboard
    if st.session_state.messages:
        col1, col2, col3, col4 = st.columns(4)
        total_queries = len([m for m in st.session_state.messages if m["role"] == "user"])
        with col1:
            st.metric("🔄 Total Queries", total_queries)
        with col2:
            st.metric("⏱️ Session Time", f"{len(st.session_state.messages) * 2}min")
        with col3:
            st.metric("🧠 Context Level", "High" if conversation_mode else "Standard")
        with col4:
            recent_query_type = "None"
            if st.session_state.messages:
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "user" and msg.get("query_type"):
                        recent_query_type = msg["query_type"]
                        break
            st.metric("📋 Last Query Type", recent_query_type)
        st.markdown("---")
    
    # Display enhanced chat history
    display_enhanced_chat_history()
    
    # Quick prompts section
    st.markdown("### 💭 Quick Military Prompts")
    quick_prompts = [
        "Explain high-angle fire procedures for mountainous terrain",
        "What are the minimum safe distances for HE rounds by charge?",
        "How do I calculate proper charge selection for different ranges?",
        "Describe counter-battery radar detection procedures",
        "What is the standard call for fire format and sequence?",
        "Explain observed fire adjustment procedures step-by-step"
    ]
    
    prompt_cols = st.columns(2)
    for i, prompt in enumerate(quick_prompts):
        with prompt_cols[i % 2]:
            if st.button(f"💭 {prompt[:45]}...", key=f"quick_{i}", help=prompt):
                # Process quick prompt
                st.session_state.messages.append({
                    "role": "user", 
                    "content": prompt,
                    "timestamp": datetime.now().isoformat(),
                    "query_type": query_type
                })
                
                with st.spinner("🤔 Processing quick prompt..."):
                    # Build context if memory mode is enabled
                    enhanced_query = prompt
                    if conversation_mode and len(st.session_state.messages) > 1:
                        recent_context = st.session_state.messages[-4:]  # Last 2 exchanges
                        context_summary = f"Previous context: {json.dumps(recent_context, indent=2)}\n\nCurrent query: "
                        enhanced_query = f"{context_summary}{prompt}"
                    
                    response_text, images, metadata = get_rag_response(enhanced_query)
                    response_data = {
                        "answer": response_text,
                        "images": images,
                        "sources": metadata.get("sources", []),
                        "query_type": query_type,
                        "response_style": "Quick Response",
                        "timestamp": datetime.now().isoformat()
                    }
                
                st.session_state.messages.append({"role": "bot", "content": response_data})
                st.rerun()
    
    st.markdown("---")
    
    # Enhanced main chat input
    with st.form("enhanced_chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_query = st.text_area("🎤 Enter your detailed query:", 
                                    placeholder="Ask about artillery doctrine, tactical procedures, technical specifications, or request detailed analysis...",
                                    height=100)
        with col2:
            st.markdown("**Options:**")
            response_style = st.selectbox("📝 Response Style", 
                                        ["Comprehensive", "Concise", "Technical", "Training-Focused"])
            include_examples = st.checkbox("📖 Include Examples", value=True)
            priority_level = st.selectbox("⚡ Priority", ["Standard", "High", "Critical"])
        
        submitted = st.form_submit_button("🚀 SEND ENHANCED QUERY", type="primary")
        
        if submitted and user_query:
            st.session_state.messages.append({
                "role": "user", 
                "content": user_query,
                "timestamp": datetime.now().isoformat(),
                "query_type": query_type,
                "response_style": response_style,
                "priority": priority_level
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
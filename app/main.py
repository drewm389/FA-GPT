# app/main.py
"""
Enhanced Streamlit Web Interface for FA-GPT (Field Artillery GPT) - Refactored for Simplicity

This refactored version incorporates streamlit-antd-components for cleaner navigation
while maintaining the existing AppState and MilitaryUI architecture for clean separation of concerns:
- AppState manages all session variables in one place
- MilitaryUI handles all rendering logic 
- main.py is a clean controller with enhanced navigation
"""
import streamlit as st
import streamlit_antd_components as sac  # Component library for cleaner navigation
from app.state import AppState
from app.military_ui import MilitaryUI

def main():
    """Main function to run the Streamlit app with enhanced navigation."""
    st.set_page_config(
        page_title="FA-GPT: Field Artillery Assistant",
        page_icon="🎖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize or get the current app state
    # This centralizes all session variables in the AppState class
    if "state" not in st.session_state:
        st.session_state.state = AppState()
    
    app_state = st.session_state.state

    # Initialize the UI class with the current state
    # The MilitaryUI class handles all the complex rendering logic
    ui = MilitaryUI(app_state)

    # Render sidebar (keep existing functionality)
    ui.render_sidebar()
    
    # Render header manually (simplified from existing UI)
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #1a2833 0%, #0a0a0a 100%); border: 2px solid #4a9eff; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: #4a9eff; font-family: 'Orbitron', monospace; font-size: 3rem; margin: 0;">🎖️ FA-GPT</h1>
        <p style="color: #cccccc; font-size: 1.2rem; margin: 0.5rem 0;">ENHANCED FIELD ARTILLERY MISSION COMMAND SYSTEM</p>
    </div>
    """, unsafe_allow_html=True)

    # --- ENHANCED NAVIGATION: Replace tabs with clean menu navigation ---
    selected_view = sac.menu([
        sac.MenuItem('INTEL DATABASE', icon='database-fill-check', description="Query documents with the RAG AI."),
        sac.MenuItem('FIRE MISSIONS', icon='crosshair', description="Plan and coordinate fire support."),
        sac.MenuItem('BALLISTICS', icon='bullseye', description="Calculate firing solutions."),
        sac.MenuItem('ORDERS PROD', icon='file-earmark-text-fill', description="Generate military orders."),
        sac.MenuItem('SYSTEM OPS', icon='gear-wide-connected', description="Monitor system status and config."),
    ], orientation='horizontal', size='small', return_index=False, key='main_nav')

    # --- Main controller logic to render the selected view ---
    if selected_view == 'INTEL DATABASE':
        ui.render_intelligence_hub()
    elif selected_view == 'FIRE MISSIONS':
        ui.render_fire_support()
    elif selected_view == 'BALLISTICS':
        ui.render_ballistics()
    elif selected_view == 'ORDERS PROD':
        ui.render_operations()
    elif selected_view == 'SYSTEM OPS':
        ui.render_system_admin()
    else:
        # Default to intelligence hub if no selection
        ui.render_intelligence_hub()

    # Footer with session information
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8em; padding: 10px;">
        FA-GPT Enhanced v3.0 | Session: {app_state.session_id[:8]}... | 
        Navigation: streamlit-antd-components | 
        🔒 Secure Mode Active | Running 100% Locally
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
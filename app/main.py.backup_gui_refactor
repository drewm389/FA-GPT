# app/main.py
"""
Main Streamlit application file for FA-GPT.
This file acts as the central controller, delegating UI rendering
and state management to their respective modules.

This refactored version separates concerns:
- AppState manages all session variables in one place
- MilitaryUI handles all rendering logic
- main.py is a clean controller that coordinates them
"""
import streamlit as st
from app.state import AppState
from app.military_ui import MilitaryUI

def main():
    """Main function to run the Streamlit app."""
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

    # Render the main application layout
    # The UI class now handles all the complex rendering logic,
    # keeping this main file clean and focused on coordination
    ui.render_sidebar()
    ui.render_header_and_nav()

    # Footer with session information
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8em; padding: 10px;">
        FA-GPT Enhanced v2.0 | Session: {app_state.session_id[:8]}... | 
        Last Updated: {st.get_option("client.toolbarMode")} | 
        🔒 Secure Mode Active
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
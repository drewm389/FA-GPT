"""Minimal MilitaryUI implementation for FA-GPT Streamlit app.

This module intentionally provides a compact version of the Field Artillery
UI so the application can launch while the full-featured UI is rebuilt.
The public methods mirror what `app/main.py` expects today.
"""

from __future__ import annotations

import streamlit as st

from app.state import AppState


class MilitaryUI:
    """Very small UI shell with the required rendering hooks."""

    def __init__(self, state: AppState) -> None:
        self.state = state
        self._load_css()

    def _load_css(self) -> None:
        """Apply a simple dark theme so the app looks polished."""
        st.markdown(
            """
            <style>
            .stApp { background: #0a111a; color: #e8eef6; }
            .fa-card { background: #111a24; padding: 1rem; border-radius: 10px; }
            .fa-header { color: #4a9eff; font-family: 'Inter', system-ui, sans-serif; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def _render_status_bar(self) -> None:
        with st.sidebar:
            st.markdown("---")
            st.write(f"Started: {self.state.session_start_time}")
            st.write(f"Messages: {len(getattr(self.state, 'messages', []))}")

    def render_sidebar(self) -> None:
        with st.sidebar:
            st.title("FA-GPT")
            st.markdown("---")
            st.write(f"Session: {self.state.session_id[:8]}")
            st.write(f"View: {self.state.current_view}")
            st.markdown("---")
            st.caption("Use the top menu to switch screens.")
        self._render_status_bar()

    def render_intelligence_hub(self) -> None:
        st.header("INTEL DATABASE")
        st.write("Search and query ingested documents (placeholder content).")
        query = st.text_input("Query", key="intel_query")
        if query:
            st.info("Document search coming soon – backend hooks ready.")

    def render_fire_support(self) -> None:
        st.header("FIRE MISSIONS")
        st.write("Fire support planning tools will live here.")
        st.button("Create mission", key="fire_support_create")

    def render_ballistics(self) -> None:
        st.header("BALLISTICS")
        st.write("Ballistic calculators will display tables and charts here.")
        with st.expander("Sample computation"):
            st.write("Placeholder ballistics data.")

    def render_operations(self) -> None:
        st.header("ORDERS PROD")
        st.write("Orders generation workflows will be reattached soon.")
        st.button("Generate order", key="orders_generate")

    def render_system_admin(self) -> None:
        st.header("SYSTEM OPS")
        st.write("Monitor integrations and system health from this panel.")
        st.write("Ollama status:", getattr(self.state, "ollama_available", "unknown"))
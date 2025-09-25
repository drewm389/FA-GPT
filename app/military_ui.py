"""Streamlit UI rendering layer for the FA-GPT Command Center."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Tuple

import streamlit as st

from app.state import AppState


class MilitaryUI:
    """High-level coordinator for Streamlit views."""

    def __init__(self, state: AppState) -> None:
        self.state = state
        self._load_css()

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------
    def _load_css(self) -> None:
        st.markdown(
            """
            <style>
            .stApp { background: #020b13; color: #dfe7f5; }
            .fa-panel { background: #0f1b28; border-radius: 14px; padding: 1.25rem; border: 1px solid rgba(74, 158, 255, 0.2); }
            .fa-metric { background: rgba(74, 158, 255, 0.08); padding: 0.75rem 1rem; border-radius: 12px; margin-bottom: 0.6rem; }
            .fa-subtle { color: rgba(223, 231, 245, 0.7); font-size: 0.85rem; }
            .fa-table thead tr { background: rgba(74, 158, 255, 0.15); }
            .css-1d391kg, .css-hxt7ib { gap: 0.6rem; }
            .stMetric { background: rgba(15, 27, 40, 0.82); border-radius: 12px; padding: 0.75rem; border: 1px solid rgba(74, 158, 255, 0.18); }
            .stMetric label { color: rgba(223, 231, 245, 0.7); text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.08em; }
            .stMetric span { color: #ffffff; }
            a { color: #4a9eff; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # ------------------------------------------------------------------
    # Sidebar and shared components
    # ------------------------------------------------------------------
    def render_sidebar(self) -> None:
        with st.sidebar:
            st.title("🎖️ FA-GPT")
            st.caption("Field Artillery Mission Command – Engineering Shell")

            st.markdown("---")
            st.metric("Session", self.state.session_id[:8])
            st.metric("Messages", len(self.state.messages))
            st.metric("Active View", self.state.current_view.replace("_", " ").title())

            if self.state.processing_status != "idle":
                st.markdown("### Processing Status")
                st.progress(self.state.processing_progress)
                st.write(self.state.processing_status.title())
                if self.state.processing_messages:
                    with st.expander("Recent activity"):
                        for msg in self.state.processing_messages[-6:]:
                            st.write(msg)

            st.markdown("### Feature Toggles")
            multimodal = st.checkbox("Multimodal Processing", value=self.state.multimodal_enabled)
            vision = st.checkbox("Vision Analysis", value=self.state.vision_analysis_enabled)
            advanced = st.checkbox("Advanced Extraction", value=self.state.advanced_extraction)

            self.state.multimodal_enabled = multimodal
            self.state.vision_analysis_enabled = vision
            self.state.advanced_extraction = advanced

            st.markdown("### Quick Actions")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reset Session", use_container_width=True):
                    self.state.reset_session()
                    st.success("Session reset; state cleared.")
            with col2:
                if st.button("Copy Summary", use_container_width=True):
                    st.write(self.state.get_session_summary())

            st.markdown("---")
            st.caption("Upload documents from here; processing hooks remain wired to the ingestion pipeline.")
            uploads = st.file_uploader("Drop PDFs", type=["pdf"], accept_multiple_files=True)
            if uploads:
                self.state.uploaded_files = [
                    {"name": file.name, "size": file.size, "type": file.type} for file in uploads
                ]
                st.success(f"Queued {len(uploads)} file(s) for process.py")

    # ------------------------------------------------------------------
    # View: Intelligence Hub
    # ------------------------------------------------------------------
    def render_intelligence_hub(self) -> None:
        self.state.current_view = "intelligence_hub"
        st.header("📊 Intelligence Hub")
        st.subheader("Ask questions about processed doctrine and telemetry")

        with st.form("intel_query_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                query = st.text_area(
                    "Mission question",
                    placeholder="e.g., Summarize counter-battery procedures for M777 in mountainous terrain",
                    height=140,
                )
            with col2:
                query_type = st.selectbox(
                    "Context",
                    ["General Doctrine", "Technical Data", "Fire Support", "Safety", "Training"],
                )
                include_sources = st.checkbox("Request sources", value=True)
                mark_priority = st.selectbox("Priority", ["Routine", "Immediate", "Flash"], index=0)

            submitted = st.form_submit_button("Log query")

        if submitted and query:
            self.state.add_message("user", query, query_type=query_type, priority=mark_priority)
            # Placeholder answer until RAG hooks are reconnected.
            response = (
                "📌 Placeholder response: doctrinal answers come from Granite-Docling + Qwen stack. "
                "Run `process.py` to ingest more PDFs and wire query_rag.py for live answers."
            )
            self.state.add_message(
                "assistant",
                response,
                query_type=query_type,
                priority=mark_priority,
                include_sources=include_sources,
                simulated=True,
            )
            st.success("Conversation updated. Placeholder response recorded for debugging.")
        elif submitted:
            st.warning("Enter a mission question to log it.")

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown("### Conversation Timeline")
            if not self.state.messages:
                st.info("No traffic yet. Submit a mission question to seed the log.")
            else:
                for role, payload in self._yield_messages(reversed(self.state.messages)):
                    self._render_message(role, payload)

        with col_right:
            st.markdown("### Session Snapshot")
            summary = self.state.get_session_summary()
            st.write("Session ID", summary["session_id"])
            st.write("Duration", f"{summary['session_duration'] / 60:.1f} min")
            st.write("Messages", summary["messages_count"])
            st.write("View", summary["current_view"].replace("_", " ").title())
            st.markdown("### Active Features")
            for feature, enabled in summary["active_features"].items():
                st.write(f"• {feature.replace('_', ' ').title()}: {'✅' if enabled else '⛔️'}")

    # ------------------------------------------------------------------
    # View: Fire Support
    # ------------------------------------------------------------------
    def render_fire_support(self) -> None:
        self.state.current_view = "fire_support"
        st.header("🎯 Fire Support Planner")
        st.subheader("Capture targets, firing units, and sync them with ballistic calculators")

        with st.form("target_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                tgt_name = st.text_input("Target Designator", value=self._safe_dict(self.state.current_target).get("name", ""))
                tgt_grid = st.text_input("Grid (MGRS)", value=self._safe_dict(self.state.current_target).get("grid", ""))
            with col2:
                tgt_description = st.text_area("Description", value=self._safe_dict(self.state.current_target).get("description", ""), height=80)
            with col3:
                tgt_priority = st.selectbox("Priority", ["Routine", "Priority", "Immediate"], index=1)
                tgt_status = st.selectbox("Status", ["Pending", "Cleared", "Engaged"])

            update_target = st.form_submit_button("Save Target")

        if update_target and tgt_name and tgt_grid:
            self.state.current_target = {
                "name": tgt_name,
                "grid": tgt_grid,
                "description": tgt_description,
                "priority": tgt_priority,
                "status": tgt_status,
                "updated_at": datetime.utcnow().isoformat(),
            }
            st.success("Target saved in session state.")
        elif update_target:
            st.warning("Target designator and grid are required.")

        st.markdown("### Firing Units")
        with st.form("firing_unit_form"):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                unit_name = st.text_input("Callsign")
            with col2:
                unit_grid = st.text_input("Gun Position Grid")
            with col3:
                unit_guns = st.number_input("Guns", min_value=1, max_value=8, value=4)
            with col4:
                unit_status = st.selectbox("Ready", ["YES", "NO"], index=0)
            add_unit = st.form_submit_button("Add unit")

        if add_unit and unit_name and unit_grid:
            self.state.firing_units.append(
                {
                    "name": unit_name,
                    "grid": unit_grid,
                    "guns": int(unit_guns),
                    "status": unit_status,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            st.success(f"{unit_name} recorded.")
        elif add_unit:
            st.warning("Provide both callsign and grid to register a unit.")

        if self.state.current_target:
            st.markdown("#### Current Target")
            st.json(self.state.current_target)

        if self.state.firing_units:
            st.markdown("#### Registered Units")
            for unit in self.state.firing_units[-5:]:
                st.write(
                    f"• {unit['name']} ({unit['grid']}) – {unit['guns']} guns – {unit['status']} "
                    f"[{self._relative_time(unit['timestamp'])}]"
                )
        else:
            st.info("No firing units logged yet.")

    # ------------------------------------------------------------------
    # View: Ballistics
    # ------------------------------------------------------------------
    def render_ballistics(self) -> None:
        self.state.current_view = "ballistics"
        st.header("🧮 Ballistic Workspace")
        st.subheader("Prototype calculators feed the Orders Generator and Mission Planner")

        with st.form("ballistic_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                range_m = st.number_input("Range (meters)", min_value=100, max_value=40000, value=13000, step=100)
            with col2:
                charge = st.selectbox("Charge", ["Green", "White", "Red", "MAC"])
            with col3:
                fuze = st.selectbox("Fuze", ["PD", "VT", "MT", "Delay"])
            col4, col5 = st.columns(2)
            with col4:
                wind = st.number_input("Crosswind (kts)", min_value=0.0, max_value=40.0, value=4.0)
            with col5:
                temp = st.number_input("Temperature (°C)", min_value=-30.0, max_value=60.0, value=20.0)
            compute = st.form_submit_button("Compute sample solution")

        if compute:
            tof = range_m / 300.0  # Simple placeholder physics
            quadrant = max(300, min(1600, int(range_m / 25)))
            correction = wind * 2.5
            self.state.ballistic_calculations = {
                "range_m": range_m,
                "charge": charge,
                "fuze": fuze,
                "wind": wind,
                "temperature": temp,
                "time_of_flight": round(tof, 1),
                "quadrant": quadrant,
                "wind_correction": round(correction, 1),
                "computed_at": datetime.utcnow().isoformat(),
            }
            st.success("Sample ballistic outputs stored in session state.")

        if self.state.ballistic_calculations:
            st.markdown("### Last Computation")
            metrics_col, details_col = st.columns([1, 1])
            with metrics_col:
                st.metric("Time of Flight", f"{self.state.ballistic_calculations['time_of_flight']} s")
                st.metric("Quadrant", f"{self.state.ballistic_calculations['quadrant']} mils")
                st.metric("Wind Correction", f"{self.state.ballistic_calculations['wind_correction']} mils")
            with details_col:
                st.json(self.state.ballistic_calculations)
        else:
            st.info("Run the calculator to populate ballistic state.")

    # ------------------------------------------------------------------
    # View: Operations / Orders
    # ------------------------------------------------------------------
    def render_operations(self) -> None:
        self.state.current_view = "operations"
        st.header("📋 Operations & Orders")
        st.subheader("Track mission plans that tie fire missions, logistics, and intel together")

        with st.form("mission_form"):
            col1, col2 = st.columns([2, 1])
            with col1:
                mission_name = st.text_input("Mission Title", value=self._safe_dict(self.state.mission_data).get("title", ""))
                mission_summary = st.text_area(
                    "Brief",
                    value=self._safe_dict(self.state.mission_data).get("brief", ""),
                    height=120,
                )
            with col2:
                phase = st.selectbox(
                    "Current Phase",
                    ["Initiation", "Prep Fires", "Execution", "Assessment"],
                    index=1,
                )
                commander = st.text_input("Commander", value=self._safe_dict(self.state.mission_data).get("commander", ""))
            save_mission = st.form_submit_button("Save mission packet")

        if save_mission and mission_name:
            self.state.mission_data = {
                "title": mission_name,
                "brief": mission_summary,
                "phase": phase,
                "commander": commander,
                "targets": len(self.state.firing_units),
                "updated_at": datetime.utcnow().isoformat(),
            }
            st.success("Mission packet updated in session state.")
        elif save_mission:
            st.warning("Provide a mission title before saving.")

        if self.state.mission_data:
            st.markdown("### Mission Overview")
            col1, col2, col3 = st.columns(3)
            col1.metric("Targets tracked", self.state.mission_data.get("targets", 0))
            col2.metric("Phase", self.state.mission_data.get("phase", "-"))
            col3.metric("Commander", self.state.mission_data.get("commander", "-"))
            st.markdown("#### Operational Narrative")
            st.write(self.state.mission_data.get("brief", ""))
        else:
            st.info("Create a mission packet to track operations data.")

    # ------------------------------------------------------------------
    # View: System Administration
    # ------------------------------------------------------------------
    def render_system_admin(self) -> None:
        self.state.current_view = "system_admin"
        st.header("⚙️ System Operations")
        st.subheader("Monitor integrations, model readiness, and infrastructure toggles")

        st.markdown("### System Health")
        health_cols = st.columns(len(self.state.system_health) or 1)
        for (component, status), col in zip(self.state.system_health.items(), health_cols):
            with col:
                col.metric(component.upper(), status.title())

        st.markdown("### Session Diagnostics")
        diag_left, diag_right = st.columns([1, 1])
        with diag_left:
            summary = self.state.get_session_summary()
            st.json(summary)
        with diag_right:
            st.markdown("#### Guidance")
            st.markdown("- Run `python system_status.py --detailed` for the full health report.")
            st.markdown("- Use `process.py --retry-failed` after clearing quarantined PDFs.")
            st.markdown("- Re-run `streamlit run app/main.py` if UI auto-refresh stalls after code reloads.")

        st.markdown("### Maintenance Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Mark Ollama Ready", use_container_width=True):
                self.state.system_health["ollama"] = "operational"
        with col2:
            if st.button("Mark Database Ready", use_container_width=True):
                self.state.system_health["database"] = "operational"
        with col3:
            if st.button("Flag GPU Issue", use_container_width=True):
                self.state.system_health["gpu"] = "investigate"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_message(self, role: str, payload: dict) -> None:
        label = "🧑‍💻 Operator" if role == "user" else "🤖 FA-GPT"
        container = st.container()
        with container:
            st.markdown(f"**{label}** · <span class='fa-subtle'>{self._relative_time(payload['timestamp'])}</span>", unsafe_allow_html=True)
            st.write(payload.get("content", ""))
            meta_bits = []
            if payload.get("query_type"):
                meta_bits.append(f"Query: {payload['query_type']}")
            if payload.get("priority"):
                meta_bits.append(f"Priority: {payload['priority']}")
            if payload.get("simulated"):
                meta_bits.append("Simulated response")
            if meta_bits:
                st.caption(" · ".join(meta_bits))
            st.markdown("---")

    @staticmethod
    def _safe_dict(candidate) -> dict:
        return candidate or {}

    @staticmethod
    def _yield_messages(messages: Iterable[dict]) -> Iterable[Tuple[str, dict]]:
        for message in messages:
            yield message.get("role", "unknown"), message

    @staticmethod
    def _relative_time(timestamp: str) -> str:
        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError:
            return "now"
        delta = datetime.now() - ts
        seconds = max(delta.total_seconds(), 1)
        if seconds < 60:
            return f"{int(seconds)}s ago"
        if seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)}h ago"
        return f"{int(seconds // 86400)}d ago"
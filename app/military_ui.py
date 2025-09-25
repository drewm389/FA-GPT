"""
Military UI Components for Streamlit Interface

Specialized UI components for artillery fire support and tactical operations.
Designed for military workflows and field artillery doctrine.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from .ballistic_computer import (
    BallisticComputer, FireMissionPlanner, Target, FiringUnit,
    WeaponSystem, AmmunitionType, ChargeType, FiringData
)

class MilitaryUIComponents:
    """Military-specific UI components for tactical operations."""
    
    def __init__(self):
        self.ballistic_computer = BallisticComputer()
        self.mission_planner = FireMissionPlanner()
    
    def render_target_input_form(self) -> Optional[Target]:
        """Render target input form with military grid coordinates."""
        st.subheader("🎯 Target Designation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_id = st.text_input(
                "Target Designation",
                placeholder="TGT001",
                help="Unique target identifier (e.g., TGT001, OBJ ALPHA)"
            )
            
            grid_coords = st.text_input(
                "Grid Coordinates (8-digit)",
                placeholder="12345678",
                help="Military Grid Reference System coordinates"
            )
            
            elevation = st.number_input(
                "Elevation (meters)",
                min_value=0,
                max_value=9000,
                value=100,
                help="Target elevation above sea level"
            )
        
        with col2:
            description = st.text_area(
                "Target Description",
                placeholder="Enemy artillery position, 3x howitzers...",
                help="Detailed target description for intelligence"
            )
            
            priority = st.selectbox(
                "Priority",
                ["IMMEDIATE", "PRIORITY", "ROUTINE"],
                index=2,
                help="Fire mission priority level"
            )
            
            observer = st.text_input(
                "Observer",
                placeholder="FO1",
                help="Forward observer call sign"
            )
        
        if st.button("🎯 Designate Target", type="primary"):
            if target_id and grid_coords and len(grid_coords) == 8:
                return Target(
                    designation=target_id,
                    grid_coordinates=grid_coords,
                    elevation_meters=elevation,
                    description=description,
                    priority=priority,
                    observer=observer
                )
            else:
                st.error("Please provide valid target designation and 8-digit grid coordinates")
        
        return None
    
    def render_firing_unit_selector(self) -> List[FiringUnit]:
        """Render firing unit selection and configuration."""
        st.subheader("🔫 Firing Unit Configuration")
        
        units = []
        num_units = st.number_input("Number of Firing Units", min_value=1, max_value=6, value=1)
        
        for i in range(num_units):
            with st.expander(f"Firing Unit {i+1}", expanded=i==0):
                col1, col2 = st.columns(2)
                
                with col1:
                    call_sign = st.text_input(
                        f"Call Sign",
                        value=f"STEEL{i+1:02d}",
                        key=f"callsign_{i}"
                    )
                    
                    grid_coords = st.text_input(
                        f"Unit Grid Coordinates",
                        placeholder="12345678",
                        key=f"grid_{i}"
                    )
                    
                    elevation = st.number_input(
                        f"Unit Elevation (m)",
                        min_value=0,
                        max_value=9000,
                        value=200,
                        key=f"elevation_{i}"
                    )
                
                with col2:
                    weapon_system = st.selectbox(
                        f"Weapon System",
                        [ws.value for ws in WeaponSystem],
                        key=f"weapon_{i}"
                    )
                    
                    # Ammunition availability
                    st.write("Ammunition Available:")
                    ammo_available = {}
                    for ammo in AmmunitionType:
                        ammo_available[ammo] = st.number_input(
                            f"{ammo.value}",
                            min_value=0,
                            max_value=200,
                            value=50,
                            key=f"ammo_{i}_{ammo.name}"
                        )
                
                if call_sign and grid_coords and len(grid_coords) == 8:
                    # Convert weapon system string back to enum
                    weapon_enum = None
                    for ws in WeaponSystem:
                        if ws.value == weapon_system:
                            weapon_enum = ws
                            break
                    
                    if weapon_enum:
                        units.append(FiringUnit(
                            call_sign=call_sign,
                            grid_coordinates=grid_coords,
                            elevation_meters=elevation,
                            weapon_system=weapon_enum,
                            ammunition_available=ammo_available
                        ))
        
        return units
    
    def render_fire_mission_display(self, mission_plan: Dict):
        """Display complete fire mission plan with tactical information."""
        if not mission_plan or not mission_plan.get("firing_solutions"):
            st.warning("No valid firing solutions available")
            return
        
        st.subheader("🎯 Fire Mission Plan")
        
        # Target information
        target = mission_plan["target"]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Target", target.designation)
            st.metric("Grid", target.grid_coordinates)
        
        with col2:
            st.metric("Elevation", f"{target.elevation_meters}m")
            st.metric("Priority", target.priority)
        
        with col3:
            st.metric("Observer", target.observer)
            st.metric("Mission Type", mission_plan["mission_type"])
        
        # Recommended solution
        if mission_plan["recommended_unit"]:
            st.subheader("📡 Recommended Firing Solution")
            
            recommended = mission_plan["recommended_unit"]
            unit = recommended["unit"]
            solution = recommended["solution"]
            
            # Fire mission data in military format
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Firing Unit", unit.call_sign)
                st.metric("Range", f"{solution.range_meters}m")
            
            with col2:
                st.metric("Azimuth", f"{solution.azimuth_mils:04d} mils")
                st.metric("Elevation", f"{solution.elevation_mils:04d} mils")
            
            with col3:
                st.metric("Charge", solution.charge.value)
                st.metric("Time of Flight", f"{solution.time_of_flight}s")
            
            with col4:
                st.metric("Ammunition", solution.ammunition.value)
                st.metric("Rounds", recommended["ammunition_expenditure"])
            
            # Generate fire mission message
            if st.button("📻 Generate Fire Mission", type="primary"):
                fire_mission = self._generate_fire_mission_message(
                    target, unit, solution, recommended["ammunition_expenditure"]
                )
                
                st.subheader("📻 Fire Mission Message")
                st.code(fire_mission, language="text")
        
        # All available solutions
        if len(mission_plan["firing_solutions"]) > 1:
            st.subheader("🔫 All Available Solutions")
            
            solutions_data = []
            for sol_data in mission_plan["firing_solutions"]:
                unit = sol_data["unit"]
                solution = sol_data["solution"]
                
                solutions_data.append({
                    "Unit": unit.call_sign,
                    "Range (m)": solution.range_meters,
                    "Azimuth": f"{solution.azimuth_mils:04d}",
                    "Elevation": f"{solution.elevation_mils:04d}",
                    "Charge": solution.charge.value,
                    "TOF (s)": solution.time_of_flight,
                    "Rounds": sol_data["ammunition_expenditure"]
                })
            
            df = pd.DataFrame(solutions_data)
            st.dataframe(df, use_container_width=True)
    
    def render_ballistic_calculator(self):
        """Render manual ballistic calculation interface."""
        st.subheader("🧮 Manual Ballistic Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Gun Data**")
            gun_grid = st.text_input("Gun Grid", placeholder="12345678")
            gun_elevation = st.number_input("Gun Elevation (m)", value=200)
            
            weapon_system = st.selectbox(
                "Weapon System",
                [ws.value for ws in WeaponSystem]
            )
            
            ammunition = st.selectbox(
                "Ammunition Type",
                [ammo.value for ammo in AmmunitionType]
            )
        
        with col2:
            st.write("**Target Data**")
            target_grid = st.text_input("Target Grid", placeholder="12345678")
            target_elevation = st.number_input("Target Elevation (m)", value=100)
            
            charge = st.selectbox(
                "Charge (optional)",
                ["Auto Select"] + [c.value for c in ChargeType]
            )
        
        if st.button("⚡ Calculate Firing Data"):
            if gun_grid and target_grid and len(gun_grid) == 8 and len(target_grid) == 8:
                # Create temporary objects for calculation
                weapon_enum = None
                for ws in WeaponSystem:
                    if ws.value == weapon_system:
                        weapon_enum = ws
                        break
                
                ammo_enum = None
                for a in AmmunitionType:
                    if a.value == ammunition:
                        ammo_enum = a
                        break
                
                charge_enum = None
                if charge != "Auto Select":
                    for c in ChargeType:
                        if c.value == charge:
                            charge_enum = c
                            break
                
                temp_unit = FiringUnit(
                    call_sign="TEMP",
                    grid_coordinates=gun_grid,
                    elevation_meters=gun_elevation,
                    weapon_system=weapon_enum,
                    ammunition_available={ammo_enum: 100}
                )
                
                temp_target = Target(
                    designation="TEMP",
                    grid_coordinates=target_grid,
                    elevation_meters=target_elevation,
                    description="Manual calculation"
                )
                
                solution = self.ballistic_computer.calculate_firing_solution(
                    temp_unit, temp_target, ammo_enum, charge_enum
                )
                
                if solution:
                    st.success("✅ Firing Solution Calculated")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Range", f"{solution.range_meters}m")
                        st.metric("Azimuth", f"{solution.azimuth_mils:04d} mils")
                    
                    with col2:
                        st.metric("Elevation", f"{solution.elevation_mils:04d} mils")
                        st.metric("Charge", solution.charge.value)
                    
                    with col3:
                        st.metric("Time of Flight", f"{solution.time_of_flight}s")
                        st.metric("Site Correction", f"{solution.site_correction} mils")
                else:
                    st.error("❌ No firing solution available for given parameters")
            else:
                st.error("Please provide valid 8-digit grid coordinates")
    
    def render_tactical_map(self, firing_units: List[FiringUnit], targets: List[Target]):
        """Render tactical situation map."""
        if not firing_units and not targets:
            return
        
        st.subheader("🗺️ Tactical Situation Map")
        
        fig = go.Figure()
        
        # Plot firing units
        for unit in firing_units:
            if len(unit.grid_coordinates) == 8:
                easting = int(unit.grid_coordinates[:4])
                northing = int(unit.grid_coordinates[4:])
                
                fig.add_trace(go.Scatter(
                    x=[easting],
                    y=[northing],
                    mode='markers+text',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='blue'
                    ),
                    text=[unit.call_sign],
                    textposition="top center",
                    name="Firing Units",
                    showlegend=True
                ))
        
        # Plot targets
        for target in targets:
            if len(target.grid_coordinates) == 8:
                easting = int(target.grid_coordinates[:4])
                northing = int(target.grid_coordinates[4:])
                
                fig.add_trace(go.Scatter(
                    x=[easting],
                    y=[northing],
                    mode='markers+text',
                    marker=dict(
                        symbol='x',
                        size=15,
                        color='red'
                    ),
                    text=[target.designation],
                    textposition="top center",
                    name="Targets",
                    showlegend=True
                ))
        
        fig.update_layout(
            title="Tactical Situation",
            xaxis_title="Easting (grid squares)",
            yaxis_title="Northing (grid squares)",
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_ammunition_status(self, firing_units: List[FiringUnit]):
        """Display ammunition status across all units."""
        if not firing_units:
            return
        
        st.subheader("📦 Ammunition Status")
        
        # Aggregate ammunition across all units
        total_ammo = {}
        for unit in firing_units:
            for ammo_type, count in unit.ammunition_available.items():
                if ammo_type not in total_ammo:
                    total_ammo[ammo_type] = 0
                total_ammo[ammo_type] += count
        
        # Display as metrics
        cols = st.columns(len(total_ammo))
        for i, (ammo_type, count) in enumerate(total_ammo.items()):
            with cols[i]:
                st.metric(ammo_type.value, count)
        
        # Detailed unit breakdown
        with st.expander("Detailed Unit Breakdown"):
            for unit in firing_units:
                st.write(f"**{unit.call_sign}** ({unit.weapon_system.value})")
                unit_data = []
                for ammo_type, count in unit.ammunition_available.items():
                    unit_data.append({
                        "Ammunition": ammo_type.value,
                        "Available": count
                    })
                
                df = pd.DataFrame(unit_data)
                st.dataframe(df, width='stretch')
    
    def _generate_fire_mission_message(self, 
                                     target: Target, 
                                     unit: FiringUnit, 
                                     solution: FiringData,
                                     rounds: int) -> str:
        """Generate formatted fire mission message."""
        timestamp = datetime.now().strftime("%d%H%M%S%b%y").upper()
        
        message_lines = [
            f"FIRE MISSION - {timestamp}",
            f"TO: {unit.call_sign}",
            f"FM: FDC",
            "",
            f"TARGET: {target.designation}",
            f"GRID: {target.grid_coordinates}",
            f"ELEVATION: {target.elevation_meters}M",
            f"DESCRIPTION: {target.description}",
            "",
            f"MISSION: {solution.ammunition.value}",
            f"CHARGE: {solution.charge.value}",
            f"AZIMUTH: {solution.azimuth_mils:04d}",
            f"ELEVATION: {solution.elevation_mils:04d}",
            f"RANGE: {solution.range_meters}M",
            f"ROUNDS: {rounds}",
            f"METHOD: AT MY COMMAND",
            f"DISTRIBUTION: CONVERGED",
            "",
            f"TIME OF FLIGHT: {solution.time_of_flight} SECONDS",
            f"PRIORITY: {target.priority}",
            f"OBSERVER: {target.observer}",
            "",
            "READY TO FIRE - ACKNOWLEDGE"
        ]
        
        return "\n".join(message_lines)

def render_military_sidebar():
    """Render military-specific sidebar with quick references."""
    with st.sidebar:
        st.header("🎖️ Military Reference")
        
        with st.expander("Quick Reference"):
            st.write("**Grid Coordinates**")
            st.write("- Use 8-digit MGRS format")
            st.write("- Example: 12345678")
            
            st.write("**Charges**")
            st.write("- Lower charges = shorter range")
            st.write("- Higher charges = longer range")
            
            st.write("**Ammunition Types**")
            st.write("- HE: High Explosive")
            st.write("- SMOKE: Screening")
            st.write("- ILLUM: Illumination")
            st.write("- WP: White Phosphorus")
        
        with st.expander("Mission Types"):
            st.write("- **DESTROY**: Complete destruction")
            st.write("- **NEUTRALIZE**: Temporary suppression")
            st.write("- **SUPPRESS**: Prevent effective fire")
            st.write("- **HARASS**: Deny movement")
        
        with st.expander("Weapon Systems"):
            for weapon in WeaponSystem:
                st.write(f"- {weapon.value}")
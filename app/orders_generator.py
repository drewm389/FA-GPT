"""
Military Orders Generation System

Automated generation of artillery fire orders, mission planning templates,
and tactical decision support documents based on U.S. Army doctrine.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from .ballistic_computer import (
    Target, FiringUnit, FiringData, WeaponSystem, 
    AmmunitionType, ChargeType
)

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Types of military orders."""
    FIRE_ORDER = "Fire Order"
    OPERATION_ORDER = "Operation Order (OPORD)"
    FRAGMENTARY_ORDER = "Fragmentary Order (FRAGO)"
    WARNING_ORDER = "Warning Order (WARNO)"
    FIRE_SUPPORT_PLAN = "Fire Support Plan"

class MissionPriority(Enum):
    """Fire mission priority levels."""
    IMMEDIATE = "IMMEDIATE"
    PRIORITY = "PRIORITY"
    ROUTINE = "ROUTINE"

class MethodOfFire(Enum):
    """Methods of fire control."""
    AT_MY_COMMAND = "AT MY COMMAND"
    WHEN_READY = "WHEN READY"
    TIME_ON_TARGET = "TIME ON TARGET"
    CONTINUOUS_FIRE = "CONTINUOUS FIRE"

@dataclass
class FireOrder:
    """Complete fire order with all tactical information."""
    order_id: str
    timestamp: datetime
    target: Target
    firing_unit: FiringUnit
    firing_data: FiringData
    rounds: int
    method_of_fire: MethodOfFire
    priority: MissionPriority
    observer: str
    fire_direction_center: str
    estimated_time_of_fire: Optional[datetime] = None
    restrictions: List[str] = None
    coordination_requirements: List[str] = None

@dataclass
class FireSupportPlan:
    """Comprehensive fire support plan for operations."""
    plan_id: str
    operation_name: str
    planning_unit: str
    effective_time: datetime
    targets: List[Target]
    firing_units: List[FiringUnit]
    coordination_measures: Dict[str, Any]
    ammunition_allocation: Dict[str, int]
    priority_of_fires: List[str]
    restrictions: List[str]

class OrdersGenerator:
    """
    Military orders generation system for artillery operations.
    
    Generates standardized military orders following U.S. Army doctrine
    and formatting standards.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.order_templates = self._load_order_templates()
    
    def _load_order_templates(self) -> Dict[str, str]:
        """Load military order templates."""
        return {
            "fire_order": """
FIRE ORDER {order_id}
DTG: {dtg}
FM: {fdc}
TO: {firing_unit}

MISSION TYPE: {mission_type}
TARGET: {target_designation}
LOCATION: {target_location}
ELEVATION: {target_elevation}M
DESCRIPTION: {target_description}

AMMUNITION: {ammunition}
CHARGE: {charge}
FUZE: {fuze}
ROUNDS: {rounds}

FIRE DATA:
AZIMUTH: {azimuth}
ELEVATION: {elevation}
RANGE: {range}M
TIME OF FLIGHT: {tof}S

METHOD OF FIRE: {method_of_fire}
PRIORITY: {priority}
OBSERVER: {observer}

{restrictions}

{coordination}

READY TO FIRE - ACKNOWLEDGE
""",
            
            "fire_support_plan": """
FIRE SUPPORT PLAN
OPERATION: {operation_name}
PLANNING UNIT: {planning_unit}
DTG: {dtg}
EFFECTIVE: {effective_time}

1. SITUATION
   a. Enemy Forces: {enemy_situation}
   b. Friendly Forces: {friendly_situation}
   c. Attachments and Detachments: {attachments}

2. MISSION
   {mission_statement}

3. EXECUTION
   a. Concept of Fire Support: {concept_of_fires}
   b. Tasks to Subordinate Units:
      {subordinate_tasks}
   c. Coordinating Instructions:
      {coordinating_instructions}

4. ADMINISTRATION AND LOGISTICS
   a. Ammunition: {ammunition_plan}
   b. Supply: {supply_plan}

5. COMMAND AND SIGNAL
   a. Command: {command_structure}
   b. Signal: {signal_plan}

ACKNOWLEDGE
""",
            
            "operation_order": """
OPERATION ORDER {order_number}
{classification}
HEADQUARTERS, {unit_designation}
{location}
{dtg}

MAPS: {maps}

1. SITUATION
   a. Area of Interest: {area_of_interest}
   b. Area of Operations: {area_of_operations}
   c. Enemy Forces: {enemy_forces}
   d. Friendly Forces: {friendly_forces}
   e. Interagency, Intergovernmental, and Nongovernmental Organizations: {ingo}
   f. Civil Considerations: {civil_considerations}
   g. Attachments and Detachments: {attachments}

2. MISSION
   {mission_statement}

3. EXECUTION
   a. Commander's Intent: {commanders_intent}
   b. Concept of Operations: {concept_of_operations}
   c. Tasks to Subordinate Units:
      {subordinate_tasks}
   d. Coordinating Instructions:
      {coordinating_instructions}

4. SUSTAINMENT
   a. Logistics: {logistics}
   b. Personnel: {personnel}
   c. Health Service Support: {health_service}

5. COMMAND AND CONTROL
   a. Command: {command}
   b. Control: {control}

ACKNOWLEDGE
{classification}
"""
        }
    
    def generate_fire_order(self, 
                          target: Target,
                          firing_unit: FiringUnit,
                          firing_data: FiringData,
                          rounds: int = 4,
                          method_of_fire: MethodOfFire = MethodOfFire.AT_MY_COMMAND,
                          fdc_call_sign: str = "STEEL FDC",
                          fuze_type: str = "PD") -> FireOrder:
        """Generate complete fire order."""
        
        order_id = f"FO{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:4].upper()}"
        
        fire_order = FireOrder(
            order_id=order_id,
            timestamp=datetime.now(),
            target=target,
            firing_unit=firing_unit,
            firing_data=firing_data,
            rounds=rounds,
            method_of_fire=method_of_fire,
            priority=MissionPriority(target.priority),
            observer=target.observer,
            fire_direction_center=fdc_call_sign
        )
        
        return fire_order
    
    def format_fire_order(self, fire_order: FireOrder) -> str:
        """Format fire order as standardized military message."""
        
        # Generate restrictions text
        restrictions_text = ""
        if fire_order.restrictions:
            restrictions_text = "RESTRICTIONS:\n" + "\n".join(f"- {r}" for r in fire_order.restrictions)
        
        # Generate coordination text
        coordination_text = ""
        if fire_order.coordination_requirements:
            coordination_text = "COORDINATION:\n" + "\n".join(f"- {c}" for c in fire_order.coordination_requirements)
        
        # Format the order
        formatted_order = self.order_templates["fire_order"].format(
            order_id=fire_order.order_id,
            dtg=fire_order.timestamp.strftime("%d%H%M%S%b%y").upper(),
            fdc=fire_order.fire_direction_center,
            firing_unit=fire_order.firing_unit.call_sign,
            mission_type="FIRE FOR EFFECT",
            target_designation=fire_order.target.designation,
            target_location=fire_order.target.grid_coordinates,
            target_elevation=fire_order.target.elevation_meters,
            target_description=fire_order.target.description,
            ammunition=fire_order.firing_data.ammunition.value,
            charge=fire_order.firing_data.charge.value,
            fuze="PD",  # Point Detonating - default
            rounds=fire_order.rounds,
            azimuth=f"{fire_order.firing_data.azimuth_mils:04d}",
            elevation=f"{fire_order.firing_data.elevation_mils:04d}",
            range=fire_order.firing_data.range_meters,
            tof=fire_order.firing_data.time_of_flight,
            method_of_fire=fire_order.method_of_fire.value,
            priority=fire_order.priority.value,
            observer=fire_order.observer,
            restrictions=restrictions_text,
            coordination=coordination_text
        )
        
        return formatted_order
    
    def generate_fire_support_plan(self,
                                 operation_name: str,
                                 planning_unit: str,
                                 targets: List[Target],
                                 firing_units: List[FiringUnit],
                                 effective_time: datetime,
                                 enemy_situation: str = "TBD",
                                 friendly_situation: str = "TBD") -> FireSupportPlan:
        """Generate comprehensive fire support plan."""
        
        plan_id = f"FSP{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:4].upper()}"
        
        # Calculate ammunition allocation
        ammunition_allocation = {}
        for unit in firing_units:
            for ammo_type, count in unit.ammunition_available.items():
                if ammo_type.value not in ammunition_allocation:
                    ammunition_allocation[ammo_type.value] = 0
                ammunition_allocation[ammo_type.value] += count
        
        # Set priority of fires based on target priority
        priority_targets = sorted(targets, 
                                key=lambda t: ["IMMEDIATE", "PRIORITY", "ROUTINE"].index(t.priority))
        priority_of_fires = [t.designation for t in priority_targets]
        
        # Standard coordination measures
        coordination_measures = {
            "no_fire_areas": [],
            "restricted_fire_areas": [],
            "fire_support_coordination_line": "TBD",
            "coordinated_fire_line": "TBD"
        }
        
        plan = FireSupportPlan(
            plan_id=plan_id,
            operation_name=operation_name,
            planning_unit=planning_unit,
            effective_time=effective_time,
            targets=targets,
            firing_units=firing_units,
            coordination_measures=coordination_measures,
            ammunition_allocation=ammunition_allocation,
            priority_of_fires=priority_of_fires,
            restrictions=[]
        )
        
        return plan
    
    def format_fire_support_plan(self, plan: FireSupportPlan) -> str:
        """Format fire support plan as military document."""
        
        # Format subordinate tasks
        subordinate_tasks = []
        for i, unit in enumerate(plan.firing_units, 1):
            task = f"   ({i}) {unit.call_sign}: Provide fire support IAW fire support plan"
            subordinate_tasks.append(task)
        
        # Format ammunition plan
        ammo_lines = []
        for ammo_type, count in plan.ammunition_allocation.items():
            ammo_lines.append(f"      - {ammo_type}: {count} rounds")
        ammunition_plan = "\n".join(ammo_lines)
        
        # Format coordinating instructions
        coord_instructions = [
            f"   (1) Priority of Fires: {', '.join(plan.priority_of_fires)}",
            "   (2) Fire Support Coordination Measures IAW Annex D (Fire Support)",
            "   (3) All fires must be coordinated through FDC",
            "   (4) Observe standard safety procedures"
        ]
        
        formatted_plan = self.order_templates["fire_support_plan"].format(
            operation_name=plan.operation_name,
            planning_unit=plan.planning_unit,
            dtg=datetime.now().strftime("%d%H%M%S%b%y").upper(),
            effective_time=plan.effective_time.strftime("%d%H%M%S%b%y").upper(),
            enemy_situation="Enemy artillery positions identified at multiple locations",
            friendly_situation="Friendly forces conducting offensive operations",
            attachments="None",
            mission_statement=f"Provide fire support for {plan.operation_name}",
            concept_of_fires="Massed fires on priority targets, sequential engagement",
            subordinate_tasks="\n".join(subordinate_tasks),
            coordinating_instructions="\n".join(coord_instructions),
            ammunition_plan=ammunition_plan,
            supply_plan="Standard Class V resupply procedures",
            command_structure=f"{plan.planning_unit} FDC maintains fire direction",
            signal_plan="Primary: FM, Alternate: Digital"
        )
        
        return formatted_plan
    
    def generate_operation_order(self,
                               order_number: str,
                               unit_designation: str,
                               location: str,
                               mission_statement: str,
                               commanders_intent: str,
                               concept_of_operations: str,
                               classification: str = "UNCLASSIFIED") -> str:
        """Generate operation order (OPORD)."""
        
        formatted_order = self.order_templates["operation_order"].format(
            order_number=order_number,
            classification=classification,
            unit_designation=unit_designation,
            location=location,
            dtg=datetime.now().strftime("%d%H%M%S%b%y").upper(),
            maps="TBD",
            area_of_interest="TBD",
            area_of_operations="TBD",
            enemy_forces="TBD",
            friendly_forces="TBD",
            ingo="None",
            civil_considerations="TBD",
            attachments="TBD",
            mission_statement=mission_statement,
            commanders_intent=commanders_intent,
            concept_of_operations=concept_of_operations,
            subordinate_tasks="TBD",
            coordinating_instructions="TBD",
            logistics="Standard resupply procedures",
            personnel="Standard personnel procedures",
            health_service="Standard medical support",
            command="As per SOP",
            control="FM and digital communications"
        )
        
        return formatted_order
    
    def generate_target_list(self, targets: List[Target]) -> str:
        """Generate formatted target list."""
        
        target_list = ["TARGET LIST", "="*50, ""]
        
        for i, target in enumerate(targets, 1):
            target_info = [
                f"{i}. TARGET: {target.designation}",
                f"   GRID: {target.grid_coordinates}",
                f"   ELEVATION: {target.elevation_meters}M",
                f"   DESCRIPTION: {target.description}",
                f"   PRIORITY: {target.priority}",
                f"   OBSERVER: {target.observer}",
                ""
            ]
            target_list.extend(target_info)
        
        return "\n".join(target_list)
    
    def generate_unit_status_report(self, firing_units: List[FiringUnit]) -> str:
        """Generate unit status report."""
        
        report = ["UNIT STATUS REPORT", "="*50, ""]
        
        for unit in firing_units:
            unit_info = [
                f"UNIT: {unit.call_sign}",
                f"LOCATION: {unit.grid_coordinates}",
                f"ELEVATION: {unit.elevation_meters}M",
                f"WEAPON SYSTEM: {unit.weapon_system.value}",
                "AMMUNITION STATUS:"
            ]
            
            for ammo_type, count in unit.ammunition_available.items():
                unit_info.append(f"  - {ammo_type.value}: {count} rounds")
            
            unit_info.extend(["", "STATUS: MISSION CAPABLE", ""])
            report.extend(unit_info)
        
        return "\n".join(report)
    
    def export_order_as_json(self, order: Any) -> str:
        """Export any order object as JSON for digital transmission."""
        try:
            if hasattr(order, '__dict__'):
                # Handle dataclass objects
                order_dict = asdict(order) if hasattr(order, '__dataclass_fields__') else order.__dict__
                
                # Convert datetime objects to strings
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: convert_datetime(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_datetime(item) for item in obj]
                    elif hasattr(obj, 'value'):  # Enum objects
                        return obj.value
                    elif hasattr(obj, '__dict__'):
                        return convert_datetime(obj.__dict__)
                    return obj
                
                converted_dict = convert_datetime(order_dict)
                return json.dumps(converted_dict, indent=2)
            else:
                return json.dumps(order, indent=2)
        except Exception as e:
            self.logger.error(f"Error exporting order as JSON: {e}")
            return "{\"error\": \"Export failed\"}"

class TacticalDecisionSupport:
    """
    Tactical decision support tools for artillery operations.
    
    Provides analytical tools for target prioritization, resource allocation,
    and tactical planning support.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def prioritize_targets(self, targets: List[Target], 
                          threat_assessment: Dict[str, int] = None) -> List[Target]:
        """
        Prioritize targets based on threat level and tactical importance.
        
        Args:
            targets: List of targets to prioritize
            threat_assessment: Optional threat scores for each target
            
        Returns:
            Sorted list of targets by priority
        """
        if not threat_assessment:
            threat_assessment = {}
        
        def priority_score(target: Target) -> int:
            """Calculate priority score for target."""
            base_score = {
                "IMMEDIATE": 100,
                "PRIORITY": 50,
                "ROUTINE": 10
            }.get(target.priority, 10)
            
            # Add threat assessment bonus
            threat_bonus = threat_assessment.get(target.designation, 0)
            
            return base_score + threat_bonus
        
        return sorted(targets, key=priority_score, reverse=True)
    
    def calculate_ammunition_requirements(self, 
                                        targets: List[Target],
                                        mission_types: Dict[str, str] = None) -> Dict[str, int]:
        """Calculate total ammunition requirements for target list."""
        if not mission_types:
            mission_types = {target.designation: "DESTROY" for target in targets}
        
        # Standard ammunition requirements by mission type
        ammo_requirements = {
            "DESTROY": {"HE": 4, "SMOKE": 1},
            "NEUTRALIZE": {"HE": 6, "SMOKE": 2},
            "SUPPRESS": {"HE": 2, "SMOKE": 3},
            "HARASS": {"HE": 1, "SMOKE": 1}
        }
        
        total_requirements = {}
        
        for target in targets:
            mission_type = mission_types.get(target.designation, "DESTROY")
            requirements = ammo_requirements.get(mission_type, {"HE": 2})
            
            for ammo_type, count in requirements.items():
                if ammo_type not in total_requirements:
                    total_requirements[ammo_type] = 0
                total_requirements[ammo_type] += count
        
        return total_requirements
    
    def assess_unit_capability(self, firing_unit: FiringUnit, targets: List[Target]) -> Dict:
        """Assess firing unit capability against target list."""
        
        capability_assessment = {
            "unit": firing_unit.call_sign,
            "engageable_targets": 0,
            "ammunition_sufficient": True,
            "range_limitations": [],
            "recommendations": []
        }
        
        # Check each target
        for target in targets:
            # Simple range calculation (would use ballistic computer in practice)
            # This is a simplified version for demonstration
            try:
                gun_easting = int(firing_unit.grid_coordinates[:4]) * 100
                gun_northing = int(firing_unit.grid_coordinates[4:]) * 100
                target_easting = int(target.grid_coordinates[:4]) * 100
                target_northing = int(target.grid_coordinates[4:]) * 100
                
                range_meters = int(((target_easting - gun_easting)**2 + 
                                  (target_northing - gun_northing)**2)**0.5)
                
                if firing_unit.min_range_meters <= range_meters <= firing_unit.max_range_meters:
                    capability_assessment["engageable_targets"] += 1
                else:
                    capability_assessment["range_limitations"].append(
                        f"{target.designation}: {range_meters}m"
                    )
            except:
                continue
        
        # Check ammunition sufficiency
        total_he_available = firing_unit.ammunition_available.get(AmmunitionType.HE, 0)
        if total_he_available < len(targets) * 2:  # Minimum 2 rounds per target
            capability_assessment["ammunition_sufficient"] = False
            capability_assessment["recommendations"].append(
                "Request additional HE ammunition"
            )
        
        # Generate recommendations
        if capability_assessment["engageable_targets"] < len(targets):
            capability_assessment["recommendations"].append(
                "Coordinate with additional firing units for full target coverage"
            )
        
        return capability_assessment
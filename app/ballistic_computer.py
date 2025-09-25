"""
Ballistic Computer for Field Artillery Fire Support

This module implements manual gunnery calculations and ballistic computations
based on U.S. Army Field Artillery doctrine and firing tables.
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChargeType(Enum):
    """Standard artillery charge types."""
    CHARGE_1 = "1"
    CHARGE_2 = "2"
    CHARGE_3 = "3"
    CHARGE_4 = "4"
    CHARGE_5 = "5"
    CHARGE_6 = "6"
    CHARGE_7 = "7"
    GREEN_BAG = "GB"
    WHITE_BAG = "WB"
    RED_BAG = "RB"

class AmmunitionType(Enum):
    """Standard ammunition types."""
    HE = "High Explosive"
    SMOKE = "Smoke"
    ILLUM = "Illumination"
    WP = "White Phosphorus"
    DPICM = "Dual Purpose Improved Conventional Munition"
    EXCALIBUR = "Excalibur Precision Guided"

class WeaponSystem(Enum):
    """Supported weapon systems."""
    M777A2 = "M777A2 155mm Towed Howitzer"
    M109A6 = "M109A6 Paladin 155mm Self-Propelled"
    M119A3 = "M119A3 105mm Towed Howitzer"
    M252 = "M252 81mm Mortar"

@dataclass
class FiringData:
    """Firing data for a specific target engagement."""
    weapon_system: WeaponSystem
    ammunition: AmmunitionType
    charge: ChargeType
    range_meters: int
    azimuth_mils: int
    elevation_mils: int
    time_of_flight: float
    deflection_left: int = 0
    deflection_right: int = 0
    site_correction: int = 0

@dataclass
class Target:
    """Target information for fire mission planning."""
    designation: str
    grid_coordinates: str
    elevation_meters: int
    description: str
    priority: str = "ROUTINE"
    observer: str = "UNKNOWN"

@dataclass
class FiringUnit:
    """Firing unit position and characteristics."""
    call_sign: str
    grid_coordinates: str
    elevation_meters: int
    weapon_system: WeaponSystem
    ammunition_available: Dict[AmmunitionType, int]
    min_range_meters: int = 200
    max_range_meters: int = 30000

class BallisticComputer:
    """
    Main ballistic computer class implementing manual gunnery calculations.
    
    Based on firing tables and ballistic principles from TC 3-09.81
    Field Artillery Manual - Cannon Gunnery.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.firing_tables = self._initialize_firing_tables()
        self.meteorological_data = self._get_standard_met_data()
        
    def _initialize_firing_tables(self) -> Dict:
        """Initialize simplified firing tables for common weapon systems."""
        # Simplified firing table data - in production would come from official tables
        return {
            WeaponSystem.M777A2: {
                AmmunitionType.HE: {
                    ChargeType.CHARGE_1: {"max_range": 8800, "muzzle_velocity": 241},
                    ChargeType.CHARGE_2: {"max_range": 11500, "muzzle_velocity": 309},
                    ChargeType.CHARGE_3: {"max_range": 14600, "muzzle_velocity": 393},
                    ChargeType.CHARGE_4: {"max_range": 17700, "muzzle_velocity": 479},
                    ChargeType.CHARGE_5: {"max_range": 22400, "muzzle_velocity": 594},
                    ChargeType.GREEN_BAG: {"max_range": 24700, "muzzle_velocity": 684},
                    ChargeType.WHITE_BAG: {"max_range": 30000, "muzzle_velocity": 827}
                }
            },
            WeaponSystem.M119A3: {
                AmmunitionType.HE: {
                    ChargeType.CHARGE_1: {"max_range": 2500, "muzzle_velocity": 153},
                    ChargeType.CHARGE_2: {"max_range": 4200, "muzzle_velocity": 201},
                    ChargeType.CHARGE_3: {"max_range": 5900, "muzzle_velocity": 245},
                    ChargeType.CHARGE_4: {"max_range": 7500, "muzzle_velocity": 295},
                    ChargeType.CHARGE_5: {"max_range": 8800, "muzzle_velocity": 330},
                    ChargeType.CHARGE_6: {"max_range": 10200, "muzzle_velocity": 368},
                    ChargeType.CHARGE_7: {"max_range": 11500, "muzzle_velocity": 400}
                }
            }
        }
    
    def _get_standard_met_data(self) -> Dict:
        """Get standard meteorological conditions."""
        return {
            "temperature_celsius": 15,
            "pressure_mb": 1013.25,
            "humidity_percent": 78,
            "wind_direction_mils": 0,
            "wind_speed_mps": 0
        }
    
    def calculate_firing_solution(self, 
                                firing_unit: FiringUnit, 
                                target: Target,
                                ammunition: AmmunitionType = AmmunitionType.HE,
                                preferred_charge: Optional[ChargeType] = None) -> Optional[FiringData]:
        """
        Calculate complete firing solution for target engagement.
        
        Args:
            firing_unit: Firing unit position and capabilities
            target: Target information
            ammunition: Type of ammunition to use
            preferred_charge: Preferred charge (if None, optimal will be selected)
            
        Returns:
            FiringData object with complete firing solution or None if no solution
        """
        try:
            # Calculate range and azimuth to target
            range_meters, azimuth_mils = self._calculate_range_azimuth(
                firing_unit.grid_coordinates, 
                target.grid_coordinates
            )
            
            # Check if target is within engagement envelope
            if not self._validate_engagement_envelope(firing_unit, range_meters):
                self.logger.warning(f"Target {target.designation} outside engagement envelope")
                return None
            
            # Select optimal charge if not specified
            if preferred_charge is None:
                optimal_charge = self._select_optimal_charge(
                    firing_unit.weapon_system, ammunition, range_meters
                )
            else:
                optimal_charge = preferred_charge
            
            if optimal_charge is None:
                self.logger.error(f"No suitable charge found for range {range_meters}m")
                return None
            
            # Calculate elevation and time of flight
            elevation_mils = self._calculate_elevation(
                firing_unit.weapon_system, ammunition, optimal_charge, range_meters
            )
            
            time_of_flight = self._calculate_time_of_flight(
                firing_unit.weapon_system, ammunition, optimal_charge, range_meters
            )
            
            # Apply site correction for elevation difference
            site_correction = self._calculate_site_correction(
                firing_unit.elevation_meters, target.elevation_meters, range_meters
            )
            
            return FiringData(
                weapon_system=firing_unit.weapon_system,
                ammunition=ammunition,
                charge=optimal_charge,
                range_meters=range_meters,
                azimuth_mils=azimuth_mils,
                elevation_mils=elevation_mils + site_correction,
                time_of_flight=time_of_flight,
                site_correction=site_correction
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating firing solution: {e}")
            return None
    
    def _calculate_range_azimuth(self, gun_grid: str, target_grid: str) -> Tuple[int, int]:
        """
        Calculate range and azimuth from gun to target.
        
        Simplified implementation - production version would use proper
        military grid coordinate system calculations.
        """
        # Extract coordinates (simplified 8-digit grid)
        # Each digit represents 10 meters (not 100m as originally coded)
        gun_easting = int(gun_grid[:4]) * 10
        gun_northing = int(gun_grid[4:]) * 10
        target_easting = int(target_grid[:4]) * 10
        target_northing = int(target_grid[4:]) * 10
        
        # Calculate differences
        delta_easting = target_easting - gun_easting
        delta_northing = target_northing - gun_northing
        
        # Calculate range
        range_meters = int(math.sqrt(delta_easting**2 + delta_northing**2))
        
        # Calculate azimuth in mils (6400 mils = 360 degrees)
        azimuth_radians = math.atan2(delta_easting, delta_northing)
        azimuth_mils = int((azimuth_radians * 6400) / (2 * math.pi))
        
        # Ensure positive azimuth
        if azimuth_mils < 0:
            azimuth_mils += 6400
            
        return range_meters, azimuth_mils
    
    def _validate_engagement_envelope(self, firing_unit: FiringUnit, range_meters: int) -> bool:
        """Validate target is within weapon engagement envelope."""
        return firing_unit.min_range_meters <= range_meters <= firing_unit.max_range_meters
    
    def _select_optimal_charge(self, 
                              weapon: WeaponSystem, 
                              ammo: AmmunitionType, 
                              range_meters: int) -> Optional[ChargeType]:
        """Select optimal charge for given range."""
        if weapon not in self.firing_tables or ammo not in self.firing_tables[weapon]:
            return None
        
        charges = self.firing_tables[weapon][ammo]
        
        # Find the minimum charge that can reach the target
        for charge, data in charges.items():
            if data["max_range"] >= range_meters:
                return charge
        
        return None
    
    def _calculate_elevation(self, 
                           weapon: WeaponSystem, 
                           ammo: AmmunitionType, 
                           charge: ChargeType, 
                           range_meters: int) -> int:
        """
        Calculate elevation angle in mils for given range.
        
        Simplified ballistic calculation - production version would use
        complete firing tables and ballistic coefficients.
        """
        if weapon not in self.firing_tables or ammo not in self.firing_tables[weapon]:
            return 800  # Default elevation
        
        charge_data = self.firing_tables[weapon][ammo].get(charge)
        if not charge_data:
            return 800
        
        muzzle_velocity = charge_data["muzzle_velocity"]
        max_range = charge_data["max_range"]
        
        # Simplified elevation calculation using ballistic approximation
        # Actual firing tables would provide exact elevation data
        g = 9.81  # gravity
        v0 = muzzle_velocity
        
        # Calculate optimal angle for maximum range
        max_angle_rad = math.pi / 4  # 45 degrees for max range
        
        # Scale angle based on desired range vs max range
        range_ratio = range_meters / max_range
        angle_rad = max_angle_rad * range_ratio
        
        # Convert to mils (1 radian = 1000 mils approximately)
        elevation_mils = int(angle_rad * 1000)
        
        # Ensure reasonable elevation limits
        elevation_mils = max(50, min(1600, elevation_mils))
        
        return elevation_mils
    
    def _calculate_time_of_flight(self, 
                                weapon: WeaponSystem, 
                                ammo: AmmunitionType, 
                                charge: ChargeType, 
                                range_meters: int) -> float:
        """Calculate time of flight in seconds."""
        if weapon not in self.firing_tables or ammo not in self.firing_tables[weapon]:
            return 30.0  # Default TOF
        
        charge_data = self.firing_tables[weapon][ammo].get(charge)
        if not charge_data:
            return 30.0
        
        muzzle_velocity = charge_data["muzzle_velocity"]
        
        # Simplified TOF calculation
        # Actual calculation would consider ballistic coefficient and trajectory
        time_of_flight = range_meters / (muzzle_velocity * 0.7)  # Approximation
        
        return round(time_of_flight, 1)
    
    def _calculate_site_correction(self, 
                                 gun_elevation: int, 
                                 target_elevation: int, 
                                 range_meters: int) -> int:
        """Calculate site correction for elevation difference."""
        elevation_diff = target_elevation - gun_elevation
        
        # Site correction in mils (simplified calculation)
        # 1 mil per 18 meters of elevation difference per 1000m range
        site_correction = int((elevation_diff * 1000) / (range_meters * 18))
        
        return site_correction
    
    def generate_fire_mission_data(self, firing_data: FiringData, rounds: int = 1) -> Dict:
        """Generate complete fire mission data for transmission."""
        return {
            "target_designation": "Unknown",
            "ammunition": firing_data.ammunition.value,
            "charge": firing_data.charge.value,
            "azimuth": f"{firing_data.azimuth_mils:04d}",
            "elevation": f"{firing_data.elevation_mils:04d}",
            "range": firing_data.range_meters,
            "time_of_flight": firing_data.time_of_flight,
            "rounds": rounds,
            "method_of_fire": "AT MY COMMAND",
            "distribution": "CONVERGED"
        }

class FireMissionPlanner:
    """
    Fire mission planning and coordination tools.
    
    Implements tactical decision support for artillery fire missions
    based on target analysis and unit capabilities.
    """
    
    def __init__(self):
        self.ballistic_computer = BallisticComputer()
        self.logger = logging.getLogger(__name__)
    
    def plan_fire_mission(self, 
                         firing_units: List[FiringUnit], 
                         target: Target,
                         mission_type: str = "DESTROY") -> Dict:
        """
        Plan complete fire mission with multiple units.
        
        Args:
            firing_units: Available firing units
            target: Target to engage
            mission_type: Type of fire mission (DESTROY, SUPPRESS, etc.)
            
        Returns:
            Complete fire mission plan
        """
        mission_plan = {
            "target": target,
            "mission_type": mission_type,
            "firing_solutions": [],
            "recommended_unit": None,
            "total_rounds": 0,
            "estimated_effects": None
        }
        
        # Calculate firing solutions for all units
        for unit in firing_units:
            solution = self.ballistic_computer.calculate_firing_solution(unit, target)
            if solution:
                mission_plan["firing_solutions"].append({
                    "unit": unit,
                    "solution": solution,
                    "ammunition_expenditure": self._calculate_ammunition_requirement(
                        mission_type, solution.ammunition
                    )
                })
        
        # Select optimal unit
        if mission_plan["firing_solutions"]:
            mission_plan["recommended_unit"] = self._select_optimal_unit(
                mission_plan["firing_solutions"]
            )
        
        return mission_plan
    
    def _calculate_ammunition_requirement(self, mission_type: str, ammo_type: AmmunitionType) -> int:
        """Calculate ammunition requirement based on mission type."""
        requirements = {
            "DESTROY": {AmmunitionType.HE: 4, AmmunitionType.DPICM: 2},
            "SUPPRESS": {AmmunitionType.HE: 2, AmmunitionType.SMOKE: 2},
            "NEUTRALIZE": {AmmunitionType.HE: 6, AmmunitionType.DPICM: 3},
            "HARASS": {AmmunitionType.HE: 1, AmmunitionType.SMOKE: 1}
        }
        
        return requirements.get(mission_type, {}).get(ammo_type, 2)
    
    def _select_optimal_unit(self, firing_solutions: List[Dict]) -> Dict:
        """Select optimal firing unit based on multiple criteria."""
        if not firing_solutions:
            return None
        
        # Score each solution (lower is better)
        scored_solutions = []
        for solution_data in firing_solutions:
            solution = solution_data["solution"]
            score = 0
            
            # Prefer shorter ranges (more accurate)
            score += solution.range_meters / 1000
            
            # Prefer lower charges (longer tube life)
            charge_scores = {
                ChargeType.CHARGE_1: 1, ChargeType.CHARGE_2: 2,
                ChargeType.CHARGE_3: 3, ChargeType.CHARGE_4: 4,
                ChargeType.CHARGE_5: 5, ChargeType.GREEN_BAG: 6,
                ChargeType.WHITE_BAG: 7, ChargeType.RED_BAG: 8
            }
            score += charge_scores.get(solution.charge, 5)
            
            scored_solutions.append((score, solution_data))
        
        # Return solution with lowest score
        return min(scored_solutions, key=lambda x: x[0])[1]
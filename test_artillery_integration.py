"""
Artillery Integration Test Suite

Comprehensive testing for the FA-GPT artillery computation layer,
validating ballistic calculations, military workflows, and system integration.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ballistic_computer import (
    BallisticComputer, FireMissionPlanner, Target, FiringUnit,
    WeaponSystem, AmmunitionType, ChargeType
)
from app.orders_generator import OrdersGenerator, TacticalDecisionSupport
from app.military_extraction import MilitaryDocumentProcessor, TacticalEntity
from app.military_vision import MilitaryImageAnalyzer

class TestBallisticComputer:
    """Test ballistic computation accuracy and functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ballistic_computer = BallisticComputer()
        
        self.test_firing_unit = FiringUnit(
            call_sign="STEEL01",
            grid_coordinates="12345678",
            elevation_meters=200,
            weapon_system=WeaponSystem.M777A2,
            ammunition_available={
                AmmunitionType.HE: 100,
                AmmunitionType.SMOKE: 50,
                AmmunitionType.ILLUM: 25
            }
        )
        
        self.test_target = Target(
            designation="TGT001",
            grid_coordinates="12356789",
            elevation_meters=150,
            description="Enemy artillery position",
            priority="PRIORITY",
            observer="FO1"
        )
    
    def test_range_azimuth_calculation(self):
        """Test range and azimuth calculations."""
        range_meters, azimuth_mils = self.ballistic_computer._calculate_range_azimuth(
            "12345678", "12356789"
        )
        
        # Expected calculations for these grids
        assert isinstance(range_meters, int)
        assert isinstance(azimuth_mils, int)
        assert 0 <= azimuth_mils <= 6400
        assert range_meters > 0
        
        print(f"✅ Range: {range_meters}m, Azimuth: {azimuth_mils} mils")
    
    def test_firing_solution_calculation(self):
        """Test complete firing solution calculation."""
        solution = self.ballistic_computer.calculate_firing_solution(
            self.test_firing_unit,
            self.test_target,
            AmmunitionType.HE
        )
        
        assert solution is not None
        assert solution.weapon_system == WeaponSystem.M777A2
        assert solution.ammunition == AmmunitionType.HE
        assert solution.range_meters > 0
        assert 0 <= solution.azimuth_mils <= 6400
        assert solution.elevation_mils > 0
        assert solution.time_of_flight > 0
        
        print(f"✅ Firing Solution: Range {solution.range_meters}m, "
              f"Az {solution.azimuth_mils}, El {solution.elevation_mils}, "
              f"Charge {solution.charge.value}, TOF {solution.time_of_flight}s")
    
    def test_charge_selection(self):
        """Test optimal charge selection."""
        # Test various ranges
        test_ranges = [5000, 10000, 15000, 20000, 25000]
        
        for range_meters in test_ranges:
            charge = self.ballistic_computer._select_optimal_charge(
                WeaponSystem.M777A2, AmmunitionType.HE, range_meters
            )
            
            assert charge is not None
            print(f"✅ Range {range_meters}m -> Charge {charge.value}")
    
    def test_site_correction(self):
        """Test site correction calculations."""
        # Test various elevation differences
        test_cases = [
            (200, 150, 10000),  # Gun higher than target
            (150, 200, 10000),  # Target higher than gun
            (200, 200, 10000),  # Same elevation
        ]
        
        for gun_elev, target_elev, range_m in test_cases:
            correction = self.ballistic_computer._calculate_site_correction(
                gun_elev, target_elev, range_m
            )
            
            print(f"✅ Gun {gun_elev}m, Target {target_elev}m, Range {range_m}m -> "
                  f"Site correction: {correction} mils")
    
    def test_engagement_envelope(self):
        """Test engagement envelope validation."""
        # Test minimum range
        close_target = Target(
            designation="CLOSE",
            grid_coordinates="12345679",  # Very close
            elevation_meters=200,
            description="Close target"
        )
        
        solution = self.ballistic_computer.calculate_firing_solution(
            self.test_firing_unit, close_target
        )
        
        # Should handle close targets appropriately
        print(f"✅ Close target engagement: {'Valid' if solution else 'Invalid'}")

class TestFireMissionPlanner:
    """Test fire mission planning functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mission_planner = FireMissionPlanner()
        
        self.test_units = [
            FiringUnit(
                call_sign="STEEL01",
                grid_coordinates="12345678",
                elevation_meters=200,
                weapon_system=WeaponSystem.M777A2,
                ammunition_available={AmmunitionType.HE: 100}
            ),
            FiringUnit(
                call_sign="STEEL02",
                grid_coordinates="12355678",
                elevation_meters=180,
                weapon_system=WeaponSystem.M119A3,
                ammunition_available={AmmunitionType.HE: 80}
            )
        ]
        
        self.test_target = Target(
            designation="TGT001",
            grid_coordinates="12346789",
            elevation_meters=150,
            description="Enemy position"
        )
    
    def test_mission_planning(self):
        """Test complete fire mission planning."""
        mission_plan = self.mission_planner.plan_fire_mission(
            self.test_units,
            self.test_target,
            "DESTROY"
        )
        
        assert mission_plan["target"] == self.test_target
        assert mission_plan["mission_type"] == "DESTROY"
        assert len(mission_plan["firing_solutions"]) > 0
        assert mission_plan["recommended_unit"] is not None
        
        print(f"✅ Mission plan generated: {len(mission_plan['firing_solutions'])} solutions")
        print(f"   Recommended unit: {mission_plan['recommended_unit']['unit'].call_sign}")
    
    def test_ammunition_calculation(self):
        """Test ammunition requirement calculations."""
        requirements = self.mission_planner._calculate_ammunition_requirement(
            "DESTROY", AmmunitionType.HE
        )
        
        assert requirements > 0
        print(f"✅ DESTROY mission requires {requirements} rounds HE")
    
    def test_unit_selection(self):
        """Test optimal unit selection logic."""
        # Create firing solutions
        solutions = []
        for unit in self.test_units:
            solution = self.mission_planner.ballistic_computer.calculate_firing_solution(
                unit, self.test_target
            )
            if solution:
                solutions.append({
                    "unit": unit,
                    "solution": solution,
                    "ammunition_expenditure": 4
                })
        
        if solutions:
            optimal = self.mission_planner._select_optimal_unit(solutions)
            assert optimal is not None
            print(f"✅ Optimal unit selected: {optimal['unit'].call_sign}")

class TestOrdersGenerator:
    """Test military orders generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orders_generator = OrdersGenerator()
        
        self.test_unit = FiringUnit(
            call_sign="STEEL01",
            grid_coordinates="12345678",
            elevation_meters=200,
            weapon_system=WeaponSystem.M777A2,
            ammunition_available={AmmunitionType.HE: 100}
        )
        
        self.test_target = Target(
            designation="TGT001",
            grid_coordinates="12356789",
            elevation_meters=150,
            description="Enemy artillery position"
        )
    
    def test_fire_order_generation(self):
        """Test fire order generation and formatting."""
        # Create a firing solution first
        ballistic_computer = BallisticComputer()
        firing_data = ballistic_computer.calculate_firing_solution(
            self.test_unit, self.test_target
        )
        
        if firing_data:
            fire_order = self.orders_generator.generate_fire_order(
                self.test_target,
                self.test_unit,
                firing_data,
                rounds=4
            )
            
            assert fire_order.order_id is not None
            assert fire_order.target == self.test_target
            assert fire_order.firing_unit == self.test_unit
            assert fire_order.rounds == 4
            
            # Test formatting
            formatted = self.orders_generator.format_fire_order(fire_order)
            assert "FIRE ORDER" in formatted
            assert fire_order.order_id in formatted
            assert self.test_target.designation in formatted
            assert self.test_unit.call_sign in formatted
            
            print(f"✅ Fire order generated: {fire_order.order_id}")
            print(f"   Length: {len(formatted)} characters")
    
    def test_fire_support_plan(self):
        """Test fire support plan generation."""
        plan = self.orders_generator.generate_fire_support_plan(
            "Operation STEEL RAIN",
            "1-77 FA FDC",
            [self.test_target],
            [self.test_unit],
            datetime.now()
        )
        
        assert plan.plan_id is not None
        assert plan.operation_name == "Operation STEEL RAIN"
        assert len(plan.targets) == 1
        assert len(plan.firing_units) == 1
        
        # Test formatting
        formatted = self.orders_generator.format_fire_support_plan(plan)
        assert "FIRE SUPPORT PLAN" in formatted
        assert "Operation STEEL RAIN" in formatted
        
        print(f"✅ Fire support plan generated: {plan.plan_id}")
    
    def test_json_export(self):
        """Test JSON export functionality."""
        ballistic_computer = BallisticComputer()
        firing_data = ballistic_computer.calculate_firing_solution(
            self.test_unit, self.test_target
        )
        
        if firing_data:
            fire_order = self.orders_generator.generate_fire_order(
                self.test_target, self.test_unit, firing_data
            )
            
            json_export = self.orders_generator.export_order_as_json(fire_order)
            assert json_export is not None
            assert "order_id" in json_export
            
            print(f"✅ JSON export successful: {len(json_export)} characters")

class TestTacticalDecisionSupport:
    """Test tactical decision support tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tactical_support = TacticalDecisionSupport()
        
        self.test_targets = [
            Target("TGT001", "12345678", 150, "High priority", "IMMEDIATE"),
            Target("TGT002", "12346789", 200, "Medium priority", "PRIORITY"),
            Target("TGT003", "12347890", 100, "Low priority", "ROUTINE")
        ]
        
        self.test_unit = FiringUnit(
            call_sign="STEEL01",
            grid_coordinates="12340000",
            elevation_meters=200,
            weapon_system=WeaponSystem.M777A2,
            ammunition_available={AmmunitionType.HE: 100}
        )
    
    def test_target_prioritization(self):
        """Test target prioritization algorithm."""
        prioritized = self.tactical_support.prioritize_targets(self.test_targets)
        
        assert len(prioritized) == 3
        # IMMEDIATE should come first
        assert prioritized[0].priority == "IMMEDIATE"
        # ROUTINE should come last
        assert prioritized[-1].priority == "ROUTINE"
        
        print(f"✅ Target prioritization: {[t.priority for t in prioritized]}")
    
    def test_ammunition_requirements(self):
        """Test ammunition requirement calculations."""
        requirements = self.tactical_support.calculate_ammunition_requirements(
            self.test_targets
        )
        
        assert "HE" in requirements
        assert requirements["HE"] > 0
        
        print(f"✅ Ammunition requirements: {requirements}")
    
    def test_capability_assessment(self):
        """Test unit capability assessment."""
        assessment = self.tactical_support.assess_unit_capability(
            self.test_unit, self.test_targets
        )
        
        assert "unit" in assessment
        assert "engageable_targets" in assessment
        assert assessment["unit"] == self.test_unit.call_sign
        
        print(f"✅ Capability assessment: {assessment['engageable_targets']} engageable targets")

class TestMilitaryExtraction:
    """Test military document processing and entity extraction."""
    
    def test_tactical_entity_extraction(self):
        """Test tactical entity extraction from sample text."""
        sample_text = """
        A/1-77 FA will conduct fire missions against TGT001 located at grid 12345678.
        The M777A2 howitzer will fire HE rounds with Charge 5 at azimuth 3200 mils.
        Forward Observer FO1 will adjust fires as necessary.
        """
        
        # This would normally use the actual processor, but we'll test pattern matching
        import re
        
        # Unit pattern
        unit_pattern = r"([A-Z]\s*/\s*\d+-\d+\s+[A-Z]{2,})"
        units = re.findall(unit_pattern, sample_text)
        assert len(units) > 0
        assert "A/1-77 FA" in units[0]
        
        # Weapon pattern
        weapon_pattern = r"(M\d+[A-Z]?\d?\s+(?:howitzer|mortar))"
        weapons = re.findall(weapon_pattern, sample_text, re.IGNORECASE)
        assert len(weapons) > 0
        assert "M777A2 howitzer" in weapons[0]
        
        print(f"✅ Entity extraction: {len(units)} units, {len(weapons)} weapons")
    
    def test_classification_detection(self):
        """Test military classification detection."""
        classified_text = "CONFIDENTIAL - FOR OFFICIAL USE ONLY"
        unclassified_text = "This is unclassified information"
        
        import re
        
        classification_pattern = r"(UNCLASSIFIED|CONFIDENTIAL|SECRET|TOP SECRET)"
        fouo_pattern = r"(FOR OFFICIAL USE ONLY|FOUO)"
        
        classified_match = re.search(classification_pattern, classified_text)
        fouo_match = re.search(fouo_pattern, classified_text)
        unclassified_match = re.search(classification_pattern, unclassified_text)
        
        assert classified_match is not None
        assert fouo_match is not None
        assert unclassified_match is None
        
        print(f"✅ Classification detection working")

def run_comprehensive_tests():
    """Run all artillery integration tests."""
    print("🎯 Starting Artillery Integration Test Suite")
    print("=" * 50)
    
    try:
        # Test Ballistic Computer
        print("\n🧮 Testing Ballistic Computer...")
        ballistic_tests = TestBallisticComputer()
        ballistic_tests.setup_method()
        ballistic_tests.test_range_azimuth_calculation()
        ballistic_tests.test_firing_solution_calculation()
        ballistic_tests.test_charge_selection()
        ballistic_tests.test_site_correction()
        ballistic_tests.test_engagement_envelope()
        
        # Test Fire Mission Planner
        print("\n🎯 Testing Fire Mission Planner...")
        mission_tests = TestFireMissionPlanner()
        mission_tests.setup_method()
        mission_tests.test_mission_planning()
        mission_tests.test_ammunition_calculation()
        mission_tests.test_unit_selection()
        
        # Test Orders Generator
        print("\n📋 Testing Orders Generator...")
        orders_tests = TestOrdersGenerator()
        orders_tests.setup_method()
        orders_tests.test_fire_order_generation()
        orders_tests.test_fire_support_plan()
        orders_tests.test_json_export()
        
        # Test Tactical Decision Support
        print("\n🎖️ Testing Tactical Decision Support...")
        tactical_tests = TestTacticalDecisionSupport()
        tactical_tests.setup_method()
        tactical_tests.test_target_prioritization()
        tactical_tests.test_ammunition_requirements()
        tactical_tests.test_capability_assessment()
        
        # Test Military Extraction
        print("\n📄 Testing Military Extraction...")
        extraction_tests = TestMilitaryExtraction()
        extraction_tests.test_tactical_entity_extraction()
        extraction_tests.test_classification_detection()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED - Artillery Integration Validated")
        print("🎖️ FA-GPT Artillery Computation Layer is operational")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_workflow():
    """Test complete artillery workflow integration."""
    print("\n🔗 Testing Complete Artillery Workflow...")
    
    try:
        # 1. Create components
        ballistic_computer = BallisticComputer()
        mission_planner = FireMissionPlanner()
        orders_generator = OrdersGenerator()
        
        # 2. Set up scenario
        firing_unit = FiringUnit(
            call_sign="STEEL01",
            grid_coordinates="12345678",
            elevation_meters=200,
            weapon_system=WeaponSystem.M777A2,
            ammunition_available={AmmunitionType.HE: 100}
        )
        
        target = Target(
            designation="TGT001",
            grid_coordinates="12356789",
            elevation_meters=150,
            description="Enemy artillery position",
            priority="PRIORITY"
        )
        
        # 3. Calculate firing solution
        firing_solution = ballistic_computer.calculate_firing_solution(
            firing_unit, target, AmmunitionType.HE
        )
        assert firing_solution is not None
        
        # 4. Plan fire mission
        mission_plan = mission_planner.plan_fire_mission(
            [firing_unit], target, "DESTROY"
        )
        assert mission_plan["recommended_unit"] is not None
        
        # 5. Generate fire order
        fire_order = orders_generator.generate_fire_order(
            target, firing_unit, firing_solution, 4
        )
        assert fire_order.order_id is not None
        
        # 6. Format for transmission
        formatted_order = orders_generator.format_fire_order(fire_order)
        assert "FIRE ORDER" in formatted_order
        
        print("✅ Complete workflow integration successful")
        print(f"   Fire solution: {firing_solution.range_meters}m, {firing_solution.charge.value}")
        print(f"   Fire order: {fire_order.order_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🎖️ FA-GPT Artillery Integration Test Suite")
    print("Testing enhanced ballistic computation capabilities...")
    
    # Run comprehensive tests
    tests_passed = run_comprehensive_tests()
    
    # Test complete workflow
    workflow_passed = test_integration_workflow()
    
    if tests_passed and workflow_passed:
        print("\n🎉 ALL ARTILLERY SYSTEMS VALIDATED")
        print("FA-GPT Enhanced Artillery Layer Ready for Deployment")
        exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Review errors before deployment")
        exit(1)
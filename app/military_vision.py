"""
Enhanced Qwen Military Vision Analysis

Specialized image analysis for military documents using Qwen 2.5 VL model.
Provides detailed captioning for tactical diagrams, firing charts, equipment
identification, and military maps while preserving the existing foundation.
"""

import logging
import base64
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import io
from pathlib import Path

from .connectors import get_ollama_client

logger = logging.getLogger(__name__)

class MilitaryImageAnalyzer:
    """
    Enhanced Qwen 2.5 VL analyzer for military image content.
    
    Provides specialized military image analysis while maintaining
    compatibility with existing Qwen integration.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = get_ollama_client()
        self.model_name = "qwen2.5-vl:latest"
        
        # Military-specific prompts
        self.military_prompts = self._initialize_military_prompts()
        
        # Equipment recognition patterns
        self.equipment_patterns = self._initialize_equipment_patterns()
    
    def _initialize_military_prompts(self) -> Dict[str, str]:
        """Initialize specialized military analysis prompts."""
        return {
            "artillery_diagram": """
Analyze this artillery diagram and extract:

**WEAPON SYSTEM IDENTIFICATION**
- Type of artillery system (howitzer, mortar, self-propelled)
- Caliber and designation if visible
- Key components and their labels

**TECHNICAL SPECIFICATIONS**
- Dimensions, ranges, or measurements shown
- Angles, elevations, or ballistic data
- Safety zones or danger areas marked

**TACTICAL INFORMATION**
- Firing positions or emplacement details
- Crew positions and roles
- Equipment setup procedures

**PROCEDURAL ELEMENTS**
- Step-by-step processes illustrated
- Safety protocols or warnings
- Operational sequences

Provide detailed military-technical analysis suitable for field artillery operations.
""",
            
            "firing_chart": """
Analyze this firing chart/table and extract:

**BALLISTIC DATA**
- Range and elevation combinations
- Charge settings and their effects
- Time of flight calculations
- Meteorological corrections

**TABULAR INFORMATION**
- Column headers and data organization
- Numerical values and their units
- Cross-reference information

**TACTICAL APPLICATION**
- How to use this chart in fire missions
- Safety considerations shown
- Limitations or restrictions noted

**AMMUNITION DETAILS**
- Types of ammunition covered
- Fuze settings if shown
- Ballistic coefficients or factors

Extract all numerical data exactly as shown for ballistic computation integration.
""",
            
            "tactical_map": """
Analyze this tactical map and identify:

**GEOGRAPHIC FEATURES**
- Terrain elevation and contours
- Natural obstacles or key terrain
- Roads, rivers, and built-up areas

**MILITARY SYMBOLS**
- Unit positions and designations
- Friendly vs enemy positions
- Command posts and support elements

**FIRE SUPPORT ELEMENTS**
- Artillery positions marked
- Target areas and designations
- Fire support coordination measures

**GRID REFERENCES**
- Military grid coordinates visible
- Scale and orientation information
- Reference points and checkpoints

**TACTICAL SITUATION**
- Overall operational picture
- Phase lines or boundaries
- Axis of advance or retreat

Provide tactical analysis suitable for artillery fire planning and coordination.
""",
            
            "equipment_identification": """
Analyze this military equipment image and identify:

**EQUIPMENT TYPE**
- Specific model and designation
- Primary function and role
- Branch of service (Army, Marines, etc.)

**TECHNICAL DETAILS**
- Key specifications visible
- Unique identifying features
- Operational capabilities

**COMPONENTS AND ACCESSORIES**
- Major subassemblies shown
- Attached equipment or accessories
- Maintenance access points

**OPERATIONAL CONTEXT**
- How this equipment is employed
- Tactical role in fire support
- Integration with other systems

Focus on details relevant to field artillery operations and fire support.
""",
            
            "procedural_diagram": """
Analyze this procedural diagram and extract:

**PROCESS STEPS**
- Sequential procedures illustrated
- Decision points or branches
- Start and end conditions

**PERSONNEL ROLES**
- Individual responsibilities shown
- Team coordination requirements
- Command relationships

**EQUIPMENT USAGE**
- Tools or equipment required
- Setup or configuration steps
- Safety equipment needed

**TACTICAL CONSIDERATIONS**
- When to use this procedure
- Battlefield conditions affecting execution
- Alternative methods shown

**SAFETY PROTOCOLS**
- Warnings or cautions highlighted
- Protective measures required
- Emergency procedures

Provide analysis suitable for training and field reference.
""",
            
            "general_military": """
Analyze this military image and provide comprehensive description covering:

**CONTENT IDENTIFICATION**
- Type of military content (diagram, photo, chart, map)
- Subject matter and scope
- Document classification if visible

**TACTICAL ELEMENTS**
- Military units, equipment, or procedures shown
- Operational context or scenario
- Geographic or temporal references

**TECHNICAL DETAILS**
- Specifications, measurements, or data
- Procedures or instructions illustrated
- Safety or operational considerations

**ARTILLERY RELEVANCE**
- Connection to field artillery operations
- Fire support applications
- Integration with gunnery procedures

**KNOWLEDGE EXTRACTION**
- Key information for military database
- Relationships to other tactical elements
- Training or reference value

Provide detailed analysis suitable for military knowledge management and tactical reference.
"""
        }
    
    def _initialize_equipment_patterns(self) -> Dict[str, List[str]]:
        """Initialize equipment recognition patterns."""
        return {
            "howitzers": [
                "M777", "M109", "M198", "M119", "Paladin",
                "155mm", "105mm", "203mm", "howitzer", "artillery"
            ],
            "vehicles": [
                "HMMWV", "M1097", "M35", "FMTV", "HEMTT",
                "truck", "trailer", "prime mover"
            ],
            "radios": [
                "AN/PRC", "AN/VRC", "SINCGARS", "radio",
                "communication", "antenna"
            ],
            "optics": [
                "M2A2", "aiming circle", "theodolite", "compass",
                "binoculars", "range finder", "PLGR", "GPS"
            ],
            "ammunition": [
                "projectile", "round", "shell", "HE", "smoke",
                "illumination", "fuze", "charge", "propellant"
            ]
        }
    
    def analyze_military_image(self, 
                             image_path: str, 
                             analysis_type: str = "general_military",
                             additional_context: str = "") -> Dict[str, Any]:
        """
        Analyze military image with specialized Qwen 2.5 VL processing.
        
        Args:
            image_path: Path to image file
            analysis_type: Type of military analysis to perform
            additional_context: Additional context for analysis
            
        Returns:
            Comprehensive military image analysis
        """
        try:
            self.logger.info(f"Analyzing military image: {image_path}")
            
            # Load and encode image
            image_data = self._encode_image(image_path)
            if not image_data:
                return {"success": False, "error": "Failed to encode image"}
            
            # Select appropriate prompt
            prompt = self.military_prompts.get(analysis_type, self.military_prompts["general_military"])
            
            # Add additional context if provided
            if additional_context:
                prompt = f"{prompt}\n\nADDITIONAL CONTEXT:\n{additional_context}"
            
            # Perform Qwen 2.5 VL analysis
            response = self._query_qwen_vision(image_data, prompt)
            
            if not response:
                return {"success": False, "error": "No response from Qwen model"}
            
            # Process and structure the response
            analysis_result = self._process_military_analysis(response, analysis_type)
            
            # Extract structured data
            structured_data = self._extract_structured_data(analysis_result["description"])
            
            result = {
                "success": True,
                "image_path": image_path,
                "analysis_type": analysis_type,
                "description": analysis_result["description"],
                "military_entities": analysis_result["entities"],
                "structured_data": structured_data,
                "equipment_identified": self._identify_equipment(analysis_result["description"]),
                "tactical_relevance": self._assess_tactical_relevance(analysis_result["description"]),
                "confidence_score": analysis_result["confidence"],
                "processing_metadata": {
                    "model": self.model_name,
                    "prompt_type": analysis_type,
                    "analysis_timestamp": self._get_timestamp()
                }
            }
            
            self.logger.info(f"Military image analysis completed: {image_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing military image {image_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_path": image_path
            }
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image for Qwen 2.5 VL processing."""
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                return encoded_image
        except Exception as e:
            self.logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    def _query_qwen_vision(self, image_data: str, prompt: str) -> Optional[str]:
        """Query Qwen 2.5 VL model with image and prompt."""
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                images=[image_data],
                options={
                    "temperature": 0.3,  # Lower temperature for more consistent military analysis
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            )
            
            return response.get("response", "")
            
        except Exception as e:
            self.logger.error(f"Error querying Qwen vision model: {e}")
            return None
    
    def _process_military_analysis(self, raw_response: str, analysis_type: str) -> Dict[str, Any]:
        """Process raw Qwen response into structured military analysis."""
        
        # Extract military entities mentioned
        entities = self._extract_military_entities(raw_response)
        
        # Assess confidence based on specificity
        confidence = self._assess_analysis_confidence(raw_response)
        
        # Clean and structure the description
        description = self._clean_military_description(raw_response)
        
        return {
            "description": description,
            "entities": entities,
            "confidence": confidence,
            "analysis_type": analysis_type
        }
    
    def _extract_military_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract military entities from analysis text."""
        entities = []
        
        # Weapon systems
        weapon_patterns = [
            r"M\d+[A-Z]?\d?",  # M777A2, M109A6, etc.
            r"\d+mm\s+(?:howitzer|mortar|gun)",
            r"(?:Paladin|HIMARS|MLRS|Excalibur)"
        ]
        
        for pattern in weapon_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "weapon_system",
                    "designation": match.group(0),
                    "context": self._get_match_context(text, match)
                })
        
        # Grid coordinates
        grid_pattern = r"[A-Z]{2}\s*\d{8,10}"
        grid_matches = re.finditer(grid_pattern, text)
        for match in grid_matches:
            entities.append({
                "type": "grid_coordinate",
                "designation": match.group(0),
                "context": self._get_match_context(text, match)
            })
        
        # Military units
        unit_patterns = [
            r"[A-Z]\s*/\s*\d+-\d+\s+[A-Z]{2,}",  # A/1-77 FA
            r"\d+(?:st|nd|rd|th)\s+(?:Infantry|Artillery|Armor|Engineer)"
        ]
        
        for pattern in unit_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "military_unit",
                    "designation": match.group(0),
                    "context": self._get_match_context(text, match)
                })
        
        return entities
    
    def _get_match_context(self, text: str, match) -> str:
        """Get surrounding context for a regex match."""
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        return text[start:end].strip()
    
    def _assess_analysis_confidence(self, text: str) -> float:
        """Assess confidence of military analysis based on content specificity."""
        confidence_indicators = {
            "high": [
                "designation", "model", "caliber", "range", "elevation",
                "grid", "coordinate", "azimuth", "charge", "ammunition"
            ],
            "medium": [
                "artillery", "howitzer", "mortar", "target", "position",
                "unit", "battery", "firing", "mission"
            ],
            "low": [
                "military", "equipment", "diagram", "chart", "map"
            ]
        }
        
        text_lower = text.lower()
        high_count = sum(1 for word in confidence_indicators["high"] if word in text_lower)
        medium_count = sum(1 for word in confidence_indicators["medium"] if word in text_lower)
        low_count = sum(1 for word in confidence_indicators["low"] if word in text_lower)
        
        # Calculate weighted confidence score
        score = (high_count * 0.6 + medium_count * 0.3 + low_count * 0.1) / 10
        return min(1.0, max(0.1, score))
    
    def _clean_military_description(self, text: str) -> str:
        """Clean and format military description text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Standardize military terminology
        replacements = {
            r'\bmils?\b': 'mils',
            r'\bmeters?\b': 'meters',
            r'\bhowitzers?\b': 'howitzer',
            r'\bartillery\s+piece': 'artillery system'
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _extract_structured_data(self, description: str) -> Dict[str, Any]:
        """Extract structured data from military description."""
        structured = {
            "specifications": {},
            "coordinates": [],
            "measurements": {},
            "procedures": [],
            "safety_notes": []
        }
        
        # Extract specifications
        spec_patterns = {
            "caliber": r"(\d+)mm",
            "range": r"range[:\s]*(\d+(?:,\d+)?)\s*(?:meters?|m)",
            "elevation": r"elevation[:\s]*(\d+)\s*(?:mils?|degrees?)",
            "azimuth": r"azimuth[:\s]*(\d+)\s*mils?"
        }
        
        for spec_type, pattern in spec_patterns.items():
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                structured["specifications"][spec_type] = matches
        
        # Extract grid coordinates
        grid_matches = re.findall(r"[A-Z]{2}\s*\d{8,10}", description)
        structured["coordinates"] = grid_matches
        
        # Extract procedural steps
        step_pattern = r"(?:step|procedure|stage)\s*\d+[:\.]?\s*([^.]+)"
        steps = re.findall(step_pattern, description, re.IGNORECASE)
        structured["procedures"] = steps
        
        # Extract safety information
        safety_pattern = r"(?:warning|caution|danger|safety)[:\.]?\s*([^.]+)"
        safety_notes = re.findall(safety_pattern, description, re.IGNORECASE)
        structured["safety_notes"] = safety_notes
        
        return structured
    
    def _identify_equipment(self, description: str) -> List[Dict[str, Any]]:
        """Identify specific military equipment mentioned."""
        equipment_found = []
        
        for category, keywords in self.equipment_patterns.items():
            for keyword in keywords:
                if keyword.lower() in description.lower():
                    equipment_found.append({
                        "category": category,
                        "item": keyword,
                        "confidence": 0.8 if len(keyword) > 5 else 0.6
                    })
        
        # Remove duplicates and sort by confidence
        unique_equipment = {}
        for item in equipment_found:
            key = f"{item['category']}_{item['item']}"
            if key not in unique_equipment or item['confidence'] > unique_equipment[key]['confidence']:
                unique_equipment[key] = item
        
        return sorted(unique_equipment.values(), key=lambda x: x['confidence'], reverse=True)
    
    def _assess_tactical_relevance(self, description: str) -> Dict[str, Any]:
        """Assess tactical relevance of the analyzed content."""
        relevance_keywords = {
            "fire_support": ["firing", "target", "mission", "artillery", "fire support"],
            "ballistics": ["range", "elevation", "charge", "ballistic", "trajectory"],
            "navigation": ["grid", "coordinate", "azimuth", "bearing", "position"],
            "equipment": ["weapon", "system", "equipment", "howitzer", "mortar"],
            "procedures": ["procedure", "step", "process", "method", "technique"],
            "safety": ["safety", "danger", "warning", "caution", "hazard"]
        }
        
        relevance_scores = {}
        description_lower = description.lower()
        
        for category, keywords in relevance_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            relevance_scores[category] = min(1.0, score / len(keywords))
        
        # Overall tactical relevance
        overall_relevance = sum(relevance_scores.values()) / len(relevance_scores)
        
        return {
            "overall_score": overall_relevance,
            "category_scores": relevance_scores,
            "is_tactically_relevant": overall_relevance > 0.3
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for processing metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_analyze_images(self, 
                           image_paths: List[str], 
                           analysis_type: str = "general_military") -> List[Dict[str, Any]]:
        """Batch analyze multiple military images."""
        results = []
        
        for image_path in image_paths:
            result = self.analyze_military_image(image_path, analysis_type)
            results.append(result)
            
            # Brief pause between analyses to avoid overwhelming the model
            import time
            time.sleep(0.5)
        
        return results
    
    def get_military_image_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of military image analysis results."""
        if not analysis_results:
            return {}
        
        summary = {
            "total_images": len(analysis_results),
            "successful_analyses": sum(1 for r in analysis_results if r.get("success")),
            "equipment_categories": set(),
            "tactical_entities": [],
            "average_confidence": 0.0,
            "most_relevant_images": []
        }
        
        successful_results = [r for r in analysis_results if r.get("success")]
        
        if successful_results:
            # Collect equipment categories
            for result in successful_results:
                for equipment in result.get("equipment_identified", []):
                    summary["equipment_categories"].add(equipment["category"])
            
            # Collect tactical entities
            for result in successful_results:
                summary["tactical_entities"].extend(result.get("military_entities", []))
            
            # Calculate average confidence
            confidences = [r.get("confidence_score", 0) for r in successful_results]
            summary["average_confidence"] = sum(confidences) / len(confidences)
            
            # Find most tactically relevant images
            relevant_images = [
                (r["image_path"], r.get("tactical_relevance", {}).get("overall_score", 0))
                for r in successful_results
            ]
            summary["most_relevant_images"] = sorted(
                relevant_images, key=lambda x: x[1], reverse=True
            )[:5]
        
        summary["equipment_categories"] = list(summary["equipment_categories"])
        
        return summary
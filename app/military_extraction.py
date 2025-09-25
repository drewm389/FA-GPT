"""
Specialized Military Extraction Pipeline

Enhanced document processing for military content with tactical entity extraction,
military classification handling, and artillery-specific data processing.
Builds upon the existing Granite-Docling foundation.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from .enhanced_granite_docling import EnhancedGraniteDoclingExtractor
from .postgres_storage import PostgreSQLStorage
from .ballistic_computer import WeaponSystem, AmmunitionType, ChargeType

logger = logging.getLogger(__name__)

@dataclass
class TacticalEntity:
    """Tactical entity extracted from military documents."""
    entity_type: str
    entity_subtype: Optional[str]
    designation: str
    description: str
    grid_coordinates: Optional[str] = None
    elevation_meters: Optional[int] = None
    confidence_score: float = 1.0
    extraction_method: str = "granite_docling"
    page_number: Optional[int] = None
    bounding_box: Optional[Dict] = None
    metadata: Dict = None

@dataclass
class MilitaryClassification:
    """Military document classification information."""
    classification_level: str  # UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP SECRET
    caveat_markings: List[str]  # FOUO, NOFORN, etc.
    classification_reason: Optional[str] = None
    declassification_date: Optional[datetime] = None
    classification_authority: Optional[str] = None
    distribution_statement: Optional[str] = None

class MilitaryDocumentProcessor:
    """
    Enhanced document processor for military content.
    
    Extends the existing Granite-Docling extraction with military-specific
    entity recognition, classification handling, and tactical data extraction.
    """
    
    def __init__(self, storage: PostgreSQLStorage):
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        self.granite_extractor = EnhancedGraniteDoclingExtractor()
        
        # Military entity patterns
        self.entity_patterns = self._initialize_entity_patterns()
        
        # Classification patterns
        self.classification_patterns = self._initialize_classification_patterns()
        
        # Artillery-specific patterns
        self.artillery_patterns = self._initialize_artillery_patterns()
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for tactical entity extraction."""
        return {
            "units": [
                r"(\d+(?:st|nd|rd|th)?\s+(?:Infantry|Armor|Artillery|Engineer|Signal|Medical|Aviation|Military Police|Transportation)(?:\s+(?:Division|Brigade|Regiment|Battalion|Company|Battery|Platoon|Squad))?)",
                r"([A-Z]\s*/\s*\d+-\d+\s+[A-Z]{2,})",  # A/1-77 FA format
                r"((?:Alpha|Bravo|Charlie|Delta|Echo|Fox)\s+(?:Company|Battery|Troop))",
                r"(Task Force\s+[A-Z][a-z]+)",
                r"(Combat Team\s+\d+(?:st|nd|rd|th)?)"
            ],
            "weapons": [
                r"(M\d+[A-Z]?\d?\s+(?:Howitzer|Mortar|Artillery|Gun))",
                r"(\d+mm\s+(?:Howitzer|Mortar|Artillery|Gun))",
                r"(M\d+\s+(?:Paladin|HIMARS|MLRS))",
                r"(Excalibur|GMLRS|ATACMS)"
            ],
            "locations": [
                r"([A-Z]{2}\s+\d{8})",  # MGRS grid coordinates
                r"(Objective\s+[A-Z][A-Z]+)",  # Objective ALPHA
                r"(Phase Line\s+[A-Z][A-Z]+)",  # Phase Line BLUE
                r"(Battle Position\s+\d+)",
                r"(Forward Operating Base\s+[A-Z][a-z]+)",
                r"(FOB\s+[A-Z][a-z]+)"
            ],
            "procedures": [
                r"(Fire Mission\s+\d+)",
                r"(Call for Fire)",
                r"(Adjust Fire)",
                r"(Fire for Effect)",
                r"(Check Firing|Cease Fire)",
                r"(Mission\s+(?:DESTROY|NEUTRALIZE|SUPPRESS|HARASS))",
                r"(Method\s+(?:AT MY COMMAND|WHEN READY|TIME ON TARGET))"
            ],
            "ammunition": [
                r"(M\d+\s+(?:HE|SMOKE|ILLUM|WP|DPICM))",
                r"(Charge\s+[1-7GB]+)",
                r"(\d+\s+rounds?\s+[A-Z]{2,})",
                r"(Fuze\s+(?:PD|VT|TIME|DELAY|PROX))"
            ],
            "coordinates": [
                r"([A-Z]{2}\s*\d{8})",  # MGRS 8-digit
                r"([A-Z]{2}\s*\d{10})",  # MGRS 10-digit
                r"(\d{1,2}°\d{1,2}'\d{1,2}\"[NS]\s+\d{1,3}°\d{1,2}'\d{1,2}\"[EW])"  # Lat/Long
            ]
        }
    
    def _initialize_classification_patterns(self) -> Dict[str, str]:
        """Initialize classification marking patterns."""
        return {
            "classification_level": r"(UNCLASSIFIED|CONFIDENTIAL|SECRET|TOP SECRET)",
            "fouo": r"(FOR OFFICIAL USE ONLY|FOUO)",
            "noforn": r"(NOT RELEASABLE TO FOREIGN NATIONALS|NOFORN)",
            "distribution": r"(DISTRIBUTION\s+[A-F])",
            "authority": r"(CLASSIFIED BY:?\s+[A-Z][A-Za-z\s,]+)",
            "reason": r"(CLASSIFICATION REASON:?\s+[A-Za-z0-9\s,.]+)",
            "declassify": r"(DECLASSIFY ON:?\s+\d{1,2}/\d{1,2}/\d{4})"
        }
    
    def _initialize_artillery_patterns(self) -> Dict[str, List[str]]:
        """Initialize artillery-specific extraction patterns."""
        return {
            "firing_data": [
                r"(AZIMUTH\s*:?\s*(\d{4})\s*mils?)",
                r"(ELEVATION\s*:?\s*(\d{3,4})\s*mils?)",
                r"(RANGE\s*:?\s*(\d+)\s*(?:meters?|m))",
                r"(CHARGE\s*:?\s*([1-7GB]+))",
                r"(TIME OF FLIGHT\s*:?\s*(\d+\.?\d*)\s*(?:seconds?|sec|s))"
            ],
            "target_data": [
                r"(TARGET\s*:?\s*([A-Z]{2,}\d*))",
                r"(GRID\s*:?\s*([A-Z]{2}\s*\d{8,10}))",
                r"(ELEVATION\s*:?\s*(\d+)\s*(?:meters?|m))",
                r"(DESCRIPTION\s*:?\s*([A-Za-z0-9\s,.-]+))"
            ],
            "unit_data": [
                r"(FIRING UNIT\s*:?\s*([A-Z0-9-]+))",
                r"(BATTERY\s*:?\s*([A-Z]\s*/\s*\d+-\d+))",
                r"(POSITION\s*:?\s*([A-Z]{2}\s*\d{8}))"
            ]
        }
    
    def process_document(self, 
                        file_path: str, 
                        document_id: str,
                        extract_entities: bool = True,
                        classify_content: bool = True) -> Dict[str, Any]:
        """
        Process military document with enhanced extraction.
        
        Args:
            file_path: Path to document file
            document_id: Unique document identifier
            extract_entities: Whether to extract tactical entities
            classify_content: Whether to detect classification markings
            
        Returns:
            Processing results with entities and classification
        """
        try:
            self.logger.info(f"Processing military document: {document_id}")
            
            # Use existing Granite-Docling extraction as foundation
            extraction_result = self.granite_extractor.extract_document(file_path, document_id)
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Enhanced military processing
            results = {
                "success": True,
                "document_id": document_id,
                "file_path": file_path,
                "base_extraction": extraction_result,
                "tactical_entities": [],
                "classification": None,
                "artillery_data": {},
                "processing_metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "processor": "MilitaryDocumentProcessor",
                    "version": "1.0"
                }
            }
            
            # Extract tactical entities from all text content
            if extract_entities:
                all_text = " ".join([
                    chunk.get("content", "") 
                    for chunk in extraction_result.get("chunks", [])
                ])
                results["tactical_entities"] = self._extract_tactical_entities(
                    all_text, document_id
                )
            
            # Detect classification markings
            if classify_content:
                results["classification"] = self._detect_classification(
                    extraction_result.get("chunks", [])
                )
            
            # Extract artillery-specific data
            results["artillery_data"] = self._extract_artillery_data(
                extraction_result.get("chunks", [])
            )
            
            # Store enhanced results
            self._store_military_results(results)
            
            self.logger.info(f"Military processing completed for {document_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing military document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }
    
    def _extract_tactical_entities(self, text: str, document_id: str) -> List[TacticalEntity]:
        """Extract tactical entities from text content."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    
                    # Determine entity subtype
                    subtype = self._classify_entity_subtype(entity_type, entity_text)
                    
                    # Extract coordinates if present
                    coordinates = self._extract_coordinates_from_entity(entity_text)
                    
                    entity = TacticalEntity(
                        entity_type=entity_type.rstrip('s'),  # Remove plural
                        entity_subtype=subtype,
                        designation=entity_text.strip(),
                        description=f"Extracted {entity_type.rstrip('s')} from document",
                        grid_coordinates=coordinates,
                        confidence_score=0.8,  # Pattern-based extraction confidence
                        extraction_method="military_pattern_extraction"
                    )
                    
                    entities.append(entity)
        
        return entities
    
    def _classify_entity_subtype(self, entity_type: str, entity_text: str) -> Optional[str]:
        """Classify entity into more specific subtype."""
        subtypes = {
            "units": {
                "artillery": ["Artillery", "FA", "Field Artillery"],
                "infantry": ["Infantry", "Inf"],
                "armor": ["Armor", "Tank"],
                "engineer": ["Engineer", "Eng"],
                "aviation": ["Aviation", "Air"]
            },
            "weapons": {
                "howitzer": ["Howitzer", "155mm", "105mm"],
                "mortar": ["Mortar", "81mm", "60mm"],
                "missile": ["HIMARS", "MLRS", "ATACMS"],
                "precision": ["Excalibur", "GMLRS"]
            },
            "locations": {
                "objective": ["Objective"],
                "phase_line": ["Phase Line"],
                "battle_position": ["Battle Position", "BP"],
                "base": ["FOB", "Forward Operating Base"]
            }
        }
        
        if entity_type not in subtypes:
            return None
        
        for subtype, keywords in subtypes[entity_type].items():
            for keyword in keywords:
                if keyword.lower() in entity_text.lower():
                    return subtype
        
        return None
    
    def _extract_coordinates_from_entity(self, entity_text: str) -> Optional[str]:
        """Extract grid coordinates from entity text."""
        coord_pattern = r"([A-Z]{2}\s*\d{8,10})"
        match = re.search(coord_pattern, entity_text)
        return match.group(1) if match else None
    
    def _detect_classification(self, chunks: List[Dict]) -> Optional[MilitaryClassification]:
        """Detect military classification markings in document."""
        all_text = " ".join([chunk.get("content", "") for chunk in chunks])
        
        # Look for classification patterns
        classification_level = None
        caveat_markings = []
        
        # Check classification level
        level_match = re.search(self.classification_patterns["classification_level"], all_text)
        if level_match:
            classification_level = level_match.group(1)
        
        # Check for FOUO
        if re.search(self.classification_patterns["fouo"], all_text):
            caveat_markings.append("FOUO")
        
        # Check for NOFORN
        if re.search(self.classification_patterns["noforn"], all_text):
            caveat_markings.append("NOFORN")
        
        # If no classification found, assume UNCLASSIFIED
        if not classification_level and not caveat_markings:
            classification_level = "UNCLASSIFIED"
        
        if classification_level or caveat_markings:
            return MilitaryClassification(
                classification_level=classification_level or "UNCLASSIFIED",
                caveat_markings=caveat_markings
            )
        
        return None
    
    def _extract_artillery_data(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Extract artillery-specific firing data and tactical information."""
        artillery_data = {
            "firing_data": [],
            "targets": [],
            "units": [],
            "procedures": []
        }
        
        all_text = " ".join([chunk.get("content", "") for chunk in chunks])
        
        # Extract firing data
        for pattern in self.artillery_patterns["firing_data"]:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                firing_element = {
                    "type": match.group(1).split()[0].lower(),
                    "value": match.group(2) if len(match.groups()) > 1 else match.group(1),
                    "full_match": match.group(0)
                }
                artillery_data["firing_data"].append(firing_element)
        
        # Extract target data
        for pattern in self.artillery_patterns["target_data"]:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                target_element = {
                    "type": match.group(1).split()[0].lower(),
                    "value": match.group(2) if len(match.groups()) > 1 else match.group(1),
                    "full_match": match.group(0)
                }
                artillery_data["targets"].append(target_element)
        
        # Extract unit data
        for pattern in self.artillery_patterns["unit_data"]:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                unit_element = {
                    "type": match.group(1).split()[0].lower(),
                    "value": match.group(2) if len(match.groups()) > 1 else match.group(1),
                    "full_match": match.group(0)
                }
                artillery_data["units"].append(unit_element)
        
        return artillery_data
    
    def _store_military_results(self, results: Dict[str, Any]):
        """Store military processing results in database."""
        try:
            document_id = results["document_id"]
            
            # Store tactical entities
            for entity in results["tactical_entities"]:
                self._store_tactical_entity(entity, document_id)
            
            # Update document metadata with military classification
            if results["classification"]:
                classification_metadata = {
                    "classification_level": results["classification"].classification_level,
                    "caveat_markings": results["classification"].caveat_markings,
                    "military_document": True
                }
                
                # Update document metadata
                self.storage.execute_query(
                    """
                    UPDATE documents 
                    SET metadata = metadata || %s 
                    WHERE id = %s
                    """,
                    (json.dumps(classification_metadata), document_id)
                )
            
            # Store artillery data in document metadata
            if results["artillery_data"]:
                artillery_metadata = {
                    "artillery_content": True,
                    "firing_data_count": len(results["artillery_data"]["firing_data"]),
                    "target_count": len(results["artillery_data"]["targets"]),
                    "unit_count": len(results["artillery_data"]["units"])
                }
                
                self.storage.execute_query(
                    """
                    UPDATE documents 
                    SET metadata = metadata || %s 
                    WHERE id = %s
                    """,
                    (json.dumps(artillery_metadata), document_id)
                )
            
        except Exception as e:
            self.logger.error(f"Error storing military results: {e}")
    
    def _store_tactical_entity(self, entity: TacticalEntity, document_id: str):
        """Store individual tactical entity in database."""
        try:
            self.storage.execute_query(
                """
                INSERT INTO tactical_entities 
                (document_id, entity_type, entity_subtype, designation, description, 
                 grid_coordinates, elevation_meters, confidence_score, extraction_method, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    entity.entity_type,
                    entity.entity_subtype,
                    entity.designation,
                    entity.description,
                    entity.grid_coordinates,
                    entity.elevation_meters,
                    entity.confidence_score,
                    entity.extraction_method,
                    json.dumps(entity.metadata or {})
                )
            )
        except Exception as e:
            self.logger.error(f"Error storing tactical entity: {e}")
    
    def extract_firing_tables(self, text_content: str) -> List[Dict[str, Any]]:
        """Extract firing table data from military documents."""
        firing_tables = []
        
        # Pattern for tabular firing data
        table_pattern = r"Range\s+Charge\s+Elevation\s+TOF[\s\S]*?(?=\n\n|\Z)"
        
        matches = re.finditer(table_pattern, text_content, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            table_text = match.group(0)
            
            # Extract individual rows
            row_pattern = r"(\d+)\s+([1-7GB]+)\s+(\d+)\s+(\d+\.?\d*)"
            rows = re.finditer(row_pattern, table_text)
            
            for row in rows:
                firing_data = {
                    "range_meters": int(row.group(1)),
                    "charge": row.group(2),
                    "elevation_mils": int(row.group(3)),
                    "time_of_flight": float(row.group(4)),
                    "extraction_confidence": 0.9
                }
                firing_tables.append(firing_data)
        
        return firing_tables
    
    def get_military_statistics(self, document_id: str) -> Dict[str, Any]:
        """Get military-specific statistics for a document."""
        try:
            # Count tactical entities by type
            entity_counts = self.storage.fetch_query(
                """
                SELECT entity_type, COUNT(*) as count
                FROM tactical_entities 
                WHERE document_id = %s
                GROUP BY entity_type
                """,
                (document_id,)
            )
            
            # Get classification info
            doc_metadata = self.storage.fetch_query(
                """
                SELECT metadata
                FROM documents
                WHERE id = %s
                """,
                (document_id,)
            )
            
            metadata = json.loads(doc_metadata[0][0]) if doc_metadata else {}
            
            return {
                "entity_counts": {row[0]: row[1] for row in entity_counts},
                "classification_level": metadata.get("classification_level", "UNKNOWN"),
                "is_military_document": metadata.get("military_document", False),
                "has_artillery_content": metadata.get("artillery_content", False),
                "firing_data_count": metadata.get("firing_data_count", 0),
                "target_count": metadata.get("target_count", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting military statistics: {e}")
            return {}

def create_unified_military_prompt() -> str:
    """
    Create unified prompt for military knowledge graph extraction.
    
    Enhanced version that covers both operational planning (MDMP) and 
    tactical execution while preserving artillery computation integration.
    """
    return """
You are a military intelligence analyst extracting tactical and operational information from U.S. Army Field Artillery doctrine documents.

Extract and structure information according to these categories:

**OPERATIONAL PLANNING (MDMP Integration)**
- Mission Analysis: Commander's intent, mission statements, operational environment
- Course of Action: Friendly forces, enemy situation, terrain analysis
- Decision Points: Critical timelines, decision criteria, branch/sequel plans
- Resource Requirements: Personnel, equipment, ammunition, logistics

**TACTICAL EXECUTION (Fire Support)**
- Fire Missions: Target designation, firing data, ammunition selection
- Unit Organization: Battery structure, weapon systems, personnel assignments
- Procedures: Gunnery techniques, safety protocols, communication procedures
- Coordination: Fire support coordination measures, clearance procedures

**ARTILLERY COMPUTATION LAYER**
- Ballistic Data: Range tables, charge selection, meteorological corrections
- Firing Solutions: Azimuth, elevation, time of flight calculations
- Target Analysis: Grid coordinates, target description, engagement criteria
- Ammunition Management: Round allocation, resupply requirements

**TECHNICAL SPECIFICATIONS**
- Weapon Systems: M777A2, M109A6, M119A3 characteristics and capabilities
- Ammunition Types: HE, SMOKE, ILLUM, WP, DPICM, EXCALIBUR specifications
- Equipment: Fire direction equipment, survey instruments, communication gear
- Safety Data: Danger areas, minimum safe distances, protective measures

**KNOWLEDGE GRAPH RELATIONSHIPS**
Create connections between:
- Units ↔ Weapon Systems ↔ Ammunition Types
- Procedures ↔ Equipment ↔ Personnel Requirements
- Targets ↔ Firing Solutions ↔ Ballistic Data
- Operations ↔ Fire Support ↔ Coordination Measures

Focus on extracting actionable military intelligence that can be integrated with ballistic computation systems while maintaining doctrinal accuracy and tactical relevance.

Preserve all technical specifications, numerical data, grid coordinates, and procedural details exactly as they appear in the source material.
"""
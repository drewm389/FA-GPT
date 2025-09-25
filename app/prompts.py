"""
================================================================================
Centralized Prompt Library for FA-GPT System
================================================================================
This module contains all specialized prompts for the Qwen 2.5 VL model,
derived from the analysis of 79 military documents. These prompts are designed
to optimize document classification, knowledge graph extraction, and image analysis.
"""

# ==============================================================================
# 1. DOCUMENT CLASSIFICATION AND IDENTIFICATION
# ==============================================================================

DOC_TYPE_IDENTIFICATION_PROMPT = """
Identify the document type by looking for these key indicators:
- Army Regulation (AR): Look for 'Army Regulation [number]', policy statements, headquarters approval.
- Field Manual (FM): Look for 'Field Manual', doctrine, training procedures, 'FM [number]'.
- Army Techniques Publication (ATP): Look for 'Army Techniques Publication', 'ATP [number]', techniques and procedures.
- Technical Manual (TM): Look for 'Technical Manual', 'TM [number]', operator instructions, PMCS procedures.
- Training Circular (TC): Look for 'Training Circular', 'TC [number]', certification procedures.
- Army Doctrine Publication (ADP): Look for 'Army Doctrine Publication', 'ADP [number]', high-level doctrine.
- Joint Publication (JP): Look for 'Joint Publication', 'JP [number]', multi-service procedures.
- Department of Army Pamphlet (DA Pam): Look for 'DA Pam [number]', guidance documents.
- Firing Tables (FT): Look for 'Firing Table', ballistic data, range/elevation tables.
Based on the text content, classify this document into one of the following categories: AR, FM, ATP, TM, TC, ADP, JP, DA_Pam, FT, or UNKNOWN.
"""

# ==============================================================================
# 2. KNOWLEDGE GRAPH EXTRACTION (ENHANCED)
# ==============================================================================

KG_EXTRACTION_PROMPT_ENHANCED = """
You are a military intelligence analyst tasked with building a comprehensive knowledge graph from a military document.
Analyze the provided text and extract entities and relationships based on the schema below.

**ENTITY SCHEMA:**
- **WeaponSystem**: A specific piece of military hardware used for projecting force (e.g., M777, M109A6 Paladin, Javelin).
- **Ammunition**: A specific type of munition (e.g., M795 HE, M825A1 Smoke, Excalibur). Properties: `nsn`, `lot_number`.
- **Procedure**: A defined sequence of actions or tasks (e.g., "Conduct a Fire Mission", "Perform PMCS", "MDMP Step 1: Receipt of Mission").
- **SafetyWarning**: A critical safety instruction or precaution (e.g., "Warning: Misfire procedures must be followed", "Danger: High Voltage").
- **GunneryTask**: A specific skill or task related to artillery operations (e.g., "Lay the Howitzer", "Compute Firing Data").
- **BallisticVariable**: A factor that affects the trajectory of a projectile (e.g., Muzzle Velocity, Air Density, Propellant Temperature).
- **MDMP_Step**: A specific step in the Military Decision Making Process (e.g., "Mission Analysis", "COA Development").
- **Planning_Product**: A document or output generated during planning (e.g., "Operations Order (OPORD)", "Fire Support Plan").
- **Staff_Section**: A specific staff group in a military unit (e.g., "S3 Operations", "Fires Cell").

**RELATIONSHIP SCHEMA:**
- **`USES`**: A WeaponSystem uses a specific type of Ammunition. (WeaponSystem -> USES -> Ammunition)
- **`REQUIRES`**: A Procedure requires a specific WeaponSystem or GunneryTask. (Procedure -> REQUIRES -> WeaponSystem)
- **`INCLUDES_STEP`**: A Procedure includes a smaller Procedure or GunneryTask as a sub-step. (Procedure -> INCLUDES_STEP -> Procedure)
- **`HAS_WARNING`**: A Procedure or WeaponSystem is associated with a SafetyWarning. (Procedure -> HAS_WARNING -> SafetyWarning)
- **`AFFECTS`**: A BallisticVariable affects a WeaponSystem or Ammunition's performance. (BallisticVariable -> AFFECTS -> WeaponSystem)
- **`PRODUCES`**: An MDMP_Step produces a specific Planning_Product. (MDMP_Step -> PRODUCES -> Planning_Product)
- **`RESPONSIBLE_FOR`**: A Staff_Section is responsible for a Procedure or Planning_Product. (Staff_Section -> RESPONSIBLE_FOR -> Procedure)
- **`PART_OF`**: An entity is a component of a larger entity (e.g., GunneryTask is PART_OF a Procedure).

**OUTPUT FORMAT:**
- Present the extracted information as a list of JSON objects.
- Each object must have `source_entity`, `relationship`, and `target_entity`.

**EXAMPLE:**
[
  {"source_entity": "M777", "relationship": "USES", "target_entity": "M795 HE"},
  {"source_entity": "Conduct a Fire Mission", "relationship": "REQUIRES", "target_entity": "M777"},
  {"source_entity": "MDMP Step 2: Mission Analysis", "relationship": "PRODUCES", "target_entity": "Fire Support Plan"}
]

Begin extraction.
"""

# ==============================================================================
# 3. SPECIALIZED IMAGE ANALYSIS PROMPTS
# ==============================================================================

IMAGE_ANALYSIS_PROMPTS = {
    "GENERIC": """
    Analyze this image from a military document. Provide a detailed description of its content.
    - Identify any text, symbols, or equipment shown.
    - Describe the purpose or context of the image if possible (e.g., training, maintenance, operational).
    - Output the analysis in a structured JSON format with 'description', 'text_in_image', and 'image_type' (e.g., photo, diagram, chart) keys.
    """,
    
    "TECHNICAL_DIAGRAM": """
    You are a military maintenance expert. Analyze this technical diagram from a Technical Manual (TM).
    - Identify and list all labeled components, parts, and their corresponding reference numbers or NSNs.
    - Transcribe any instructional text or callouts.
    - Describe the primary system or subsystem being illustrated.
    - Explain the purpose of the diagram (e.g., disassembly, inspection, lubrication points).
    - Output a structured JSON with keys: 'system_name', 'purpose', 'components', and 'instructions'.
    """,
    
    "FIRING_TABLE": """
    You are an expert field artillery NCO. Analyze this image of a Firing Table (FT or TFT).
    - Identify the weapon system and ammunition type this table is for.
    - Transcribe the key columns, such as 'Range (meters)', 'Elevation (mils)', 'Drift (mils)', 'Time of Flight (seconds)', and 'Propellant/Charge'.
    - Extract any correction factors for variables like propellant temperature or muzzle velocity variation.
    - Summarize the purpose of this table in a single sentence.
    - Output a structured JSON with keys: 'weapon_system', 'ammunition_type', 'table_data' (as a list of dicts), and 'correction_factors'.
    """,
    
    "TACTICAL_MAP": """
    You are a military intelligence analyst. Analyze this tactical map or operational graphic.
    - Identify and describe all military symbols (e.g., unit locations, objectives, phase lines, fire support coordination measures).
    - Transcribe any text labels, grid coordinates, or annotations on the map.
    - Describe the overall tactical situation being depicted. What is the apparent mission or operation?
    - Identify the map scale, north orientation, and any legend information if present.
    - Output a structured JSON with keys: 'operation_type', 'unit_symbols', 'fscms', and 'tactical_summary'.
    """,
    
    "MDMP_CHART": """
    You are a military operations planner. Analyze this chart or diagram related to the Military Decision Making Process (MDMP).
    - Identify which step of the MDMP is being illustrated.
    - List the key inputs, processes, and outputs shown for this step.
    - Identify which staff sections are shown to have responsibilities.
    - Transcribe all text from the diagram.
    - Output a structured JSON with keys: 'mdmp_step', 'inputs', 'processes', 'outputs', and 'staff_roles'.
    """
}

# ==============================================================================
# 4. FIRE SUPPORT AND ARTILLERY SPECIFIC PROMPTS
# ==============================================================================

FIRE_SUPPORT_EXTRACTION_PROMPT = """
When analyzing fire support documents, extract:
- Equipment designations: M109A6 Paladin, M777 Howitzer, MLRS, HIMARS
- Ammunition types: M795 HE, M825 Smoke, M483 DPICM, FASCAM, RAAM, SADARM
- Ballistic data: Range, Elevation, Charge, Time of Flight, Muzzle Velocity
- Fire mission procedures: Call for Fire, Fire Direction Center operations
- Coordination measures: Fire Support Coordination Line, Restricted Fire Area
- Targeting processes: Intelligence preparation, target acquisition, battle damage assessment
"""

MAINTENANCE_TECHNICAL_PROMPT = """
For technical and maintenance documents, focus on:
- PMCS procedures: Preventive Maintenance Checks and Services
- Safety warnings: DANGER, WARNING, CAUTION statements
- Technical specifications: NSN numbers, part numbers, tolerances
- Operational procedures: Step-by-step instructions, checklists
- Equipment identifiers: Model numbers, serial numbers, nomenclature
"""

ORGANIZATIONAL_OPERATIONAL_PROMPT = """
When processing organizational documents, extract:
- Command structures: Brigade, Battalion, Company, Platoon, Squad
- Roles and responsibilities: Commander, Staff, NCO duties
- Operational concepts: Mission command, operations process, targeting
- Training requirements: Standards, certification, qualification procedures
- Planning processes: MDMP, targeting working groups, assessment
"""

# ==============================================================================
# 5. SPECIALIZED GUNNERY AND BALLISTICS PROMPTS
# ==============================================================================

GUNNERY_FUNDAMENTALS_PROMPT = """
When processing TC 3-09.81 or similar gunnery documents, extract:
- Gunnery Problem Solution (6 steps): Target location determination, chart data calculation, altitude/site compensation, nonstandard condition adjustment, firing data conversion (shell/charge/fuze/deflection/QE), weapon application
- Five Requirements for Accurate Fire: Target location/size accuracy, firing unit location accuracy, weapon/ammunition information accuracy, meteorological information accuracy, computational procedure accuracy
- Gunnery Team Structure: Observer (FOs, FISTs, ANGLICO, FCTs), Fire Direction Center (tactical/technical fire direction), Firing Battery (howitzer sections, ammunition section)
- Indirect Fire Definition: Fire delivered at targets not visible to firing unit, requires gunnery problem solution for accurate engagement
"""

BALLISTICS_ANALYSIS_PROMPT = """
When analyzing ballistics content, extract:
- Internal Ballistics: Chamber pressure curves, propellant burning characteristics, projectile acceleration within bore, muzzle velocity factors
- External Ballistics: Trajectory elements (origin/summit/level point), standard atmosphere vs vacuum effects, air resistance/drag factors
- Terminal Ballistics: Projectile effects on target, weaponeering principles, target analysis procedures, munition effectiveness
- Trajectory Components: Initial elements (angle of departure, muzzle velocity), Summit (maximum ordinate, time to summit), Terminal (angle of fall, impact point)
- Dispersion Analysis: Mean Point of Impact (MPI), Probable Error concepts (PER-Range, PED-Deflection, PETS-Time-to-Burst, PEHS-Height-of-Burst, PERB-Range-to-Burst)
"""

# ==============================================================================
# 6. MDMP AND PLANNING PROMPTS
# ==============================================================================

MDMP_EXTRACTION_PROMPT = """
When processing MDMP Handbook documents, extract:
- MDMP Definition: Iterative planning methodology integrating activities of commander/staff/subordinate headquarters/partners to understand situation/mission, develop/compare COAs, decide on COA
- Seven-Step Process: Receipt of Mission, Mission Analysis, COA Development, COA Analysis, COA Comparison, COA Approval, Orders Production
- Staff Responsibilities: Executive Officer coordination, S-2 intelligence analysis, S-3 operations planning, functional area expertise
- Planning Products: Operations Orders (OPORD), Warning Orders (WARNORD), Course of Action (COA) comparisons, risk assessments
"""

ARMY_DESIGN_METHODOLOGY_PROMPT = """
For Army Design Methodology concepts, identify:
- ADM Definition: Methodology for applying critical/creative thinking to understand/visualize/describe problems and approaches to solving them
- ADM Activities: Frame operational environment, frame problems, develop operational approach, transition to detailed planning, reframing throughout
- Environmental Framing: Current state of operational environment and desired end state, analyze operational/mission variables
- Problem Framing: Understanding and learning within activities requiring revisiting previous learning, iterative process
"""

# ==============================================================================
# 7. SAFETY AND REGULATORY PROMPTS
# ==============================================================================

SAFETY_REGULATORY_PROMPT = """
For safety and regulatory content, identify:
- Range safety procedures: Surface danger zones, safety officers
- Emergency management: All-hazards approach, NIMS, ICS
- Distribution restrictions: Approved for public release, FOUO markings
- Regulatory compliance: Nuclear regulatory requirements, environmental
- Safety warnings: DANGER, WARNING, CAUTION classifications
- Risk management: Hazard identification, risk assessment, mitigation measures
"""

# ==============================================================================
# 8. SPECIALIZED MUNITIONS AND EQUIPMENT PROMPTS
# ==============================================================================

FASCAM_MUNITIONS_PROMPT = """
For FASCAM systems content, identify:
- FASCAM Systems: RAAMS (Remote Anti-Armor Mine System), ADAM (Area Denial Artillery Munition), minefield density calculations
- Mine Employment Tables: Low/Medium/High density (0.001/0.002/0.004), module sizing (400x400m, 200x200m), aimpoint distribution
- Safety Procedures: Safety zone calculations, emplacement procedures, clearance operations
- Employment Planning: Target area analysis, delivery accuracy requirements, duration of effect
"""

SMOKE_ILLUMINATION_PROMPT = """
When processing smoke and illumination munitions content, extract:
- Smoke Munitions: M825 (Red Phosphorus), M116 HC (Hexachloroethane), M110/M60A2 WP (White Phosphorus)
- Illumination Systems: M485 projectile, candle power calculations, coordinated illumination missions
- Employment Procedures: Quick Smoke technique, firing interval determination, weather considerations
- Safety Considerations: Toxic fume hazards, fire hazards, downwind effects
"""

# ==============================================================================
# 9. JOINT AND MULTINATIONAL OPERATIONS PROMPTS
# ==============================================================================

JOINT_OPERATIONS_PROMPT = """
For joint publications (JP), extract:
- Multi-service coordination: Army, Navy, Air Force, Marine Corps procedures
- Command relationships: Operational control, tactical control, support relationships
- Interoperability requirements: Communications, logistics, planning integration
- Legal authorities: Title 10, Posse Comitatus Act, Stafford Act
- Unified command structures: Combatant commanders, joint task forces
"""

MULTINATIONAL_OPERATIONS_PROMPT = """
When processing multinational operations content, identify:
- Coalition Planning: Bilateral planning (two nations), multinational planning frameworks
- Cultural Considerations: Language barriers, cultural differences, national sensitivities
- Information Sharing: Classification levels, national caveats, intelligence sharing agreements
- Command Structures: Lead nation concept, parallel command structures, integrated headquarters
"""

# ==============================================================================
# 10. COMPREHENSIVE TERMINOLOGY DATABASE
# ==============================================================================

MILITARY_TERMINOLOGY_EXTRACTION = """
Extract military-specific terminology including:
- Acronyms: PMCS, FDC, FSO, FIST, DIVARTY, BCT, MDMP, NIMS, ICS, MTTP
- Equipment: Howitzer, Artillery, Mortar, Radar, Communications, MLRS, HIMARS
- Operations: Fire support, Sustainment, Intelligence, Maneuver, Targeting, Assessment
- Munitions: Projectile, Fuze, Propellant, Charge, Warhead, DPICM, FASCAM, RAAM
- Planning Terms: COA, WARNORD, OPORD, FRAGO, IPB, CCIR, PIR, FFIR
- Command Terms: DIVARTY, BCT, FAB, FSE, FSCOORD, FDO, FSO
"""

# ==============================================================================
# 11. DOCUMENT STRUCTURE PATTERN RECOGNITION
# ==============================================================================

DOCUMENT_STRUCTURE_PROMPT = """
Recognize these structural patterns:
- Military numbering: AR 525-27, FM 3-09, ATP 3-09.50, TM 9-2350-314-10
- Cross-references: 'See also', 'Reference', 'In accordance with'
- Hierarchical organization: Chapters, sections, paragraphs, subparagraphs
- Tabular data: Tables, charts, matrices, decision trees
- Procedural sequences: Step 1, Step 2, sequential instructions
- Distribution statements: Public release, FOUO, classified markings
"""

# ==============================================================================
# 12. QUALITY ASSURANCE PROMPTS
# ==============================================================================

QUALITY_ASSURANCE_PROMPT = """
Ensure extraction accuracy by:
- Verifying technical specifications against established standards
- Cross-referencing related documents and publications
- Identifying and flagging contradictory information
- Noting publication dates and revision status
- Highlighting safety-critical information and warnings
- Preserving exact technical terminology and nomenclature
"""
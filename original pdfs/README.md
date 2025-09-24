# Original PDFs Collection

This directory contains metadata and manifests for the complete U.S. Army doctrine and field artillery document collection used in the FA-GPT system.

## Collection Overview

**Total Documents:** 83 files (~1.2GB)  
**Doctrine Documents:** 67 files (~620MB)  
**Tabular Firing Tables:** 16 files (~590MB)  

## Key Documents

### 🎖️ **Critical Operational Documents**
- **TC 3-09.81** Field Artillery Manual Cannon Gunnery (235MB)
- **FM 3-09** Fire Support and Field Artillery Operations (9.9MB)
- **FM 5-0** Planning and Orders Production (13.9MB)
- **ATP 5-0.2-1** Staff Reference Guide (16.3MB)

### 🎯 **Critical Tactical Documents**
- **Major TFTs** Complete 155mm ballistic data (460MB)
- **ATP 3-09.30** Observed Fires (6.8MB)
- **ATP 3-09.50** Field Artillery Cannon Battery (3.4MB)
- **AR 385-63** Range Safety (15.2MB)

## Document Categories

### 📚 Doctrine Documents (`/doctrine/`)
- **Field Manuals (FM)**: Core doctrinal publications
- **Army Doctrine Publications (ADP)**: Foundational doctrine  
- **Army Techniques Publications (ATP)**: Technical procedures
- **Training Circulars (TC)**: Specialized training materials
- **Army Regulations (AR)**: Administrative guidance
- **Department of Army Pamphlets**: Supplementary materials
- **Joint Publications (JP)**: Joint service doctrine
- **Student Texts (ST)**: Educational materials

### 📊 Tabular Firing Tables (`/TFTs/`)
- **Firing Tables (FT)**: Ballistic data for projectiles and charges
- **Range/Fuze Tables (RFT)**: Supplementary firing data  
- **Addendum Tables (ADD)**: Additional projectile variants

**Projectile Types Covered:**
- High Explosive (HE) - M795, variants
- Dual Purpose Improved Conventional Munition (DPICM)
- Family of Scatterable Mines (FASCAM) - ADAM/RAAM
- Improved Smoke - M825/M825A1
- Sense and Destroy Armor (SADARM)
- Anti-Personnel/Anti-Materiel (APICM)

## FA-GPT Processing Pipeline

These documents are processed through the FA-GPT unified knowledge extraction system:

1. **📄 Multimodal Extraction**: IBM Granite-Docling processes text, tables, and images
2. **🧠 Knowledge Graph Generation**: Qwen 2.5 VL creates unified operational-tactical graphs
3. **🔍 Vector Database**: pgvector enables semantic search across all content
4. **💬 RAG Interface**: Streamlit provides conversational access to military knowledge

## Knowledge Graph Entities Extracted

### **Operational Planning (MDMP)**
- MDMP_Step, Planning_Product, Staff_Section, Command_Post_Function

### **Tactical Execution (Gunnery)**  
- GunneryTask, SafetyProcedure, BallisticData, BallisticVariable
- WeaponSystem, Ammunition, Publication

### **Unified Relationships**
- PRODUCES, RESPONSIBLE_FOR, INFORMS (operational)
- REQUIRES_SAFETY_CHECK, HAS_BALLISTIC_DATA (tactical)
- REFERENCES_PUBLICATION (cross-domain)

## File Access

Due to GitHub file size limitations, the actual PDFs are stored locally. See `PDF_MANIFEST.md` for complete file listings and sizes.

To add PDFs to the repository, install Git LFS and follow the instructions in the manifest.

**Status:** ✅ Ready for FA-GPT ingestion and knowledge extraction

Last updated: September 23, 2025
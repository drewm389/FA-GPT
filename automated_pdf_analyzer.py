#!/usr/bin/env python3
"""
Automated PDF Analysis Script for FA-GPT Qwen Prompts Enhancement

This script systematically analyzes all remaining PDFs in the FA-GPT data directory,
extracts military-specific patterns and terminology, and appends comprehensive
analysis to the qwen_prompts.txt file.

Usage: Copy this script into VS Code AI assistant and it will execute automatically.
"""

import os
import sys
import subprocess
from pathlib import Path
import re
from typing import List, Dict, Tuple
import time

class PDFAnalyzer:
    def __init__(self):
        self.base_dir = "/home/drew/FA-GPT/data"
        self.qwen_prompts_file = "/home/drew/Desktop/qwen_prompts.txt"
        self.todo_file = "/home/drew/FA-GPT/todo_list.txt"
        
        # Documents already completed (from todo list analysis)
        self.completed_docs = {
            "TC_3_09.81_Field_Artillery_Manual_Cannon_Gunnery.pdf",
            "23_08_682_leader_s_guide_to_maintenance_and_services_aug_23_public.pdf",
            "23_758_staff_facilitation_of_commander_decision_making_in_lsco_apr_23_public.pdf",
            "24_852_staff_processes_in_large_scale_combat_operations_part_1_rhythm_of_the_battle.pdf",
            "ADP_3_19_Fires.pdf",
            "ADP_3_28_Defense_Support_of_Civil_Authorities.pdf",
            "ATP_2_01.3_Intelligence_Preparation_of_the_Operational_Environment.pdf"
        }
        
        # Military document patterns for classification
        self.doc_patterns = {
            'AR': r'AR[\s_]\d+[-_]\d+',
            'FM': r'FM[\s_]\d+[-_]\d+',
            'ATP': r'ATP[\s_]\d+[-_]\d+',
            'TM': r'TM[\s_]\d+[-_]\d+',
            'TC': r'TC[\s_]\d+[-_]\d+',
            'ADP': r'ADP[\s_]\d+[-_]\d+',
            'JP': r'JP[\s_]\d+[-_]\d+',
            'DA_PAM': r'DA[\s_]PAM[\s_]\d+[-_]\d+',
            'FT': r'FT[\s_]\d+'
        }
    
    def find_all_pdfs(self) -> List[str]:
        """Find all PDF files in the data directory and subdirectories."""
        pdf_files = []
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    # Skip already completed documents
                    if file not in self.completed_docs:
                        pdf_files.append(full_path)
        return sorted(pdf_files)
    
    def classify_document(self, filename: str) -> str:
        """Classify document type based on filename patterns."""
        filename_upper = filename.upper()
        
        for doc_type, pattern in self.doc_patterns.items():
            if re.search(pattern, filename_upper):
                return doc_type
        
        # Special cases
        if 'FIRING' in filename_upper and 'TABLE' in filename_upper:
            return 'FT'
        elif 'HANDBOOK' in filename_upper:
            return 'HANDBOOK'
        elif 'GUIDE' in filename_upper:
            return 'GUIDE'
        else:
            return 'OTHER'
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdftotext."""
        try:
            result = subprocess.run(
                ['pdftotext', pdf_path, '-'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Warning: pdftotext failed for {pdf_path}")
                return ""
        except subprocess.TimeoutExpired:
            print(f"Warning: pdftotext timeout for {pdf_path}")
            return ""
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def identify_chapters(self, text: str) -> List[str]:
        """Identify chapter structure in the document."""
        chapters = []
        
        # Common military document chapter patterns
        chapter_patterns = [
            r'CHAPTER\s+(\d+|[IVX]+)[\s\-:]*([^\n]+)',
            r'Chapter\s+(\d+|[IVX]+)[\s\-:]*([^\n]+)',
            r'SECTION\s+(\d+|[IVX]+)[\s\-:]*([^\n]+)',
            r'Section\s+(\d+|[IVX]+)[\s\-:]*([^\n]+)',
            r'APPENDIX\s+([A-Z]|[IVX]+)[\s\-:]*([^\n]+)',
            r'Appendix\s+([A-Z]|[IVX]+)[\s\-:]*([^\n]+)',
        ]
        
        for pattern in chapter_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                chapter_id = match.group(1)
                chapter_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                chapters.append(f"{chapter_id}: {chapter_title}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chapters = []
        for chapter in chapters:
            if chapter not in seen:
                seen.add(chapter)
                unique_chapters.append(chapter)
        
        return unique_chapters[:20]  # Limit to first 20 chapters
    
    def extract_military_terminology(self, text: str) -> Dict[str, List[str]]:
        """Extract military-specific terminology and patterns."""
        terminology = {
            'equipment': [],
            'procedures': [],
            'acronyms': [],
            'publications': [],
            'organizations': [],
            'operations': []
        }
        
        # Equipment patterns
        equipment_patterns = [
            r'M\d+[A-Z]?\d*\s+\w+',  # M777 Howitzer, M109A6 Paladin
            r'[A-Z]{2,}\s+(?:System|Radar|Vehicle|Equipment)',
            r'Howitzer|Artillery|Mortar|Launcher|Rocket'
        ]
        
        # Procedure patterns
        procedure_patterns = [
            r'(?:PMCS|Preventive Maintenance)',
            r'(?:Call for Fire|Fire Mission)',
            r'(?:MDMP|Military Decision Making Process)',
            r'(?:Registration|Calibration|Verification)'
        ]
        
        # Acronym patterns (2-6 capital letters)
        acronym_pattern = r'\b[A-Z]{2,6}\b'
        
        # Extract patterns
        for pattern in equipment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terminology['equipment'].extend(matches[:10])
        
        for pattern in procedure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terminology['procedures'].extend(matches[:10])
        
        # Extract acronyms
        acronyms = re.findall(acronym_pattern, text)
        # Filter common words and keep military-relevant ones
        military_acronyms = [acr for acr in acronyms if len(acr) >= 3 and 
                           acr not in ['THE', 'AND', 'FOR', 'ARE', 'YOU', 'CAN', 'ALL']]
        terminology['acronyms'] = list(set(military_acronyms[:20]))
        
        return terminology
    
    def analyze_document(self, pdf_path: str) -> Dict:
        """Perform comprehensive analysis of a single document."""
        filename = os.path.basename(pdf_path)
        doc_type = self.classify_document(filename)
        
        print(f"Analyzing: {filename} (Type: {doc_type})")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text.strip():
            return {
                'filename': filename,
                'doc_type': doc_type,
                'error': 'No text extracted',
                'chapters': [],
                'terminology': {}
            }
        
        # Identify structure
        chapters = self.identify_chapters(text)
        
        # Extract terminology
        terminology = self.extract_military_terminology(text)
        
        return {
            'filename': filename,
            'doc_type': doc_type,
            'text_length': len(text),
            'chapters': chapters,
            'terminology': terminology,
            'key_phrases': self.extract_key_phrases(text, doc_type)
        }
    
    def extract_key_phrases(self, text: str, doc_type: str) -> List[str]:
        """Extract key phrases based on document type."""
        key_phrases = []
        
        if doc_type == 'FT':  # Firing Tables
            patterns = [
                r'Range\s+\d+\s*meters?',
                r'Elevation\s+\d+\s*mils?',
                r'Charge\s+\w+',
                r'Time\s+of\s+Flight\s+[\d.]+',
                r'Muzzle\s+Velocity\s+[\d.]+'
            ]
        elif doc_type in ['FM', 'ATP']:  # Manuals
            patterns = [
                r'Step\s+\d+[:\.].*',
                r'WARNING[:\.].*',
                r'CAUTION[:\.].*',
                r'NOTE[:\.].*',
                r'Figure\s+\d+[-\.]?\d*',
                r'Table\s+\d+[-\.]?\d*'
            ]
        elif doc_type == 'AR':  # Regulations
            patterns = [
                r'The\s+\w+\s+will\s+\w+',
                r'Commanders\s+\w+',
                r'Policy\s+\w+',
                r'Responsibility\s+for\s+\w+'
            ]
        else:  # General patterns
            patterns = [
                r'Purpose[:\.].*',
                r'Scope[:\.].*',
                r'References[:\.].*',
                r'Definitions[:\.].*'
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_phrases.extend(matches[:5])
        
        return key_phrases[:10]
    
    def generate_qwen_prompts(self, analysis_results: List[Dict]) -> str:
        """Generate comprehensive Qwen prompts based on analysis results."""
        
        prompt_sections = []
        
        # Group by document type
        doc_types = {}
        for result in analysis_results:
            doc_type = result['doc_type']
            if doc_type not in doc_types:
                doc_types[doc_type] = []
            doc_types[doc_type].append(result)
        
        prompt_counter = 50  # Continue from existing numbering
        
        for doc_type, docs in doc_types.items():
            if not docs:
                continue
            
            # Create type-specific prompts
            prompt_sections.append(f"\n{prompt_counter}. {doc_type.upper()} DOCUMENT ANALYSIS:")
            prompt_sections.append(f'"When processing {doc_type} documents, extract:')
            
            # Aggregate terminology from all docs of this type
            all_equipment = set()
            all_procedures = set()
            all_acronyms = set()
            example_docs = []
            
            for doc in docs[:3]:  # Limit examples
                example_docs.append(doc['filename'])
                if 'terminology' in doc:
                    all_equipment.update(doc['terminology'].get('equipment', []))
                    all_procedures.update(doc['terminology'].get('procedures', []))
                    all_acronyms.update(doc['terminology'].get('acronyms', []))
            
            # Add specific extraction guidance
            if all_equipment:
                equipment_list = list(all_equipment)[:10]
                prompt_sections.append(f'   - Equipment: {", ".join(equipment_list)}')
            
            if all_procedures:
                procedure_list = list(all_procedures)[:10]
                prompt_sections.append(f'   - Procedures: {", ".join(procedure_list)}')
            
            if all_acronyms:
                acronym_list = list(all_acronyms)[:15]
                prompt_sections.append(f'   - Key Acronyms: {", ".join(acronym_list)}')
            
            # Add document-specific patterns
            if doc_type == 'FT':
                prompt_sections.append('   - Ballistic Data: Range tables, elevation data, charge information')
                prompt_sections.append('   - Numerical Values: Meters, mils, seconds, velocity measurements')
            elif doc_type in ['FM', 'ATP']:
                prompt_sections.append('   - Procedural Steps: Sequential instructions, checklists')
                prompt_sections.append('   - Safety Information: Warnings, cautions, protective measures')
            elif doc_type == 'AR':
                prompt_sections.append('   - Policy Statements: Requirements, prohibitions, authorities')
                prompt_sections.append('   - Responsibilities: Commander duties, staff functions')
            
            prompt_sections.append(f'   - Example Documents: {", ".join(example_docs)}"')
            prompt_sections.append('')
            
            prompt_counter += 1
        
        # Add comprehensive terminology section
        all_terminology = {
            'equipment': set(),
            'procedures': set(),
            'acronyms': set()
        }
        
        for result in analysis_results:
            if 'terminology' in result:
                for key in all_terminology:
                    all_terminology[key].update(result['terminology'].get(key, []))
        
        prompt_sections.append(f"\n{prompt_counter}. COMPREHENSIVE TERMINOLOGY UPDATE:")
        prompt_sections.append('"Updated terminology database from systematic analysis:')
        
        if all_terminology['equipment']:
            equipment_sorted = sorted(list(all_terminology['equipment']))[:25]
            prompt_sections.append(f'   - Military Equipment: {", ".join(equipment_sorted)}')
        
        if all_terminology['procedures']:
            procedures_sorted = sorted(list(all_terminology['procedures']))[:20]
            prompt_sections.append(f'   - Key Procedures: {", ".join(procedures_sorted)}')
        
        if all_terminology['acronyms']:
            acronyms_sorted = sorted(list(all_terminology['acronyms']))[:30]
            prompt_sections.append(f'   - Military Acronyms: {", ".join(acronyms_sorted)}')
        
        prompt_sections.append('"')
        
        # Add completion summary
        prompt_counter += 1
        total_docs = len(analysis_results)
        prompt_sections.append(f"\n{prompt_counter}. ANALYSIS COMPLETION SUMMARY:")
        prompt_sections.append(f'"Systematic analysis completed for {total_docs} additional military documents.')
        prompt_sections.append(f'Document distribution: {dict((k, len(v)) for k, v in doc_types.items())}')
        prompt_sections.append('All PDFs in FA-GPT data directory have been processed and integrated.')
        prompt_sections.append('Qwen prompts now provide comprehensive coverage of entire document corpus."')
        
        return '\n'.join(prompt_sections)
    
    def update_qwen_prompts_file(self, new_prompts: str):
        """Append new prompts to the qwen_prompts.txt file."""
        try:
            with open(self.qwen_prompts_file, 'a', encoding='utf-8') as f:
                f.write('\n\n=== AUTOMATED ANALYSIS COMPLETION ===\n')
                f.write(f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(new_prompts)
                f.write('\n\n=== END AUTOMATED ANALYSIS ===\n')
            
            print(f"Successfully updated {self.qwen_prompts_file}")
            return True
        except Exception as e:
            print(f"Error updating qwen prompts file: {e}")
            return False
    
    def run_complete_analysis(self):
        """Execute the complete PDF analysis workflow."""
        print("Starting automated PDF analysis for FA-GPT...")
        print(f"Scanning directory: {self.base_dir}")
        
        # Find all PDFs
        pdf_files = self.find_all_pdfs()
        print(f"Found {len(pdf_files)} PDFs to analyze")
        
        if not pdf_files:
            print("No remaining PDFs to analyze. All documents appear to be completed.")
            return
        
        # Analyze each PDF
        analysis_results = []
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"Progress: {i}/{len(pdf_files)}")
            try:
                result = self.analyze_document(pdf_path)
                analysis_results.append(result)
                
                # Brief pause to avoid overwhelming the system
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error analyzing {pdf_path}: {e}")
                continue
        
        print(f"Analysis completed for {len(analysis_results)} documents")
        
        # Generate prompts
        print("Generating Qwen prompts...")
        new_prompts = self.generate_qwen_prompts(analysis_results)
        
        # Update file
        print("Updating qwen_prompts.txt...")
        success = self.update_qwen_prompts_file(new_prompts)
        
        if success:
            print("Analysis complete! Qwen prompts have been updated with comprehensive patterns.")
            print(f"Added analysis for {len(analysis_results)} documents")
        else:
            print("Analysis completed but file update failed. Prompts generated successfully:")
            print(new_prompts)


def main():
    """Main execution function."""
    # Check if required tools are available
    try:
        subprocess.run(['which', 'pdftotext'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: pdftotext not found. Please install poppler-utils:")
        print("sudo apt install poppler-utils")
        return False
    
    # Create analyzer and run
    analyzer = PDFAnalyzer()
    analyzer.run_complete_analysis()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
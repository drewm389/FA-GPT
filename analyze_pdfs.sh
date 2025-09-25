#!/bin/bash

# Script to analyze all PDFs and extract Qwen prompt keywords.

# Directory containing the PDF files
PDF_DIR="/home/drew/FA-GPT/data/documents"

# Output file for the prompts
OUTPUT_FILE="/home/drew/Desktop/qwen_prompts.txt"

# List of all PDF files
PDF_FILES=$(find "$PDF_DIR" -type f -name "*.pdf")

# Keywords to search for
KEYWORDS="firing table|field manual|technical manual|army regulation|training circular|doctrine|range|elevation|charge|projectile|velocity|maintenance|pmcs|safety|warning|procedure|tactics|operation|logistics|sustainment|brigade|battalion|company|platoon|squad|leader|commander|staff|planning|orders|mission|fm|atp|adp|ar|tc|tm|jp"

echo "Starting analysis of all PDF documents..."

# Loop through each PDF file
for pdf_file in $PDF_FILES; do
    echo "--- Analyzing: $(basename "$pdf_file") ---"
    
    # Extract text and grep for keywords, then append to the output file
    {
        echo ""
        echo "========================================================================"
        echo "ANALYSIS FOR: $(basename "$pdf_file")"
        echo "========================================================================"
        pdftotext -l 10 "$pdf_file" - | grep -i -E -o ".{0,40}$KEYWORDS.{0,40}" | sort -u
        echo ""
    } >> "$OUTPUT_FILE"

done

echo "--- Analysis complete. All findings saved to $OUTPUT_FILE ---"

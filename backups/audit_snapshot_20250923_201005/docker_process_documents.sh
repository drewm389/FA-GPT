#!/bin/bash
# docker_process_documents.sh - Process documents through the Docker container

LIMIT=$1

if [ -z "$LIMIT" ]; then
  echo "Processing all documents"
  docker compose exec streamlit python -c "
import os
import time
from pathlib import Path
from app.simple_ingestion import process_and_ingest_document

document_dir = '/app/data/documents'
count = 0

for root, _, files in os.walk(document_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            count += 1
            pdf_path = os.path.join(root, file)
            print(f'\nProcessing {count}: {os.path.basename(pdf_path)}')
            try:
                start_time = time.time()
                process_and_ingest_document(pdf_path)
                duration = time.time() - start_time
                print(f'✅ Successfully processed in {duration:.2f} seconds')
            except Exception as e:
                print(f'❌ Error processing document: {str(e)}')

print('\nDocument processing complete!')
"
else
  echo "Processing $LIMIT document(s)"
  docker compose exec streamlit python -c "
import os
import time
from pathlib import Path
from app.simple_ingestion import process_and_ingest_document

document_dir = '/app/data/documents'
count = 0
limit = $LIMIT

for root, _, files in os.walk(document_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            count += 1
            if count > limit:
                break
            pdf_path = os.path.join(root, file)
            print(f'\nProcessing {count}/{limit}: {os.path.basename(pdf_path)}')
            try:
                start_time = time.time()
                process_and_ingest_document(pdf_path)
                duration = time.time() - start_time
                print(f'✅ Successfully processed in {duration:.2f} seconds')
            except Exception as e:
                print(f'❌ Error processing document: {str(e)}')
            
    if count >= limit:
        break

print('\nDocument processing complete!')
"
fi
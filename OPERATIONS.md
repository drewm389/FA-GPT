# FA-GPT Operational Guide

## Quick Start Commands

### System Startup
```bash
# Start all services with GPU configuration
./start.sh

# Verify system status
python system_status.py --detailed
```

### Document Processing
```bash
# Process single document
python -m app.simple_ingestion --file /path/to/document.pdf --verbose

# Process batch of documents
python process.py --input-dir data/documents --limit 5

# Retry failed documents from quarantine
python process.py --retry-failed

# Clear database and reprocess
python process.py --clear-db --input-dir data/documents --limit 5
```

### Web Interface
```bash
# Launch the Streamlit shell from project root
PYTHONPATH=$(pwd) streamlit run app/main.py
```

### System Monitoring
```bash
# Quick status check
python system_status.py

# Detailed system information
python system_status.py --detailed --verbose

# Services only (for CI/CD)
python system_status.py --services-only
```

## Command Reference

### simple_ingestion.py
Primary document processing interface.

```bash
# Single file processing
python -m app.simple_ingestion --file /absolute/path/to/document.pdf

# Directory with specific file
python -m app.simple_ingestion --input-dir data/documents --test-single filename.pdf

# Batch processing with limits
python -m app.simple_ingestion --input-dir data/documents --limit 10 --verbose

# Clear database before processing
python -m app.simple_ingestion --input-dir data/documents --clear-db --verbose
```

**Options**:
- `--input-dir PATH`: Root directory containing documents (default: data/documents)
- `--test-single FILE`: Single filename within --input-dir to process
- `--file PATH`: Absolute path to a single PDF to process  
- `--limit N`: Limit the number of documents to process
- `--clear-db`: Clear existing database entries before processing
- `--verbose`: Enable verbose logging (DEBUG level)

### process.py
Unified document processing CLI that replaces the former helper scripts.

```bash
# Process all new documents under data/documents
python process.py

# Process only a handful of documents
python process.py --limit 5

# Use a custom directory
python process.py --input-dir /path/to/pdfs

# Force reprocessing of every document (ignores previous runs)
python process.py --reprocess-all

# Retry items moved to the quarantine folder
python process.py --retry-failed

# Drop ingestion tables before running (DESTRUCTIVE)
python process.py --clear-db

# Add a delay between documents (seconds)
python process.py --delay 2

# Stop immediately on the first failure
python process.py --stop-on-error
```

**Options**:
- `--input-dir PATH`: Directory that will be scanned recursively for PDFs (default: data/documents)
- `--limit N`: Limit the number of documents processed in the run
- `--retry-failed`: Process only items in `data/quarantine`
- `--reprocess-all`: Ignore previous runs and reprocess everything in the input directory
- `--clear-db`: Drop ingestion tables before processing (requires confirmation)
- `--delay SECONDS`: Pause between document runs (floating point allowed)
- `--stop-on-error`: Abort the run after the first failure

### system_status.py
System health monitoring and diagnostics.

```bash
# Standard status check
python system_status.py

# Detailed system information
python system_status.py --detailed

# Services only (minimal output)
python system_status.py --services-only

# Verbose monitoring
python system_status.py --detailed --verbose
```

**Options**:
- `--detailed`: Show detailed information including dependencies
- `--services-only`: Show only service status
- `--verbose`: Enable verbose logging (DEBUG level)

## Service Management

### Starting Services
```bash
./start.sh          # Start all FA-GPT services
./status.sh         # Check service status
./stop.sh           # Stop all services
```

### Docker Compose Operations
```bash
# Start services in background
docker-compose up -d

# View service logs
docker-compose logs -f postgres
docker-compose logs -f ollama

# Restart specific service
docker-compose restart postgres

# Stop all services
docker-compose down
```

## Logging and Diagnostics

### Log Files
```bash
# Main system log
tail -f logs/fa-gpt-system.log

# Real-time error monitoring
tail -f logs/fa-gpt-system.log | grep "ERROR\|EXCEPTION"

# Performance monitoring
tail -f logs/fa-gpt-system.log | grep "Performance\|⏱️"
```

### Log Rotation
- **File size limit**: 10MB per log file
- **Backup count**: 5 rotating backup files
- **Location**: `logs/fa-gpt-system.log*`

### Verbose Logging
Enable DEBUG-level logging with `--verbose` flag:
```bash
python system_status.py --verbose          # Debug system status
python process_documents.py --verbose       # Debug document processing  
python -m app.simple_ingestion --verbose   # Debug ingestion pipeline
```

## Database Operations

### Connection Testing
```bash
# Test database connectivity
python system_status.py --services-only

# Direct PostgreSQL connection
psql -h localhost -p 5432 -U postgres -d vectordb
```

### Database Management
```bash
# Clear database (fresh start)
python process_documents.py --clear-db

# Clear specific tables
python -c "
from app.simple_ingestion import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS fa_gpt_documents CASCADE;')
conn.commit()
conn.close()
"
```

### Vector Search Queries
```sql
-- Connect to database
\c vectordb

-- Check vector extensions
\dx

-- Query document embeddings
SELECT filename, content[1:100] FROM fa_gpt_documents LIMIT 5;

-- Vector similarity search example
SELECT filename, 1 - (embedding <=> query_vector) AS similarity 
FROM fa_gpt_documents 
ORDER BY embedding <=> query_vector 
LIMIT 10;
```

## GPU and Performance

### GPU Status Monitoring
```bash
# AMD GPU status
rocm-smi

# PyTorch GPU detection
python -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
print(f'GPU Count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'GPU Name: {torch.cuda.get_device_name(0)}')
"
```

### MIOpen Configuration Check
```bash
# Verify MIOpen environment variables
env | grep MIOPEN

# Expected values:
# MIOPEN_ENABLE_SQLITE_KERNDB=0
# MIOPEN_ENABLE_SQLITE_PERFDB=0
# MIOPEN_USER_DB_PATH=/tmp/miopen_cache_text
# MIOPEN_FIND_ENFORCE=SEARCH
# MIOPEN_USE_GEMM=1
# MIOPEN_DEBUG_DISABLE_MLIR=1
```

### Performance Optimization
```bash
# Process smallest files first (optimal ordering)
python process_documents.py --input-dir data/documents --limit 10

# Monitor processing speed
python process_documents.py --verbose | grep "⏱️\|Performance"

# Memory-efficient single document testing
python -m app.simple_ingestion --file small_test.pdf --verbose
```

## Troubleshooting

### Common Issues and Solutions

#### GPU Processing Crashes
**Symptoms**: MIOpen database errors, GPU crashes during processing
**Solution**: 
```bash
# Restart with proper MIOpen configuration
./stop.sh
./start.sh

# Verify MIOpen settings
env | grep MIOPEN

# Test GPU processing with small file
python -m app.simple_ingestion --file small_test.pdf --verbose
```

#### Database Connection Failures
**Symptoms**: PostgreSQL connection refused, authentication errors
**Solution**:
```bash
# Check PostgreSQL service
docker-compose ps postgres
docker-compose logs postgres

# Restart database service
docker-compose restart postgres

# Test connection
python system_status.py --services-only
```

#### Ollama Model Issues
**Symptoms**: Model not found, inference errors
**Solution**:
```bash
# Check available models
ollama list

# Download required models
ollama pull qwen2.5vl:7b
ollama pull nomic-embed-text

# Test model inference
ollama run qwen2.5vl:7b "Test prompt"
```

#### Document Processing Failures
**Symptoms**: PDF extraction fails, silent processing errors
**Solution**:
```bash
# Enable verbose logging for debugging
python -m app.simple_ingestion --file problematic.pdf --verbose

# Check PDF diagnostics
python -c "
from app.enhanced_granite_docling import Enhanced_Granite_Docling_Processor
processor = Enhanced_Granite_Docling_Processor()
diagnostics = processor._extract_pdf_diagnostics('problematic.pdf')
print(diagnostics)
"

# Try with smaller documents first
python process_documents.py --input-dir test_docs --limit 1 --verbose
```

### Performance Issues

#### Slow Processing Speed
**Diagnosis**:
```bash
# Monitor GPU utilization
rocm-smi -l

# Check system resources
htop

# Profile processing time
python process_documents.py --limit 1 --verbose
```

**Solutions**:
- Ensure GPU is being utilized (check rocm-smi output)
- Verify sufficient VRAM available
- Process smaller batches to identify bottlenecks
- Check for disk I/O constraints

#### Memory Issues
**Symptoms**: Out of memory errors, GPU OOM, system freezing
**Solutions**:
```bash
# Process smaller batches
python process_documents.py --limit 1

# Monitor memory usage during processing
watch -n 1 'nvidia-smi || rocm-smi'

# Clear GPU cache between processing
python -c "
import torch
torch.cuda.empty_cache()
"
```

## Backup and Recovery

### Data Backup
```bash
# Database backup
pg_dump -h localhost -U postgres vectordb > backup_$(date +%Y%m%d).sql

# Document data backup
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/ images/

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz app/ *.py *.sh *.yml
```

### System Recovery
```bash
# Restore database
psql -h localhost -U postgres vectordb < backup_YYYYMMDD.sql

# Restore data
tar -xzf data_backup_YYYYMMDD.tar.gz

# Restart services
./stop.sh && ./start.sh

# Verify system health
python system_status.py --detailed
```

## Development and Testing

### Development Mode
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt

# Test with sample documents
mkdir test_docs
cp sample.pdf test_docs/
python process_documents.py --input-dir test_docs --verbose
```

### Integration Testing
```bash
# End-to-end pipeline test
python -m app.simple_ingestion --file test.pdf --verbose --clear-db

# Service connectivity test
python system_status.py --services-only

# Performance benchmark
time python process_documents.py --limit 5 --verbose
```

### Custom Configuration
```bash
# Create local environment file
cp .env.example .env
nano .env

# Override settings
export OLLAMA_HOST=localhost
export POSTGRES_HOST=localhost

# Test custom configuration
python system_status.py --verbose
```

This operational guide provides practical commands and procedures for daily operation and maintenance of the FA-GPT system.
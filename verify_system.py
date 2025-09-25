# verify_system.py
"""
Comprehensive FA-GPT System Health Verification
Verifies all critical components before system startup to prevent silent failures
"""

import os
import sys
import json
from pathlib import Path

def verify_system_health():
    """A comprehensive check of all critical FA-GPT components."""
    print("🚀 Verifying FA-GPT System Health...")
    errors = 0
    warnings = 0

    # 1. Check Python Environment
    print(f"🐍 Python Version: {sys.version}")
    if sys.version_info < (3, 9):
        print("⚠️  WARNING: Python 3.9+ recommended for optimal performance.")
        warnings += 1

    # 2. Check GPU Availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            gpu_name = torch.cuda.get_device_name(current_device)
            print(f"✅ GPU: {gpu_count} GPU(s) available. Current: {gpu_name}")
            
            # Test GPU computation
            test_tensor = torch.randn(10, 10).cuda()
            result = test_tensor @ test_tensor.T
            del test_tensor, result
            torch.cuda.empty_cache()
            print("✅ GPU: Computation test passed")
        else:
            print("❌ CRITICAL: GPU not accessible by PyTorch. FA-GPT requires GPU acceleration.")
            errors += 1
    except ImportError:
        print("❌ CRITICAL: PyTorch not installed.")
        errors += 1
    except Exception as e:
        print(f"❌ CRITICAL: GPU test failed: {e}")
        errors += 1

    # 3. Check Critical Dependencies
    critical_packages = {
        'tiktoken': 'Token-aware text processing',
        'clip': 'Multimodal embeddings', 
        'docling': 'Document processing',
        'ollama': 'Local LLM/VLM',
        'psycopg2': 'PostgreSQL connection',
        'streamlit': 'Web interface'
    }
    
    for package, description in critical_packages.items():
        try:
            __import__(package)
            print(f"✅ Package: {package} ({description})")
        except ImportError:
            print(f"❌ CRITICAL: Missing {package} - {description}")
            errors += 1

    # 4. Check Docling and Models
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        print("✅ Docling: Document converter initialized successfully")
    except Exception as e:
        print(f"❌ CRITICAL: Docling initialization failed: {e}")
        errors += 1
        
    # 5. Check Database Connection
    try:
        from app.connectors import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Database: PostgreSQL connected - {db_version[:50]}...")
        
        # Check for pgvector extension
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_pgvector = cursor.fetchone()[0]
        if has_pgvector:
            print("✅ Database: pgvector extension available")
        else:
            print("⚠️  WARNING: pgvector extension not found - vector operations may not work")
            warnings += 1
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ CRITICAL: Database connection failed: {e}")
        errors += 1
        
    # 6. Check Ollama Connection and Models
    try:
        import ollama
        client = ollama.Client()
        models_response = client.list()
        
        # Handle different response formats
        if hasattr(models_response, 'models'):
            models_list = models_response.models
        elif isinstance(models_response, dict) and 'models' in models_response:
            models_list = models_response['models']
        else:
            models_list = models_response if isinstance(models_response, list) else []
        
        # Extract model names safely
        models = []
        for model in models_list:
            if isinstance(model, dict) and 'name' in model:
                models.append(model['name'])
            elif hasattr(model, 'name'):
                models.append(model.name)
            elif isinstance(model, str):
                models.append(model)
        
        if models:
            print(f"✅ Ollama: Connected. Available models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
            
            # Check for required models
            required_models = ['qwen2.5-coder:7b', 'llama3.2-vision:11b']
            missing_models = [m for m in required_models if not any(m in model for model in models)]
            if missing_models:
                print(f"⚠️  WARNING: Recommended models missing: {missing_models}")
                warnings += 1
        else:
            print("⚠️  WARNING: Ollama connected but no models found")
            warnings += 1
    except Exception as e:
        print(f"❌ CRITICAL: Ollama connection failed: {e}")
        errors += 1

    # 7. Check File System Permissions
    critical_dirs = ['data', 'logs', 'images', 'backups']
    for dir_name in critical_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            if os.access(dir_path, os.R_OK | os.W_OK):
                print(f"✅ Filesystem: {dir_name}/ writable")
            else:
                print(f"❌ CRITICAL: No write access to {dir_name}/")
                errors += 1
        else:
            print(f"⚠️  WARNING: Directory {dir_name}/ does not exist")
            warnings += 1

    # 8. Check Configuration
    try:
        from app.config import settings
        print(f"✅ Config: Settings loaded - Database: {settings.postgres_db}")
        print(f"✅ Config: Multimodal embeddings: {'enabled' if settings.use_multimodal_embeddings else 'disabled'}")
        print(f"✅ Config: VLM Model: {settings.vlm_model}")
    except Exception as e:
        print(f"❌ CRITICAL: Configuration loading failed: {e}")
        errors += 1

    # 9. Memory and Disk Space Check
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        memory_gb = memory.available / (1024**3)
        disk_gb = disk.free / (1024**3)
        
        print(f"✅ Resources: {memory_gb:.1f}GB RAM available, {disk_gb:.1f}GB disk free")
        
        if memory_gb < 8:
            print("⚠️  WARNING: Low memory - recommend 16GB+ for optimal performance")
            warnings += 1
        if disk_gb < 10:
            print("⚠️  WARNING: Low disk space - recommend 50GB+ free space")
            warnings += 1
    except ImportError:
        print("⚠️  WARNING: psutil not available - cannot check system resources")
        warnings += 1
    except Exception as e:
        print(f"⚠️  WARNING: Resource check failed: {e}")
        warnings += 1

    # Summary
    print("-" * 60)
    if errors == 0 and warnings == 0:
        print("🎉 SYSTEM HEALTH: EXCELLENT - All components operational")
        return True
    elif errors == 0:
        print(f"✅ SYSTEM HEALTH: GOOD - {warnings} warnings but no critical errors")
        print("💡 System can run but consider addressing warnings for optimal performance")
        return True
    else:
        print(f"💔 SYSTEM HEALTH: CRITICAL - {errors} errors, {warnings} warnings")
        print("🚨 RESOLVE CRITICAL ERRORS BEFORE PROCEEDING")
        return False

if __name__ == "__main__":
    success = verify_system_health()
    sys.exit(0 if success else 1)
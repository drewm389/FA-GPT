#!/usr/bin/env python3
"""
FA-GPT System Status Monitor

This script provides comprehensive status updates for all FA-GPT components
with enhanced terminal formatting and emoji indicators.

Usage:
    python system_status.py
    python system_status.py --detailed
    python system_status.py --services-only
    python system_status.py --verbose
"""

import os
import sys
import subprocess
import requests
import psycopg2
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import structured logging
from app.logging_config import get_logger

# Initialize structured logger
logger = get_logger("system-status")

def check_process(process_name):
    """Check if a process is running."""
    try:
        result = subprocess.run(['pgrep', '-f', process_name], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_port(host, port, timeout=3):
    """Check if a service is responding on a specific port."""
    try:
        response = requests.get(f"http://{host}:{port}", timeout=timeout)
        return response.status_code in [200, 404]  # 404 is also "responding"
    except:
        return False

def check_database():
    """Check PostgreSQL database connection."""
    try:
        from app.config import settings
        conn = psycopg2.connect(settings.postgres_uri)
        conn.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

def check_ollama_models():
    """Check available Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        models.append({
                            'name': parts[0],
                            'id': parts[1],
                            'size': parts[2]
                        })
            return True, models
        return False, "Ollama not responding"
    except Exception as e:
        return False, str(e)

def check_python_dependencies():
    """Check critical Python dependencies."""
    dependencies = [
        'streamlit',
        'ollama', 
        'psycopg2',
        'docling',
        'sentence_transformers',
        'transformers'
    ]
    
    results = {}
    for dep in dependencies:
        try:
            __import__(dep)
            results[dep] = "✅ Available"
        except ImportError:
            results[dep] = "❌ Missing"
    
    return results

def display_header():
    """Display system status header."""
    print("🤖 FA-GPT System Status Monitor")
    print("=" * 60)
    print()

def display_services():
    """Display service status."""
    print("🔧 CORE SERVICES:")
    
    # Ollama Service
    ollama_process = check_process("ollama serve")
    ollama_api = check_port("localhost", 11434)
    
    if ollama_process and ollama_api:
        print("✅ Ollama: Running and responding on http://localhost:11434")
    elif ollama_process:
        print("⚠️  Ollama: Process running but API not responding")
    else:
        print("❌ Ollama: Not running")
    
    # PostgreSQL Database
    db_status, db_message = check_database()
    if db_status:
        print("✅ PostgreSQL: Connected and operational")
    else:
        print(f"❌ PostgreSQL: {db_message}")
    
    # Streamlit (if running)
    streamlit_running = check_process("streamlit")
    if streamlit_running:
        if check_port("localhost", 8501):
            print("✅ Streamlit: Running on http://localhost:8501")
        else:
            print("⚠️  Streamlit: Process running but web interface not responding")
    else:
        print("💤 Streamlit: Not currently running")
    
    print()

def display_models():
    """Display AI model status."""
    print("🧠 AI MODELS:")
    
    model_status, models = check_ollama_models()
    if model_status and models:
        for model in models:
            print(f"✅ {model['name']} - Size: {model['size']}")
    elif model_status:
        print("⚠️  Ollama responding but no models found")
    else:
        print("❌ Cannot retrieve model information")
    
    print()

def display_configuration():
    """Display system configuration."""
    print("📊 SYSTEM CONFIGURATION:")
    
    try:
        from app.config import settings
        print(f"• VLM Model: {settings.vlm_model}")
        print(f"• LLM Model: {settings.llm_model}")
        print(f"• Embedding Model: {settings.embedding_model}")
        print(f"• Database: PostgreSQL + pgvector + Apache AGE")
        print(f"• Multimodal Embeddings: {'Enabled' if settings.use_multimodal_embeddings else 'Disabled'}")
    except Exception as e:
        print(f"❌ Cannot load configuration: {e}")
    
    print()

def display_dependencies():
    """Display Python dependency status."""
    print("📦 PYTHON DEPENDENCIES:")
    
    deps = check_python_dependencies()
    for dep, status in deps.items():
        print(f"{status} {dep}")
    
    print()

def display_next_steps():
    """Display suggested next steps."""
    print("🎯 AVAILABLE ACTIONS:")
    print("• Test RAG system: python query_rag.py")
    print("• Start Streamlit: streamlit run app/main.py")
    print("• Process documents: python -m app.simple_ingestion")
    print("• Verify Docling: python verify_docling.py")
    print("• Check detailed logs: tail -f /tmp/ollama.log")
    print()

def main():
    """Main status display function with professional CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FA-GPT System Status Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --detailed --verbose
  %(prog)s --services-only
  %(prog)s --verbose
        """
    )
    parser.add_argument('--detailed', action='store_true', 
                       help='Show detailed information including dependencies')
    parser.add_argument('--services-only', action='store_true',
                       help='Show only service status')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging (DEBUG level)')
    
    args = parser.parse_args()
    
    # Configure logger with verbosity
    if args.verbose:
        logger = get_logger("system-status", verbose=True)
        logger.info("🔍 Verbose system monitoring enabled")
    
    logger.info("🔍 FA-GPT System Status Monitor Starting...")
    logger.log_environment_info()
    
    try:
        display_header()
        display_services()
        
        if not args.services_only:
            display_models()
            display_configuration()
            
            if args.detailed:
                display_dependencies()
            
            display_next_steps()
        
        # Overall system health
        ollama_ok = check_process("ollama serve") and check_port("localhost", 11434)
        db_ok, _ = check_database()
        
        if ollama_ok and db_ok:
            logger.info("🚀 System operational - all core services running")
            print("🚀 OVERALL STATUS: ✅ SYSTEM OPERATIONAL")
        else:
            logger.warning("⚠️  Some services need attention")
            print("⚠️  OVERALL STATUS: ❌ SOME SERVICES NEED ATTENTION")
            
    except KeyboardInterrupt:
        logger.info("🛑 Status monitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.log_exception(e, "System status monitoring failed")
        sys.exit(1)
        
        if not ollama_ok:
            print("   💡 Start Ollama: ollama serve")
        if not db_ok:
            print("   💡 Check PostgreSQL configuration and connection")

if __name__ == "__main__":
    main()
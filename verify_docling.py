# verify_docling.py
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_docling_installation():
    """
    Verifies that the Docling library and its core models are installed and accessible.
    """
    print("--- 🚀 Starting Docling Verification ---")
    
    try:
        # 1. Test core Docling import
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import ConversionStatus
        logging.info("✅ SUCCESS: Core `docling` library imported successfully.")
        
        # 2. Test instantiation of the DocumentConverter
        # This step implicitly downloads and loads necessary models on first run.
        logging.info("Attempting to instantiate DocumentConverter...")
        logging.info("This may take several minutes on the first run as it downloads models...")
        
        # Point to a specific cache directory for local/container execution
        cache_dir = os.path.expanduser("~/.cache/docling_verify")
        os.makedirs(cache_dir, exist_ok=True)
        
        converter = DocumentConverter(cache_dir=cache_dir)
        logging.info("✅ SUCCESS: DocumentConverter instantiated successfully.")
        logging.info(f"   - Models are cached or were downloaded to: {cache_dir}")
        
        print("\n--- ✅ Docling Verification Complete: System is operational. ---")
        return True

    except ImportError as e:
        logging.error(f"❌ FAILURE: Failed to import docling components. Error: {e}")
        logging.error("   - This indicates the `docling` package is not correctly installed in the environment.")
        return False
    except Exception as e:
        logging.error(f"❌ FAILURE: An error occurred during DocumentConverter instantiation. Error: {e}")
        logging.error("   - This often points to issues with model downloads, dependencies (like torch or mlx), or permissions.")
        return False

if __name__ == "__main__":
    verify_docling_installation()
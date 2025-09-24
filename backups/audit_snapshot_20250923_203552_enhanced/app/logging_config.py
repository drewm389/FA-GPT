"""
Logging configuration module for FA-GPT

Provides centralized, structured logging with file and console handlers.
Includes performance timing, error diagnostics, and debug capabilities.
"""

import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

class FAGPTLogger:
    """
    Centralized logging system for FA-GPT with structured output,
    file rotation, and diagnostic capabilities.
    """
    
    def __init__(self, name: str, log_dir: str = "logs", verbose: bool = False):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Error file handler (errors only)
        error_handler = logging.FileHandler(self.log_dir / f"{name}_errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
    
    def log_environment_info(self):
        """Log system environment information for debugging."""
        env_info = {
            'HSA_OVERRIDE_GFX_VERSION': os.environ.get('HSA_OVERRIDE_GFX_VERSION', 'Not set'),
            'HIP_VISIBLE_DEVICES': os.environ.get('HIP_VISIBLE_DEVICES', 'Not set'),
            'MIOPEN_USER_DB_PATH': os.environ.get('MIOPEN_USER_DB_PATH', 'Not set'),
            'MIOPEN_ENABLE_SQLITE_KERNDB': os.environ.get('MIOPEN_ENABLE_SQLITE_KERNDB', 'Not set'),
            'MIOPEN_ENABLE_SQLITE_PERFDB': os.environ.get('MIOPEN_ENABLE_SQLITE_PERFDB', 'Not set'),
            'PYTORCH_ROCM_ARCH': os.environ.get('PYTORCH_ROCM_ARCH', 'Not set'),
        }
        self.logger.debug(f"Environment configuration: {env_info}")
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with full stack trace."""
        self.logger.error(f"{context}: {str(exception)}")
        self.logger.debug(f"Full traceback for {context}: {traceback.format_exc()}")
    
    def log_performance(self, operation: str, duration: float):
        """Log performance metrics."""
        self.logger.info(f"⏱️  {operation} completed in {duration:.2f} seconds")
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg)

# Global logger instances
def get_logger(name: str, verbose: bool = False) -> FAGPTLogger:
    """Get or create a logger instance."""
    return FAGPTLogger(name, verbose=verbose)

# Default logger for general use
logger = get_logger("fa-gpt")
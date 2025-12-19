"""
Logging configuration for SMBX NPC Editor
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    debug: bool = False,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configure application logging
    
    Args:
        debug: Enable debug level logging
        log_to_file: Write logs to file
        log_dir: Directory for log files (default: ~/.smbx_npc_editor/logs)
        
    Returns:
        Configured root logger
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path.home() / ".smbx_npc_editor" / "logs"
    
    # Create log directory if needed
    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set log level
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (detailed, always DEBUG)
    if log_to_file:
        log_file = log_dir / f"npc_editor_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Also log to a "latest.log" file for easy access
        latest_log = log_dir / "latest.log"
        latest_handler = logging.FileHandler(latest_log, mode='w', encoding='utf-8')
        latest_handler.setLevel(logging.DEBUG)
        latest_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(latest_handler)
    
    # Console handler (less verbose)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info(f"Logging initialized (level: {logging.getLevelName(level)})")
    if log_to_file:
        root_logger.info(f"Log files: {log_dir}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)


# Exception hook to log uncaught exceptions
def exception_hook(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Call default handler for KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def install_exception_hook():
    """Install global exception hook"""
    sys.excepthook = exception_hook
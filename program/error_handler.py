"""
Error handling and user notification system for SMBX NPC Editor
"""

import logging
import traceback
from enum import Enum
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QMainWindow

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler:
    """Centralized error handling and user notification"""
    
    def __init__(self, parent_window: Optional[QMainWindow] = None):
        """
        Initialize error handler
        
        Args:
            parent_window: Parent window for dialogs (optional)
        """
        self.parent = parent_window
        self.logger = logging.getLogger(__name__)
    
    def handle_file_error(
        self, 
        filepath: str, 
        error: Exception, 
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: str = ""
    ) -> None:
        """
        Handle and display file operation errors
        
        Args:
            filepath: Path to the file that caused the error
            error: The exception that occurred
            severity: Error severity level
            context: Additional context about what was being done
        """
        # Log the full error with traceback
        self.logger.error(
            f"File operation failed: {filepath} ({context})", 
            exc_info=error
        )
        
        if not self.parent:
            return
        
        # Create user-friendly message
        error_msg = str(error)
        if not error_msg:
            error_msg = f"{type(error).__name__}"
        
        context_msg = f"\n\nContext: {context}" if context else ""
        
        if severity == ErrorSeverity.CRITICAL:
            QMessageBox.critical(
                self.parent,
                "Critical Error",
                f"Failed to access file:\n{filepath}\n\n{error_msg}{context_msg}"
            )
        elif severity == ErrorSeverity.ERROR:
            QMessageBox.warning(
                self.parent,
                "File Error",
                f"Could not load file:\n{filepath}\n\n{error_msg}{context_msg}"
            )
        elif severity == ErrorSeverity.WARNING:
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(
                    f"Warning: {error_msg}", 5000
                )
        else:  # INFO
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(error_msg, 3000)
    
    def handle_generic_error(
        self,
        error: Exception,
        title: str = "Error",
        context: str = "",
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> None:
        """
        Handle general application errors
        
        Args:
            error: The exception that occurred
            title: Dialog title
            context: Additional context
            severity: Error severity level
        """
        self.logger.error(f"{title}: {context}", exc_info=error)
        
        if not self.parent:
            return
        
        error_msg = str(error)
        context_msg = f"\n\n{context}" if context else ""
        
        if severity == ErrorSeverity.CRITICAL:
            QMessageBox.critical(
                self.parent,
                title,
                f"{error_msg}{context_msg}"
            )
        elif severity == ErrorSeverity.ERROR:
            QMessageBox.warning(
                self.parent,
                title,
                f"{error_msg}{context_msg}"
            )
        elif severity == ErrorSeverity.WARNING:
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(error_msg, 5000)
    
    def show_info(self, message: str, title: str = "Information") -> None:
        """Show informational message"""
        if self.parent:
            QMessageBox.information(self.parent, title, message)
        else:
            self.logger.info(f"{title}: {message}")
    
    def show_warning(self, message: str, title: str = "Warning") -> None:
        """Show warning message"""
        if self.parent:
            QMessageBox.warning(self.parent, title, message)
        else:
            self.logger.warning(f"{title}: {message}")
    
    def ask_confirmation(
        self, 
        message: str, 
        title: str = "Confirm"
    ) -> bool:
        """
        Ask for user confirmation
        
        Args:
            message: Question to ask
            title: Dialog title
            
        Returns:
            True if user confirmed, False otherwise
        """
        if not self.parent:
            return False
        
        reply = QMessageBox.question(
            self.parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return reply == QMessageBox.StandardButton.Yes
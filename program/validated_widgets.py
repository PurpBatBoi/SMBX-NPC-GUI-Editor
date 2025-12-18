"""
Custom widgets with validation feedback for SMBX NPC Editor
"""

from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette, QColor

class ValidatedSpinBox(QSpinBox):
    """SpinBox that shows visual feedback when values are clamped"""
    
    valueChangedWithValidation = pyqtSignal(int, bool)  # value, was_clamped
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_stylesheet = ""
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_style)
        
        # Store the last valid value
        self.last_value = self.value()
        self.valueChanged.connect(self._on_value_changed)
    
    def _on_value_changed(self, value):
        self.last_value = value
    
    def setValue(self, value):
        """Override to detect clamping"""
        original_value = value
        clamped = False
        
        # Check if value needs clamping
        if value < self.minimum():
            value = self.minimum()
            clamped = True
        elif value > self.maximum():
            value = self.maximum()
            clamped = True
        
        super().setValue(value)
        
        if clamped:
            self.show_validation_feedback(original_value, value)
            self.valueChangedWithValidation.emit(value, True)
        else:
            self.valueChangedWithValidation.emit(value, False)
    
    def show_validation_feedback(self, attempted_value, actual_value):
        """Show visual feedback that value was clamped"""
        # Flash orange border
        self.setStyleSheet("QSpinBox { border: 2px solid #FF9800; background-color: #FFF3E0; }")
        
        # Show tooltip
        if attempted_value < self.minimum():
            message = f"Value {attempted_value} too small (min: {self.minimum()})"
        else:
            message = f"Value {attempted_value} too large (max: {self.maximum()})"
        
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), message, self)
        
        # Reset after 2 seconds
        self.reset_timer.start(2000)
    
    def reset_style(self):
        """Reset to normal appearance"""
        self.setStyleSheet("")
    
    def validate(self, input_text, pos):
        """Override validation to provide better feedback"""
        state, text, position = super().validate(input_text, pos)
        return state, text, position


class ValidatedDoubleSpinBox(QDoubleSpinBox):
    """DoubleSpinBox that shows visual feedback when values are clamped"""
    
    valueChangedWithValidation = pyqtSignal(float, bool)  # value, was_clamped
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_stylesheet = ""
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_style)
        
        self.last_value = self.value()
        self.valueChanged.connect(self._on_value_changed)
    
    def _on_value_changed(self, value):
        self.last_value = value
    
    def setValue(self, value):
        """Override to detect clamping"""
        original_value = value
        clamped = False
        
        # Check if value needs clamping
        if value < self.minimum():
            value = self.minimum()
            clamped = True
        elif value > self.maximum():
            value = self.maximum()
            clamped = True
        
        super().setValue(value)
        
        if clamped:
            self.show_validation_feedback(original_value, value)
            self.valueChangedWithValidation.emit(value, True)
        else:
            self.valueChangedWithValidation.emit(value, False)
    
    def show_validation_feedback(self, attempted_value, actual_value):
        """Show visual feedback that value was clamped"""
        # Flash orange border
        self.setStyleSheet("QDoubleSpinBox { border: 2px solid #FF9800; background-color: #FFF3E0; }")
        
        # Show tooltip
        if attempted_value < self.minimum():
            message = f"Value {attempted_value:.2f} too small (min: {self.minimum():.2f})"
        else:
            message = f"Value {attempted_value:.2f} too large (max: {self.maximum():.2f})"
        
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), message, self)
        
        # Reset after 2 seconds
        self.reset_timer.start(2000)
    
    def reset_style(self):
        """Reset to normal appearance"""
        self.setStyleSheet("")

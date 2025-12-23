from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QRadioButton, QButtonGroup, 
                             QFrame, QToolButton, QLabel, QFormLayout, QVBoxLayout,
                             QSplitter, QSplitterHandle, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QComboBox, QPushButton, QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from typing import Optional, Any
from ..validated_widgets import ValidatedSpinBox, ValidatedDoubleSpinBox

# --- ClickableLabel ---
class ClickableLabel(QLabel):
    """Label that emits a signal when clicked"""
    clicked = pyqtSignal(str)  # Emits the param_key
    
    def __init__(self, text: str, param_key: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.param_key = param_key
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.param_key)
        super().mousePressEvent(event)

# --- TriStateBoolWidget ---
class TriStateBoolWidget(QWidget):
    stateChanged = pyqtSignal()
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.btn_true = QRadioButton("True")
        self.btn_false = QRadioButton("False")
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(False)
        self.button_group.addButton(self.btn_true)
        self.button_group.addButton(self.btn_false)
        layout.addWidget(self.btn_true)
        layout.addWidget(self.btn_false)
        layout.addStretch()
        self.btn_true.toggled.connect(self._on_true_toggled)
        self.btn_false.toggled.connect(self._on_false_toggled)
        
    def _on_true_toggled(self, checked: bool):
        if checked: self.btn_false.setChecked(False)
        self.stateChanged.emit()
        
    def _on_false_toggled(self, checked: bool):
        if checked: self.btn_true.setChecked(False)
        else:
            if not self.btn_true.isChecked(): self.stateChanged.emit()
        self.stateChanged.emit()
        
    def get_state(self) -> Optional[bool]:
        if self.btn_true.isChecked(): return True
        elif self.btn_false.isChecked(): return False
        return None
        
    def set_state(self, value: Optional[bool]):
        self.blockSignals(True)
        if value is True:
            self.btn_true.setChecked(True)
            self.btn_false.setChecked(False)
        elif value is False:
            self.btn_true.setChecked(False)
            self.btn_false.setChecked(True)
        else:
            self.btn_true.setChecked(False)
            self.btn_false.setChecked(False)
        self.blockSignals(False)

# --- CollapsibleBox ---
class CollapsibleBox(QWidget):
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            .QFrame { background-color: #444; border-radius: 3px; }
            .QFrame:hover { background-color: #555; }
        """)
        self.header_frame.mousePressEvent = self.on_header_clicked
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(10)

        self.arrow_btn = QToolButton()
        self.arrow_btn.setArrowType(Qt.ArrowType.RightArrow)
        self.arrow_btn.setStyleSheet("QToolButton { border: none; background: transparent; color: white; }")
        self.arrow_btn.setCheckable(True)
        self.arrow_btn.setChecked(False)
        self.arrow_btn.clicked.connect(self.toggle_view)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-weight: bold; color: white;")

        header_layout.addWidget(self.arrow_btn)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.content_area = QWidget()
        self.content_layout = QFormLayout()
        self.content_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_area.setLayout(self.content_layout)
        self.content_area.setVisible(False)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.header_frame)
        lay.addWidget(self.content_area)
        
    def on_header_clicked(self, event):
        self.toggle_view()

    def toggle_view(self):
        checked = not self.arrow_btn.isChecked()
        self.arrow_btn.setChecked(checked)
        self.arrow_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.content_area.setVisible(checked)

    def expand(self):
        if not self.arrow_btn.isChecked(): self.toggle_view()
            
    def collapse(self):
        if self.arrow_btn.isChecked(): self.toggle_view()

    def add_row(self, label, widget: QWidget):
        """Add a row with either a string label or a widget label"""
        self.content_layout.addRow(label, widget)


class _FixedHandle(QSplitterHandle):
    def mousePressEvent(self, event):
        event.ignore()
    def mouseMoveEvent(self, event):
        event.ignore()
    def mouseReleaseEvent(self, event):
        event.ignore()


class NoResizeSplitter(QSplitter):
    def createHandle(self):
        return _FixedHandle(self.orientation(), self)

# --- ColorPickerWidget ---
class ColorPickerWidget(QWidget):
    colorChanged = pyqtSignal(str) # Emits hex string 0xAARRGGBB
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.line_edit = QLineEdit("0xFFFFFF")
        self.line_edit.textChanged.connect(self._on_text_changed)
        
        self.btn_pick = QPushButton()
        self.btn_pick.setFixedSize(24, 24)
        self.btn_pick.setStyleSheet("background-color: white; border: 1px solid #555;")
        self.btn_pick.clicked.connect(self.pick_color)
        
        layout.addWidget(self.btn_pick)
        layout.addWidget(self.line_edit)
        
        self.current_color_str = "0xFFFFFF"
        self._on_text_changed(self.current_color_str)

    def _on_text_changed(self, text):
        self.current_color_str = text
        self.update_button_color(text)
        self.colorChanged.emit(text)

    def pick_color(self):
        # Try to parse current color
        c = QColor(Qt.GlobalColor.white)
        text = self.line_edit.text().strip()
        
        # Parse 0xRRGGBB
        if text.startswith("0x") and len(text) == 8:
            r = int(text[2:4], 16)
            g = int(text[4:6], 16)
            b = int(text[6:8], 16)
            c = QColor(r, g, b)
        elif text.startswith("#"):
            c = QColor(text)
        elif QColor.isValidColor(text):
            c = QColor(text)
            
        dialog = QColorDialog(c, self)
        # Disable Alpha Channel
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        if dialog.exec():
            new_color = dialog.currentColor()
            # Format as 0xRRGGBB
            hex_str = f"0x{new_color.red():02X}{new_color.green():02X}{new_color.blue():02X}"
            self.line_edit.setText(hex_str)

    def update_button_color(self, text):
        c = QColor(Qt.GlobalColor.white)
        valid = False
        text = text.strip()
        
        try:
            if text.startswith("0x") and len(text) == 8:
                r = int(text[2:4], 16)
                g = int(text[4:6], 16)
                b = int(text[6:8], 16)
                c = QColor(r, g, b)
                valid = True
            elif QColor.isValidColor(text):
                c = QColor(text)
                valid = True
        except:
            pass
            
        if valid:
            style = f"background-color: rgb({c.red()}, {c.green()}, {c.blue()}); border: 1px solid #888;"
            self.btn_pick.setStyleSheet(style)
        else:
            self.btn_pick.setStyleSheet("background-color: transparent; border: 1px solid red;")

    def setValue(self, value):
        if value != self.line_edit.text():
            self.line_edit.setText(str(value))
    
    def value(self):
        return self.line_edit.text()

def get_widget_value(widget: QWidget) -> Any:
    """Helper to get value from various widget types"""
    if isinstance(widget, TriStateBoolWidget): return widget.get_state()
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): 
        return widget.value()
    elif isinstance(widget, QLineEdit): return widget.text() if widget.text() else None
    elif isinstance(widget, QComboBox): return widget.currentData()
    elif isinstance(widget, ColorPickerWidget): return widget.value()
    return None
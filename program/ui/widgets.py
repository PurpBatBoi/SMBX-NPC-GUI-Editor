from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QRadioButton, QButtonGroup, 
                             QFrame, QToolButton, QLabel, QFormLayout, QVBoxLayout,
                             QSplitter, QSplitterHandle, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, Any
from ..validated_widgets import ValidatedSpinBox, ValidatedDoubleSpinBox

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

    def add_row(self, label: str, widget: QWidget):
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

def get_widget_value(widget: QWidget) -> Any:
    """Helper to get value from various widget types"""
    if isinstance(widget, TriStateBoolWidget): return widget.get_state()
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): 
        return widget.value()
    elif isinstance(widget, QLineEdit): return widget.text() if widget.text() else None
    elif isinstance(widget, QComboBox): return widget.currentData()
    return None

# tests/smoke_test.py
import sys
import os
# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication

app = QApplication([])

try:
    print("Testing Phase 1 modules...")
    from program.ui.widgets import TriStateBoolWidget, CollapsibleBox
    w = TriStateBoolWidget()
    print("- Widgets instantiated")
    
    print("Testing Phase 2 modules...")
    from program.ui.styles import AppColors, AppStyles
    print("- Styles imported")
    
    from program.utils.image_utils import load_legacy_sprite
    print("- Image utils imported")
    
    from program.ui.form_builder import FormBuilder
    fb = FormBuilder()
    print("- FormBuilder instantiated")
    
    from program.controllers.file_controller import FileController
    # FileController needs arguments, just checking import for now
    print("- FileController imported")
    
    print("Testing MainWindow integration...")
    from program.editor_window import MainWindow
    mw = MainWindow()
    print("- MainWindow instantiated")
    
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
print("Smoke test passed")

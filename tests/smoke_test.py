
# tests/smoke_test.py
import sys
import os
# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication

app = QApplication([])

try:
    from program.ui.widgets import TriStateBoolWidget, CollapsibleBox
    w = TriStateBoolWidget()
    b = CollapsibleBox("Test")
    print("Widgets instantiated successfully")
    
    # Try importing MainWindow to check for broken imports
    from program.editor_window import MainWindow
    print("MainWindow imported successfully")
    
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
print("Smoke test passed")

from PyQt6.QtGui import QColor

class AppColors:
    # Theme
    BACKGROUND = QColor(30, 30, 30)
    GRID = QColor(50, 50, 50)
    GRID_CENTER = QColor(100, 100, 100)
    TEXT_PRIMARY = QColor(200, 200, 200)
    
    # Overlays
    HITBOX_FILL = QColor(0, 255, 0, 30)
    HITBOX_BORDER = QColor(0, 255, 0)
    HITBOX_BORDER_DIM = QColor(0, 255, 0, 80)
    
    GFX_BORDER = QColor(255, 50, 50)
    GFX_BORDER_DIM = QColor(255, 50, 50, 80)

    # Lighting
    LIGHT_FILL = QColor(50, 150, 255, 40)
    LIGHT_BORDER = QColor(50, 150, 255)

class AppStyles:
    HEADER_FRAME = """
        .QFrame { background-color: #444; border-radius: 3px; }
        .QFrame:hover { background-color: #555; }
    """
    
    ARROW_BUTTON = "QToolButton { border: none; background: transparent; color: white; }"
    
    LABEL_TITLE = "font-weight: bold; color: white;"
    
    BTN_HITBOX_MODE = """
        QPushButton { background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; } 
        QPushButton:checked { background-color: #2e7d32; }
    """
    
    BTN_STEP = """
        QPushButton { 
            background-color: #1976d2; 
            color: white; 
            font-weight: bold; 
            font-size: 16px;
            border-radius: 4px;
        }
        QPushButton:hover { 
            background-color: #1565c0; 
        }
        QPushButton:pressed {
            background-color: #0d47a1;
        }
    """
    
    BTN_PLAY_PAUSE = """
        QPushButton { 
            background-color: #e53935; 
            color: white; 
            font-weight: bold; 
            font-size: 16px;
            border-radius: 4px;
        }
        QPushButton:checked { 
            background-color: #43a047; 
        }
        QPushButton:hover { 
            background-color: #c62828; 
        }
        QPushButton:checked:hover { 
            background-color: #388e3c; 
        }
    """

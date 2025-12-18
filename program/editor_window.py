import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QCheckBox, QComboBox, 
                             QRadioButton, QFileDialog, QFrame, QPushButton, 
                             QFormLayout, QSlider, QSizePolicy, QToolButton, QButtonGroup)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from .npc_data import NPCData
from .preview_widget import AnimationPreview

class TriStateBoolWidget(QWidget):
    """A widget with two radio buttons: 'True' and 'False (Forced)'.
    
    States:
    - None: Neither button checked (property not written to file)
    - True: 'True' button checked (property = true in file)
    - False: 'False (Forced)' button checked (property = false in file)
    """
    
    stateChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.btn_true = QRadioButton("True")
        self.btn_false = QRadioButton("False (Forced)")
        
        # Button group allows deselecting all buttons
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(False)  # Allow manual deselection
        self.button_group.addButton(self.btn_true)
        self.button_group.addButton(self.btn_false)
        
        layout.addWidget(self.btn_true)
        layout.addWidget(self.btn_false)
        layout.addStretch()
        
        # Connect signals
        self.btn_true.toggled.connect(self._on_true_toggled)
        self.btn_false.toggled.connect(self._on_false_toggled)
    
    def _on_true_toggled(self, checked):
        if checked:
            self.btn_false.setChecked(False)
            self.stateChanged.emit()
    
    def _on_false_toggled(self, checked):
        if checked:
            self.btn_true.setChecked(False)
            self.stateChanged.emit()
        elif not self.btn_true.isChecked():
            # If unchecking false and true isn't checked, emit change
            self.stateChanged.emit()
    
    def get_state(self):
        """Returns None, True, or False"""
        if self.btn_true.isChecked():
            return True
        elif self.btn_false.isChecked():
            return False
        else:
            return None
    
    def set_state(self, value):
        """Sets the state. value can be None, True, or False"""
        self.blockSignals(True)
        if value is True:
            self.btn_true.setChecked(True)
            self.btn_false.setChecked(False)
        elif value is False:
            self.btn_true.setChecked(False)
            self.btn_false.setChecked(True)
        else:  # None
            self.btn_true.setChecked(False)
            self.btn_false.setChecked(False)
        self.blockSignals(False)

class CollapsibleBox(QWidget):
    """A custom widget that has a title bar and collapsible content."""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        # Toggle Button (Header)
        self.toggle_button = QToolButton(text=title, checkable=True, checked=True)
        self.toggle_button.setStyleSheet("QToolButton { border: none; font-weight: bold; background-color: #444; color: white; padding: 5px; border-radius: 3px; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.clicked.connect(self.on_pressed)

        # Content Area
        self.content_area = QWidget()
        self.content_layout = QFormLayout()
        self.content_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_area.setLayout(self.content_layout)
        
        # Main Layout
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.content_area.setVisible(checked)
        
    def add_row(self, label, widget):
        self.content_layout.addRow(label, widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBX Animation Editor")
        self.resize(1000, 700)
        
        self.npc_data = NPCData()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- Left Panel ---
        control_panel = QFrame()
        control_panel.setFixedWidth(380)
        control_layout = QVBoxLayout(control_panel)
        
        # 1. File Buttons
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("Load .txt")
        btn_load.clicked.connect(self.load_file)
        btn_save = QPushButton("Save .txt")
        btn_save.clicked.connect(self.save_file)
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_save)
        control_layout.addLayout(btn_layout)

        control_layout.addSpacing(10)
        
        # Mode Selector
        mode_frame = QFrame()
        mode_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        mode_frame.setStyleSheet("QFrame { background-color: #3a3a3a; border-radius: 4px; padding: 5px; }")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(8, 8, 8, 8)
        
        mode_label = QLabel("File Format:")
        mode_label.setStyleSheet("font-weight: bold; color: white;")
        mode_layout.addWidget(mode_label)
        
        mode_btn_layout = QHBoxLayout()
        self.rb_txt = QRadioButton("TXT Mode")
        self.rb_txt.setChecked(True)
        self.rb_txt.setToolTip("Save as .txt file (SMBX 1.3 format)")
        self.rb_txt.toggled.connect(self.on_mode_change)
        
        self.rb_ini = QRadioButton("INI Mode")
        self.rb_ini.setToolTip("Save as .ini file (SMBX2 format)")
        self.rb_ini.toggled.connect(self.on_mode_change)
        
        mode_btn_layout.addWidget(self.rb_txt)
        mode_btn_layout.addWidget(self.rb_ini)
        mode_layout.addLayout(mode_btn_layout)
        
        control_layout.addWidget(mode_frame)

        control_layout.addSpacing(10)

        # 2. Collapsible Sections
        self.inputs = {}
        self.bool_inputs = {}  # Separate storage for tri-state bools

        # --- Helper Functions ---
        
        def add_spin(section, internal_key, display_label, min_v, max_v, tip):
            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setToolTip(tip)
            spin.valueChanged.connect(self.on_change)
            self.inputs[internal_key] = spin
            section.add_row(display_label, spin)

        def add_dual_spin(section, main_label, key1, key2, sub_label1, sub_label2, min_v, max_v, tip1, tip2):
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(5)

            # Spinbox 1
            if sub_label1: 
                lbl1 = QLabel(sub_label1)
                lbl1.setFixedWidth(35)
                l.addWidget(lbl1)
            s1 = QSpinBox()
            s1.setRange(min_v, max_v)
            s1.setToolTip(tip1)
            s1.valueChanged.connect(self.on_change)
            s1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            l.addWidget(s1)
            
            # Spinbox 2
            if sub_label2: 
                lbl2 = QLabel(sub_label2)
                lbl2.setStyleSheet("margin-left: 5px;")
                lbl2.setFixedWidth(40)
                l.addWidget(lbl2)
            s2 = QSpinBox()
            s2.setRange(min_v, max_v)
            s2.setToolTip(tip2)
            s2.valueChanged.connect(self.on_change)
            s2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            l.addWidget(s2)

            self.inputs[key1] = s1
            self.inputs[key2] = s2
            section.add_row(main_label, container)
        
        def add_tristate_bool(section, internal_key, display_label, tip):
            widget = TriStateBoolWidget()
            widget.setToolTip(tip)
            widget.stateChanged.connect(self.on_change)
            self.bool_inputs[internal_key] = widget
            section.add_row(display_label, widget)

        # === SECTION: ANIMATION ===
        self.section_anim = CollapsibleBox("Animation")
        control_layout.addWidget(self.section_anim)

        add_spin(self.section_anim, 'frames', 'Frames', 1, 100, "Frames per direction")
        add_spin(self.section_anim, 'framespeed', 'Frame Speed', 1, 100, "Ticks per Frame (Lower = Faster)")
        add_dual_spin(self.section_anim, "GFX", 'gfxwidth', 'gfxheight', "Width:", "Height:", 1, 1024, "gfxwidth", "gfxheight")
        add_dual_spin(self.section_anim, "GFX Offset", 'gfxoffsetx', 'gfxoffsety', "X:", "Y:", -500, 500, "gfxoffsetx", "gfxoffsety")
        
        self.combo_style = QComboBox()
        self.combo_style.addItems(["0: Goomba (L=R)", "1: Koopa (Sep L/R)", "2: SMB2 (L/R/UD)"])
        self.combo_style.currentIndexChanged.connect(self.on_change)
        self.section_anim.add_row("Frame Style", self.combo_style)
        
        add_tristate_bool(self.section_anim, 'foreground', 'Foreground Priority', 
                         "If True, NPC renders in front of blocks. If not set, uses default.")

        control_layout.addSpacing(5)

        # === SECTION: COLLISION ===
        self.section_col = CollapsibleBox("Collision")
        control_layout.addWidget(self.section_col)

        add_dual_spin(self.section_col, "Hitbox", 'width', 'height', "Width:", "Height:", 1, 1024, "width", "height")
        
        # Boolean collision properties
        add_tristate_bool(self.section_col, 'noblockcollision', 'No Block Collision',
                         "If true, NPC won't interact with blocks/NPCs (unless thrown)")
        add_tristate_bool(self.section_col, 'npcblock', 'NPC Block',
                         "Whether this NPC blocks other NPCs' movement")
        add_tristate_bool(self.section_col, 'npcblocktop', 'NPC Block Top',
                         "Whether thrown NPCs bounce off this NPC from the top")
        add_tristate_bool(self.section_col, 'playerblock', 'Player Block',
                         "Whether this NPC blocks player movement")
        add_tristate_bool(self.section_col, 'playerblocktop', 'Player Block Top',
                         "Whether players/NPCs can stand on this NPC")
        
        # 3. View Settings
        control_layout.addSpacing(10)
        view_box = QFrame()
        view_box.setFrameStyle(QFrame.Shape.StyledPanel)
        view_layout = QVBoxLayout(view_box)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Preview:"))
        self.rb_left = QRadioButton("Left")
        self.rb_left.setChecked(True)
        self.rb_left.toggled.connect(self.on_direction_change)
        self.rb_right = QRadioButton("Right")
        self.rb_right.toggled.connect(self.on_direction_change)
        dir_layout.addWidget(self.rb_left)
        dir_layout.addWidget(self.rb_right)
        view_layout.addLayout(dir_layout)

        control_layout.addStretch()
        control_layout.addWidget(view_box)
        layout.addWidget(control_panel)

        # --- Right Panel (Preview) ---
        self.preview = AnimationPreview(self.npc_data)
        self.preview.dataChanged.connect(self.sync_spinboxes_from_visual_edit)
        layout.addWidget(self.preview)

        # --- FLOATING HUD BUTTON ---
        self.btn_hitbox_mode = QPushButton("Hitbox Adjustment Mode", self.preview)
        self.btn_hitbox_mode.setCheckable(True)
        self.btn_hitbox_mode.move(10, 10)
        self.btn_hitbox_mode.resize(180, 30)
        self.btn_hitbox_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hitbox_mode.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 50, 50, 200);
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(70, 70, 70, 255);
            }
            QPushButton:checked {
                background-color: #2e7d32; 
                border: 1px solid #1b5e20;
                font-weight: bold;
            }
        """)
        self.btn_hitbox_mode.toggled.connect(self.on_mode_toggle)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            "Open NPC File", 
            "", 
            "NPC Files (*.txt *.ini);;TXT Files (*.txt);;INI Files (*.ini);;All Files (*)"
        )
        if fname:
            if self.npc_data.load(fname):
                self.update_ui_from_data()
                self.preview.load_image()
                
                # Update mode selector based on loaded file
                if self.npc_data.file_mode == "ini":
                    self.rb_ini.setChecked(True)
                else:
                    self.rb_txt.setChecked(True)
                
                self.setWindowTitle(f"Editing: {os.path.basename(fname)}")

    def save_file(self):
        self.update_data_from_ui() 
        self.npc_data.save()

    def update_ui_from_data(self):
        p = self.npc_data.params
        self.block_signals_all(True)
        
        # Regular integer parameters
        self.inputs['frames'].setValue(p.get('frames', 1))
        self.inputs['framespeed'].setValue(p.get('framespeed', 8))
        self.inputs['gfxwidth'].setValue(p.get('gfxwidth', 32))
        self.inputs['gfxheight'].setValue(p.get('gfxheight', 32))
        self.inputs['width'].setValue(p.get('width', 32))
        self.inputs['height'].setValue(p.get('height', 32))
        self.inputs['gfxoffsetx'].setValue(p.get('gfxoffsetx', 0))
        self.inputs['gfxoffsety'].setValue(p.get('gfxoffsety', 0))
        
        style = p.get('framestyle', 0)
        if 0 <= style <= 2:
            self.combo_style.setCurrentIndex(style)
        
        # Tri-state boolean parameters
        for key, widget in self.bool_inputs.items():
            widget.set_state(p.get(key))
        
        self.block_signals_all(False)
        self.preview.update_timer()

    def sync_spinboxes_from_visual_edit(self):
        p = self.npc_data.params
        self.block_signals_all(True)
        self.inputs['gfxwidth'].setValue(p['gfxwidth'])
        self.inputs['gfxheight'].setValue(p['gfxheight'])
        self.inputs['width'].setValue(p['width'])
        self.inputs['height'].setValue(p['height'])
        self.inputs['gfxoffsetx'].setValue(p['gfxoffsetx'])
        self.inputs['gfxoffsety'].setValue(p['gfxoffsety'])
        self.block_signals_all(False)

    def update_data_from_ui(self):
        p = self.npc_data.params
        p['frames'] = self.inputs['frames'].value()
        p['framespeed'] = self.inputs['framespeed'].value()
        p['gfxwidth'] = self.inputs['gfxwidth'].value()
        p['gfxheight'] = self.inputs['gfxheight'].value()
        p['width'] = self.inputs['width'].value()
        p['height'] = self.inputs['height'].value()
        p['gfxoffsetx'] = self.inputs['gfxoffsetx'].value()
        p['gfxoffsety'] = self.inputs['gfxoffsety'].value()
        p['framestyle'] = self.combo_style.currentIndex()
        
        # Update tri-state booleans
        for key, widget in self.bool_inputs.items():
            p[key] = widget.get_state()

    def on_change(self):
        self.update_data_from_ui()
        self.preview.update_timer()
        self.preview.update()

    def on_mode_toggle(self, checked):
        self.preview.set_hitbox_mode(checked)
        if checked:
            self.btn_hitbox_mode.setText("Hitbox Mode (ACTIVE)")
        else:
            self.btn_hitbox_mode.setText("Hitbox Adjustment Mode")

    def on_direction_change(self):
        self.preview.show_direction = 1 if self.rb_right.isChecked() else 0
        self.preview.update()
    
    def on_mode_change(self):
        """Update the file mode when user changes format selector"""
        if self.rb_ini.isChecked():
            self.npc_data.file_mode = "ini"
        else:
            self.npc_data.file_mode = "txt"

    def block_signals_all(self, b):
        for w in self.inputs.values():
            w.blockSignals(b)
        for w in self.bool_inputs.values():
            w.blockSignals(b)
        self.combo_style.blockSignals(b)
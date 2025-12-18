import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QCheckBox, QComboBox, 
                             QRadioButton, QFileDialog, QFrame, QPushButton, 
                             QFormLayout, QSlider, QSizePolicy)
from PyQt6.QtCore import Qt
from .npc_data import NPCData
from .preview_widget import AnimationPreview

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBX Animation Editor")
        self.resize(1000, 650)
        
        self.npc_data = NPCData()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- Left Panel ---
        control_panel = QFrame()
        control_panel.setFixedWidth(340)
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

        # 2. Form Inputs
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.inputs = {}
        
        def add_spin(internal_key, display_label, min_v, max_v, tip):
            spin = QSpinBox()
            spin.setRange(min_v, max_v)
            spin.setToolTip(tip)
            spin.valueChanged.connect(self.on_change)
            self.inputs[internal_key] = spin
            self.form_layout.addRow(display_label, spin)

        def add_dual_spin(main_label, key1, key2, sub_label1, sub_label2, min_v, max_v, tip1, tip2):
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(5)

            # --- SPINBOX 1 ---
            if sub_label1: 
                lbl1 = QLabel(sub_label1)
                lbl1.setFixedWidth(35)  # Reduced slightly for better left alignment
                l.addWidget(lbl1)
            
            s1 = QSpinBox()
            s1.setRange(min_v, max_v)
            s1.setToolTip(tip1)
            s1.valueChanged.connect(self.on_change)
            s1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            l.addWidget(s1)
            
            # --- SPINBOX 2 ---
            if sub_label2: 
                lbl2 = QLabel(sub_label2)
                lbl2.setStyleSheet("margin-left: 5px;")
                lbl2.setFixedWidth(40)  # Reduced slightly for better left alignment
                l.addWidget(lbl2)
                
            s2 = QSpinBox()
            s2.setRange(min_v, max_v)
            s2.setToolTip(tip2)
            s2.valueChanged.connect(self.on_change)
            s2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            l.addWidget(s2)

            self.inputs[key1] = s1
            self.inputs[key2] = s2
            self.form_layout.addRow(main_label, container)

        # -- REORDERED & RENAMED FIELDS --
        
        add_spin('frames', 'Frames', 1, 100, "Frames per direction")
        add_spin('framespeed', 'Frame Speed', 1, 100, "Ticks per Frame (TLDR: Lower, the faster)")
        
        # GFX Size
        add_dual_spin("GFX", 'gfxwidth', 'gfxheight', "Width:", "Height:", 1, 1024, "gfxwidth", "gfxheight")
        
        # GFX Offset (Moved up)
        add_dual_spin("GFX Offset", 'gfxoffsetx', 'gfxoffsety', "X:", "Y:", -500, 500, "gfxoffsetx", "gfxoffsety")

        self.combo_style = QComboBox()
        self.combo_style.addItems(["0: Goomba (L=R)", "1: Koopa (Sep L/R)", "2: SMB2 (L/R/UD)"])
        self.combo_style.currentIndexChanged.connect(self.on_change)
        self.form_layout.addRow("Frame Style", self.combo_style)

        # Hitbox
        add_dual_spin("Hitbox", 'width', 'height', "Width:", "Height:", 1, 1024, "width", "height")

        self.chk_fg = QCheckBox("True")
        self.chk_fg.stateChanged.connect(self.on_change)
        self.form_layout.addRow("Foreground Priority", self.chk_fg)

        control_layout.addLayout(self.form_layout)
        
        # 3. View Settings
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

        control_layout.addWidget(view_box)
        
        control_layout.addStretch()
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
        fname, _ = QFileDialog.getOpenFileName(self, "Open NPC Txt", "", "Text Files (*.txt)")
        if fname:
            if self.npc_data.load(fname):
                self.update_ui_from_data()
                self.preview.load_image()
                self.setWindowTitle(f"Editing: {os.path.basename(fname)}")

    def save_file(self):
        self.update_data_from_ui() 
        self.npc_data.save()

    def update_ui_from_data(self):
        p = self.npc_data.params
        self.block_signals_all(True)
        
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
            
        self.chk_fg.setChecked(p.get('foreground', False))
        
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
        p['foreground'] = self.chk_fg.isChecked()

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

    def block_signals_all(self, b):
        for w in self.inputs.values():
            w.blockSignals(b)
        self.combo_style.blockSignals(b)
        self.chk_fg.blockSignals(b)
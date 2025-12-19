import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, 
                             QRadioButton, QFileDialog, QFrame, QPushButton, 
                             QFormLayout, QSizePolicy, QToolButton, QScrollArea,
                             QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QButtonGroup, QSplitter, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QFileSystemWatcher
from PyQt6.QtGui import QUndoStack, QAction, QKeySequence
from .npc_data import NPCData
from .npc_definitions import NPC_DEFS
from .preview_widget import AnimationPreview
from .undo_commands import (ChangeParameterCommand, ChangeMultipleParametersCommand,
                            ToggleParameterCommand, AddCustomParameterCommand,
                            RemoveCustomParameterCommand, ChangeCustomParameterCommand)
from .validated_widgets import ValidatedSpinBox, ValidatedDoubleSpinBox
from .ui.widgets import TriStateBoolWidget, CollapsibleBox, NoResizeSplitter, get_widget_value



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBX Visual NPC Editor")
        self.resize(1100, 800)
        self.showMaximized() # Start maximized
        
        # Undo/Redo Stack
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(50)
        self.setAcceptDrops(True)

        self.npc_data = NPCData()
        self.ui_sections = {}
        self.all_widgets = {}
        self.param_checkboxes = {}
        self.category_keys = {}
        self._drag_snapshot = {}

        self.is_saving = False
        self.watched_files = []
        self.is_loading = False
        
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_external_file_change)
        
        self.setup_menu_bar()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Panel
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumWidth(450)
        scroll_content = QWidget()
        self.form_layout = QVBoxLayout(scroll_content)

        self.generate_standard_ui()

        # Custom Props
        self.custom_box = CollapsibleBox("Custom / Extra Properties")
        self.custom_table = QTableWidget()
        self.custom_table.setColumnCount(2)
        self.custom_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.custom_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.custom_table.setMinimumHeight(150)
        self.custom_table.itemChanged.connect(self.on_custom_table_change)

        custom_btn_lay = QHBoxLayout()
        btn_add_custom = QPushButton("+ Add")
        btn_add_custom.clicked.connect(self.add_custom_row)
        btn_rem_custom = QPushButton("- Remove")
        btn_rem_custom.clicked.connect(self.remove_custom_row)
        custom_btn_lay.addWidget(btn_add_custom)
        custom_btn_lay.addWidget(btn_rem_custom)

        self.custom_box.content_layout.addRow(custom_btn_lay)
        self.custom_box.content_layout.addRow(self.custom_table)
        self.form_layout.addWidget(self.custom_box)
        self.form_layout.addStretch(1)
        self.scroll_area.setWidget(scroll_content)
        
        splitter = NoResizeSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.scroll_area)
        main_layout.addWidget(splitter, 1)

        # Right Panel
        right_panel = QWidget()
        right_panel.setMinimumWidth(400)
        r_layout = QVBoxLayout(right_panel)
        
        view_ctrl = QHBoxLayout()
        self.rb_left = QRadioButton("Left")
        self.rb_left.setChecked(True)
        self.rb_left.toggled.connect(self.on_direction_change)
        self.rb_right = QRadioButton("Right")
        self.rb_right.toggled.connect(self.on_direction_change)
        view_ctrl.addWidget(QLabel("Preview:"))
        view_ctrl.addWidget(self.rb_left)
        view_ctrl.addWidget(self.rb_right)
        view_ctrl.addStretch()
        r_layout.addLayout(view_ctrl)

        self.preview = AnimationPreview(self.npc_data)
        self.preview.dataChanged.connect(self.sync_ui_from_visual)
        self.preview.dragStarted.connect(self.on_visual_drag_start)
        self.preview.dragFinished.connect(self.on_visual_drag_complete)
        
        r_layout.addWidget(self.preview)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # Overlay Buttons (Children of Preview)
        self.btn_hitbox_mode = QPushButton("Hitbox Adjustment Mode", self.preview)
        self.btn_hitbox_mode.setCheckable(True)
        self.btn_hitbox_mode.resize(180, 30)
        self.btn_hitbox_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hitbox_mode.setStyleSheet("""
            QPushButton { background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; } 
            QPushButton:checked { background-color: #2e7d32; }
        """)
        self.btn_hitbox_mode.toggled.connect(self.on_mode_toggle)

        # Animation control buttons - Step Through and Play/Pause
        self.btn_step_frame = QPushButton("⏩", self.preview)  # Fast-forward symbol
        self.btn_step_frame.setFixedSize(40, 30)
        self.btn_step_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_step_frame.setStyleSheet("""
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
        """)
        self.btn_step_frame.setToolTip("Step to next frame")
        self.btn_step_frame.clicked.connect(self.on_step_frame)

        self.btn_play_pause = QPushButton("⏸", self.preview)  # Pause symbol
        self.btn_play_pause.setCheckable(True)
        self.btn_play_pause.setFixedSize(40, 30)
        self.btn_play_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_pause.setStyleSheet("""
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
        """)
        self.btn_play_pause.setToolTip("Pause/Resume animation")
        self.btn_play_pause.toggled.connect(self.on_pause_toggled)

        # Store reference to right panel for proper button positioning
        self.right_panel = right_panel

        # Initial positioning
        self.reposition_overlay_buttons()

    def reposition_overlay_buttons(self):
        """Anchor overlay buttons to preview corners and align animation buttons properly"""
        if hasattr(self, 'btn_hitbox_mode'):
            self.btn_hitbox_mode.move(10, 10)
        
        if hasattr(self, 'btn_play_pause') and hasattr(self, 'btn_step_frame'):
            # Get preview widget dimensions
            preview_width = self.preview.width()
            preview_height = self.preview.height()
            
            # Button dimensions
            button_height = self.btn_play_pause.height()
            button_width = self.btn_play_pause.width()
            
            # Padding and gap constants
            right_pad = 10  # Distance from right edge
            button_gap = 5   # Gap between buttons
            
            # The mode label is drawn at (10, height - 10) in the preview's paintEvent
            # Text baseline is at height - 10, so we position buttons to align with this
            # Button bottom edge should be at the same Y as text baseline
            label_baseline_y = preview_height - 10
            
            # Calculate button Y position so its bottom aligns with label baseline
            # We want: button_top + button_height = label_baseline_y
            y_pos = label_baseline_y - button_height
            
            # Calculate horizontal positions from right edge
            # Pause button is rightmost
            pause_x = preview_width - button_width - right_pad
            
            # Step button is to the left with a small gap
            step_x = pause_x - button_width - button_gap
            
            # Ensure buttons don't go off-screen (safety check)
            if step_x < 10:
                step_x = 10
                pause_x = step_x + button_width + button_gap
            
            self.btn_step_frame.move(step_x, y_pos)
            self.btn_play_pause.move(pause_x, y_pos)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposition_overlay_buttons()

    def on_pause_toggled(self, paused):
        """Handle pause/resume toggle - only affects preview, not saved data"""
        self.preview.toggle_pause(paused)
        # Update button symbol and tooltip
        if paused:
            self.btn_play_pause.setText("▶")  # Play symbol
            self.btn_play_pause.setToolTip("Resume animation")
        else:
            self.btn_play_pause.setText("⏸")  # Pause symbol
            self.btn_play_pause.setToolTip("Pause animation")
    
    def on_step_frame(self):
        """Manually advance to next frame - preview only, not saved"""
        self.preview.manual_step_frame()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        
        action_load = QAction("&Open...", self)
        action_load.setShortcut(QKeySequence.StandardKey.Open)
        action_load.triggered.connect(self.load_file)
        file_menu.addAction(action_load)
        
        action_save = QAction("&Save", self)
        action_save.setShortcut(QKeySequence.StandardKey.Save)
        action_save.triggered.connect(self.save_file)
        file_menu.addAction(action_save)
        
        file_menu.addSeparator()
        action_exit = QAction("E&xit", self)
        action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        edit_menu = menubar.addMenu("&Edit")
        self.action_undo = self.undo_stack.createUndoAction(self, "&Undo")
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(self.action_undo)
        
        self.action_redo = self.undo_stack.createRedoAction(self, "&Redo")
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(self.action_redo)
        self.undo_stack.indexChanged.connect(self.on_undo_stack_changed)

    def on_undo_stack_changed(self, idx):
        if self.undo_stack.canUndo():
            self.status_bar.showMessage(f"Action: {self.undo_stack.undoText()}", 3000)

    def _register_widget(self, key, widget):
        self.all_widgets[key] = widget



    def _add_param_widget(self, section, key, definition):
        dtype = definition.get('type')
        widget = None
        if dtype == bool:
            widget = TriStateBoolWidget()
            widget.stateChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == int:
            widget = ValidatedSpinBox()
            widget.setRange(definition.get('min', -9999), definition.get('max', 9999))
            widget.valueChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == float:
            widget = ValidatedDoubleSpinBox()
            widget.setRange(definition.get('min', -9999.0), definition.get('max', 9999.0))
            widget.setSingleStep(definition.get('step', 0.1))
            widget.valueChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == str:
            widget = QLineEdit()
            widget.textChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == "enum":
            widget = QComboBox()
            for k, v in definition.get('choices', {}).items(): widget.addItem(v, k)
            widget.currentIndexChanged.connect(lambda: self.on_standard_change(key))
        
        if widget:
            widget.setToolTip(definition.get('tips', key))
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)
            chk = QCheckBox()
            chk.setChecked(False)
            chk.toggled.connect(lambda checked, k=key: self.on_param_enabled(k, checked))
            container_layout.addWidget(chk)
            container_layout.addWidget(widget, 1)
            section.add_row(definition.get('label', key), container)
            self._register_widget(key, widget)
            self.param_checkboxes[key] = chk

    def _add_dual_int_widget(self, section, label_row, key1, def1, key2, def2, sublabel1, sublabel2):
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        chk = QCheckBox()
        chk.setChecked(False)
        chk.toggled.connect(lambda checked, k=key1: self.on_param_enabled(k, checked))
        chk.toggled.connect(lambda checked, k=key2: self.on_param_enabled(k, checked))
        lay.addWidget(chk)
        if sublabel1: lay.addWidget(QLabel(sublabel1))
        w1 = ValidatedSpinBox()
        w1.setRange(def1.get('min', -9999), def1.get('max', 9999))
        w1.setToolTip(def1.get('tips', key1))
        w1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w1.valueChanged.connect(lambda: self.on_standard_change(key1))
        lay.addWidget(w1)
        if sublabel2: lay.addWidget(QLabel(sublabel2))
        w2 = ValidatedSpinBox()
        w2.setRange(def2.get('min', -9999), def2.get('max', 9999))
        w2.setToolTip(def2.get('tips', key2))
        w2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w2.valueChanged.connect(lambda: self.on_standard_change(key2))
        lay.addWidget(w2)
        section.add_row(label_row, container)
        self._register_widget(key1, w1)
        self._register_widget(key2, w2)
        self.param_checkboxes[key1] = chk
        self.param_checkboxes[key2] = chk

    def generate_standard_ui(self):
        categories = sorted(list(set(d['category'] for d in NPC_DEFS.values())))
        priority = ["Animation", "Collision", "Interaction", "Behaviour"]
        categories.sort(key=lambda x: priority.index(x) if x in priority else 99)
        pairs_config = [('gfxwidth', 'gfxheight', 'GFX Size', 'W:', 'H:'), ('width', 'height', 'Hitbox Size', 'W:', 'H:'), ('gfxoffsetx', 'gfxoffsety', 'GFX Offset', 'X:', 'Y:')]
        pair_map = {p[0]: ('primary', p) for p in pairs_config}
        pair_map.update({p[1]: ('secondary', p) for p in pairs_config})
        for cat in categories:
            section = CollapsibleBox(cat)
            self.form_layout.addWidget(section)
            self.ui_sections[cat] = section
            self.category_keys[cat] = []
            if cat == "Animation": section.expand()
        for key, definition in NPC_DEFS.items():
            cat = definition['category']
            section = self.ui_sections[cat]
            self.category_keys[cat].append(key)
            if key in pair_map:
                role, data = pair_map[key]
                if role == 'primary':
                    k1, k2, main_label, sub1, sub2 = data
                    self._add_dual_int_widget(section, main_label, k1, NPC_DEFS.get(k1), k2, NPC_DEFS.get(k2), sub1, sub2)
            else:
                self._add_param_widget(section, key, definition)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open NPC Txt", "", "Text Files (*.txt)")
        if fname: self._process_load_path(fname)

    def save_file(self):
        if not self.npc_data.filepath:
            fname, _ = QFileDialog.getSaveFileName(self, "Save NPC Config", "", "Text Files (*.txt)")
            if not fname: return
            self.npc_data.filepath = fname
            self.setWindowTitle(f"Editing: {os.path.basename(fname)}")
            self._update_file_watcher()
        self.is_saving = True
        self.npc_data.save()
        self.status_bar.showMessage(f"Saved: {os.path.basename(self.npc_data.filepath)}", 3000)
        QTimer.singleShot(500, lambda: setattr(self, 'is_saving', False))

    def update_ui_from_data(self):
        for key, widget in self.all_widgets.items():
            val = self.npc_data.standard_params.get(key)
            default = NPC_DEFS[key]['default']
            chk = self.param_checkboxes.get(key)
            widget.blockSignals(True)
            if chk:
                chk.blockSignals(True)
                is_active = (val is not None)
                chk.setChecked(is_active)
                widget.setEnabled(is_active)
                chk.blockSignals(False)
            display_val = val if val is not None else default
            if isinstance(widget, TriStateBoolWidget): widget.set_state(display_val)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): widget.setValue(display_val)
            elif isinstance(widget, QLineEdit): widget.setText(str(display_val))
            elif isinstance(widget, QComboBox):
                idx = widget.findData(display_val)
                if idx >= 0: widget.setCurrentIndex(idx)
            widget.blockSignals(False)

        for cat, keys in self.category_keys.items():
            section = self.ui_sections.get(cat)
            if not section: continue
            has_active = any(self.npc_data.standard_params.get(k) is not None for k in keys)
            if has_active: section.expand()
            else: section.collapse()

        self.custom_table.blockSignals(True)
        self.custom_table.setRowCount(0)
        has_custom = False
        for k, v in self.npc_data.custom_params.items():
            row = self.custom_table.rowCount()
            self.custom_table.insertRow(row)
            self.custom_table.setItem(row, 0, QTableWidgetItem(k))
            self.custom_table.setItem(row, 1, QTableWidgetItem(str(v)))
            has_custom = True
        self.custom_table.blockSignals(False)
        if has_custom: self.custom_box.expand()
        
        # Update animation button states based on current frame count
        self._update_animation_button_states()
        
        self.preview.update_timer()
        self.preview.update()

    def on_standard_change(self, key):
        if self.is_loading: return
        widget, chk = self.all_widgets.get(key), self.param_checkboxes.get(key)
        if not widget or not chk or not chk.isChecked(): return
        new_value, old_value = get_widget_value(widget), self.npc_data.standard_params.get(key)
        if new_value == old_value: return
        self.undo_stack.push(ChangeParameterCommand(self.npc_data, key, old_value, new_value, ui_callback=self.update_single_widget))
        
        # Update animation button states if frames changed
        if key == 'frames':
            self._update_animation_button_states()
        
        self.preview.update_timer()
        self.preview.update()
    
    def _update_animation_button_states(self):
        """Enable/disable animation control buttons based on frame count"""
        # Get current frames from data (this reflects real-time changes)
        frames = int(self.npc_data.standard_params.get('frames') or 1)
        
        if frames <= 1:
            self.btn_play_pause.setEnabled(False)
            self.btn_step_frame.setEnabled(False)
            self.btn_play_pause.setToolTip("No animation frames to play (frames = 1)")
            self.btn_step_frame.setToolTip("No animation frames to step through")
        else:
            self.btn_play_pause.setEnabled(True)
            self.btn_step_frame.setEnabled(True)
            paused = self.btn_play_pause.isChecked()
            if paused:
                self.btn_play_pause.setToolTip("Resume animation")
            else:
                self.btn_play_pause.setToolTip("Pause animation")
            self.btn_step_frame.setToolTip("Step to next frame")

    def on_param_enabled(self, key, checked):
        if self.is_loading:
            w = self.all_widgets.get(key)
            if w: w.setEnabled(checked)
            return
        widget = self.all_widgets.get(key)
        if not widget: return
        old_enabled = self.npc_data.standard_params.get(key) is not None
        value = get_widget_value(widget) if checked else None
        self.undo_stack.push(ToggleParameterCommand(self.npc_data, key, old_enabled, checked, value, ui_callback=self.update_single_checkbox))
        self.preview.update_timer()
        self.preview.update()

    def update_single_widget(self, key, value):
        widget = self.all_widgets.get(key)
        if not widget: return
        widget.blockSignals(True)
        display = value if value is not None else NPC_DEFS[key]['default']
        if isinstance(widget, TriStateBoolWidget): widget.set_state(display)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): widget.setValue(display)
        elif isinstance(widget, QLineEdit): widget.setText(str(display))
        elif isinstance(widget, QComboBox):
            idx = widget.findData(display)
            if idx >= 0: widget.setCurrentIndex(idx)
        widget.blockSignals(False)
        self.preview.update_timer()
        self.preview.update()

    def update_single_checkbox(self, key, enabled):
        chk, widget = self.param_checkboxes.get(key), self.all_widgets.get(key)
        if chk:
            chk.blockSignals(True)
            chk.setChecked(enabled)
            chk.blockSignals(False)
        if widget: widget.setEnabled(enabled)

    def on_visual_drag_start(self):
        keys = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        self._drag_snapshot = {k: self.npc_data.standard_params.get(k) for k in keys}
    
    def on_visual_drag_complete(self):
        if self.is_loading: return
        keys = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        changes = {}
        for key in keys:
            old_val, new_val = self._drag_snapshot.get(key), self.npc_data.standard_params.get(key)
            if old_val != new_val:
                changes[key] = (old_val, new_val)
                chk = self.param_checkboxes.get(key)
                if chk and not chk.isChecked():
                    chk.blockSignals(True)
                    chk.setChecked(True)
                    self.all_widgets[key].setEnabled(True)
                    chk.blockSignals(False)
        if changes:
            self.undo_stack.push(ChangeMultipleParametersCommand(self.npc_data, changes, ui_callback=self.update_single_widget, description="Visual Edit"))
        self._drag_snapshot = {}

    def sync_ui_from_visual(self):
        p, keys = self.npc_data.standard_params, ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        for key in keys:
            widget = self.all_widgets.get(key)
            val = p.get(key)
            if widget and val is not None:
                widget.blockSignals(True)
                widget.setValue(val)
                widget.blockSignals(False)

    def _update_file_watcher(self):
        if self.watched_files: self.watcher.removePaths(self.watched_files)
        self.watched_files = []
        if self.npc_data.filepath and os.path.exists(self.npc_data.filepath): self.watched_files.append(self.npc_data.filepath)
        if self.preview.image_path and os.path.exists(self.preview.image_path): self.watched_files.append(self.preview.image_path)
        if hasattr(self.preview, 'mask_path') and self.preview.mask_path and os.path.exists(self.preview.mask_path): self.watched_files.append(self.preview.mask_path)
        if self.watched_files: self.watcher.addPaths(self.watched_files)

    def on_external_file_change(self, path):
        if self.is_saving: return
        if not os.path.exists(path):
            QTimer.singleShot(100, lambda: self._update_file_watcher())
            return
        if path == self.npc_data.filepath:
            self.is_loading = True
            if self.npc_data.load(path): self.update_ui_from_data()
            self.is_loading = False
        elif path == self.preview.image_path or (hasattr(self.preview, 'mask_path') and path == self.preview.mask_path):
            self.preview.load_image()
            self.status_bar.showMessage("Graphics reloaded", 2000)

    def on_custom_table_change(self):
        self.npc_data.custom_params = {}
        for r in range(self.custom_table.rowCount()):
            k_item, v_item = self.custom_table.item(r, 0), self.custom_table.item(r, 1)
            if k_item and v_item and k_item.text().strip(): self.npc_data.set_custom(k_item.text().strip(), v_item.text().strip())
    
    def add_custom_row(self):
        if self.is_loading: return
        self.undo_stack.push(AddCustomParameterCommand(self.npc_data, f"new_param_{self.custom_table.rowCount()}", "0", ui_callback=self.refresh_custom_table))
    
    def remove_custom_row(self):
        if self.is_loading: return
        cur = self.custom_table.currentRow()
        if cur >= 0:
            k_item, v_item = self.custom_table.item(cur, 0), self.custom_table.item(cur, 1)
            if k_item: self.undo_stack.push(RemoveCustomParameterCommand(self.npc_data, k_item.text().strip(), v_item.text().strip() if v_item else "", ui_callback=self.refresh_custom_table))
    
    def refresh_custom_table(self):
        self.custom_table.blockSignals(True)
        self.custom_table.setRowCount(0)
        for k, v in self.npc_data.custom_params.items():
            row = self.custom_table.rowCount()
            self.custom_table.insertRow(row)
            self.custom_table.setItem(row, 0, QTableWidgetItem(k))
            self.custom_table.setItem(row, 1, QTableWidgetItem(str(v)))
        self.custom_table.blockSignals(False)
    
    def on_mode_toggle(self, checked):
        self.preview.set_hitbox_mode(checked)
        self.btn_hitbox_mode.setText("Hitbox Mode (ACTIVE)" if checked else "Hitbox Adjustment Mode")
    
    def on_direction_change(self):
        self.preview.show_direction = 1 if self.rb_right.isChecked() else 0
        self.preview.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".txt"):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and file_path.lower().endswith(".txt"):
                self._process_load_path(file_path)
                break
    
    def _process_load_path(self, fname):
        self.is_loading = True
        if self.npc_data.load(fname):
            self.scroll_area.verticalScrollBar().setValue(0)
            self.update_ui_from_data()
            self.preview.load_image()
            self.setWindowTitle(f"Editing: {os.path.basename(fname)}")
            self._update_file_watcher()
            self.undo_stack.clear()
            if "Animation" in self.ui_sections: self.ui_sections["Animation"].expand()
            self.status_bar.showMessage(f"Loaded: {os.path.basename(fname)}", 5000)
        self.is_loading = False
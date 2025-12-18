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

# --- TriStateBoolWidget (Unchanged) ---
class TriStateBoolWidget(QWidget):
    stateChanged = pyqtSignal()
    def __init__(self, parent=None):
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
    def _on_true_toggled(self, checked):
        if checked: self.btn_false.setChecked(False)
        self.stateChanged.emit()
    def _on_false_toggled(self, checked):
        if checked: self.btn_true.setChecked(False)
        else:
            if not self.btn_true.isChecked(): self.stateChanged.emit()
        self.stateChanged.emit()
    def get_state(self):
        if self.btn_true.isChecked(): return True
        elif self.btn_false.isChecked(): return False
        return None
    def set_state(self, value):
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

# --- CollapsibleBox (Unchanged) ---
class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
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

    def add_row(self, label, widget):
        self.content_layout.addRow(label, widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBX Visual NPC Editor")
        self.resize(1100, 800)
        
        # Undo/Redo Stack
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(50)  # Keep last 50 actions
        
        self.npc_data = NPCData()
        self.ui_sections = {}
        self.all_widgets = {}
        self.param_checkboxes = {}
        self.category_keys = {}
        # New variable to store values before a visual drag
        self._drag_snapshot = {}

        self.is_saving = False
        self.watched_files = []
        self.is_loading = False  # Flag to prevent undo during load
        
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_external_file_change)
        
        # Setup Menu Bar with Undo/Redo
        self.setup_menu_bar()
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(450)
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
        scroll.setWidget(scroll_content)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)
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
        # 1. dataChanged now only synchronizes the SpinBoxes/UI for visual feedback
        self.preview.dataChanged.connect(self.sync_ui_from_visual)
        
        # 2. dragStarted captures the "Before" state
        self.preview.dragStarted.connect(self.on_visual_drag_start)
        
        # 3. dragFinished creates the single Undo command
        self.preview.dragFinished.connect(self.on_visual_drag_complete)
        r_layout.addWidget(self.preview)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.btn_hitbox_mode = QPushButton("Hitbox Adjustment Mode", self.preview)
        self.btn_hitbox_mode.setCheckable(True)
        self.btn_hitbox_mode.move(10, 10)
        self.btn_hitbox_mode.resize(180, 30)
        self.btn_hitbox_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hitbox_mode.setStyleSheet("QPushButton { background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; } QPushButton:checked { background-color: #2e7d32; }")
        self.btn_hitbox_mode.toggled.connect(self.on_mode_toggle)

    def setup_menu_bar(self):
        """Setup menu bar with undo/redo actions"""
        menubar = self.menuBar()
        
        # File Menu
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
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo Action
        self.action_undo = self.undo_stack.createUndoAction(self, "&Undo")
        self.action_undo.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(self.action_undo)
        
        # Redo Action
        self.action_redo = self.undo_stack.createRedoAction(self, "&Redo")
        self.action_redo.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(self.action_redo)
        
        # Connect undo stack signals for status updates
        self.undo_stack.indexChanged.connect(self.on_undo_stack_changed)

    def on_undo_stack_changed(self, idx):
        """Update status bar when undo/redo occurs"""
        if self.undo_stack.canUndo():
            self.status_bar.showMessage(f"Action: {self.undo_stack.undoText()}", 3000)

    def _register_widget(self, key, widget):
        self.all_widgets[key] = widget

    def _get_widget_value(self, widget):
        if isinstance(widget, TriStateBoolWidget): return widget.get_state()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): 
            return widget.value()
        elif isinstance(widget, QLineEdit): return widget.text() if widget.text() else None
        elif isinstance(widget, QComboBox): return widget.currentData()
        return None

    def _add_param_widget(self, section, key, definition):
        dtype = definition.get('type')
        widget = None
        if dtype == bool:
            widget = TriStateBoolWidget()
            widget.stateChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == int:
            widget = ValidatedSpinBox()  # Use validated version
            widget.setRange(definition.get('min', -9999), definition.get('max', 9999))
            widget.valueChanged.connect(lambda: self.on_standard_change(key))
        elif dtype == float:
            widget = ValidatedDoubleSpinBox()  # Use validated version
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
        w1 = ValidatedSpinBox()  # Use validated version
        w1.setRange(def1.get('min', -9999), def1.get('max', 9999))
        w1.setToolTip(def1.get('tips', key1))
        w1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w1.valueChanged.connect(lambda: self.on_standard_change(key1))
        lay.addWidget(w1)
        
        if sublabel2: lay.addWidget(QLabel(sublabel2))
        w2 = ValidatedSpinBox()  # Use validated version
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
                continue
            else:
                self._add_param_widget(section, key, definition)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open NPC Txt", "", "Text Files (*.txt)")
        if fname:
            self.is_loading = True
            if self.npc_data.load(fname):
                self.update_ui_from_data()
                self.preview.load_image()
                self.setWindowTitle(f"Editing: {os.path.basename(fname)}")
                self._update_file_watcher()
                # Clear undo stack when loading new file
                self.undo_stack.clear()
                self.status_bar.showMessage(f"Loaded: {os.path.basename(fname)}", 5000)
            self.is_loading = False

    def save_file(self):
        # 1. Handle "Save As" if no file is currently loaded
        if not self.npc_data.filepath:
            fname, _ = QFileDialog.getSaveFileName(self, "Save NPC Config", "", "Text Files (*.txt)")
            if not fname:
                return # User cancelled
            self.npc_data.filepath = fname
            self.setWindowTitle(f"Editing: {os.path.basename(fname)}")
            self._update_file_watcher()

        # 2. Save
        self.is_saving = True
        self.npc_data.save()
        self.status_bar.showMessage(f"Saved: {os.path.basename(self.npc_data.filepath)}", 3000)
        QTimer.singleShot(500, lambda: setattr(self, 'is_saving', False))

    def update_ui_from_data(self):
        # 1. Update Widgets
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
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)): 
                widget.setValue(display_val)
            elif isinstance(widget, QLineEdit): widget.setText(str(display_val))
            elif isinstance(widget, QComboBox):
                idx = widget.findData(display_val)
                if idx >= 0: widget.setCurrentIndex(idx)
            widget.blockSignals(False)

        # 2. Update Categories (Expand active ones)
        for cat, keys in self.category_keys.items():
            section = self.ui_sections.get(cat)
            if not section: continue
            
            has_active = any(self.npc_data.standard_params.get(k) is not None for k in keys)
            if has_active: section.expand()
            else: section.collapse()

        # 3. Custom Table
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
        
        self.preview.update_timer()
        self.preview.update()

    def on_standard_change(self, key):
        """Handle standard parameter change with undo support"""
        if self.is_loading:
            return  # Don't create undo commands during file load
        
        widget = self.all_widgets.get(key)
        chk = self.param_checkboxes.get(key)
        if not widget or not chk:
            return
        
        if not chk.isChecked():
            return  # Parameter is disabled
        
        new_value = self._get_widget_value(widget)
        old_value = self.npc_data.standard_params.get(key)
        
        # Don't create command if value unchanged
        if new_value == old_value:
            return
        
        # Create undo command
        cmd = ChangeParameterCommand(
            self.npc_data,
            key,
            old_value,
            new_value,
            ui_callback=self.update_single_widget
        )
        self.undo_stack.push(cmd)
        
        self.preview.update_timer()
        self.preview.update()

    def on_param_enabled(self, key, checked):
        """Handle parameter enable/disable with undo support"""
        if self.is_loading:
            widget = self.all_widgets.get(key)
            if widget:
                widget.setEnabled(checked)
            return
        
        widget = self.all_widgets.get(key)
        if not widget:
            return
        
        old_enabled = self.npc_data.standard_params.get(key) is not None
        value = self._get_widget_value(widget) if checked else None
        
        # Create undo command
        cmd = ToggleParameterCommand(
            self.npc_data,
            key,
            old_enabled,
            checked,
            value,
            ui_callback=self.update_single_checkbox
        )
        self.undo_stack.push(cmd)
        
        self.preview.update_timer()
        self.preview.update()

    def update_single_widget(self, key, value):
        """Update a single widget from undo/redo"""
        widget = self.all_widgets.get(key)
        if not widget:
            return
        
        widget.blockSignals(True)
        
        if value is None:
            # Use default
            default = NPC_DEFS[key]['default']
            if isinstance(widget, TriStateBoolWidget):
                widget.set_state(default)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)):
                widget.setValue(default)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(default))
        else:
            if isinstance(widget, TriStateBoolWidget):
                widget.set_state(value)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox, ValidatedSpinBox, ValidatedDoubleSpinBox)):
                widget.setValue(value)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                idx = widget.findData(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        
        widget.blockSignals(False)
        self.preview.update_timer()
        self.preview.update()

    def update_single_checkbox(self, key, enabled):
        """Update checkbox state from undo/redo"""
        chk = self.param_checkboxes.get(key)
        widget = self.all_widgets.get(key)
        
        if chk:
            chk.blockSignals(True)
            chk.setChecked(enabled)
            chk.blockSignals(False)
        
        if widget:
            widget.setEnabled(enabled)

    def on_visual_drag_finished(self):
        """Handle visual drag completion with undo support"""
        if self.is_loading:
            return
        
        # Collect all changed keys
        changes = {}
        keys_to_check = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        
        for key in keys_to_check:
            widget = self.all_widgets.get(key)
            if not widget:
                continue
            
            new_val = self.npc_data.standard_params.get(key)
            
            # Get the old value from widget (it hasn't been updated yet)
            widget.blockSignals(True)
            old_val = widget.value()
            widget.blockSignals(False)
            
            if new_val != old_val:
                changes[key] = (old_val, new_val)
                
                # Enable checkbox if needed
                chk = self.param_checkboxes.get(key)
                if chk and not chk.isChecked():
                    chk.blockSignals(True)
                    chk.setChecked(True)
                    chk.blockSignals(False)
        
        if changes:
            cmd = ChangeMultipleParametersCommand(
                self.npc_data,
                changes,
                ui_callback=self.update_single_widget,
                description="Visual edit"
            )
            self.undo_stack.push(cmd)
        
        # Update widgets to show new values
        self.sync_ui_from_visual()

    def sync_ui_from_visual(self):
        """Real-time UI update during drag (No Undo commands here)"""
        p = self.npc_data.standard_params
        keys = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
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
        if self.npc_data.filepath and os.path.exists(self.npc_data.filepath):
            self.watched_files.append(self.npc_data.filepath)
        if self.preview.image_path and os.path.exists(self.preview.image_path):
            self.watched_files.append(self.preview.image_path)
        if self.watched_files: self.watcher.addPaths(self.watched_files)

    def on_external_file_change(self, path):
        if self.is_saving: return
        
        # Handle Atomic Saves (File deleted then recreated)
        if not os.path.exists(path):
            QTimer.singleShot(100, lambda: self._update_file_watcher())
            return
            
        if path == self.npc_data.filepath:
            print(f"External reload: {path}")
            self.is_loading = True
            if self.npc_data.load(path):
                self.update_ui_from_data()
            self.is_loading = False
            self.status_bar.showMessage("File reloaded (external change)", 3000)
        elif path == self.preview.image_path:
            self.preview.load_image()
            self.status_bar.showMessage("Image reloaded", 2000)
            
        # Re-add to watcher
        if path in self.watched_files:
            self.watcher.removePath(path)
            self.watcher.addPath(path)

    def on_custom_table_change(self):
        """Handle custom table edits (currently without undo - TODO)"""
        self.npc_data.custom_params = {}
        for r in range(self.custom_table.rowCount()):
            k_item = self.custom_table.item(r, 0)
            v_item = self.custom_table.item(r, 1)
            if k_item and v_item and k_item.text().strip():
                self.npc_data.set_custom(k_item.text().strip(), v_item.text().strip())
    
    def add_custom_row(self):
        """Add custom parameter with undo support"""
        if self.is_loading:
            return
        
        key = f"new_param_{self.custom_table.rowCount()}"
        value = "0"
        
        cmd = AddCustomParameterCommand(
            self.npc_data,
            key,
            value,
            ui_callback=self.refresh_custom_table
        )
        self.undo_stack.push(cmd)
    
    def remove_custom_row(self):
        """Remove custom parameter with undo support"""
        if self.is_loading:
            return
        
        cur = self.custom_table.currentRow()
        if cur >= 0:
            k_item = self.custom_table.item(cur, 0)
            v_item = self.custom_table.item(cur, 1)
            
            if k_item:
                key = k_item.text().strip()
                old_value = v_item.text().strip() if v_item else ""
                
                cmd = RemoveCustomParameterCommand(
                    self.npc_data,
                    key,
                    old_value,
                    ui_callback=self.refresh_custom_table
                )
                self.undo_stack.push(cmd)
    
    def refresh_custom_table(self):
        """Refresh custom table display"""
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
    
    def on_visual_drag_start(self):
        """Capture values before the user starts moving the mouse"""
        keys = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        self._drag_snapshot = {k: self.npc_data.standard_params.get(k) for k in keys}
    
    def on_visual_drag_complete(self):
        """Compare current values to snapshot and push one Undo command"""
        if self.is_loading: return
        
        keys = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        changes = {}
        
        for key in keys:
            old_val = self._drag_snapshot.get(key)
            new_val = self.npc_data.standard_params.get(key)
            
            if old_val != new_val:
                changes[key] = (old_val, new_val)
                
                # Ensure the checkbox for this parameter is enabled
                chk = self.param_checkboxes.get(key)
                if chk and not chk.isChecked():
                    chk.blockSignals(True)
                    chk.setChecked(True)
                    self.all_widgets[key].setEnabled(True)
                    chk.blockSignals(False)
        
        if changes:
            cmd = ChangeMultipleParametersCommand(
                self.npc_data,
                changes,
                ui_callback=self.update_single_widget,
                description="Visual Edit"
            )
            self.undo_stack.push(cmd)
        
        self._drag_snapshot = {}
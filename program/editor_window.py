import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, 
                             QRadioButton, QFileDialog, QFrame, QPushButton, 
                             QFormLayout, QSizePolicy, QToolButton, QScrollArea,
                             QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from .npc_data import NPCData
from .npc_definitions import NPC_DEFS
from .preview_widget import AnimationPreview

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
        if checked:
            self.btn_true.setChecked(False)
        else:
            if not self.btn_true.isChecked():
                self.stateChanged.emit()
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

# --- UPDATED CollapsibleBox ---
class CollapsibleBox(QWidget):
    # Signal emitted when the checkbox is toggled (True = Enabled/Added, False = Disabled/Deleted)
    toggled = pyqtSignal(bool)

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        # Header Layout (Frame for background styling)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(".QFrame { background-color: #444; border-radius: 3px; }")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(10)

        # 1. Expand/Collapse Arrow
        self.arrow_btn = QToolButton()
        self.arrow_btn.setArrowType(Qt.ArrowType.RightArrow)
        self.arrow_btn.setStyleSheet("QToolButton { border: none; background: transparent; color: white; }")
        self.arrow_btn.setCheckable(True)
        self.arrow_btn.setChecked(False)
        self.arrow_btn.clicked.connect(self.on_arrow_clicked)
        
        # 2. Category Checkbox (The "Add/Delete" feature)
        self.chk_enable = QCheckBox(title)
        self.chk_enable.setStyleSheet("QCheckBox { font-weight: bold; color: white; }")
        self.chk_enable.setChecked(False) # Default to disabled/unchecked
        self.chk_enable.toggled.connect(self.on_checkbox_toggled)

        header_layout.addWidget(self.arrow_btn)
        header_layout.addWidget(self.chk_enable)
        header_layout.addStretch()

        # Content Area
        self.content_area = QWidget()
        self.content_layout = QFormLayout()
        self.content_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_area.setLayout(self.content_layout)
        self.content_area.setVisible(False)
        
        # Main Layout
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.header_frame)
        lay.addWidget(self.content_area)
        
    def on_arrow_clicked(self):
        checked = self.arrow_btn.isChecked()
        self.arrow_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        self.content_area.setVisible(checked)

    def on_checkbox_toggled(self, checked):
        # Auto-expand if enabled
        if checked:
            self.arrow_btn.setChecked(True)
            self.on_arrow_clicked()
        
        # Enable/Disable all child widgets visually
        self.content_area.setEnabled(checked)
        self.toggled.emit(checked)

    def add_row(self, label, widget):
        self.content_layout.addRow(label, widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMBX NPC Editor")
        self.resize(1100, 800)
        
        self.npc_data = NPCData()
        self.ui_sections = {}
        self.all_widgets = {}
        
        # Track which keys belong to which category for bulk enable/disable
        self.category_keys = {} 

        # File Watcher
        self.is_saving = False
        self.watched_files = []
        self.watcher = None # Initialized after imports usually, sticking to simple logic here for context
        # (Assuming QFileSystemWatcher imported in previous step)
        from PyQt6.QtCore import QFileSystemWatcher
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_external_file_change)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- LEFT PANEL ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(420) # Slightly wider for checkboxes
        scroll_content = QWidget()
        self.form_layout = QVBoxLayout(scroll_content)
        
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("Load .txt")
        btn_load.clicked.connect(self.load_file)
        btn_save = QPushButton("Save .txt")
        btn_save.clicked.connect(self.save_file)
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_save)
        self.form_layout.addLayout(btn_layout)
        self.form_layout.addSpacing(10)

        self.generate_standard_ui()

        # Remove extra spacing before custom box for alignment
        # self.form_layout.addSpacing(10)
        self.custom_box = CollapsibleBox("Custom / Extra Properties")
        self.custom_box.chk_enable.setChecked(True)
        self.custom_box.chk_enable.setText("Custom Properties (Always Active)")
        self.custom_box.chk_enable.setEnabled(False)

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

        # Reduce stretch to avoid offset
        self.form_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # --- RIGHT PANEL ---
        right_panel = QWidget()
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
        r_layout.addWidget(self.preview)
        main_layout.addWidget(right_panel)

        self.btn_hitbox_mode = QPushButton("Hitbox Adjustment Mode", self.preview)
        self.btn_hitbox_mode.setCheckable(True)
        self.btn_hitbox_mode.move(10, 10)
        self.btn_hitbox_mode.resize(180, 30)
        self.btn_hitbox_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hitbox_mode.setStyleSheet("QPushButton { background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; } QPushButton:checked { background-color: #2e7d32; }")
        self.btn_hitbox_mode.toggled.connect(self.on_mode_toggle)

    def _register_widget(self, key, widget):
        """Helper to register widget to master dict and logic."""
        self.all_widgets[key] = widget
        # The category is derived from the widget's parent, 
        # but we need to track keys per category for the toggle logic.
        # We'll fill self.category_keys in generate_standard_ui

    def _add_param_widget(self, section, key, definition):
        dtype = definition.get('type')
        label_text = definition.get('label', key)
        tip = definition.get('tips', key)
        widget = None
        if dtype == bool:
            widget = TriStateBoolWidget()
            widget.stateChanged.connect(self.on_standard_change)
        elif dtype == int:
            widget = QSpinBox()
            widget.setRange(definition.get('min', -9999), definition.get('max', 9999))
            widget.valueChanged.connect(self.on_standard_change)
        elif dtype == float:
            widget = QDoubleSpinBox()
            widget.setRange(definition.get('min', -9999.0), definition.get('max', 9999.0))
            widget.setSingleStep(definition.get('step', 0.1))
            widget.valueChanged.connect(self.on_standard_change)
        elif dtype == str:
            widget = QLineEdit()
            widget.textChanged.connect(self.on_standard_change)
        elif dtype == "enum":
            widget = QComboBox()
            for k, v in definition.get('choices', {}).items():
                widget.addItem(v, k)
            widget.currentIndexChanged.connect(self.on_standard_change)
        if widget:
            widget.setToolTip(tip)
            section.add_row(label_text, widget)
            self._register_widget(key, widget)

    def _add_dual_int_widget(self, section, label_row, key1, def1, key2, def2, sublabel1, sublabel2):
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        if sublabel1: lay.addWidget(QLabel(sublabel1))
        w1 = QSpinBox()
        w1.setRange(def1.get('min', -9999), def1.get('max', 9999))
        w1.setToolTip(def1.get('tips', key1))
        w1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w1.valueChanged.connect(self.on_standard_change)
        lay.addWidget(w1)
        if sublabel2: lay.addWidget(QLabel(sublabel2))
        w2 = QSpinBox()
        w2.setRange(def2.get('min', -9999), def2.get('max', 9999))
        w2.setToolTip(def2.get('tips', key2))
        w2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w2.valueChanged.connect(self.on_standard_change)
        lay.addWidget(w2)
        section.add_row(label_row, container)
        self._register_widget(key1, w1)
        self._register_widget(key2, w2)

    def generate_standard_ui(self):
        categories = sorted(list(set(d['category'] for d in NPC_DEFS.values())))
        priority = ["Animation", "Collision", "Interaction", "Behaviour"]
        categories.sort(key=lambda x: priority.index(x) if x in priority else 99)
        
        pairs_config = [('gfxwidth', 'gfxheight', 'GFX Size', 'W:', 'H:'), ('width', 'height', 'Hitbox Size', 'W:', 'H:'), ('gfxoffsetx', 'gfxoffsety', 'GFX Offset', 'X:', 'Y:')]
        pair_map = {p[0]: ('primary', p) for p in pairs_config}
        pair_map.update({p[1]: ('secondary', p) for p in pairs_config})

        for cat in categories:
            section = CollapsibleBox(cat)
            
            # Connect the checkbox toggle signal
            # Use lambda to capture the category name
            section.toggled.connect(lambda checked, c=cat: self.on_category_toggled(c, checked))
            
            self.form_layout.addWidget(section)
            self.ui_sections[cat] = section
            self.category_keys[cat] = [] # Init list of keys
            
            # Auto-expand Animation
            if cat == "Animation":
                section.arrow_btn.setChecked(True)
                section.on_arrow_clicked()
        
        for key, definition in NPC_DEFS.items():
            cat = definition['category']
            section = self.ui_sections[cat]
            self.category_keys[cat].append(key) # Track key for this category

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
            if self.npc_data.load(fname):
                self.update_ui_from_data()
                self.preview.load_image()
                self.setWindowTitle(f"Editing: {os.path.basename(fname)}")
                self._update_file_watcher()

    def save_file(self):
        self.on_standard_change() # Commit current widget values
        self.on_custom_table_change()
        self.is_saving = True
        self.npc_data.save()
        self.is_saving = False

    def update_ui_from_data(self):
        """Updates all widgets and enables/disables categories based on loaded data."""
        
        # 1. Determine which categories are active
        active_categories = set()
        for cat, keys in self.category_keys.items():
            is_active = False
            for key in keys:
                if self.npc_data.standard_params.get(key) is not None:
                    is_active = True
                    break
            
            # Animation and Collision usually have defaults (32x32, frames=1), 
            # so they will almost always be active if the file loaded defaults.
            # But strictly speaking, if load() returns None for everything, they should be unchecked.
            # However, npc_data.load resets specific defaults.
            if is_active:
                active_categories.add(cat)

        # 2. Update Sections (Checkboxes)
        for cat, section in self.ui_sections.items():
            should_check = (cat in active_categories)
            section.blockSignals(True) # Prevent triggering on_category_toggled loop
            section.chk_enable.setChecked(should_check)
            section.content_area.setEnabled(should_check) # Visually enable/disable
            section.blockSignals(False)

        # 3. Update Widgets
        for key, widget in self.all_widgets.items():
            val = self.npc_data.standard_params.get(key)
            default = NPC_DEFS[key]['default']
            widget.blockSignals(True)
            if isinstance(widget, TriStateBoolWidget):
                widget.set_state(val)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(val if val is not None else default)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(val) if val is not None else str(default))
            elif isinstance(widget, QComboBox):
                idx = widget.findData(val if val is not None else default)
                if idx >= 0: widget.setCurrentIndex(idx)
            widget.blockSignals(False)

        # 4. Custom Table
        self.custom_table.blockSignals(True)
        self.custom_table.setRowCount(0)
        for k, v in self.npc_data.custom_params.items():
            row = self.custom_table.rowCount()
            self.custom_table.insertRow(row)
            self.custom_table.setItem(row, 0, QTableWidgetItem(k))
            self.custom_table.setItem(row, 1, QTableWidgetItem(str(v)))
        self.custom_table.blockSignals(False)
        
        self.preview.update_timer()
        self.preview.update()

    def on_category_toggled(self, category, checked):
        """Called when a category checkbox is clicked."""
        keys = self.category_keys.get(category, [])
        
        if not checked:
            # DISABLE: Set all params in this category to None
            for key in keys:
                self.npc_data.set_standard(key, None)
        else:
            # ENABLE: Read values from widgets and put back into data
            # (Widgets retain values even when disabled, so we just read them)
            for key in keys:
                widget = self.all_widgets.get(key)
                if widget:
                    # Helper logic to pull value
                    val = None
                    if isinstance(widget, TriStateBoolWidget): val = widget.get_state()
                    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)): val = widget.value()
                    elif isinstance(widget, QLineEdit): val = widget.text() if widget.text() else None
                    elif isinstance(widget, QComboBox): val = widget.currentData()
                    
                    # If it matches default, and it's a bool, maybe keep it None? 
                    # User explicitly enabled the category, so let's write the values even if default?
                    # No, strict SMBX optimization: if default, usually omit.
                    # But for "Line Guide", usually you want 'lineguided=true'.
                    
                    # Special logic: If widget is TriState and None, force it to Default?
                    # Actually, if we just unchecked it, it was None. Now we check it.
                    # We should probably force write values.
                    
                    self.npc_data.set_standard(key, val)

    def on_standard_change(self):
        """Called when any individual widget changes."""
        for cat, section in self.ui_sections.items():
            # If a category is disabled, ignore changes (shouldn't happen if widgets disabled, but safety)
            if not section.chk_enable.isChecked():
                continue
                
            # Loop keys in this category
            keys = self.category_keys.get(cat, [])
            for key in keys:
                widget = self.all_widgets.get(key)
                if not widget: continue
                
                val = None
                if isinstance(widget, TriStateBoolWidget): val = widget.get_state()
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)): val = widget.value()
                elif isinstance(widget, QLineEdit): val = widget.text() if widget.text() else None
                elif isinstance(widget, QComboBox): val = widget.currentData()
                
                # Update Data
                # Note: We don't check for defaults here strictly, because if the category is ENABLED,
                # we generally want the data to be present in the model, even if default, 
                # so the Preview Widget works correctly (it relies on standard_params).
                # The Save logic in npc_data.py can handle stripping defaults if we want, 
                # OR we strip them here.
                # Current npc_data.save logic: If val is None, skip. If val matches keys, write.
                
                # Logic: If val == Default, do we write?
                # For integers: Yes, usually.
                # For bools: TriState widget returns None if neither selected.
                
                if isinstance(widget, TriStateBoolWidget) and val is None:
                    self.npc_data.set_standard(key, None)
                else:
                    self.npc_data.set_standard(key, val)

        self.preview.update_timer()
        self.preview.update()

    def sync_ui_from_visual(self):
        p = self.npc_data.standard_params
        keys_to_update = ['gfxwidth', 'gfxheight', 'gfxoffsetx', 'gfxoffsety', 'width', 'height']
        for key in keys_to_update:
            widget = self.all_widgets.get(key)
            if widget:
                widget.blockSignals(True)
                widget.setValue(p.get(key, 0))
                widget.blockSignals(False)

    # ... Rest of methods (file watcher, custom table, etc.) unchanged ...
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
        if path == self.npc_data.filepath:
            self.npc_data.load(path)
            self.update_ui_from_data()
        elif path == self.preview.image_path:
            self.preview.load_image()
        self.watcher.addPath(path)

    def on_custom_table_change(self):
        self.npc_data.custom_params = {}
        for r in range(self.custom_table.rowCount()):
            k_item = self.custom_table.item(r, 0)
            v_item = self.custom_table.item(r, 1)
            if k_item and v_item and k_item.text().strip():
                self.npc_data.set_custom(k_item.text().strip(), v_item.text().strip())
    def add_custom_row(self):
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)
        self.custom_table.setItem(row, 0, QTableWidgetItem("new_param"))
        self.custom_table.setItem(row, 1, QTableWidgetItem("0"))
    def remove_custom_row(self):
        cur = self.custom_table.currentRow()
        if cur >= 0:
            self.custom_table.removeRow(cur)
            self.on_custom_table_change()
    def on_mode_toggle(self, checked):
        self.preview.set_hitbox_mode(checked)
        self.btn_hitbox_mode.setText("Hitbox Mode (ACTIVE)" if checked else "Hitbox Adjustment Mode")
    def on_direction_change(self):
        self.preview.show_direction = 1 if self.rb_right.isChecked() else 0
        self.preview.update()
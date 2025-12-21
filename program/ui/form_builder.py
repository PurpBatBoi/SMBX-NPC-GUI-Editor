from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, 
                             QComboBox, QSizePolicy)
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional, List
from .widgets import (TriStateBoolWidget, ValidatedSpinBox, 
                              ValidatedDoubleSpinBox, CollapsibleBox, ClickableLabel)

class FormBuilder:
    """
    Constructs the property editor UI based on NPC_DEFS schema.
    Returns:
        tuple: (layout_widget, ui_sections_dict, category_keys_dict, all_widgets_dict, checkbox_map)
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.all_widgets = {}
        self.param_checkboxes = {}

    def build_standard_ui(self, npc_defs: Dict[str, Any], layout: QVBoxLayout):
        ui_sections = {}
        category_keys = {}
        
        # 1. Sort Categories
        categories = sorted(list(set(d['category'] for d in npc_defs.values())))
        priority = ["Animation", "Collision", "Interaction", "Behaviour"]
        categories.sort(key=lambda x: priority.index(x) if x in priority else 99)
        
        # 2. Create Sections
        for cat in categories:
            section = CollapsibleBox(cat)
            layout.addWidget(section)
            ui_sections[cat] = section
            category_keys[cat] = []
            if cat == "Animation": section.expand()
            
        # 3. Populate Sections - all parameters are added individually now
        for key, definition in npc_defs.items():
            cat = definition['category']
            section = ui_sections[cat]
            category_keys[cat].append(key)
            self._add_param_widget(section, key, definition)
                
        return ui_sections, category_keys, self.all_widgets, self.param_checkboxes

    def _add_param_widget(self, section, key, definition):
        dtype = definition.get('type')
        widget = None
        
        if dtype == bool:
            widget = TriStateBoolWidget()
        elif dtype == int:
            widget = ValidatedSpinBox()
            widget.setRange(definition.get('min', -9999), definition.get('max', 9999))
        elif dtype == float:
            widget = ValidatedDoubleSpinBox()
            widget.setRange(definition.get('min', -9999.0), definition.get('max', 9999.0))
            widget.setSingleStep(definition.get('step', 0.1))
        elif dtype == str:
            widget = QLineEdit()
        elif dtype == "enum":
            widget = QComboBox()
            for k, v in definition.get('choices', {}).items(): widget.addItem(v, k)
        
        if widget:
            widget.setProperty("param_key", key)
            widget.setToolTip(definition.get('tips', key))
            
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)
            
            chk = QCheckBox()
            chk.setChecked(False)
            chk.setProperty("param_key", key) # Tag for easy identification
            
            container_layout.addWidget(chk)
            container_layout.addWidget(widget, 1)
            
            # Create clickable label
            label_text = definition.get('label', key)
            label = ClickableLabel(label_text, key)
            if self.parent:
                label.clicked.connect(lambda k=key: self.parent.update_description(k))
            
            section.add_row(label, container)
            
            self.all_widgets[key] = widget
            self.param_checkboxes[key] = chk
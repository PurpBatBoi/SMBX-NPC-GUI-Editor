from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, 
                             QComboBox, QSizePolicy)
from typing import Dict, Any, Optional, List
from .widgets import (TriStateBoolWidget, ValidatedSpinBox, 
                              ValidatedDoubleSpinBox, CollapsibleBox)

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
        
        # 2. Define Pair Mappings (e.g. Width/Height)
        pairs_config = [
            ('gfxwidth', 'gfxheight', 'GFX Size', 'W:', 'H:'), 
            ('width', 'height', 'Hitbox Size', 'W:', 'H:'), 
            ('gfxoffsetx', 'gfxoffsety', 'GFX Offset', 'X:', 'Y:')
        ]
        pair_map = {p[0]: ('primary', p) for p in pairs_config}
        pair_map.update({p[1]: ('secondary', p) for p in pairs_config})
        
        # 3. Create Sections
        for cat in categories:
            section = CollapsibleBox(cat)
            layout.addWidget(section)
            ui_sections[cat] = section
            category_keys[cat] = []
            if cat == "Animation": section.expand()
            
        # 4. Populate Sections
        for key, definition in npc_defs.items():
            cat = definition['category']
            section = ui_sections[cat]
            category_keys[cat].append(key)
            
            if key in pair_map:
                role, data = pair_map[key]
                if role == 'primary':
                    k1, k2, main_label, sub1, sub2 = data
                    self._add_dual_int_widget(section, main_label, 
                                            k1, npc_defs.get(k1), 
                                            k2, npc_defs.get(k2), 
                                            sub1, sub2)
            else:
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
            
            section.add_row(definition.get('label', key), container)
            
            self.all_widgets[key] = widget
            self.param_checkboxes[key] = chk

    def _add_dual_int_widget(self, section, label_row, key1, def1, key2, def2, sublabel1, sublabel2):
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        
        chk = QCheckBox()
        chk.setChecked(False)
        lay.addWidget(chk)
        
        if sublabel1: lay.addWidget(QLabel(sublabel1))
        w1 = ValidatedSpinBox()
        w1.setRange(def1.get('min', -9999), def1.get('max', 9999))
        w1.setToolTip(def1.get('tips', key1))
        w1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w1.setProperty("param_key", key1)
        lay.addWidget(w1)
        
        if sublabel2: lay.addWidget(QLabel(sublabel2))
        w2 = ValidatedSpinBox()
        w2.setRange(def2.get('min', -9999), def2.get('max', 9999))
        w2.setToolTip(def2.get('tips', key2))
        w2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        w2.setProperty("param_key", key2)
        lay.addWidget(w2)
        
        section.add_row(label_row, container)
        
        self.all_widgets[key1] = w1
        self.all_widgets[key2] = w2
        self.param_checkboxes[key1] = chk
        self.param_checkboxes[key2] = chk

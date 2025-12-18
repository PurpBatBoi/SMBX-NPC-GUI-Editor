import os
import re
from .npc_definitions import NPC_DEFS

class NPCData:
    def __init__(self):
        self.standard_params = {k: None for k in NPC_DEFS}
        self.custom_params = {}
        # Mapping lowercase -> canonical key
        self.key_map = {k.lower(): k for k in NPC_DEFS}
        self.comments = {} # Store inline comments: key -> comment_str
        self.header_comments = [] # Store top-of-file comments
        
        self._apply_defaults()
        self.filepath = ""

    def _apply_defaults(self):
        self.standard_params['gfxwidth'] = 32
        self.standard_params['gfxheight'] = 32
        self.standard_params['width'] = 32
        self.standard_params['height'] = 32
        self.standard_params['frames'] = 1
        self.standard_params['framespeed'] = 8
        self.standard_params['framestyle'] = 0

    def set_standard(self, key, value):
        self.standard_params[key] = value

    def set_custom(self, key, value_str):
        self.custom_params[key] = str(value_str)

    def load(self, filepath):
        self.filepath = filepath
        self.standard_params = {k: None for k in NPC_DEFS}
        self.custom_params = {}
        self.comments = {}
        self.header_comments = []
        
        # Defaults for Preview
        self._apply_defaults()

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            header_done = False
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                
                # Check for comment
                comment_part = ""
                content = line
                if '#' in line:
                    parts = line.split('#', 1)
                    content = parts[0]
                    comment_part = '#' + parts[1].rstrip('\n')
                
                clean = content.strip()
                
                # Parse Key=Value
                if '=' in clean:
                    header_done = True
                    parts = clean.split('=', 1)
                    raw_key = parts[0].strip()
                    key_lower = raw_key.lower()
                    val_str = parts[1].strip()

                    # Store comment
                    if comment_part:
                        # If known key, map to canonical, else raw
                        k = self.key_map.get(key_lower, raw_key)
                        self.comments[k] = comment_part

                    if key_lower in self.key_map:
                        real_key = self.key_map[key_lower]
                        self._parse_value(real_key, val_str)
                    else:
                        self.custom_params[raw_key] = val_str
                
                # Header comments (before any keys)
                elif not header_done and stripped.startswith('#'):
                    self.header_comments.append(line)

            return True
        except Exception as e:
            print(f"Load Error: {e}")
            return False

    def _parse_value(self, key, val_str):
        def_type = NPC_DEFS[key]['type']
        try:
            if def_type == bool:
                self.standard_params[key] = (val_str.lower() == 'true')
            elif def_type == int:
                self.standard_params[key] = int(float(val_str))
            elif def_type == float:
                self.standard_params[key] = float(val_str)
            elif def_type == "enum":
                self.standard_params[key] = int(float(val_str))
            else:
                self.standard_params[key] = val_str
        except ValueError:
            self.standard_params[key] = NPC_DEFS[key]['default']

    def save(self):
        if not self.filepath: return

        active_standard = {k: v for k, v in self.standard_params.items() if v is not None}
        active_custom = self.custom_params.copy()
        
        lines = []
        
        # 1. Header Comments
        lines.extend(self.header_comments)
        if self.header_comments and not lines[-1].endswith('\n'):
            lines.append('\n')

        # 2. Group by Category
        # Define priority order for categories
        priority = ["Animation", "Collision", "Interaction", "Behaviour", "AI / Identity", "Line Guide", "Lighting", "Editor"]
        all_categories = sorted(list(set(d['category'] for d in NPC_DEFS.values())))
        all_categories.sort(key=lambda x: priority.index(x) if x in priority else 99)

        written_keys = set()

        for cat in all_categories:
            # Get all keys for this category from Schema
            cat_keys = [k for k, d in NPC_DEFS.items() if d['category'] == cat]
            
            # Filter for active keys
            keys_to_write = [k for k in cat_keys if k in active_standard]
            
            if keys_to_write:
                for k in keys_to_write:
                    val = active_standard[k]
                    # Format value
                    if val is True: s_val = "true"
                    elif val is False: s_val = "false"
                    else: s_val = str(val)
                    
                    # Attach comment if exists
                    comment = " " + self.comments[k] if k in self.comments else ""
                    lines.append(f"{k} = {s_val}{comment}\n")
                    written_keys.add(k)
                
                # Append newline after category block
                lines.append("\n")

        # 3. Write Custom/Extra Params
        if active_custom:
            for k, v in active_custom.items():
                # Sanitize value to prevent file corruption
                clean_v = str(v).replace('\n', '')
                comment = " " + self.comments[k] if k in self.comments else ""
                lines.append(f"{k} = {clean_v}{comment}\n")
            lines.append("\n")

        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Saved {self.filepath}")
        except Exception as e:
            print(f"Save Error: {e}")
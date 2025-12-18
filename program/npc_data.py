import os
from .npc_definitions import NPC_DEFS

class NPCData:
    def __init__(self):
        self.standard_params = {}
        # Create a mapping of lowercase keys to the actual keys in NPC_DEFS
        # This handles cases like "lineSpeed" vs "linespeed"
        self.key_map = {}
        
        for key in NPC_DEFS:
            self.standard_params[key] = None
            self.key_map[key.lower()] = key
            
        # Defaults for a brand new instance (before loading file)
        self.standard_params['gfxwidth'] = 32
        self.standard_params['gfxheight'] = 32
        self.standard_params['width'] = 32
        self.standard_params['height'] = 32
        self.standard_params['frames'] = 1
        self.standard_params['framespeed'] = 8
        self.standard_params['framestyle'] = 0
        self.standard_params['gfxoffsetx'] = 0
        self.standard_params['gfxoffsety'] = 0

        self.custom_params = {}
        self.filepath = ""

    # Compatibility shim for preview_widget
    @property
    def params(self):
        return self.standard_params

    def set_standard(self, key, value):
        self.standard_params[key] = value

    def set_custom(self, key, value_str):
        self.custom_params[key] = str(value_str)

    def load(self, filepath):
        self.filepath = filepath
        
        # Reset all to None.
        for key in NPC_DEFS: self.standard_params[key] = None
        self.custom_params = {}
        
        # Do NOT force defaults here. Let the file dictate what is enabled.
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if '=' in line:
                        parts = line.split('=', 1)
                        raw_key = parts[0].strip()
                        key_lower = raw_key.lower()
                        val_str = parts[1].strip()
                        
                        # Use the map to find the canonical key in NPC_DEFS
                        if key_lower in self.key_map:
                            real_key = self.key_map[key_lower]
                            def_type = NPC_DEFS[real_key]['type']
                            try:
                                if def_type == bool:
                                    self.standard_params[real_key] = (val_str.lower() == 'true')
                                elif def_type == int:
                                    self.standard_params[real_key] = int(float(val_str))
                                elif def_type == float:
                                    self.standard_params[real_key] = float(val_str)
                                elif def_type == "enum":
                                    self.standard_params[real_key] = int(val_str)
                                else:
                                    self.standard_params[real_key] = val_str
                            except ValueError:
                                # Fallback if conversion fails
                                if def_type == int or def_type == "enum":
                                    self.standard_params[real_key] = 0
                                else:
                                    self.standard_params[real_key] = val_str
                        else:
                            # Not in definitions, treat as custom
                            self.custom_params[raw_key] = val_str
            return True
        except Exception as e:
            print(f"Load Error: {e}")
            return False

    def save(self):
        if not self.filepath: return
        try:
            lines = []
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    lines = f.readlines()
            
            # Prepare dictionary of values to write (Standard + Custom)
            # Only include Standard params that are NOT None (Enabled)
            to_write = self.custom_params.copy()
            for k, v in self.standard_params.items():
                if v is not None:
                    to_write[k] = v

            new_lines = []
            written_keys = set()
            
            for line in lines:
                clean = line.strip()
                if '=' in line and clean and clean[0].isalpha():
                    raw_key = line.split('=', 1)[0].strip()
                    key_lower = raw_key.lower()
                    
                    # 1. Check if this line corresponds to a Standard Param (via Map)
                    canonical_key = self.key_map.get(key_lower)
                    
                    if canonical_key:
                        # It is a recognized standard parameter
                        if canonical_key in to_write:
                            # It is Enabled -> Update the line
                            val = to_write[canonical_key]
                            val_str = "true" if isinstance(val, bool) and val else "false" if isinstance(val, bool) else str(val)
                            new_lines.append(f"{canonical_key} = {val_str}\n")
                            written_keys.add(canonical_key)
                        else:
                            # It is Disabled (None) -> SKIP the line (Delete it)
                            pass
                    
                    # 2. Check if it corresponds to a Custom Param (exact match usually)
                    elif raw_key in to_write:
                         val = to_write[raw_key]
                         val_str = "true" if isinstance(val, bool) and val else "false" if isinstance(val, bool) else str(val)
                         new_lines.append(f"{raw_key} = {val_str}\n")
                         written_keys.add(raw_key)
                    
                    # 3. Unknown key -> Keep it as is
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # Ensure file ends with newline
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')

            # Append new parameters that weren't in the original file
            for k, v in to_write.items():
                if k not in written_keys:
                    # Check if we already handled this via case-insensitive matching logic
                    # If 'k' is a standard param, we might have skipped it if the file didn't have it.
                    # But if we just added it in UI, it needs to be appended.
                    
                    # Note: written_keys contains the keys we successfully updated in the file.
                    # If we simply enabled a new checkbox that wasn't in the file, it won't be in written_keys.
                    val_str = "true" if isinstance(v, bool) and v else "false" if isinstance(v, bool) else str(v)
                    new_lines.append(f"{k} = {val_str}\n")
            
            with open(self.filepath, 'w') as f:
                f.writelines(new_lines)
            print(f"Saved {self.filepath}")
            
        except Exception as e:
            print(f"Save Error: {e}")
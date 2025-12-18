import os
from .npc_definitions import NPC_DEFS

class NPCData:
    def __init__(self):
        self.standard_params = {}
        for key in NPC_DEFS:
            self.standard_params[key] = None
            
        # Defaults
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
        for key in NPC_DEFS: self.standard_params[key] = None
        self.custom_params = {}
        
        # Reset specific defaults to avoid math errors if file is empty
        self.standard_params['gfxwidth'] = 32
        self.standard_params['gfxheight'] = 32
        self.standard_params['frames'] = 1
        self.standard_params['framestyle'] = 0
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if '=' in line:
                        parts = line.split('=', 1)
                        key = parts[0].strip().lower()
                        val_str = parts[1].strip()
                        
                        if key in NPC_DEFS:
                            def_type = NPC_DEFS[key]['type']
                            try:
                                if def_type == bool:
                                    self.standard_params[key] = (val_str.lower() == 'true')
                                elif def_type == int:
                                    self.standard_params[key] = int(float(val_str))
                                elif def_type == float:
                                    self.standard_params[key] = float(val_str)
                                elif def_type == "enum":
                                    # FIX: Convert enum values (like framestyle) to int
                                    self.standard_params[key] = int(val_str)
                                else:
                                    self.standard_params[key] = val_str
                            except ValueError:
                                # Fallback if conversion fails (e.g. bad number)
                                if def_type == int or def_type == "enum":
                                    self.standard_params[key] = 0
                                else:
                                    self.standard_params[key] = val_str
                        else:
                            self.custom_params[key] = val_str
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
            
            to_write = self.custom_params.copy()
            for k, v in self.standard_params.items():
                if v is not None:
                    to_write[k] = v

            new_lines = []
            written_keys = set()
            
            for line in lines:
                clean = line.strip()
                if '=' in line and clean and clean[0].isalpha():
                    key = line.split('=', 1)[0].strip().lower()
                    
                    if key in to_write:
                        written_keys.add(key)
                        val = to_write[key]
                        if isinstance(val, bool):
                            val_str = "true" if val else "false"
                        else:
                            val_str = str(val)
                        new_lines.append(f"{key} = {val_str}\n")
                    elif key in self.standard_params and self.standard_params[key] is None:
                        # Key exists in standard params but is None (Default) -> Remove it from file
                        pass 
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')

            for k, v in to_write.items():
                if k not in written_keys:
                    if isinstance(v, bool):
                        val_str = "true" if v else "false"
                    else:
                        val_str = str(v)
                    new_lines.append(f"{k} = {val_str}\n")
            
            with open(self.filepath, 'w') as f:
                f.writelines(new_lines)
            print(f"Saved {self.filepath}")
            
        except Exception as e:
            print(f"Save Error: {e}")
import os
import configparser

class NPCData:
    """Manages specific animation data.
    
    Boolean parameters can have three states:
    - None: Not written to file (uses game's default)
    - True: Written as 'true' (TXT) or '1' (INI)
    - False: Written as 'false' (TXT) or '0' (INI) - forced override
    """
    def __init__(self):
        # Define boolean keys first so they are available for reset
        self.boolean_keys = {
            'foreground',
            'noblockcollision',
            'npcblock',
            'npcblocktop',
            'playerblock',
            'playerblocktop'
        }
        
        # Initialize params with defaults
        self.params = {}
        self.reset_defaults()
        
        self.filepath = ""
        self.file_mode = "txt"  # "txt" or "ini"
        
        # Mapping between internal keys and INI keys
        self.ini_mapping = {
            'frames': 'frames',
            'framespeed': 'frame-delay',
            'framestyle': 'frame-style',
            'gfxwidth': 'gfx-width',
            'gfxheight': 'gfx-height',
            'gfxoffsetx': 'gfx-offset-x',
            'gfxoffsety': 'gfx-offset-y',
            'width': 'physical-width',
            'height': 'physical-height',
            'foreground': 'foreground',
            'noblockcollision': 'noblockcollision',
            'npcblock': 'npcblock',
            'npcblocktop': 'npcblocktop',
            'playerblock': 'playerblock',
            'playerblocktop': 'playerblocktop'
        }
        
        self.ini_reverse_mapping = {v: k for k, v in self.ini_mapping.items()}

    def reset_defaults(self):
        """Resets all parameters to their base default values."""
        self.params = {
            'frames': 1,
            'framespeed': 8,
            'framestyle': 0,
            'gfxwidth': 32,
            'gfxheight': 32,
            'gfxoffsetx': 0,
            'gfxoffsety': 0,
            'width': 32,
            'height': 32,
        }
        
        # Reset booleans to None
        for key in self.boolean_keys:
            self.params[key] = None

    def framespeed_to_frame_delay(self, framespeed):
        return int((framespeed / 64.0) * 1000)
    
    def frame_delay_to_framespeed(self, frame_delay):
        return int((frame_delay / 1000.0) * 64)

    def load(self, filepath):
        """Load from either TXT or INI file based on extension"""
        # CRITICAL FIX: Reset data before loading new file to prevent pollution
        self.reset_defaults()
        
        self.filepath = filepath
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.ini':
            self.file_mode = "ini"
            return self.load_ini(filepath)
        else:
            self.file_mode = "txt"
            return self.load_txt(filepath)
    
    def load_txt(self, filepath):
        """Load from TXT format"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if '=' in line:
                        parts = line.split('=', 1)
                        key = parts[0].strip().lower()
                        val = parts[1].strip()
                        
                        if key in self.params:
                            if key in self.boolean_keys:
                                if val.lower() == 'true':
                                    self.params[key] = True
                                elif val.lower() == 'false':
                                    self.params[key] = False
                            else:
                                try:
                                    self.params[key] = int(val)
                                except ValueError:
                                    pass 
            return True
        except Exception as e:
            print(f"Load TXT Error: {e}")
            return False
    
    def load_ini(self, filepath):
        """Load from INI format"""
        try:
            config = configparser.ConfigParser()
            config.read(filepath)
            
            if 'npc' not in config:
                print("Warning: No [npc] section found in INI file")
                return False
            
            npc_section = config['npc']
            
            for ini_key, internal_key in self.ini_reverse_mapping.items():
                if ini_key in npc_section:
                    val = npc_section[ini_key].strip()
                    
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    
                    if internal_key in self.boolean_keys:
                        if val == '1':
                            self.params[internal_key] = True
                        elif val == '0':
                            self.params[internal_key] = False
                    elif internal_key == 'framespeed':
                        try:
                            frame_delay = int(val)
                            self.params['framespeed'] = self.frame_delay_to_framespeed(frame_delay)
                        except ValueError:
                            pass
                    else:
                        try:
                            self.params[internal_key] = int(val)
                        except ValueError:
                            pass
            
            return True
        except Exception as e:
            print(f"Load INI Error: {e}")
            return False

    def save(self):
        if not self.filepath: 
            return
        
        if self.file_mode == "ini":
            self.save_ini()
        else:
            self.save_txt()
    
    def save_txt(self):
        try:
            lines = []
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    lines = f.readlines()
            
            keys_to_write = {}
            for key, val in self.params.items():
                if key in self.boolean_keys:
                    if val is not None:
                        keys_to_write[key] = val
                else:
                    keys_to_write[key] = val
            
            new_lines = []
            keys_found_in_file = set()
            
            for line in lines:
                clean_line = line.strip()
                if '=' in line and clean_line and clean_line[0].isalpha():
                    key_part = line.split('=', 1)[0]
                    key = key_part.strip().lower()
                    
                    if key in self.params:
                        keys_found_in_file.add(key)
                        if key in keys_to_write:
                            val = keys_to_write[key]
                            val_str = str(val).lower() if isinstance(val, bool) else str(val)
                            new_lines.append(f"{key} = {val_str}\n")
                        else:
                            pass
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            keys_to_append = {k: v for k, v in keys_to_write.items() 
                            if k not in keys_found_in_file and v is not None}
            
            if keys_to_append:
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines.append('\n')

                for key, val in keys_to_append.items():
                    val_str = str(val).lower() if isinstance(val, bool) else str(val)
                    new_lines.append(f"{key} = {val_str}\n")
                
            with open(self.filepath, 'w') as f:
                f.writelines(new_lines)
            print(f"TXT file saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save TXT Error: {e}")
    
    def save_ini(self):
        try:
            config = configparser.ConfigParser()
            
            if os.path.exists(self.filepath):
                config.read(self.filepath)
            
            if 'npc' not in config:
                config['npc'] = {}
            
            existing_keys = list(config['npc'].keys()) if 'npc' in config else []
            new_npc_section = {}
            
            if 'npc' in config:
                for key in existing_keys:
                    new_npc_section[key] = config['npc'][key]
            
            for internal_key, val in self.params.items():
                ini_key = self.ini_mapping.get(internal_key)
                if not ini_key:
                    continue
                
                if internal_key in self.boolean_keys:
                    if val is not None:
                        new_npc_section[ini_key] = '1' if val else '0'
                    elif ini_key in new_npc_section:
                        del new_npc_section[ini_key]
                elif internal_key == 'framespeed':
                    frame_delay = self.framespeed_to_frame_delay(val)
                    new_npc_section[ini_key] = str(frame_delay)
                else:
                    new_npc_section[ini_key] = str(val)
            
            config['npc'] = new_npc_section
            
            with open(self.filepath, 'w') as f:
                config.write(f)
            print(f"INI file saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save INI Error: {e}")
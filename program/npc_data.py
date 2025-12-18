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
        # Integer/numeric parameters (always written to file)
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
        
        # Boolean parameters (None means not written to file)
        # These will be merged into params dict but handled specially during save
        self.boolean_keys = {
            'foreground',
            'noblockcollision',
            'npcblock',
            'npcblocktop',
            'playerblock',
            'playerblocktop'
        }
        
        # Initialize boolean params as None (not set)
        for key in self.boolean_keys:
            self.params[key] = None
        
        self.filepath = ""
        self.file_mode = "txt"  # "txt" or "ini"
        
        # Mapping between internal keys and INI keys
        # internal_key: ini_key
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
        
        # Reverse mapping for loading
        self.ini_reverse_mapping = {v: k for k, v in self.ini_mapping.items()}

    def load(self, filepath):
        """Load from either TXT or INI file based on extension"""
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
                                # Parse boolean
                                if val.lower() == 'true':
                                    self.params[key] = True
                                elif val.lower() == 'false':
                                    self.params[key] = False
                                # If neither, leave as None (shouldn't happen in valid files)
                            else:
                                # Parse integer
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
                    
                    # Remove quotes if present
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    
                    if internal_key in self.boolean_keys:
                        # Parse boolean (INI uses 0/1)
                        if val == '1':
                            self.params[internal_key] = True
                        elif val == '0':
                            self.params[internal_key] = False
                    else:
                        # Parse integer
                        try:
                            self.params[internal_key] = int(val)
                        except ValueError:
                            pass
            
            return True
        except Exception as e:
            print(f"Load INI Error: {e}")
            return False

    def save(self):
        """Save to either TXT or INI file based on current mode"""
        if not self.filepath: 
            return
        
        if self.file_mode == "ini":
            self.save_ini()
        else:
            self.save_txt()
    
    def save_txt(self):
        """Save to TXT format"""
        try:
            # 1. Read the original file
            lines = []
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    lines = f.readlines()
            
            # Separate params into those that should be written vs those that should be omitted
            keys_to_write = {}
            for key, val in self.params.items():
                if key in self.boolean_keys:
                    # Only write boolean if explicitly set (not None)
                    if val is not None:
                        keys_to_write[key] = val
                else:
                    # Always write numeric params
                    keys_to_write[key] = val
            
            new_lines = []
            keys_found_in_file = set()
            
            # 2. Iterate through original lines
            for line in lines:
                clean_line = line.strip()
                
                # Check if this line is a property assignment we recognize
                # We also check if it starts with a letter to avoid messing up comments
                if '=' in line and clean_line and clean_line[0].isalpha():
                    key_part = line.split('=', 1)[0]
                    key = key_part.strip().lower()
                    
                    if key in self.params:
                        keys_found_in_file.add(key)
                        
                        if key in keys_to_write:
                            # Replace line with new value
                            val = keys_to_write[key]
                            val_str = str(val).lower() if isinstance(val, bool) else str(val)
                            new_lines.append(f"{key} = {val_str}\n")
                        else:
                            # This is a boolean that is now None - REMOVE the line
                            # (don't append it to new_lines)
                            pass
                    else:
                        # Keep custom property exactly as is
                        new_lines.append(line)
                else:
                    # Keep comments/newlines exactly as is
                    new_lines.append(line)
            
            # 3. Append any NEW keys that weren't in the original file
            # Only append keys that should be written (not None booleans)
            keys_to_append = {k: v for k, v in keys_to_write.items() 
                            if k not in keys_found_in_file and v is not None}
            
            if keys_to_append:
                # FIX: Ensure the file ends with a newline before appending
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines.append('\n')

                for key, val in keys_to_append.items():
                    val_str = str(val).lower() if isinstance(val, bool) else str(val)
                    new_lines.append(f"{key} = {val_str}\n")
                
            # 4. Write back
            with open(self.filepath, 'w') as f:
                f.writelines(new_lines)
            print(f"TXT file saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save TXT Error: {e}")
    
    def save_ini(self):
        """Save to INI format"""
        try:
            config = configparser.ConfigParser()
            
            # Read existing file if it exists
            if os.path.exists(self.filepath):
                config.read(self.filepath)
            
            # Ensure [npc] section exists
            if 'npc' not in config:
                config['npc'] = {}
            
            # Update only our managed parameters
            for internal_key, val in self.params.items():
                ini_key = self.ini_mapping.get(internal_key)
                if not ini_key:
                    continue
                
                if internal_key in self.boolean_keys:
                    # Only write boolean if explicitly set (not None)
                    if val is not None:
                        config['npc'][ini_key] = '1' if val else '0'
                    elif ini_key in config['npc']:
                        # Remove the key if it was set to None
                        del config['npc'][ini_key]
                else:
                    # Always write numeric params
                    config['npc'][ini_key] = str(val)
            
            # Write back
            with open(self.filepath, 'w') as f:
                config.write(f)
            print(f"INI file saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save INI Error: {e}")
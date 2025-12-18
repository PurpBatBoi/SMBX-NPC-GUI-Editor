import os

class NPCData:
    """Manages specific animation data.
    
    Boolean parameters can have three states:
    - None: Not written to file (uses game's default)
    - True: Written as 'true' 
    - False: Written as 'false' (forced override)
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

    def load(self, filepath):
        self.filepath = filepath
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
            print(f"Load Error: {e}")
            return False

    def save(self):
        if not self.filepath: return
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
            print(f"File saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save Error: {e}")
import os

class NPCData:
    """Manages specific animation data."""
    def __init__(self):
        # These are the ONLY keys the editor is allowed to touch.
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
            'foreground': False
        }
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
            
            keys_to_write = self.params.copy()
            new_lines = []
            
            # 2. Iterate through original lines
            for line in lines:
                clean_line = line.strip()
                
                # Check if this line is a property assignment we recognize
                # We also check if it starts with a letter to avoid messing up comments
                if '=' in line and clean_line and clean_line[0].isalpha():
                    key_part = line.split('=', 1)[0]
                    key = key_part.strip().lower()
                    
                    if key in keys_to_write:
                        # Replace line with new value
                        val = keys_to_write[key]
                        val_str = str(val).lower() if isinstance(val, bool) else str(val)
                        new_lines.append(f"{key} = {val_str}\n")
                        del keys_to_write[key]
                    else:
                        # Keep custom property exactly as is
                        new_lines.append(line)
                else:
                    # Keep comments/newlines exactly as is
                    new_lines.append(line)
            
            # 3. Append any NEW keys (like 'foreground' if it was missing)
            if keys_to_write:
                # FIX: Ensure the file ends with a newline before appending
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines.append('\n')

                for key, val in keys_to_write.items():
                    val_str = str(val).lower() if isinstance(val, bool) else str(val)
                    new_lines.append(f"{key} = {val_str}\n")
                
            # 4. Write back
            with open(self.filepath, 'w') as f:
                f.writelines(new_lines)
            print(f"File saved to {self.filepath}")
            
        except Exception as e:
            print(f"Save Error: {e}")
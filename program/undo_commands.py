"""
Undo/Redo Command Classes for SMBX NPC Editor

Each command captures a state change and can undo/redo it.
"""

from PyQt6.QtGui import QUndoCommand
import copy

class ChangeParameterCommand(QUndoCommand):
    """Command for changing a single standard parameter"""
    
    def __init__(self, data, key, old_value, new_value, ui_callback=None):
        super().__init__(f"Change {key}")
        self.data = data
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.ui_callback = ui_callback
    
    def redo(self):
        self.data.set_standard(self.key, self.new_value)
        if self.ui_callback:
            self.ui_callback(self.key, self.new_value)
    
    def undo(self):
        self.data.set_standard(self.key, self.old_value)
        if self.ui_callback:
            self.ui_callback(self.key, self.old_value)
    
    def id(self):
        # Return the same ID for commands that modify the same parameter
        # This allows Qt to merge consecutive edits
        return hash(self.key) & 0xFFFF
    
    def mergeWith(self, other):
        # If the other command is the same type and same key...
        if other.id() != self.id():
            return False
        
        # Update the target value to the newest one, but KEEP the original old_value
        self.new_value = other.new_value
        return True


class ChangeMultipleParametersCommand(QUndoCommand):
    """Command for changing multiple parameters at once (e.g., visual drag)"""
    
    def __init__(self, data, changes_dict, ui_callback=None, description="Edit multiple"):
        super().__init__(description)
        self.data = data
        self.changes = changes_dict  # {key: (old_val, new_val)}
        self.ui_callback = ui_callback
    
    def redo(self):
        for key, (old_val, new_val) in self.changes.items():
            self.data.set_standard(key, new_val)
            if self.ui_callback:
                self.ui_callback(key, new_val)
    
    def undo(self):
        for key, (old_val, new_val) in self.changes.items():
            self.data.set_standard(key, old_val)
            if self.ui_callback:
                self.ui_callback(key, old_val)


class ToggleParameterCommand(QUndoCommand):
    """Command for enabling/disabling a parameter (checkbox toggle)"""
    
    def __init__(self, data, key, was_enabled, is_enabled, value, ui_callback=None):
        super().__init__(f"Toggle {key}")
        self.data = data
        self.key = key
        self.was_enabled = was_enabled
        self.is_enabled = is_enabled
        self.value = value
        self.ui_callback = ui_callback
    
    def redo(self):
        if self.is_enabled:
            self.data.set_standard(self.key, self.value)
        else:
            self.data.set_standard(self.key, None)
        
        if self.ui_callback:
            self.ui_callback(self.key, self.is_enabled)
    
    def undo(self):
        if self.was_enabled:
            self.data.set_standard(self.key, self.value)
        else:
            self.data.set_standard(self.key, None)
        
        if self.ui_callback:
            self.ui_callback(self.key, self.was_enabled)


class ChangeCustomParameterCommand(QUndoCommand):
    """Command for editing custom/unknown parameters"""
    
    def __init__(self, data, key, old_value, new_value, ui_callback=None):
        super().__init__(f"Change custom {key}")
        self.data = data
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
        self.ui_callback = ui_callback
    
    def redo(self):
        if self.new_value is None:
            if self.key in self.data.custom_params:
                del self.data.custom_params[self.key]
        else:
            self.data.custom_params[self.key] = self.new_value
        
        if self.ui_callback:
            self.ui_callback()
    
    def undo(self):
        if self.old_value is None:
            if self.key in self.data.custom_params:
                del self.data.custom_params[self.key]
        else:
            self.data.custom_params[self.key] = self.old_value
        
        if self.ui_callback:
            self.ui_callback()


class AddCustomParameterCommand(QUndoCommand):
    """Command for adding a new custom parameter row"""
    
    def __init__(self, data, key, value, ui_callback=None):
        super().__init__("Add custom parameter")
        self.data = data
        self.key = key
        self.value = value
        self.ui_callback = ui_callback
    
    def redo(self):
        self.data.custom_params[self.key] = self.value
        if self.ui_callback:
            self.ui_callback()
    
    def undo(self):
        if self.key in self.data.custom_params:
            del self.data.custom_params[self.key]
        if self.ui_callback:
            self.ui_callback()


class RemoveCustomParameterCommand(QUndoCommand):
    """Command for removing a custom parameter row"""
    
    def __init__(self, data, key, old_value, ui_callback=None):
        super().__init__("Remove custom parameter")
        self.data = data
        self.key = key
        self.old_value = old_value
        self.ui_callback = ui_callback
    
    def redo(self):
        if self.key in self.data.custom_params:
            del self.data.custom_params[self.key]
        if self.ui_callback:
            self.ui_callback()
    
    def undo(self):
        self.data.custom_params[self.key] = self.old_value
        if self.ui_callback:
            self.ui_callback()

import os
from PyQt6.QtCore import QObject, QFileSystemWatcher, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFileDialog

class FileController(QObject):
    fileLoaded = pyqtSignal(str) # Path
    fileSaved = pyqtSignal(str)  # Path
    fileExternalChange = pyqtSignal(str) # Path
    
    def __init__(self, parent_window, npc_data):
        super().__init__(parent_window)
        self.window = parent_window
        self.npc_data = npc_data
        
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._on_file_changed)
        
        self.watched_files = []
        self.is_saving = False

    def load_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self.window, "Open NPC Txt", "", "Text Files (*.txt)")
        if fname:
            return self.process_load_path(fname)
        return False

    def save_dialog(self):
        # Return True if save proceeded, False if cancelled
        if not self.npc_data.filepath:
            fname, _ = QFileDialog.getSaveFileName(self.window, "Save NPC Config", "", "Text Files (*.txt)")
            if not fname: return False
            self.npc_data.filepath = fname
        
        self.save_current()
        return True

    def save_current(self):
        self.is_saving = True
        self.update_watcher() # Ensure we are watching before save, though we ignore self-events
        if self.npc_data.save():
            self.fileSaved.emit(self.npc_data.filepath)
        
        # Debounce the 'is_saving' flag reset
        QTimer.singleShot(500, lambda: setattr(self, 'is_saving', False))

    def process_load_path(self, fname):
        if self.npc_data.load(fname):
            self.update_watcher()
            self.fileLoaded.emit(fname)
            return True
        return False

    def update_watcher(self, extra_paths=None):
        if self.watched_files: 
            self.watcher.removePaths(self.watched_files)
        self.watched_files = []
        
        paths = []
        if self.npc_data.filepath and os.path.exists(self.npc_data.filepath): 
            paths.append(self.npc_data.filepath)
            
        if extra_paths:
            for p in extra_paths:
                if p and os.path.exists(p): paths.append(p)
                
        if paths:
            self.watcher.addPaths(paths)
            self.watched_files = paths

    def _on_file_changed(self, path):
        if self.is_saving: return
        
        if not os.path.exists(path):
            # File deleted?
            QTimer.singleShot(100, lambda: self.update_watcher())
            return
            
        self.fileExternalChange.emit(path)

"""
Application configuration system for SMBX NPC Editor
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application-wide configuration"""
    
    # Paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".smbx_npc_editor")
    recent_files_max: int = 10
    recent_files: List[str] = field(default_factory=list)
    
    # Window settings
    window_width: int = 1100
    window_height: int = 800
    window_maximized: bool = True
    splitter_position: int = 450  # Left panel width
    
    # Preview settings
    default_zoom: int = 6
    max_zoom: int = 16
    min_zoom: int = 1
    grid_size: int = 32
    
    # Animation
    default_frame_count: int = 1
    default_frame_speed: int = 8
    default_frame_style: int = 0
    
    # Performance
    undo_limit: int = 50
    file_watch_interval: int = 500  # ms
    preview_update_debounce: int = 16  # ms (~60 FPS)
    enable_auto_save: bool = False
    auto_save_interval: int = 300  # seconds
    
    # UI Colors (stored as hex strings)
    color_background: str = "#1e1e1e"
    color_grid: str = "#323232"
    color_hitbox: str = "#00ff00"
    color_gfxbox: str = "#ff3232"
    
    # Editor behavior
    auto_expand_categories: bool = True
    show_tooltips: bool = True
    confirm_on_exit: bool = False
    
    # Debug
    debug_mode: bool = False
    log_to_file: bool = True
    
    def __post_init__(self):
        """Ensure config_dir is a Path object"""
        if isinstance(self.config_dir, str):
            self.config_dir = Path(self.config_dir)
    
    @property
    def config_file(self) -> Path:
        """Path to the configuration file"""
        return self.config_dir / "config.json"
    
    def load(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config_file.exists():
            logger.info("No config file found, using defaults")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update fields from loaded data
            for key, value in data.items():
                if hasattr(self, key):
                    # Special handling for Path objects
                    if key == 'config_dir':
                        setattr(self, key, Path(value))
                    else:
                        setattr(self, key, value)
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return True
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict
            data = asdict(self)
            
            # Convert Path objects to strings for JSON serialization
            data['config_dir'] = str(data['config_dir'])
            
            # Write to file with pretty formatting
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
            return False
    
    def add_recent_file(self, filepath: str) -> None:
        """
        Add a file to the recent files list
        
        Args:
            filepath: Path to the file
        """
        # Remove if already in list
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        
        # Add to front of list
        self.recent_files.insert(0, filepath)
        
        # Trim to max length
        self.recent_files = self.recent_files[:self.recent_files_max]
        
        logger.debug(f"Added to recent files: {filepath}")
    
    def get_recent_files(self) -> List[str]:
        """
        Get list of recent files (filtered for existing files)
        
        Returns:
            List of file paths that still exist
        """
        return [f for f in self.recent_files if Path(f).exists()]
    
    def get_color(self, color_key: str) -> QColor:
        """
        Get a QColor from a hex string config value
        
        Args:
            color_key: Config key (e.g., 'color_background')
            
        Returns:
            QColor object
        """
        hex_color = getattr(self, color_key, "#000000")
        return QColor(hex_color)
    
    def set_color(self, color_key: str, color: QColor) -> None:
        """
        Set a color config value from a QColor
        
        Args:
            color_key: Config key (e.g., 'color_background')
            color: QColor object
        """
        setattr(self, color_key, color.name())
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        logger.info("Resetting configuration to defaults")
        default_config = AppConfig()
        
        for key in asdict(default_config).keys():
            if key != 'recent_files':  # Preserve recent files
                setattr(self, key, getattr(default_config, key))


# Global config instance
_config: AppConfig = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance
    
    Returns:
        AppConfig instance
    """
    global _config
    if _config is None:
        _config = AppConfig()
        _config.load()
    return _config


def save_config() -> bool:
    """
    Save the global configuration
    
    Returns:
        True if successful
    """
    global _config
    if _config is not None:
        return _config.save()
    return False
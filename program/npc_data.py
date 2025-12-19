"""
NPC Data model with type safety and error handling
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .npc_definitions import NPC_DEFS

logger = logging.getLogger(__name__)


class NPCData:
    """
    Manages NPC configuration data and file I/O
    
    This class handles loading, parsing, and saving SMBX NPC configuration
    files (.txt format). It maintains both standard parameters (defined in
    NPC_DEFS) and custom/extra parameters.
    
    Attributes:
        standard_params: Dict mapping parameter names to values (or None if unset)
        custom_params: Dict of custom parameter key-value pairs
        key_map: Case-insensitive lookup map for standard parameter names
        comments: Inline comments for each parameter
        header_comments: List of comments at top of file
        filepath: Path to the currently loaded file
    
    Example:
        >>> data = NPCData()
        >>> success = data.load("npc-1.txt")
        >>> if success:
        ...     data.set_standard('frames', 4)
        ...     data.save()
    """
    
    def __init__(self):
        """Initialize NPC data with empty state"""
        self.standard_params: Dict[str, Optional[Any]] = {
            k: None for k in NPC_DEFS
        }
        self.custom_params: Dict[str, str] = {}
        
        # Mapping lowercase -> canonical key for case-insensitive lookup
        self.key_map: Dict[str, str] = {k.lower(): k for k in NPC_DEFS}
        
        # Store inline comments: key -> comment_str
        self.comments: Dict[str, str] = {}
        
        # Store top-of-file comments
        self.header_comments: List[str] = []
        
        self._apply_defaults()
        self.filepath: str = ""
    
    def _apply_defaults(self) -> None:
        """Apply default values for essential parameters"""
        # These defaults ensure the preview works even with empty files
        defaults = {
            'gfxwidth': 32,
            'gfxheight': 32,
            'width': 32,
            'height': 32,
            'frames': 1,
            'framespeed': 8,
            'framestyle': 0
        }
        
        for key, value in defaults.items():
            self.standard_params[key] = value
        
        logger.debug(f"Applied default values: {defaults}")
    
    def set_standard(self, key: str, value: Optional[Any]) -> None:
        """
        Set a standard parameter value
        
        Args:
            key: Parameter name (must be in NPC_DEFS)
            value: Parameter value (or None to unset)
            
        Raises:
            ValueError: If key is not a valid parameter name
        """
        if key not in NPC_DEFS:
            raise ValueError(f"Unknown parameter: {key}")
        
        self.standard_params[key] = value
        logger.debug(f"Set parameter: {key} = {value}")
    
    def set_custom(self, key: str, value_str: str) -> None:
        """
        Set a custom/extra parameter value
        
        Args:
            key: Parameter name
            value_str: Parameter value as string
        """
        self.custom_params[key] = str(value_str)
        logger.debug(f"Set custom parameter: {key} = {value_str}")
    
    def load(self, filepath: str) -> bool:
        """
        Load NPC config from file
        
        Args:
            filepath: Path to .txt config file
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading NPC config from: {filepath}")
        
        # Convert to Path for better path handling
        path = Path(filepath)
        
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return False
        
        if not path.is_file():
            logger.error(f"Not a file: {filepath}")
            return False
        
        # Reset state
        self.filepath = filepath
        self.standard_params = {k: None for k in NPC_DEFS}
        self.custom_params = {}
        self.comments = {}
        self.header_comments = []
        
        # Apply defaults for preview
        self._apply_defaults()
        
        try:
            # Try UTF-8 first, then fall back to Latin-1
            encodings = ['utf-8', 'latin-1', 'cp1252']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    logger.debug(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    logger.debug(f"Failed to read with {encoding} encoding")
                    continue
            
            if lines is None:
                logger.error(f"Could not read file with any supported encoding")
                return False
            
            # Parse lines
            header_done = False
            param_count = 0
            
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    continue
                
                # Parse comment
                comment_part = ""
                content = line
                if '#' in line:
                    parts = line.split('#', 1)
                    content = parts[0]
                    comment_part = '#' + parts[1].rstrip('\n')
                
                clean = content.strip()
                
                # Parse Key=Value pairs
                if '=' in clean:
                    header_done = True
                    try:
                        parts = clean.split('=', 1)
                        raw_key = parts[0].strip()
                        key_lower = raw_key.lower()
                        val_str = parts[1].strip()
                        
                        # Store comment
                        if comment_part:
                            k = self.key_map.get(key_lower, raw_key)
                            self.comments[k] = comment_part
                        
                        # Determine if standard or custom parameter
                        if key_lower in self.key_map:
                            real_key = self.key_map[key_lower]
                            self._parse_value(real_key, val_str, line_num)
                            param_count += 1
                        else:
                            self.custom_params[raw_key] = val_str
                            logger.debug(f"Line {line_num}: Custom param {raw_key} = {val_str}")
                    
                    except Exception as e:
                        logger.warning(
                            f"Line {line_num}: Failed to parse '{clean}': {e}"
                        )
                
                # Header comments (before any keys)
                elif not header_done and stripped.startswith('#'):
                    self.header_comments.append(line)
            
            logger.info(
                f"Successfully loaded {param_count} standard parameters "
                f"and {len(self.custom_params)} custom parameters"
            )
            return True
        
        except PermissionError as e:
            logger.error(f"Permission denied reading file: {filepath}", exc_info=e)
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error loading file: {filepath}", exc_info=e)
            return False
    
    def _parse_value(self, key: str, val_str: str, line_num: int = 0) -> None:
        """
        Parse and set a parameter value from string
        
        Args:
            key: Parameter name (canonical form)
            val_str: Value as string
            line_num: Line number in file (for error reporting)
        """
        def_type = NPC_DEFS[key]['type']
        
        try:
            if def_type == bool:
                parsed_value = (val_str.lower() == 'true')
            elif def_type == int:
                parsed_value = int(float(val_str))
            elif def_type == float:
                parsed_value = float(val_str)
            elif def_type == "enum":
                parsed_value = int(float(val_str))
            else:  # str
                parsed_value = val_str
            
            self.standard_params[key] = parsed_value
            logger.debug(f"Line {line_num}: Parsed {key} = {parsed_value}")
        
        except (ValueError, TypeError) as e:
            # Fall back to default
            default_value = NPC_DEFS[key]['default']
            self.standard_params[key] = default_value
            logger.warning(
                f"Line {line_num}: Invalid value for {key}: '{val_str}', "
                f"using default: {default_value}"
            )
    
    def save(self) -> bool:
        """
        Save NPC config to file
        
        Returns:
            True if successful, False otherwise
        """
        if not self.filepath:
            logger.error("Cannot save: no filepath set")
            return False
        
        logger.info(f"Saving NPC config to: {self.filepath}")
        
        try:
            # Collect active parameters
            active_standard = {
                k: v for k, v in self.standard_params.items() 
                if v is not None
            }
            active_custom = self.custom_params.copy()
            
            lines = []
            
            # 1. Header Comments
            lines.extend(self.header_comments)
            if self.header_comments and not lines[-1].endswith('\n'):
                lines.append('\n')
            
            # 2. Group by Category
            priority_order = [
                "Animation", "Collision", "Interaction", "Behaviour", 
                "AI / Identity", "Line Guide", "Lighting", "Editor"
            ]
            
            all_categories = sorted(
                list(set(d['category'] for d in NPC_DEFS.values()))
            )
            all_categories.sort(
                key=lambda x: priority_order.index(x) 
                if x in priority_order else 99
            )
            
            written_keys = set()
            
            for cat in all_categories:
                # Get keys for this category
                cat_keys = [
                    k for k, d in NPC_DEFS.items() 
                    if d['category'] == cat
                ]
                
                # Filter for active keys
                keys_to_write = [k for k in cat_keys if k in active_standard]
                
                if keys_to_write:
                    for k in keys_to_write:
                        val = active_standard[k]
                        
                        # Format value
                        if val is True:
                            s_val = "true"
                        elif val is False:
                            s_val = "false"
                        else:
                            s_val = str(val)
                        
                        # Attach comment if exists
                        comment = " " + self.comments[k] if k in self.comments else ""
                        lines.append(f"{k} = {s_val}{comment}\n")
                        written_keys.add(k)
                    
                    # Newline after category block
                    lines.append("\n")
            
            # 3. Write Custom/Extra Params
            if active_custom:
                for k, v in active_custom.items():
                    # Sanitize value to prevent file corruption
                    clean_v = str(v).replace('\n', '')
                    comment = " " + self.comments[k] if k in self.comments else ""
                    lines.append(f"{k} = {clean_v}{comment}\n")
                lines.append("\n")
            
            # Write to file
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(
                f"Successfully saved {len(written_keys)} standard parameters "
                f"and {len(active_custom)} custom parameters"
            )
            return True
        
        except PermissionError as e:
            logger.error(f"Permission denied writing to: {self.filepath}", exc_info=e)
            return False
        
        except Exception as e:
            logger.error(f"Error saving file: {self.filepath}", exc_info=e)
            return False
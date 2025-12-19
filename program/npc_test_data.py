"""
Basic test suite for SMBX NPC Editor

Run with: pytest tests/ -v
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from npc_data import NPCData


class TestNPCData:
    """Tests for NPCData class"""
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary NPC config file"""
        config_path = tmp_path / "npc-test.txt"
        config_path.write_text("""# Test NPC Configuration
gfxwidth = 32
gfxheight = 64
frames = 4
framespeed = 8
jumphurt = true
nohurt = false
speed = 1.5

# Custom parameters
custom_param = test_value
""")
        return config_path
    
    def test_init(self):
        """Test NPCData initialization"""
        data = NPCData()
        
        assert data.standard_params is not None
        assert data.custom_params == {}
        assert data.filepath == ""
        
        # Check defaults are applied
        assert data.standard_params['gfxwidth'] == 32
        assert data.standard_params['frames'] == 1
    
    def test_load_basic_config(self, temp_config):
        """Test loading a basic configuration"""
        data = NPCData()
        result = data.load(str(temp_config))
        
        assert result is True
        assert data.filepath == str(temp_config)
        assert data.standard_params['gfxwidth'] == 32
        assert data.standard_params['gfxheight'] == 64
        assert data.standard_params['frames'] == 4
        assert data.standard_params['framespeed'] == 8
        assert data.standard_params['jumphurt'] is True
        assert data.standard_params['nohurt'] is False
        assert data.standard_params['speed'] == 1.5
        assert 'custom_param' in data.custom_params
        assert data.custom_params['custom_param'] == 'test_value'
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist"""
        data = NPCData()
        result = data.load("/nonexistent/path/npc.txt")
        
        assert result is False
    
    def test_preserve_comments(self, tmp_path):
        """Test that comments are preserved during load"""
        config_path = tmp_path / "test-comments.txt"
        config_path.write_text("""
# Header comment
gfxwidth = 32  # Frame width comment
frames = 4     # Number of frames
""")
        
        data = NPCData()
        data.load(str(config_path))
        
        assert len(data.header_comments) > 0
        assert 'gfxwidth' in data.comments
        assert '# Frame width comment' in data.comments['gfxwidth']
    
    def test_case_insensitive_keys(self, tmp_path):
        """Test case-insensitive parameter loading"""
        config_path = tmp_path / "test-case.txt"
        config_path.write_text("""
GfxWidth = 64
FRAMES = 2
FrAmeSpEeD = 12
""")
        
        data = NPCData()
        data.load(str(config_path))
        
        assert data.standard_params['gfxwidth'] == 64
        assert data.standard_params['frames'] == 2
        assert data.standard_params['framespeed'] == 12
    
    def test_set_standard_valid(self):
        """Test setting a valid standard parameter"""
        data = NPCData()
        data.set_standard('frames', 8)
        
        assert data.standard_params['frames'] == 8
    
    def test_set_standard_invalid(self):
        """Test setting an invalid parameter raises error"""
        data = NPCData()
        
        with pytest.raises(ValueError):
            data.set_standard('invalid_key', 123)
    
    def test_save_and_reload(self, tmp_path):
        """Test saving and reloading a configuration"""
        config_path = tmp_path / "test-save.txt"
        
        # Create and save
        data1 = NPCData()
        data1.filepath = str(config_path)
        data1.set_standard('frames', 8)
        data1.set_standard('framespeed', 12)
        data1.set_standard('jumphurt', True)
        data1.set_custom('custom_param', 'test_value')
        
        result = data1.save()
        assert result is True
        assert config_path.exists()
        
        # Reload and verify
        data2 = NPCData()
        result = data2.load(str(config_path))
        assert result is True
        assert data2.standard_params['frames'] == 8
        assert data2.standard_params['framespeed'] == 12
        assert data2.standard_params['jumphurt'] is True
        assert 'custom_param' in data2.custom_params
    
    def test_invalid_values_use_defaults(self, tmp_path):
        """Test that invalid values fall back to defaults"""
        config_path = tmp_path / "test-invalid.txt"
        config_path.write_text("""
frames = not_a_number
framespeed = invalid
jumphurt = maybe
""")
        
        data = NPCData()
        data.load(str(config_path))
        
        # Should use defaults for invalid values
        from npc_definitions import NPC_DEFS
        assert data.standard_params['frames'] == NPC_DEFS['frames']['default']
        assert data.standard_params['framespeed'] == NPC_DEFS['framespeed']['default']
        assert data.standard_params['jumphurt'] == NPC_DEFS['jumphurt']['default']


class TestNPCDataEdgeCases:
    """Edge case tests"""
    
    def test_empty_file(self, tmp_path):
        """Test loading an empty file"""
        config_path = tmp_path / "empty.txt"
        config_path.write_text("")
        
        data = NPCData()
        result = data.load(str(config_path))
        
        assert result is True
        # Should still have defaults
        assert data.standard_params['frames'] == 1
    
    def test_only_comments(self, tmp_path):
        """Test file with only comments"""
        config_path = tmp_path / "comments-only.txt"
        config_path.write_text("""
# This is a comment
# Another comment
# More comments
""")
        
        data = NPCData()
        result = data.load(str(config_path))
        
        assert result is True
        assert len(data.header_comments) == 3
    
    def test_malformed_lines(self, tmp_path):
        """Test that malformed lines are skipped gracefully"""
        config_path = tmp_path / "malformed.txt"
        config_path.write_text("""
frames = 4
this line has no equals sign
gfxwidth = 32
= missing key
framespeed = 8
""")
        
        data = NPCData()
        result = data.load(str(config_path))
        
        # Should still load successfully, skipping bad lines
        assert result is True
        assert data.standard_params['frames'] == 4
        assert data.standard_params['gfxwidth'] == 32
        assert data.standard_params['framespeed'] == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
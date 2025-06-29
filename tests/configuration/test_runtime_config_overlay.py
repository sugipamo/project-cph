import pytest
from src.configuration.runtime_config_overlay import RuntimeConfigOverlay, DebugConfigProvider


class TestRuntimeConfigOverlay:
    """Tests for RuntimeConfigOverlay class"""
    
    def test_init(self):
        """Test initialization of RuntimeConfigOverlay"""
        overlay = RuntimeConfigOverlay()
        assert overlay._overlay_config == {}
        assert overlay._active is False
        assert overlay.is_active() is False
    
    def test_set_overlay_simple(self):
        """Test setting a simple overlay value"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("key", "value")
        
        assert overlay._overlay_config == {"key": "value"}
        assert overlay.is_active() is True
    
    def test_set_overlay_nested(self):
        """Test setting a nested overlay value"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("parent.child.key", "value")
        
        assert overlay._overlay_config == {
            "parent": {
                "child": {
                    "key": "value"
                }
            }
        }
        assert overlay.is_active() is True
    
    def test_set_overlay_multiple(self):
        """Test setting multiple overlay values"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("config.log_level", "DEBUG")
        overlay.set_overlay("config.timeout", 30)
        overlay.set_overlay("feature.enabled", True)
        
        assert overlay._overlay_config == {
            "config": {
                "log_level": "DEBUG",
                "timeout": 30
            },
            "feature": {
                "enabled": True
            }
        }
    
    def test_get_overlay_simple(self):
        """Test getting a simple overlay value"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("key", "value")
        
        assert overlay.get_overlay("key", "default") == "value"
    
    def test_get_overlay_nested(self):
        """Test getting a nested overlay value"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("parent.child.key", "value")
        
        assert overlay.get_overlay("parent.child.key", "default") == "value"
    
    def test_get_overlay_not_exists(self):
        """Test getting non-existent overlay returns default"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("existing", "value")
        
        assert overlay.get_overlay("nonexistent", "default") == "default"
        assert overlay.get_overlay("existing.nested", "default") == "default"
    
    def test_get_overlay_inactive(self):
        """Test getting overlay when inactive returns default"""
        overlay = RuntimeConfigOverlay()
        assert overlay.get_overlay("any.key", "default") == "default"
    
    def test_get_overlay_type_error(self):
        """Test getting overlay handles TypeError"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("scalar", "value")
        
        # Trying to access scalar value as dict should return default
        assert overlay.get_overlay("scalar.nested", "default") == "default"
    
    def test_has_overlay_exists(self):
        """Test checking if overlay exists"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("config.log_level", "DEBUG")
        
        assert overlay.has_overlay("config.log_level") is True
        assert overlay.has_overlay("config") is True
    
    def test_has_overlay_not_exists(self):
        """Test checking if non-existent overlay"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("config.log_level", "DEBUG")
        
        assert overlay.has_overlay("nonexistent") is False
        assert overlay.has_overlay("config.timeout") is False
    
    def test_has_overlay_inactive(self):
        """Test checking overlay when inactive"""
        overlay = RuntimeConfigOverlay()
        assert overlay.has_overlay("any.key") is False
    
    def test_has_overlay_type_error(self):
        """Test has_overlay handles TypeError"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("scalar", "value")
        
        assert overlay.has_overlay("scalar.nested") is False
    
    def test_clear_overlay(self):
        """Test clearing overlay"""
        overlay = RuntimeConfigOverlay()
        overlay.set_overlay("key1", "value1")
        overlay.set_overlay("key2", "value2")
        
        assert overlay.is_active() is True
        assert len(overlay._overlay_config) > 0
        
        overlay.clear_overlay()
        
        assert overlay._overlay_config == {}
        assert overlay.is_active() is False


class TestDebugConfigProvider:
    """Tests for DebugConfigProvider class"""
    
    def test_init(self):
        """Test initialization of DebugConfigProvider"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        assert provider.overlay is overlay
    
    def test_enable_debug_mode(self):
        """Test enabling debug mode"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        
        assert overlay.get_overlay("logging_config.default_level", "INFO") == "DEBUG"
        assert overlay.get_overlay("output.show_step_details", False) is True
        assert overlay.get_overlay("debug", False) is True
    
    def test_disable_debug_mode(self):
        """Test disabling debug mode"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        assert overlay.is_active() is True
        
        provider.disable_debug_mode()
        assert overlay.is_active() is False
    
    def test_get_log_level_with_overlay(self):
        """Test getting log level with overlay"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        provider.enable_debug_mode()
        assert provider.get_log_level("INFO") == "DEBUG"
    
    def test_get_log_level_without_overlay(self):
        """Test getting log level without overlay"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        assert provider.get_log_level("INFO") == "INFO"
    
    def test_is_debug_enabled(self):
        """Test checking if debug is enabled"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        assert provider.is_debug_enabled() is False
        
        provider.enable_debug_mode()
        assert provider.is_debug_enabled() is True
        
        provider.disable_debug_mode()
        assert provider.is_debug_enabled() is False
    
    def test_should_show_step_details(self):
        """Test checking if step details should be shown"""
        overlay = RuntimeConfigOverlay()
        provider = DebugConfigProvider(overlay)
        
        assert provider.should_show_step_details() is False
        
        provider.enable_debug_mode()
        assert provider.should_show_step_details() is True
        
        provider.disable_debug_mode()
        assert provider.should_show_step_details() is False
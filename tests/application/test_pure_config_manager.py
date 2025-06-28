"""Tests for PureConfigManager."""
import pytest
from typing import Dict, Any

from src.application.pure_config_manager import PureConfigManager
from src.domain.config_node import ConfigNode


class TestPureConfigManager:
    """Test cases for PureConfigManager."""

    def test_init(self):
        """Test initialization of PureConfigManager."""
        manager = PureConfigManager()
        assert manager.root_node is None
        assert manager._system_dir is None
        assert manager._env_dir is None
        assert manager._language is None

    def test_initialize_from_config_dict(self):
        """Test initialization from config dictionary."""
        manager = PureConfigManager()
        config_dict = {
            "test": {
                "value": "hello",
                "nested": {
                    "item": 42
                }
            }
        }
        
        manager.initialize_from_config_dict(
            config_dict=config_dict,
            system_dir="/system",
            env_dir="/env",
            language="python"
        )
        
        assert manager.root_node is not None
        assert manager._system_dir == "/system"
        assert manager._env_dir == "/env"
        assert manager._language == "python"

    def test_resolve_config_not_initialized(self):
        """Test resolve_config when manager is not initialized."""
        manager = PureConfigManager()
        
        with pytest.raises(RuntimeError, match="ConfigManager has not been initialized"):
            manager.resolve_config(["test", "value"], str)

    def test_resolve_config_simple(self):
        """Test resolving simple config values."""
        manager = PureConfigManager()
        config_dict = {
            "test": {
                "value": "hello",
                "number": 42,
                "flag": True
            }
        }
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        assert manager.resolve_config(["test", "value"], str) == "hello"
        assert manager.resolve_config(["test", "number"], int) == 42
        assert manager.resolve_config(["test", "flag"], bool) is True

    def test_resolve_config_type_conversion(self):
        """Test type conversion in resolve_config."""
        manager = PureConfigManager()
        config_dict = {
            "test": {
                "str_as_int": "123",
                "int_as_str": 456,
                "bool_as_str": "true",
                "bool_as_str_false": "false"
            }
        }
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        # String to int conversion
        assert manager.resolve_config(["test", "str_as_int"], int) == 123
        
        # Int to string conversion
        assert manager.resolve_config(["test", "int_as_str"], str) == "456"
        
        # String to bool conversion
        assert manager.resolve_config(["test", "bool_as_str"], bool) is True
        assert manager.resolve_config(["test", "bool_as_str_false"], bool) is False

    def test_resolve_config_not_found(self):
        """Test resolve_config with non-existent path."""
        manager = PureConfigManager()
        config_dict = {"test": {"value": "hello"}}
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        with pytest.raises(KeyError, match="Config path"):
            manager.resolve_config(["nonexistent", "path"], str)

    def test_resolve_config_type_mismatch(self):
        """Test resolve_config with type mismatch that can't be converted."""
        manager = PureConfigManager()
        config_dict = {"test": {"value": {"nested": "object"}}}
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        with pytest.raises(TypeError):
            manager.resolve_config(["test", "value"], int)

    def test_resolve_template_typed_not_initialized(self):
        """Test resolve_template_typed when manager is not initialized."""
        manager = PureConfigManager()
        
        with pytest.raises(RuntimeError, match="ConfigManager has not been initialized"):
            manager.resolve_template_typed("test", {}, str)

    @pytest.mark.skip(reason="Template resolution requires regex_ops dependency")
    def test_resolve_template_typed_simple(self):
        """Test simple template resolution."""
        manager = PureConfigManager()
        config_dict = {
            "paths": {
                "base": "/home/user",
                "project": "${paths.base}/project"
            }
        }
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        result = manager.resolve_template_typed("${paths.base}/test", {}, str)
        assert result == "/home/user/test"

    @pytest.mark.skip(reason="Template resolution requires regex_ops dependency")
    def test_resolve_template_typed_with_context(self):
        """Test template resolution with context."""
        manager = PureConfigManager()
        config_dict = {"greeting": "Hello"}
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        result = manager.resolve_template_typed(
            "${greeting}, ${name}!",
            {"name": "World"},
            str
        )
        assert result == "Hello, World!"

    @pytest.mark.skip(reason="Template resolution requires regex_ops dependency")
    def test_resolve_template_typed_type_conversion(self):
        """Test template resolution with type conversion."""
        manager = PureConfigManager()
        config_dict = {"number": 42}
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        # Number to string conversion
        result = manager.resolve_template_typed("${number}", {}, str)
        assert result == "42"

    @pytest.mark.skip(reason="Template resolution requires regex_ops dependency")
    def test_resolve_template_typed_type_mismatch(self):
        """Test template resolution with type mismatch."""
        manager = PureConfigManager()
        config_dict = {"value": "string"}
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        with pytest.raises(TypeError, match="Template result type mismatch"):
            manager.resolve_template_typed("${value}", {}, int)

    def test_get_language(self):
        """Test get_language method."""
        manager = PureConfigManager()
        assert manager.get_language() is None
        
        manager.initialize_from_config_dict({}, "/system", "/env", "rust")
        assert manager.get_language() == "rust"

    def test_get_system_dir(self):
        """Test get_system_dir method."""
        manager = PureConfigManager()
        assert manager.get_system_dir() is None
        
        manager.initialize_from_config_dict({}, "/system/path", "/env", "python")
        assert manager.get_system_dir() == "/system/path"

    def test_get_env_dir(self):
        """Test get_env_dir method."""
        manager = PureConfigManager()
        assert manager.get_env_dir() is None
        
        manager.initialize_from_config_dict({}, "/system", "/env/path", "python")
        assert manager.get_env_dir() == "/env/path"

    def test_nested_config_resolution(self):
        """Test resolving deeply nested config values."""
        manager = PureConfigManager()
        config_dict = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep_value"
                    }
                }
            }
        }
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        result = manager.resolve_config(["level1", "level2", "level3", "value"], str)
        assert result == "deep_value"

    def test_bool_string_variations(self):
        """Test various boolean string conversions."""
        manager = PureConfigManager()
        config_dict = {
            "bools": {
                "true1": "true",
                "true2": "True",
                "true3": "1",
                "true4": "yes",
                "true5": "on",
                "false1": "false",
                "false2": "0",
                "false3": "no",
                "false4": "off"
            }
        }
        
        manager.initialize_from_config_dict(config_dict, "/system", "/env", "python")
        
        # True values
        assert manager.resolve_config(["bools", "true1"], bool) is True
        assert manager.resolve_config(["bools", "true2"], bool) is True
        assert manager.resolve_config(["bools", "true3"], bool) is True
        assert manager.resolve_config(["bools", "true4"], bool) is True
        assert manager.resolve_config(["bools", "true5"], bool) is True
        
        # False values
        assert manager.resolve_config(["bools", "false1"], bool) is False
        assert manager.resolve_config(["bools", "false2"], bool) is False
        assert manager.resolve_config(["bools", "false3"], bool) is False
        assert manager.resolve_config(["bools", "false4"], bool) is False
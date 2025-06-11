"""Test cases for detailed override behavior in JsonConfigLoader."""

from unittest.mock import patch

import pytest

from src.infrastructure.config.json_config_loader import JsonConfigLoader


class TestJsonConfigLoaderOverrideBehavior:
    """Test detailed override behavior in JsonConfigLoader."""

    @pytest.fixture
    def loader(self):
        """Create a JsonConfigLoader instance."""
        return JsonConfigLoader()

    def test_language_override_with_conflicting_nested_keys(self, loader):
        """Test that language config properly overrides nested shared config keys."""
        shared_mock = {
            "output": {
                "show_workflow_summary": True,
                "show_step_details": False,
                "step_details": {
                    "show_type": True,
                    "show_command": True,
                    "max_command_length": 80
                }
            },
            "timeout_seconds": 300
        }

        language_mock = {
            "test_lang": {
                "output": {
                    "show_workflow_summary": False,  # Override shared
                    "show_step_details": True,       # Override shared
                    "step_details": {
                        "show_type": False,           # Override nested shared
                        "max_command_length": 120     # Override nested shared
                        # Note: show_command should inherit from shared
                    },
                    "custom_lang_setting": "value"   # Language-only setting
                },
                "custom_timeout": 600                 # Language-only setting
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_lang")

            # Top-level overrides
            assert config["output"]["show_workflow_summary"] is False  # Overridden
            assert config["output"]["show_step_details"] is True       # Overridden

            # Nested overrides
            assert config["output"]["step_details"]["show_type"] is False    # Overridden
            assert config["output"]["step_details"]["max_command_length"] == 120  # Overridden

            # Inherited nested values
            assert config["output"]["step_details"]["show_command"] is True  # Inherited

            # Language-only settings
            assert config["output"]["custom_lang_setting"] == "value"
            assert config["custom_timeout"] == 600

            # Shared-only settings
            assert config["timeout_seconds"] == 300

    def test_language_override_preserves_unrelated_shared_keys(self, loader):
        """Test that language overrides don't affect unrelated shared keys."""
        shared_mock = {
            "paths": {
                "contest_current_path": "./contest_current",
                "workspace_path": "./workspace"
            },
            "environment_logging": {
                "enabled": True,
                "show_language_name": True
            }
        }

        language_mock = {
            "test_lang": {
                "paths": {
                    "contest_current_path": "./custom_current"  # Override only this
                    # workspace_path should inherit from shared
                },
                "language_specific": "value"
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_lang")

            # Overridden value
            assert config["paths"]["contest_current_path"] == "./custom_current"

            # Inherited value
            assert config["paths"]["workspace_path"] == "./workspace"

            # Completely unrelated shared config should be preserved
            assert config["environment_logging"]["enabled"] is True
            assert config["environment_logging"]["show_language_name"] is True

            # Language-specific setting
            assert config["language_specific"] == "value"

    def test_override_with_different_data_types(self, loader):
        """Test override behavior with different data types."""
        shared_mock = {
            "string_value": "shared_string",
            "int_value": 100,
            "bool_value": True,
            "list_value": ["shared1", "shared2"],
            "dict_value": {"nested": "shared"}
        }

        language_mock = {
            "test_lang": {
                "string_value": "lang_string",        # String override
                "int_value": 200,                     # Int override
                "bool_value": False,                  # Bool override
                "list_value": ["lang1", "lang2"],     # List override (complete replacement)
                "dict_value": {"nested": "lang", "extra": "value"}  # Dict override (merge)
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_lang")

            assert config["string_value"] == "lang_string"
            assert config["int_value"] == 200
            assert config["bool_value"] is False
            assert config["list_value"] == ["lang1", "lang2"]  # Complete replacement
            assert config["dict_value"]["nested"] == "lang"    # Overridden
            assert config["dict_value"]["extra"] == "value"    # Added

    def test_real_world_cpp_override_scenario(self, loader):
        """Test a realistic scenario where cpp config might override shared settings."""
        # Mock a scenario where cpp wants custom output format
        shared_mock = {
            "format_presets": {
                "standard": {
                    "description": "標準的なフォーマット",
                    "templates": {
                        "default": "{test_name} | {status}",
                        "summary": "{passed}/{total} passed"
                    }
                }
            },
            "output": {
                "show_workflow_summary": True
            }
        }

        # Real cpp config structure
        language_mock = {
            "cpp": {
                "aliases": ["c++", "cpp"],
                "language_id": "5003",
                "source_file_name": "main.cpp",
                "format_presets": {
                    "standard": {
                        "description": "C++向け標準フォーマット",  # Override description
                        "templates": {
                            "default": "C++ {test_name} | {status}",  # Override template
                            "error": "C++ Error: {error_message}"     # Add new template
                            # summary should inherit from shared
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("cpp")

            # Language-specific settings
            assert config["aliases"] == ["c++", "cpp"]
            assert config["language_id"] == "5003"
            assert config["source_file_name"] == "main.cpp"

            # Overridden format preset
            assert config["format_presets"]["standard"]["description"] == "C++向け標準フォーマット"
            assert config["format_presets"]["standard"]["templates"]["default"] == "C++ {test_name} | {status}"
            assert config["format_presets"]["standard"]["templates"]["error"] == "C++ Error: {error_message}"

            # Inherited template
            assert config["format_presets"]["standard"]["templates"]["summary"] == "{passed}/{total} passed"

            # Inherited shared settings
            assert config["output"]["show_workflow_summary"] is True

    def test_multiple_inheritance_levels(self, loader):
        """Test that the inheritance works correctly with system->shared->language chain."""
        # This test verifies the complete inheritance chain
        cpp_config = loader.get_language_config("cpp")

        # Should have settings from all levels:
        # 1. System level (through get_env_config)
        # 2. Shared level (user shared config)
        # 3. Language level (cpp specific)

        # From shared level
        assert "paths" in cpp_config
        assert "output" in cpp_config
        assert "environment_logging" in cpp_config

        # From language level
        assert "aliases" in cpp_config
        assert "language_id" in cpp_config
        assert "source_file_name" in cpp_config
        assert "commands" in cpp_config

        # Verify priority: language should override shared when there's conflict
        # (There's no current conflict, but verify language-specific values exist)
        assert cpp_config["language_id"] == "5003"
        assert "c++" in cpp_config["aliases"]

        # Verify shared values are accessible
        assert cpp_config["paths"]["contest_current_path"] == "./contest_current"

    def test_empty_override_preserves_all_shared(self, loader):
        """Test that empty language config still gets all shared config."""
        shared_mock = {
            "key1": "value1",
            "key2": {"nested": "value2"},
            "key3": ["list", "items"]
        }

        language_mock = {"empty_lang": {}}

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("empty_lang")

            # Should be identical to shared config
            assert config == shared_mock
            assert config["key1"] == "value1"
            assert config["key2"]["nested"] == "value2"
            assert config["key3"] == ["list", "items"]

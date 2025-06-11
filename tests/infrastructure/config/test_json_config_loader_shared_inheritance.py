"""Test cases for JsonConfigLoader's shared configuration inheritance behavior."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.infrastructure.config.json_config_loader import JsonConfigLoader


class TestJsonConfigLoaderSharedInheritance:
    """Test shared configuration inheritance in JsonConfigLoader."""

    @pytest.fixture
    def loader(self):
        """Create a JsonConfigLoader instance."""
        return JsonConfigLoader()

    def test_language_config_inherits_shared_settings(self, loader):
        """Test that language config includes shared configuration as base."""
        cpp_config = loader.get_language_config("cpp")

        # Should include shared settings
        assert "paths" in cpp_config
        assert "output" in cpp_config
        assert "environment_logging" in cpp_config
        assert "format_presets" in cpp_config

        # Should include language-specific settings
        assert "aliases" in cpp_config
        assert "language_id" in cpp_config
        assert "source_file_name" in cpp_config

        # Verify shared settings content
        assert cpp_config["paths"]["contest_current_path"] == "./contest_current"
        assert cpp_config["environment_logging"]["enabled"] is True

    def test_language_specific_settings_override_shared(self, loader):
        """Test that language-specific settings override shared ones when keys conflict."""
        # Create a mock scenario where shared and language configs have overlapping keys
        shared_mock = {
            "shared": {
                "test_key": "shared_value",
                "paths": {"test_path": "shared_path"},
                "nested": {"shared_only": "value1", "override_me": "shared"}
            }
        }

        language_mock = {
            "test_language": {
                "test_key": "language_value",
                "language_only": "lang_value",
                "nested": {"override_me": "language", "language_only": "value2"}
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock["shared"]), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_language")

            # Language-specific value should override shared
            assert config["test_key"] == "language_value"

            # Language-only keys should be present
            assert config["language_only"] == "lang_value"

            # Shared-only keys should be present
            assert config["paths"]["test_path"] == "shared_path"

            # Nested override should work correctly
            assert config["nested"]["override_me"] == "language"
            assert config["nested"]["shared_only"] == "value1"
            assert config["nested"]["language_only"] == "value2"

    def test_nonexistent_language_returns_shared_config_only(self, loader):
        """Test that requesting config for non-existent language returns shared config."""
        config = loader.get_language_config("nonexistent_language")

        # Should contain shared settings
        assert "paths" in config
        assert "output" in config
        assert "environment_logging" in config

        # Should not contain language-specific settings
        assert "aliases" not in config
        assert "language_id" not in config
        assert "source_file_name" not in config

        # Should have expected number of keys (only shared)
        shared_config = loader.get_shared_config()
        assert len(config) == len(shared_config)

    def test_empty_language_config_with_shared_base(self, loader):
        """Test that empty language config still includes shared settings."""
        # Mock empty language config
        with patch.object(loader, 'get_env_config', return_value={"empty_lang": {}}):
            config = loader.get_language_config("empty_lang")

            # Should still contain shared settings
            shared_config = loader.get_shared_config()
            assert len(config) == len(shared_config)

            for key in shared_config:
                assert key in config
                assert config[key] == shared_config[key]

    def test_deep_merge_behavior_in_language_config(self, loader):
        """Test deep merge behavior when nested dictionaries exist in both configs."""
        shared_mock = {
            "nested_config": {
                "level1": {
                    "shared_key": "shared_value",
                    "level2": {
                        "deep_shared": "deep_value"
                    }
                }
            }
        }

        language_mock = {
            "test_lang": {
                "nested_config": {
                    "level1": {
                        "lang_key": "lang_value",
                        "level2": {
                            "deep_lang": "deep_lang_value"
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=shared_mock), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_lang")

            # Both shared and language keys should exist at same level
            assert config["nested_config"]["level1"]["shared_key"] == "shared_value"
            assert config["nested_config"]["level1"]["lang_key"] == "lang_value"

            # Deep nested keys should also merge correctly
            assert config["nested_config"]["level1"]["level2"]["deep_shared"] == "deep_value"
            assert config["nested_config"]["level1"]["level2"]["deep_lang"] == "deep_lang_value"

    def test_language_config_key_count_increase(self, loader):
        """Test that language config has more keys after inheritance implementation."""
        # Test all actual languages
        for language in ["cpp", "python", "rust"]:
            config = loader.get_language_config(language)
            shared_config = loader.get_shared_config()

            # Language config should have at least as many keys as shared config
            assert len(config) >= len(shared_config)

            # Should include all shared keys
            for shared_key in shared_config:
                assert shared_key in config

    def test_backwards_compatibility_of_language_config_content(self, loader):
        """Test that existing language-specific keys are still accessible."""
        cpp_config = loader.get_language_config("cpp")

        # Original language-specific keys should still work
        assert "aliases" in cpp_config
        assert "c++" in cpp_config["aliases"]
        assert "cpp" in cpp_config["aliases"]

        assert cpp_config["language_id"] == "5003"
        assert cpp_config["source_file_name"] == "main.cpp"
        assert "commands" in cpp_config

        # Shared keys should also be available
        assert "paths" in cpp_config
        assert "output" in cpp_config

    def test_get_shared_config_independence(self, loader):
        """Test that get_shared_config still works independently."""
        shared_config = loader.get_shared_config()
        cpp_config = loader.get_language_config("cpp")

        # Shared config should not include language-specific keys
        assert "aliases" not in shared_config
        assert "language_id" not in shared_config
        assert "source_file_name" not in shared_config

        # But should include expected shared keys
        assert "paths" in shared_config
        assert "output" in shared_config

        # Shared config should be subset of language config
        for key, value in shared_config.items():
            assert key in cpp_config
            # For simple values, they should be equal
            if not isinstance(value, dict):
                assert cpp_config[key] == value

    def test_system_config_integration_with_language_inheritance(self, loader):
        """Test that system config is properly inherited through shared to language."""
        # Get language config which should include system + shared + language
        cpp_config = loader.get_language_config("cpp")

        # Test that we can access the full merged configuration
        full_config = loader.get_env_config()

        # System config should be accessible through the full config
        assert "shared" in full_config
        shared_section = full_config["shared"]

        # Verify that system configurations are included in shared section
        # Note: System configs are merged at the system level, not as separate top-level keys
        assert "docker_security" in shared_section or "docker" in shared_section
        assert "paths" in shared_section  # User config should be present

        # Language config should have all the merged shared configuration
        assert "docker" in cpp_config  # Docker config from shared/user config
        assert "paths" in cpp_config    # Paths from shared/user config

        # Verify that language-specific settings are preserved
        assert "aliases" in cpp_config
        assert "language_id" in cpp_config
        assert cpp_config["language_id"] == "5003"

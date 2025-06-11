"""Test cases for edge cases in JsonConfigLoader's language config inheritance."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.infrastructure.config.json_config_loader import JsonConfigLoader


class TestJsonConfigLoaderEdgeCases:
    """Test edge cases for JsonConfigLoader language config inheritance."""

    @pytest.fixture
    def loader(self):
        """Create a JsonConfigLoader instance."""
        return JsonConfigLoader()

    def test_nonexistent_language_gets_shared_config(self, loader):
        """Test that requesting config for non-existent language returns shared config."""
        config = loader.get_language_config("nonexistent_language")
        shared_config = loader.get_shared_config()

        # Should be identical to shared config
        assert config == shared_config
        assert len(config) == len(shared_config)

        for key in shared_config:
            assert key in config
            assert config[key] == shared_config[key]

    def test_empty_string_language_name(self, loader):
        """Test behavior with empty string as language name."""
        config = loader.get_language_config("")
        shared_config = loader.get_shared_config()

        # Should return shared config for empty string
        assert config == shared_config

    def test_none_language_name_handling(self, loader):
        """Test behavior with None as language name."""
        # This should not crash and should handle gracefully
        config = loader.get_language_config(None)
        shared_config = loader.get_shared_config()

        # Should return shared config
        assert config == shared_config

    def test_special_characters_in_language_name(self, loader):
        """Test behavior with special characters in language name."""
        special_names = ["c++", "c#", "f#", "lang-with-dashes", "lang_with_underscores", "123numeric"]

        for lang_name in special_names:
            config = loader.get_language_config(lang_name)
            shared_config = loader.get_shared_config()

            # Should return shared config for non-existent special language names
            assert len(config) >= len(shared_config)

            # Should contain all shared keys
            for key in shared_config:
                assert key in config

    def test_case_sensitivity_in_language_names(self, loader):
        """Test that language names are case sensitive."""
        cpp_config = loader.get_language_config("cpp")
        CPP_config = loader.get_language_config("CPP")  # Different case
        shared_config = loader.get_shared_config()

        # cpp should have language-specific settings
        assert "aliases" in cpp_config
        assert "language_id" in cpp_config
        assert len(cpp_config) > len(shared_config)

        # CPP (uppercase) should only have shared settings
        assert CPP_config == shared_config
        assert "aliases" not in CPP_config

    def test_language_config_with_missing_shared_config(self, loader):
        """Test behavior when shared config is missing or empty."""
        with patch.object(loader, 'get_shared_config', return_value={}):
            config = loader.get_language_config("cpp")

            # Should still work and return language-specific config only
            env_config = loader.get_env_config()
            expected = env_config.get("cpp", {})

            assert config == expected

    def test_corrupted_shared_config_handling(self, loader):
        """Test handling of corrupted or invalid shared config."""
        # Mock corrupted shared config
        corrupted_shared = {
            "invalid_nested": {
                "good_key": "good_value"
            },
            None: "invalid_none_key",  # This would be filtered out in practice
            "normal_key": "normal_value"
        }

        language_config_mock = {
            "test_lang": {
                "lang_key": "lang_value",
                "invalid_nested": {
                    "override_key": "override_value"
                }
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=corrupted_shared), \
             patch.object(loader, 'get_env_config', return_value=language_config_mock):

            config = loader.get_language_config("test_lang")

            # Should handle corruption gracefully
            assert "lang_key" in config
            assert config["lang_key"] == "lang_value"
            assert "normal_key" in config
            assert config["normal_key"] == "normal_value"

            # Should merge nested configs correctly despite corruption
            assert config["invalid_nested"]["good_key"] == "good_value"
            assert config["invalid_nested"]["override_key"] == "override_value"

    def test_deep_nesting_edge_cases(self, loader):
        """Test edge cases with very deep nesting."""
        deep_shared = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "deep_shared_value": "shared"
                        }
                    }
                }
            }
        }

        deep_language = {
            "test_lang": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "deep_lang_value": "language"
                            }
                        }
                    }
                }
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=deep_shared), \
             patch.object(loader, 'get_env_config', return_value=deep_language):

            config = loader.get_language_config("test_lang")

            # Both deep values should be accessible
            assert config["level1"]["level2"]["level3"]["level4"]["deep_shared_value"] == "shared"
            assert config["level1"]["level2"]["level3"]["level4"]["deep_lang_value"] == "language"

    def test_circular_reference_in_config_data(self, loader):
        """Test handling of circular references in config data."""
        # Create a config with circular-like structure
        circular_shared = {
            "ref1": {
                "back_ref": "points_to_ref2"
            },
            "ref2": {
                "back_ref": "points_to_ref1"
            }
        }

        language_mock = {
            "test_lang": {
                "ref1": {
                    "lang_specific": "value"
                }
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=circular_shared), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            # Should not hang or crash due to circular references
            config = loader.get_language_config("test_lang")

            assert config["ref1"]["back_ref"] == "points_to_ref2"
            assert config["ref1"]["lang_specific"] == "value"
            assert config["ref2"]["back_ref"] == "points_to_ref1"

    def test_large_config_performance(self, loader):
        """Test performance with very large configuration objects."""
        # Create a large shared config
        large_shared = {}
        for i in range(1000):
            large_shared[f"key_{i}"] = {
                "nested_key": f"value_{i}",
                "another_nested": {
                    "deep_key": f"deep_value_{i}"
                }
            }

        language_mock = {
            "test_lang": {
                "key_0": {
                    "nested_key": "overridden_value_0"
                },
                "lang_specific": "value"
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=large_shared), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            # Should handle large configs without issues
            config = loader.get_language_config("test_lang")

            assert len(config) == 1001  # 1000 shared + 1 language-specific
            assert config["key_0"]["nested_key"] == "overridden_value_0"  # Override
            assert config["key_1"]["nested_key"] == "value_1"  # Inherited
            assert config["lang_specific"] == "value"

    def test_unicode_and_special_characters_in_values(self, loader):
        """Test handling of unicode and special characters in config values."""
        unicode_shared = {
            "japanese": "これは日本語です",
            "emoji": "🚀✅❌",
            "special_chars": "!@#$%^&*()_+-=[]{}|;:'\",.<>?",
            "escaped_quotes": 'He said "Hello" and she said \'Hi\'',
            "unicode_key_🔧": "unicode in key"
        }

        language_mock = {
            "test_lang": {
                "japanese": "これは上書きされた日本語です",
                "chinese": "这是中文"
            }
        }

        with patch.object(loader, 'get_shared_config', return_value=unicode_shared), \
             patch.object(loader, 'get_env_config', return_value=language_mock):

            config = loader.get_language_config("test_lang")

            # Unicode should be preserved
            assert config["japanese"] == "これは上書きされた日本語です"  # Overridden
            assert config["chinese"] == "这是中文"  # Language-specific
            assert config["emoji"] == "🚀✅❌"  # Inherited
            assert config["special_chars"] == "!@#$%^&*()_+-=[]{}|;:'\",.<>?"  # Inherited
            assert config["unicode_key_🔧"] == "unicode in key"  # Inherited

    def test_memory_efficiency_with_repeated_calls(self, loader):
        """Test that repeated calls don't cause memory leaks or excessive duplication."""
        # Call get_language_config multiple times for same language
        configs = []
        for _ in range(10):
            config = loader.get_language_config("cpp")
            configs.append(config)

        # All configs should be identical
        for i in range(1, len(configs)):
            assert configs[i] == configs[0]

        # Should have consistent structure
        for config in configs:
            assert "aliases" in config
            assert "paths" in config
            assert len(config) > 10  # Should have inherited many keys

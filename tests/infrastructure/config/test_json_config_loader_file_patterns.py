"""Tests for JsonConfigLoader file patterns and operations functionality."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.infrastructure.config.json_config_loader import JsonConfigLoader


class TestJsonConfigLoaderFilePatterns:
    """Test JsonConfigLoader file patterns functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "contest_env"
            config_dir.mkdir()

            # Create shared config
            shared_dir = config_dir / "shared"
            shared_dir.mkdir()
            shared_config = {
                "shared": {
                    "file_operations": {
                        "move_test_files": [
                            ["workspace.test_files", "contest_current.test_files"],
                            ["workspace.contest_files", "contest_stock.contest_files"]
                        ],
                        "cleanup_workspace": [
                            ["workspace.temp_files", "contest_stock.temp_files"]
                        ]
                    },
                    "default_patterns": {
                        "test_files": {
                            "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                            "contest_current": ["test/"],
                            "contest_stock": ["test/"]
                        }
                    }
                }
            }
            with open(shared_dir / "env.json", 'w', encoding='utf-8') as f:
                json.dump(shared_config, f, indent=2)

            # Create cpp config
            cpp_dir = config_dir / "cpp"
            cpp_dir.mkdir()
            cpp_config = {
                "cpp": {
                    "file_patterns": {
                        "test_files": {
                            "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                            "contest_current": ["test/"],
                            "contest_stock": ["test/"]
                        },
                        "contest_files": {
                            "workspace": ["main.cpp", "*.h", "*.hpp"],
                            "contest_current": ["main.cpp"],
                            "contest_stock": ["main.cpp", "*.h", "*.hpp"]
                        },
                        "build_files": {
                            "workspace": ["build/**/*", "*.o", "*.exe"],
                            "contest_current": [],
                            "contest_stock": []
                        }
                    }
                }
            }
            with open(cpp_dir / "env.json", 'w', encoding='utf-8') as f:
                json.dump(cpp_config, f, indent=2)

            # Create python config
            python_dir = config_dir / "python"
            python_dir.mkdir()
            python_config = {
                "python": {
                    "file_patterns": {
                        "test_files": {
                            "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                            "contest_current": ["test/"],
                            "contest_stock": ["test/"]
                        },
                        "contest_files": {
                            "workspace": ["main.py", "*.py"],
                            "contest_current": ["main.py"],
                            "contest_stock": ["main.py", "*.py"]
                        }
                    }
                }
            }
            with open(python_dir / "env.json", 'w', encoding='utf-8') as f:
                json.dump(python_config, f, indent=2)

            yield str(config_dir)

    @pytest.fixture
    def loader(self, temp_config_dir):
        """Create JsonConfigLoader with temp config."""
        return JsonConfigLoader(temp_config_dir)

    def test_get_file_patterns_cpp(self, loader):
        """Test getting file patterns for cpp."""
        patterns = loader.get_file_patterns("cpp")

        assert "test_files" in patterns
        assert "contest_files" in patterns
        assert "build_files" in patterns

        # Check test_files patterns
        test_files = patterns["test_files"]
        assert "workspace" in test_files
        assert "contest_current" in test_files
        assert "contest_stock" in test_files
        assert "test/**/*.txt" in test_files["workspace"]
        assert "test/**/*.in" in test_files["workspace"]
        assert "test/**/*.out" in test_files["workspace"]

        # Check contest_files patterns
        contest_files = patterns["contest_files"]
        assert "main.cpp" in contest_files["workspace"]
        assert "*.h" in contest_files["workspace"]
        assert "*.hpp" in contest_files["workspace"]

    def test_get_file_patterns_python(self, loader):
        """Test getting file patterns for python."""
        patterns = loader.get_file_patterns("python")

        assert "test_files" in patterns
        assert "contest_files" in patterns
        assert "build_files" not in patterns  # Not defined for python

        contest_files = patterns["contest_files"]
        assert "main.py" in contest_files["workspace"]
        assert "*.py" in contest_files["workspace"]

    def test_get_file_patterns_nonexistent_language(self, loader):
        """Test getting file patterns for non-existent language."""
        patterns = loader.get_file_patterns("nonexistent")

        assert patterns == {}

    def test_get_file_patterns_missing_file_patterns_key(self, temp_config_dir):
        """Test getting file patterns when file_patterns key is missing."""
        # Create config without file_patterns
        rust_dir = Path(temp_config_dir) / "rust"
        rust_dir.mkdir()
        rust_config = {
            "rust": {
                "other_config": "value"
            }
        }
        with open(rust_dir / "env.json", 'w', encoding='utf-8') as f:
            json.dump(rust_config, f, indent=2)

        loader = JsonConfigLoader(temp_config_dir)
        patterns = loader.get_file_patterns("rust")

        assert patterns == {}

    def test_get_file_operations(self, loader):
        """Test getting file operations from shared config."""
        operations = loader.get_file_operations()

        assert "move_test_files" in operations
        assert "cleanup_workspace" in operations

        move_test_files = operations["move_test_files"]
        assert len(move_test_files) == 2
        assert move_test_files[0] == ["workspace.test_files", "contest_current.test_files"]
        assert move_test_files[1] == ["workspace.contest_files", "contest_stock.contest_files"]

        cleanup_workspace = operations["cleanup_workspace"]
        assert len(cleanup_workspace) == 1
        assert cleanup_workspace[0] == ["workspace.temp_files", "contest_stock.temp_files"]

    def test_get_file_operations_missing_shared_config(self):
        """Test getting file operations when shared config is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "contest_env"
            config_dir.mkdir()

            loader = JsonConfigLoader(str(config_dir))
            operations = loader.get_file_operations()

            assert operations == {}

    def test_get_file_operations_missing_file_operations_key(self, temp_config_dir):
        """Test getting file operations when file_operations key is missing."""
        # Overwrite shared config without file_operations
        shared_dir = Path(temp_config_dir) / "shared"
        shared_config = {
            "shared": {
                "other_config": "value"
            }
        }
        with open(shared_dir / "env.json", 'w', encoding='utf-8') as f:
            json.dump(shared_config, f, indent=2)

        loader = JsonConfigLoader(temp_config_dir)
        operations = loader.get_file_operations()

        assert operations == {}

    def test_get_default_patterns(self, loader):
        """Test getting default patterns from shared config."""
        default_patterns = loader.get_default_patterns()

        assert "test_files" in default_patterns
        test_files = default_patterns["test_files"]
        assert "workspace" in test_files
        assert "contest_current" in test_files
        assert "contest_stock" in test_files
        assert "test/**/*.txt" in test_files["workspace"]

    def test_get_default_patterns_missing(self, temp_config_dir):
        """Test getting default patterns when not defined."""
        # Overwrite shared config without default_patterns
        shared_dir = Path(temp_config_dir) / "shared"
        shared_config = {
            "shared": {
                "file_operations": {}
            }
        }
        with open(shared_dir / "env.json", 'w', encoding='utf-8') as f:
            json.dump(shared_config, f, indent=2)

        loader = JsonConfigLoader(temp_config_dir)
        default_patterns = loader.get_default_patterns()

        assert default_patterns == {}

    def test_has_file_patterns_support(self, loader):
        """Test checking if language has file patterns support."""
        assert loader.has_file_patterns_support("cpp") is True
        assert loader.has_file_patterns_support("python") is True
        assert loader.has_file_patterns_support("nonexistent") is False

    def test_has_file_patterns_support_partial(self, temp_config_dir):
        """Test checking file patterns support with partial config."""
        # Create language config without file_patterns
        rust_dir = Path(temp_config_dir) / "rust"
        rust_dir.mkdir()
        rust_config = {
            "rust": {
                "other_config": "value"
            }
        }
        with open(rust_dir / "env.json", 'w', encoding='utf-8') as f:
            json.dump(rust_config, f, indent=2)

        loader = JsonConfigLoader(temp_config_dir)
        assert loader.has_file_patterns_support("rust") is False

    def test_get_supported_languages(self, loader):
        """Test getting list of languages with file patterns support."""
        supported = loader.get_supported_languages()

        assert "cpp" in supported
        assert "python" in supported
        assert "shared" not in supported  # shared is not a language

    def test_get_supported_languages_empty_config(self):
        """Test getting supported languages with empty config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "contest_env"
            config_dir.mkdir()

            loader = JsonConfigLoader(str(config_dir))
            supported = loader.get_supported_languages()

            assert supported == []

    def test_integration_with_existing_methods(self, loader):
        """Test that new methods work with existing JsonConfigLoader functionality."""
        # Test that existing methods still work
        env_config = loader.get_env_config()
        assert "shared" in env_config
        assert "cpp" in env_config
        assert "python" in env_config

        # Test language-specific config still works
        cpp_config = loader.get_language_config("cpp")
        assert "file_patterns" in cpp_config

        # Test shared config still works
        shared_config = loader.get_shared_config()
        assert "file_operations" in shared_config

    def test_error_handling_corrupted_json(self, temp_config_dir):
        """Test error handling with corrupted JSON files."""
        # Corrupt the cpp config file
        cpp_dir = Path(temp_config_dir) / "cpp"
        with open(cpp_dir / "env.json", 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')  # Invalid JSON

        loader = JsonConfigLoader(temp_config_dir)

        # Should handle corrupted file gracefully
        patterns = loader.get_file_patterns("cpp")
        assert patterns == {}

        # Other languages should still work
        patterns = loader.get_file_patterns("python")
        assert len(patterns) > 0

    def test_error_handling_missing_directory(self):
        """Test error handling with missing config directory."""
        loader = JsonConfigLoader("/nonexistent/path")

        patterns = loader.get_file_patterns("cpp")
        assert patterns == {}

        operations = loader.get_file_operations()
        assert operations == {}

        supported = loader.get_supported_languages()
        assert supported == []

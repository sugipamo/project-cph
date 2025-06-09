"""Tests for configuration parser pure functions."""
from src.workflow.preparation.file.config_parser import create_folder_mapper_config


class TestCreateFolderMapperConfig:
    """Test create_folder_mapper_config function."""

    def test_extract_language_specific_paths(self):
        """Test extraction of language-specific paths."""
        env_json = {
            "languages": {
                "python": {
                    "paths": {
                        "contest_current_path": "/python/current",
                        "workspace_path": "/python/workspace"
                    }
                }
            }
        }

        result = create_folder_mapper_config(env_json, "python")

        assert result["contest_current_path"] == "/python/current"
        assert result["workspace_path"] == "/python/workspace"

    def test_fallback_to_shared_paths(self):
        """Test fallback to shared paths when language-specific not available."""
        env_json = {
            "languages": {
                "python": {
                    "paths": {
                        "contest_current_path": "/python/current"
                    }
                }
            },
            "shared": {
                "paths": {
                    "workspace_path": "/shared/workspace",
                    "contest_template_path": "/shared/templates"
                }
            }
        }

        result = create_folder_mapper_config(env_json, "python")

        assert result["contest_current_path"] == "/python/current"
        assert result["workspace_path"] == "/shared/workspace"
        assert result["contest_template_path"] == "/shared/templates"

    def test_language_specific_overrides_shared(self):
        """Test that language-specific paths override shared paths."""
        env_json = {
            "languages": {
                "python": {
                    "paths": {
                        "workspace_path": "/python/workspace"
                    }
                }
            },
            "shared": {
                "paths": {
                    "workspace_path": "/shared/workspace"
                }
            }
        }

        result = create_folder_mapper_config(env_json, "python")

        assert result["workspace_path"] == "/python/workspace"

    def test_empty_config(self):
        """Test handling of empty configuration."""
        env_json = {}

        result = create_folder_mapper_config(env_json, "python")

        assert result == {}

    def test_missing_language(self):
        """Test handling of missing language configuration."""
        env_json = {
            "languages": {
                "cpp": {
                    "paths": {
                        "workspace_path": "/cpp/workspace"
                    }
                }
            }
        }

        result = create_folder_mapper_config(env_json, "python")

        assert result == {}

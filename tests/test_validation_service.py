"""Tests for ValidationService."""
import pytest
from src.application.services.validation_service import ValidationService


class TestValidationService:
    """Test cases for ValidationService."""

    def test_validate_env_json_valid_single_language(self):
        """Test validation with a valid single language configuration."""
        data = {
            "python": {
                "version": "3.9",
                "packages": ["numpy", "pandas"]
            }
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_valid_multiple_languages(self):
        """Test validation with multiple language configurations."""
        data = {
            "python": {
                "version": "3.9",
                "packages": ["numpy"]
            },
            "javascript": {
                "version": "18",
                "packages": ["express"]
            },
            "shared": {
                "timeout": 30
            }
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_with_shared_configs(self):
        """Test validation with various shared configuration keys."""
        data = {
            "python": {"version": "3.9"},
            "shared": {"timeout": 30},
            "__common__": {"memory": "512MB"},
            "common": {"cpu": 2},
            "base": {"network": "bridge"}
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_invalid_root_not_dict(self):
        """Test validation fails when root is not a dictionary."""
        data = ["not", "a", "dict"]
        
        with pytest.raises(ValueError, match="root must be a dictionary"):
            ValidationService.validate_env_json(data, "/test/env.json", None)

    def test_validate_env_json_no_languages(self):
        """Test validation fails when no language configurations are present."""
        data = {
            "shared": {"timeout": 30},
            "__common__": {"memory": "512MB"}
        }
        
        with pytest.raises(ValueError, match="No language configurations found"):
            ValidationService.validate_env_json(data, "/test/env.json", None)

    def test_validate_env_json_empty_dict(self):
        """Test validation fails for empty dictionary."""
        data = {}
        
        with pytest.raises(ValueError, match="No language configurations found"):
            ValidationService.validate_env_json(data, "/test/env.json", None)

    def test_validate_env_json_invalid_language_config_not_dict(self):
        """Test validation fails when language configuration is not a dictionary."""
        data = {
            "python": {"version": "3.9"},
            "javascript": "not a dict"
        }
        
        with pytest.raises(ValueError, match="Language configuration for 'javascript'.*must be a dictionary"):
            ValidationService.validate_env_json(data, "/test/env.json", None)

    def test_validate_env_json_mixed_valid_invalid_languages(self):
        """Test validation fails when one language config is invalid."""
        data = {
            "python": {"version": "3.9"},
            "javascript": {"version": "18"},
            "ruby": ["not", "a", "dict"]
        }
        
        with pytest.raises(ValueError, match="Language configuration for 'ruby'.*must be a dictionary"):
            ValidationService.validate_env_json(data, "/test/env.json", None)

    def test_validate_env_json_with_shared_config_parameter(self):
        """Test validation with shared_config parameter (currently unused)."""
        data = {
            "python": {"version": "3.9"}
        }
        shared_config = {"global_timeout": 60}
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", shared_config)
        assert result is True

    def test_validate_env_json_complex_language_configs(self):
        """Test validation with complex nested language configurations."""
        data = {
            "python": {
                "version": "3.9",
                "packages": {
                    "numpy": "1.21.0",
                    "pandas": "1.3.0"
                },
                "settings": {
                    "debug": True,
                    "optimization": {
                        "level": 2,
                        "cache": True
                    }
                }
            },
            "shared": {
                "environment": {
                    "NODE_ENV": "production"
                }
            }
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_language_with_empty_dict(self):
        """Test validation with language having empty configuration."""
        data = {
            "python": {}  # Empty but still valid dict
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_path_in_error_message(self):
        """Test that the path is included in error messages."""
        data = {
            "python": "invalid"
        }
        
        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "/specific/path/env.json", None)
        
        assert "/specific/path/env.json" in str(exc_info.value)

    def test_validate_env_json_none_values(self):
        """Test validation with None values in language config."""
        data = {
            "python": {
                "version": None,
                "packages": None
            }
        }
        
        # Should pass - None values are valid within a dict
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True

    def test_validate_env_json_numeric_values(self):
        """Test validation with numeric values in configuration."""
        data = {
            "python": {
                "version": 3.9,  # numeric instead of string
                "workers": 4,
                "memory_mb": 1024
            }
        }
        
        result = ValidationService.validate_env_json(data, "/path/to/env.json", None)
        assert result is True
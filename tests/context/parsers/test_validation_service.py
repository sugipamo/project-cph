"""Tests for ValidationService"""

import pytest

from src.context.parsers.validation_service import ValidationService


class TestValidationService:
    """Test cases for ValidationService"""

    def test_validate_env_json_valid_basic(self):
        """Test validation with valid basic env.json"""
        data = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [{"type": "shell", "cmd": ["python", "main.py"]}]
                    }
                }
            }
        }

        result = ValidationService.validate_env_json(data, "test.json")
        assert result

    def test_validate_env_json_valid_with_shared(self):
        """Test validation with shared configuration"""
        data = {
            "shared": {
                "environment_logging": {"enabled": True}
            },
            "python": {
                "commands": {
                    "test": {
                        "steps": [{"type": "shell", "cmd": ["python", "main.py"]}]
                    }
                }
            }
        }
        shared_config = {"environment_logging": {"enabled": True}}

        result = ValidationService.validate_env_json(data, "test.json", shared_config)
        assert result

    def test_validate_env_json_multiple_languages(self):
        """Test validation with multiple language configurations"""
        data = {
            "python": {
                "commands": {
                    "test": {"steps": []}
                }
            },
            "cpp": {
                "commands": {
                    "compile": {"steps": []}
                }
            },
            "rust": {
                "commands": {
                    "build": {"steps": []}
                }
            }
        }

        result = ValidationService.validate_env_json(data, "test.json")
        assert result

    def test_validate_env_json_with_reserved_keys(self):
        """Test validation with reserved keys like shared, common, etc."""
        data = {
            "shared": {"config": "value"},
            "__common__": {"config": "value"},
            "common": {"config": "value"},
            "base": {"config": "value"},
            "python": {
                "commands": {
                    "test": {"steps": []}
                }
            }
        }

        result = ValidationService.validate_env_json(data, "test.json")
        assert result

    def test_validate_env_json_invalid_root_not_dict(self):
        """Test validation fails when root is not a dictionary"""
        data = "not a dictionary"

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "root must be a dictionary" in str(exc_info.value)
        assert "test.json" in str(exc_info.value)

    def test_validate_env_json_invalid_root_list(self):
        """Test validation fails when root is a list"""
        data = ["item1", "item2"]

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "root must be a dictionary" in str(exc_info.value)

    def test_validate_env_json_invalid_no_languages(self):
        """Test validation fails when no language configurations are found"""
        data = {
            "shared": {"config": "value"},
            "__common__": {"config": "value"},
            "common": {"config": "value"},
            "base": {"config": "value"}
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "No language configurations found" in str(exc_info.value)
        assert "test.json" in str(exc_info.value)

    def test_validate_env_json_invalid_empty_dict(self):
        """Test validation fails with empty dictionary"""
        data = {}

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "No language configurations found" in str(exc_info.value)

    def test_validate_env_json_invalid_language_not_dict(self):
        """Test validation fails when language config is not a dictionary"""
        data = {
            "python": "not a dictionary"
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "Language configuration for 'python'" in str(exc_info.value)
        assert "must be a dictionary" in str(exc_info.value)
        assert "test.json" in str(exc_info.value)

    def test_validate_env_json_invalid_language_list(self):
        """Test validation fails when language config is a list"""
        data = {
            "python": ["item1", "item2"]
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "Language configuration for 'python'" in str(exc_info.value)
        assert "must be a dictionary" in str(exc_info.value)

    def test_validate_env_json_invalid_language_number(self):
        """Test validation fails when language config is a number"""
        data = {
            "python": 123
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "Language configuration for 'python'" in str(exc_info.value)
        assert "must be a dictionary" in str(exc_info.value)

    def test_validate_env_json_mixed_valid_invalid_languages(self):
        """Test validation fails when some language configs are invalid"""
        data = {
            "python": {
                "commands": {"test": {"steps": []}}
            },
            "cpp": "invalid config",
            "rust": {
                "commands": {"build": {"steps": []}}
            }
        }

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, "test.json")

        assert "Language configuration for 'cpp'" in str(exc_info.value)
        assert "must be a dictionary" in str(exc_info.value)

    def test_validate_env_json_path_in_error_messages(self):
        """Test that the file path is included in error messages"""
        data = {"python": "invalid"}
        path = "/path/to/env.json"

        with pytest.raises(ValueError) as exc_info:
            ValidationService.validate_env_json(data, path)

        assert path in str(exc_info.value)

    def test_validate_env_json_special_language_names(self):
        """Test validation with special language names"""
        data = {
            "python3.12": {
                "commands": {"test": {"steps": []}}
            },
            "c++17": {
                "commands": {"compile": {"steps": []}}
            },
            "node-v18": {
                "commands": {"run": {"steps": []}}
            }
        }

        result = ValidationService.validate_env_json(data, "test.json")
        assert result

    def test_validate_env_json_case_sensitivity(self):
        """Test validation with case-sensitive language names"""
        data = {
            "Python": {
                "commands": {"test": {"steps": []}}
            },
            "CPP": {
                "commands": {"compile": {"steps": []}}
            }
        }

        result = ValidationService.validate_env_json(data, "test.json")
        assert result

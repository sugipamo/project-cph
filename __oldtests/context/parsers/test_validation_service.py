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

        result = ValidationService.validate_env_json(data, "test.json", None)
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

        result = ValidationService.validate_env_json(data, "test.json", None)
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

        result = ValidationService.validate_env_json(data, "test.json", None)
        assert result










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

        result = ValidationService.validate_env_json(data, "test.json", None)
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

        result = ValidationService.validate_env_json(data, "test.json", None)
        assert result

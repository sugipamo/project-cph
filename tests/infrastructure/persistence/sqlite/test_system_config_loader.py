"""Tests for SystemConfigLoader class."""
from unittest.mock import MagicMock, Mock

import pytest

from src.infrastructure.di_container import DIKey
from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader


class TestSystemConfigLoader:
    """Test cases for SystemConfigLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_container = Mock()
        self.mock_config_repo = Mock()
        self.loader = SystemConfigLoader(self.mock_container)

    def test_init(self):
        """Test SystemConfigLoader initialization."""
        assert self.loader.container == self.mock_container
        assert self.loader._config_repo is None

    def test_config_repo_property_lazy_loading(self):
        """Test config_repo property lazy loading."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        # First access should trigger resolve
        result = self.loader.config_repo

        assert result == self.mock_config_repo
        self.mock_container.resolve.assert_called_once_with(DIKey.SYSTEM_CONFIG_REPOSITORY)

        # Second access should use cached value
        result2 = self.loader.config_repo
        assert result2 == self.mock_config_repo
        # Should still be called only once
        assert self.mock_container.resolve.call_count == 1

    def test_load_config_basic(self):
        """Test load_config method with basic configuration."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        # Mock basic config values
        self.mock_config_repo.get_config.side_effect = lambda key: {
            "command": "build",
            "language": "cpp",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "A",
            "docker": {"enabled": True},
            "output": {"format": "json"}
        }.get(key)

        # Mock language configs
        self.mock_config_repo.get_configs_by_category.return_value = [
            {"config_key": "language.cpp", "config_value": {"compiler": "g++"}},
            {"config_key": "language.python", "config_value": {"interpreter": "python3"}}
        ]

        config = self.loader.load_config()

        assert config["command"] == "build"
        assert config["language"] == "cpp"
        assert config["env_type"] == "local"
        assert config["contest_name"] == "abc123"
        assert config["problem_name"] == "A"
        assert config["docker"] == {"enabled": True}
        assert config["output"] == {"format": "json"}
        assert "env_json" in config
        assert config["env_json"]["cpp"] == {"compiler": "g++"}
        assert config["env_json"]["python"] == {"interpreter": "python3"}

    def test_load_config_with_none_values(self):
        """Test load_config method with None values."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        # Mock with None values
        self.mock_config_repo.get_config.return_value = None
        self.mock_config_repo.get_configs_by_category.return_value = []

        config = self.loader.load_config()

        assert config["command"] is None
        assert config["language"] is None
        assert config["env_type"] is None
        assert config["contest_name"] is None
        assert config["problem_name"] is None
        assert config["env_json"] == {}

    def test_load_config_with_nested_language_keys(self):
        """Test load_config with nested language configuration keys."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.return_value = None

        # Mock language configs with nested keys (should be ignored)
        self.mock_config_repo.get_configs_by_category.return_value = [
            {"config_key": "language.cpp", "config_value": {"compiler": "g++"}},
            {"config_key": "language.cpp.flags", "config_value": ["-std=c++17"]},  # Should be ignored
            {"config_key": "language.python", "config_value": {"interpreter": "python3"}}
        ]

        config = self.loader.load_config()

        # Only top-level language configs should be included
        assert len(config["env_json"]) == 2
        assert "cpp" in config["env_json"]
        assert "python" in config["env_json"]

    def test_get_env_config_with_data(self):
        """Test get_env_config method with language data."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_configs_by_category.return_value = [
            {"config_key": "language.cpp", "config_value": {"compiler": "g++"}},
            {"config_key": "language.python", "config_value": {"interpreter": "python3"}}
        ]

        env_config = self.loader.get_env_config()

        assert env_config["cpp"] == {"compiler": "g++"}
        assert env_config["python"] == {"interpreter": "python3"}

    def test_get_env_config_empty_fallback(self):
        """Test get_env_config method with empty data fallback."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_configs_by_category.return_value = []

        env_config = self.loader.get_env_config()

        # Should return default structure
        assert env_config == {
            "cpp": {},
            "python": {},
            "rust": {}
        }

    def test_save_config(self):
        """Test save_config method."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.loader.save_config("test_key", "test_value", "test_category")

        self.mock_config_repo.set_config.assert_called_once_with(
            "test_key", "test_value", "test_category"
        )

    def test_save_config_without_category(self):
        """Test save_config method without category."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.loader.save_config("test_key", "test_value")

        self.mock_config_repo.set_config.assert_called_once_with(
            "test_key", "test_value", None
        )

    def test_get_current_context(self):
        """Test get_current_context method."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.side_effect = lambda key: {
            "command": "test",
            "language": "cpp",
            "env_type": "docker",
            "contest_name": "abc123",
            "problem_name": "A"
        }.get(key)

        context = self.loader.get_current_context()

        expected_context = {
            "command": "test",
            "language": "cpp",
            "env_type": "docker",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        assert context == expected_context

    def test_get_user_specified_context(self):
        """Test get_user_specified_context method."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        expected_context = {"language": "cpp", "contest_name": "abc123"}
        self.mock_config_repo.get_user_specified_configs.return_value = expected_context

        context = self.loader.get_user_specified_context()

        assert context == expected_context
        self.mock_config_repo.get_user_specified_configs.assert_called_once()

    def test_get_context_summary(self):
        """Test get_context_summary method."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        expected_summary = {
            "command": {"value": "test", "user_specified": True},
            "language": {"value": "cpp", "user_specified": False}
        }
        self.mock_config_repo.get_execution_context_summary.return_value = expected_summary

        summary = self.loader.get_context_summary()

        assert summary == expected_summary
        self.mock_config_repo.get_execution_context_summary.assert_called_once()

    def test_update_current_context_all_params(self):
        """Test update_current_context with all parameters."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        # Mock getting old values
        self.mock_config_repo.get_config.side_effect = lambda key: {
            "contest_name": "old_contest",
            "problem_name": "old_problem"
        }.get(key)

        self.loader.update_current_context(
            contest_name="new_contest",
            problem_name="new_problem",
            language="python",
            command="build",
            env_type="docker"
        )

        # Check that old values were saved and new values were set
        expected_calls = [
            (("old_contest_name", "old_contest"), {}),
            (("contest_name", "new_contest"), {}),
            (("old_problem_name", "old_problem"), {}),
            (("problem_name", "new_problem"), {}),
            (("language", "python"), {}),
            (("command", "build"), {}),
            (("env_type", "docker"), {})
        ]

        assert self.mock_config_repo.set_config.call_count == 7
        for i, (expected_args, expected_kwargs) in enumerate(expected_calls):
            actual_call = self.mock_config_repo.set_config.call_args_list[i]
            assert actual_call[0] == expected_args
            assert actual_call[1] == expected_kwargs

    def test_update_current_context_partial_params(self):
        """Test update_current_context with partial parameters."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.return_value = None

        self.loader.update_current_context(language="rust")

        self.mock_config_repo.set_config.assert_called_once_with("language", "rust")

    def test_update_current_context_with_old_values(self):
        """Test update_current_context saves old values when they exist."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.side_effect = lambda key: {
            "contest_name": "existing_contest"
        }.get(key)

        self.loader.update_current_context(contest_name="new_contest")

        # Should save old value and set new value
        expected_calls = [
            (("old_contest_name", "existing_contest"), {}),
            (("contest_name", "new_contest"), {})
        ]

        assert self.mock_config_repo.set_config.call_count == 2
        for i, (expected_args, _expected_kwargs) in enumerate(expected_calls):
            actual_call = self.mock_config_repo.set_config.call_args_list[i]
            assert actual_call[0] == expected_args

    def test_clear_context_value(self):
        """Test clear_context_value method."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.loader.clear_context_value("test_key")

        self.mock_config_repo.set_config.assert_called_once_with("test_key", None)

    def test_has_user_specified_true(self):
        """Test has_user_specified method when value exists."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.return_value = "some_value"

        result = self.loader.has_user_specified("test_key")

        assert result is True
        self.mock_config_repo.get_config.assert_called_once_with("test_key")

    def test_has_user_specified_false(self):
        """Test has_user_specified method when value is None."""
        self.mock_container.resolve.return_value = self.mock_config_repo

        self.mock_config_repo.get_config.return_value = None

        result = self.loader.has_user_specified("test_key")

        assert result is False
        self.mock_config_repo.get_config.assert_called_once_with("test_key")

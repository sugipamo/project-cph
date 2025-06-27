import pytest
from unittest.mock import Mock, MagicMock
from src.configuration.system_config_loader import SystemConfigLoader
from src.infrastructure.di_container import DIKey


class MockConfigRepository:
    """Mock configuration repository for testing"""
    def __init__(self):
        self.configs = {}
        self.category_configs = {}
        
    def get_config(self, key):
        return self.configs.get(key)
        
    def set_config(self, key, value, category=None, description=None):
        self.configs[key] = value
        if category:
            if category not in self.category_configs:
                self.category_configs[category] = []
            self.category_configs[category].append({
                "config_key": key,
                "config_value": value,
                "category": category,
                "description": description
            })
            
    def get_configs_by_category(self, category):
        return self.category_configs.get(category, [])
        
    def get_user_specified_configs(self):
        return {k: v for k, v in self.configs.items() if v is not None}
        
    def get_execution_context_summary(self):
        context_keys = ["command", "language", "env_type", "contest_name", "problem_name"]
        summary = {}
        for key in context_keys:
            value = self.configs.get(key)
            summary[key] = {
                "value": value,
                "specified": value is not None
            }
        return summary


class TestSystemConfigLoader:
    @pytest.fixture
    def mock_container(self):
        container = Mock()
        mock_repo = MockConfigRepository()
        container.resolve.return_value = mock_repo
        return container, mock_repo
        
    def test_init(self, mock_container):
        container, _ = mock_container
        loader = SystemConfigLoader(container)
        assert loader.container == container
        assert loader._config_repo is None
        
    def test_config_repo_lazy_load(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # First access triggers loading
        repo = loader.config_repo
        assert repo == mock_repo
        container.resolve.assert_called_once_with(DIKey.SYSTEM_CONFIG_REPOSITORY)
        
        # Second access uses cached value
        repo2 = loader.config_repo
        assert repo2 == mock_repo
        assert container.resolve.call_count == 1
        
    def test_load_config_basic(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set up test data
        mock_repo.set_config("command", "run")
        mock_repo.set_config("language", "python")
        mock_repo.set_config("env_type", "local")
        mock_repo.set_config("contest_name", "abc123")
        mock_repo.set_config("problem_name", "A")
        
        config = loader.load_config()
        
        assert config["command"] == "run"
        assert config["language"] == "python"
        assert config["env_type"] == "local"
        assert config["contest_name"] == "abc123"
        assert config["problem_name"] == "A"
        assert "env_json" in config
        
    def test_load_config_with_language_configs(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set up language configurations
        mock_repo.set_config("language.python", {"run": "python3"}, "language")
        mock_repo.set_config("language.cpp", {"compile": "g++"}, "language")
        
        config = loader.load_config()
        
        assert config["env_json"]["python"] == {"run": "python3"}
        assert config["env_json"]["cpp"] == {"compile": "g++"}
        
    def test_load_config_with_docker_and_output(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        mock_repo.set_config("docker", {"image": "ubuntu:latest"})
        mock_repo.set_config("output", {"format": "json"})
        
        config = loader.load_config()
        
        assert config["docker"] == {"image": "ubuntu:latest"}
        assert config["output"] == {"format": "json"}
        
    def test_get_env_config(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set up language configurations
        mock_repo.set_config("language.rust", {"build": "cargo build"}, "language")
        mock_repo.set_config("language.python", {"run": "python3"}, "language")
        
        env_config = loader.get_env_config()
        
        assert env_config["rust"] == {"build": "cargo build"}
        assert env_config["python"] == {"run": "python3"}
        
    def test_get_env_config_default(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # No language configs set
        env_config = loader.get_env_config()
        
        # Should return default structure
        assert env_config == {
            "cpp": {},
            "python": {},
            "rust": {}
        }
        
    def test_save_config(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        loader.save_config("test_key", "test_value", "test_category")
        
        assert mock_repo.get_config("test_key") == "test_value"
        assert len(mock_repo.get_configs_by_category("test_category")) == 1
        
    def test_get_current_context(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set up context
        mock_repo.set_config("command", "test")
        mock_repo.set_config("language", "cpp")
        mock_repo.set_config("env_type", "docker")
        mock_repo.set_config("contest_name", "abc200")
        mock_repo.set_config("problem_name", "B")
        
        context = loader.get_current_context()
        
        assert context == {
            "command": "test",
            "language": "cpp",
            "env_type": "docker",
            "contest_name": "abc200",
            "problem_name": "B"
        }
        
    def test_get_user_specified_context(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set some configs, leave others as None
        mock_repo.set_config("command", "run")
        mock_repo.set_config("language", None)
        mock_repo.set_config("contest_name", "abc300")
        
        user_specified = loader.get_user_specified_context()
        
        assert user_specified == {
            "command": "run",
            "contest_name": "abc300"
        }
        
    def test_get_context_summary(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set some configs
        mock_repo.set_config("command", "build")
        mock_repo.set_config("language", None)
        
        summary = loader.get_context_summary()
        
        assert summary["command"]["value"] == "build"
        assert summary["command"]["specified"] is True
        assert summary["language"]["value"] is None
        assert summary["language"]["specified"] is False
        
    def test_update_current_context(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set initial values
        mock_repo.set_config("contest_name", "old_contest")
        mock_repo.set_config("problem_name", "old_problem")
        
        # Update context
        loader.update_current_context(
            contest_name="new_contest",
            problem_name="new_problem",
            language="rust",
            command="submit",
            env_type="local"
        )
        
        # Check new values
        assert mock_repo.get_config("contest_name") == "new_contest"
        assert mock_repo.get_config("problem_name") == "new_problem"
        assert mock_repo.get_config("language") == "rust"
        assert mock_repo.get_config("command") == "submit"
        assert mock_repo.get_config("env_type") == "local"
        
        # Check old values were saved
        assert mock_repo.get_config("old_contest_name") == "old_contest"
        assert mock_repo.get_config("old_problem_name") == "old_problem"
        
    def test_update_current_context_partial(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Update only some values
        loader.update_current_context(
            contest_name="abc400",
            problem_name=None,
            language=None,
            command="test",
            env_type=None
        )
        
        assert mock_repo.get_config("contest_name") == "abc400"
        assert mock_repo.get_config("command") == "test"
        
    def test_clear_context_value(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set a value
        mock_repo.set_config("test_key", "test_value")
        assert mock_repo.get_config("test_key") == "test_value"
        
        # Clear it
        loader.clear_context_value("test_key")
        assert mock_repo.get_config("test_key") is None
        
    def test_has_user_specified(self, mock_container):
        container, mock_repo = mock_container
        loader = SystemConfigLoader(container)
        
        # Set one value, leave another as None
        mock_repo.set_config("specified_key", "value")
        mock_repo.set_config("unspecified_key", None)
        
        assert loader.has_user_specified("specified_key") is True
        assert loader.has_user_specified("unspecified_key") is False
        assert loader.has_user_specified("nonexistent_key") is False
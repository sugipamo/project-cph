"""System configuration loader for SQLite-based configuration management."""
from typing import Any, Dict, Optional

from src.infrastructure.di_container import DIKey


class SystemConfigLoader:
    """Loads system configuration from SQLite."""

    def __init__(self, container):
        """Initialize with DI container."""
        self.container = container
        self._config_repo = None

    @property
    def config_repo(self):
        """Lazy load config repository."""
        if self._config_repo is None:
            self._config_repo = self.container.resolve(DIKey.SYSTEM_CONFIG_REPOSITORY)
        return self._config_repo

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from SQLite.

        Returns:
            Dictionary containing full system configuration
        """
        # Build configuration from SQLite
        config = {}

        # Get execution context
        config["command"] = self.config_repo.get_config("command")
        config["language"] = self.config_repo.get_config("language")
        config["env_type"] = self.config_repo.get_config("env_type")
        config["contest_name"] = self.config_repo.get_config("contest_name")
        config["problem_name"] = self.config_repo.get_config("problem_name")

        # Get language configurations
        env_json = {}
        for lang_config in self.config_repo.get_configs_by_category("language"):
            key = lang_config["config_key"]
            if key.startswith("language.") and key.count(".") == 1:
                # This is a top-level language config
                lang_name = key.split(".", 1)[1]
                env_json[lang_name] = lang_config["config_value"]

        if env_json:
            config["env_json"] = env_json

        # Get Docker configuration
        docker_config = self.config_repo.get_config("docker")
        if docker_config:
            config["docker"] = docker_config

        # Get output configuration
        output_config = self.config_repo.get_config("output")
        if output_config:
            config["output"] = output_config

        return config

    def save_config(self, key: str, value: Any, category: Optional[str] = None) -> None:
        """Save a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            category: Optional category for grouping
        """
        self.config_repo.set_config(key, value, category)

    def get_current_context(self) -> Dict[str, Any]:
        """Get current execution context."""
        return {
            "command": self.config_repo.get_config("command"),
            "language": self.config_repo.get_config("language"),
            "env_type": self.config_repo.get_config("env_type"),
            "contest_name": self.config_repo.get_config("contest_name"),
            "problem_name": self.config_repo.get_config("problem_name"),
        }

    def update_current_context(self, **kwargs) -> None:
        """Update current execution context."""
        if "command" in kwargs:
            self.save_config("command", kwargs["command"], "execution")
        if "language" in kwargs:
            self.save_config("language", kwargs["language"], "execution")
        if "env_type" in kwargs:
            self.save_config("env_type", kwargs["env_type"], "execution")
        if "contest_name" in kwargs:
            self.save_config("contest_name", kwargs["contest_name"], "contest")
        if "problem_name" in kwargs:
            self.save_config("problem_name", kwargs["problem_name"], "contest")

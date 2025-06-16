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

    def get_env_config(self) -> Dict[str, Any]:
        """Get environment configuration (env.json equivalent)."""
        env_config = {}

        # Get language configurations
        for lang_config in self.config_repo.get_configs_by_category("language"):
            key = lang_config["config_key"]
            if key.startswith("language.") and key.count(".") == 1:
                # This is a top-level language config
                lang_name = key.split(".", 1)[1]
                env_config[lang_name] = lang_config["config_value"]

        # If no language configs found, return default structure
        if not env_config:
            env_config = {
                "cpp": {},
                "python": {},
                "rust": {}
            }

        return env_config

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

    def get_user_specified_context(self) -> Dict[str, Any]:
        """Get only user-specified execution context values."""
        return self.config_repo.get_user_specified_configs()

    def get_context_summary(self) -> Dict[str, Any]:
        """Get execution context with specification status."""
        return self.config_repo.get_execution_context_summary()

    def update_current_context(self, contest_name: Optional[str] = None,
                              problem_name: Optional[str] = None,
                              language: Optional[str] = None,
                              command: Optional[str] = None,
                              env_type: Optional[str] = None) -> None:
        """Update current execution context."""
        if contest_name is not None:
            # Save old contest name before updating
            old_contest = self.config_repo.get_config("contest_name")
            if old_contest:
                self.config_repo.set_config("old_contest_name", old_contest)
            self.config_repo.set_config("contest_name", contest_name)
        if problem_name is not None:
            # Save old problem name before updating
            old_problem = self.config_repo.get_config("problem_name")
            if old_problem:
                self.config_repo.set_config("old_problem_name", old_problem)
            self.config_repo.set_config("problem_name", problem_name)
        if language is not None:
            self.config_repo.set_config("language", language)
        if command is not None:
            self.config_repo.set_config("command", command)
        if env_type is not None:
            self.config_repo.set_config("env_type", env_type)

    def clear_context_value(self, key: str) -> None:
        """Clear a specific context value (set to NULL)."""
        self.config_repo.set_config(key, None)

    def has_user_specified(self, key: str) -> bool:
        """Check if a configuration was user-specified (not NULL)."""
        value = self.config_repo.get_config(key)
        return value is not None

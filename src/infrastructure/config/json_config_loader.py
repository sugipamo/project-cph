"""JSON-based configuration loader for environment files."""
import json
from pathlib import Path
from typing import Any, Dict


class JsonConfigLoader:
    """Loads configuration from JSON files in contest_env directory."""

    def __init__(self, base_path: str = "./contest_env"):
        """Initialize with base path to configuration directory.

        Args:
            base_path: Path to contest_env directory
        """
        self.base_path = Path(base_path)

    def get_env_config(self) -> Dict[str, Any]:
        """Load environment configuration from JSON files.

        Returns:
            Dictionary containing merged configuration from all env.json files
        """
        config = {}

        # Load shared configuration first
        shared_config = self._load_config_file("shared")
        if shared_config:
            config.update(shared_config)

        # Load language-specific configurations
        for lang_dir in self.base_path.iterdir():
            if lang_dir.is_dir() and lang_dir.name != "shared":
                lang_config = self._load_config_file(lang_dir.name)
                if lang_config:
                    config.update(lang_config)

        return config

    def _load_config_file(self, subdir: str) -> Dict[str, Any]:
        """Load configuration from a specific subdirectory.

        Args:
            subdir: Subdirectory name (e.g., 'python', 'shared')

        Returns:
            Dictionary with configuration data or empty dict if file doesn't exist
        """
        config_file = self.base_path / subdir / "env.json"

        if not config_file.exists():
            return {}

        try:
            with open(config_file, encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load {config_file}: {e}")
            return {}

    def get_paths_for_language(self, language: str) -> Dict[str, str]:
        """Get path configuration for a specific language.

        Args:
            language: Language name (e.g., 'python')

        Returns:
            Dictionary of path configurations
        """
        config = self.get_env_config()

        # Start with shared paths
        paths = {}
        if "shared" in config and "paths" in config["shared"]:
            paths.update(config["shared"]["paths"])

        # Override with language-specific paths if they exist
        if language in config and "paths" in config[language]:
            paths.update(config[language]["paths"])

        return paths

    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get full configuration for a specific language.

        Args:
            language: Language name

        Returns:
            Dictionary with language configuration
        """
        config = self.get_env_config()
        return config.get(language, {})

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

    def get_shared_config(self) -> Dict[str, Any]:
        """Get shared configuration from shared/env.json.

        Returns:
            Dictionary with shared configuration
        """
        return self._load_config_file("shared").get("shared", {})

    def get_constants(self) -> Dict[str, Any]:
        """Get constants from shared configuration.

        Returns:
            Dictionary with constants configuration
        """
        shared_config = self.get_shared_config()
        return shared_config.get("constants", {})

    def get_constant_value(self, category: str, key: str, default: Any = None) -> Any:
        """Get a specific constant value.

        Args:
            category: Constant category (e.g., 'directories', 'operation_types')
            key: Constant key within category
            default: Default value if not found

        Returns:
            Constant value or default
        """
        constants = self.get_constants()
        return constants.get(category, {}).get(key, default)

    def get_directory_name(self, key: str) -> str:
        """Get directory name constant.

        DEPRECATED: Use DirectoryName enum instead.

        Args:
            key: Directory key (e.g., 'test', 'workspace')

        Returns:
            Directory name
        """
        from src.domain.constants.operation_type import DirectoryName

        # Map keys to enum values
        directory_map = {
            'test': DirectoryName.TEST.value,
            'template': DirectoryName.TEMPLATE.value,
            'stock': DirectoryName.STOCK.value,
            'current': DirectoryName.CURRENT.value,
            'workspace': DirectoryName.WORKSPACE.value,
            'contest_env': DirectoryName.CONTEST_ENV.value,
        }
        return directory_map.get(key, key)

    def get_operation_type(self, key: str) -> str:
        """Get operation type constant.

        DEPRECATED: Use WorkspaceOperationType enum instead.

        Args:
            key: Operation key (e.g., 'move_test_files')

        Returns:
            Operation type string
        """
        from src.domain.constants.operation_type import WorkspaceOperationType

        # Map keys to enum values
        operation_map = {
            'workspace_switch': WorkspaceOperationType.WORKSPACE_SWITCH.value,
            'move_test_files': WorkspaceOperationType.MOVE_TEST_FILES.value,
            'cleanup_workspace': WorkspaceOperationType.CLEANUP_WORKSPACE.value,
            'archive_current': WorkspaceOperationType.ARCHIVE_CURRENT.value,
        }
        return operation_map.get(key, key)

    def get_message(self, key: str) -> str:
        """Get message constant.

        Args:
            key: Message key

        Returns:
            Message string
        """
        return self.get_constant_value("messages", key, key)

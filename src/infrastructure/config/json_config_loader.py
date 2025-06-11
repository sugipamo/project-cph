"""JSON-based configuration loader for environment files."""
import json
from pathlib import Path
from typing import Any, Dict, List


class JsonConfigLoader:
    """Loads configuration from JSON files in contest_env directory and system config."""

    def __init__(self, base_path: str = "./contest_env", system_config_path: str = "./config/system"):
        """Initialize with base path to configuration directory.

        Args:
            base_path: Path to contest_env directory
            system_config_path: Path to system configuration directory
        """
        self.base_path = Path(base_path)
        self.system_config_path = Path(system_config_path)

    def get_env_config(self) -> Dict[str, Any]:
        """Load environment configuration from JSON files.

        Returns:
            Dictionary containing merged configuration from all env.json files and system config
        """
        config = {}

        # Load system configuration first (lowest priority)
        system_config = self._load_system_config()
        if system_config:
            config = self._deep_merge(config, system_config)

        # Check if base path exists
        if not self.base_path.exists():
            return config

        # Load shared configuration
        shared_config = self._load_config_file("shared")
        if shared_config:
            config = self._deep_merge(config, shared_config)

        # Load language-specific configurations (highest priority)
        try:
            for lang_dir in self.base_path.iterdir():
                if lang_dir.is_dir() and lang_dir.name != "shared":
                    lang_config = self._load_config_file(lang_dir.name)
                    if lang_config:
                        config = self._deep_merge(config, lang_config)
        except (OSError, PermissionError):
            # Handle cases where directory doesn't exist or can't be read
            pass

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

        Language configuration inherits from shared configuration as a base,
        with language-specific settings overriding shared ones.

        Args:
            language: Language name

        Returns:
            Dictionary with language configuration (shared + language-specific)
        """
        # Get shared configuration as base
        shared_config = self.get_shared_config()

        # Get language-specific configuration
        config = self.get_env_config()
        language_config = config.get(language, {})

        # Merge shared config as base with language config overriding
        return self._deep_merge(shared_config, language_config)

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

    def get_file_patterns(self, language: str) -> Dict[str, Dict[str, List[str]]]:
        """Get file patterns configuration for a specific language.

        Args:
            language: Language name (e.g., 'cpp', 'python')

        Returns:
            Dictionary containing file patterns for the language.
            Format: {pattern_group: {location: [patterns]}}
            where location is one of: workspace, contest_current, contest_stock
        """
        lang_config = self.get_language_config(language)
        return lang_config.get("file_patterns", {})

    def get_file_operations(self) -> Dict[str, List[List[str]]]:
        """Get file operations configuration from shared config.

        Returns:
            Dictionary containing file operations definitions.
            Format: {operation_name: [[source_ref, dest_ref], ...]}
            where references are in format "location.pattern_group"
        """
        shared_config = self.get_shared_config()
        return shared_config.get("file_operations", {})

    def get_default_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Get default file patterns from shared configuration.

        Returns:
            Dictionary containing default file patterns that can be
            used as fallback when language-specific patterns are not available.
        """
        shared_config = self.get_shared_config()
        return shared_config.get("default_patterns", {})

    def has_file_patterns_support(self, language: str) -> bool:
        """Check if a language has file patterns configuration.

        Args:
            language: Language name to check

        Returns:
            True if the language has file_patterns defined, False otherwise
        """
        patterns = self.get_file_patterns(language)
        return len(patterns) > 0

    def get_supported_languages(self) -> List[str]:
        """Get list of languages that have file patterns support.

        Returns:
            List of language names that have file_patterns defined
        """
        supported = []

        # Check if base path exists
        if not self.base_path.exists():
            return supported

        try:
            for lang_dir in self.base_path.iterdir():
                if lang_dir.is_dir() and lang_dir.name != "shared" and self.has_file_patterns_support(lang_dir.name):
                    supported.append(lang_dir.name)
        except (OSError, PermissionError):
            # Handle cases where directory doesn't exist or can't be read
            pass

        return supported

    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration from system config directory.

        Returns:
            Dictionary containing merged system configuration
        """
        system_config = {}

        if not self.system_config_path.exists():
            return system_config

        # Load all system config files
        system_files = [
            "docker_security.json",
            "docker_defaults.json",
            "system_constants.json",
            "dev_config.json"
        ]

        for config_file in system_files:
            file_path = self.system_config_path / config_file
            if file_path.exists():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        config_data = json.load(f)
                        # Merge system config data
                        system_config.update(config_data)
                except (OSError, json.JSONDecodeError) as e:
                    print(f"Warning: Failed to load system config {file_path}: {e}")

        # Wrap in 'shared' key to match expected structure
        return {"shared": system_config} if system_config else {}

    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with update_dict taking priority.

        Args:
            base_dict: The base dictionary
            update_dict: The dictionary to merge in (higher priority)

        Returns:
            A new dictionary with merged values
        """
        result = base_dict.copy()

        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

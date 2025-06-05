"""
env.json based execution context for eliminating hardcoded values
"""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.context.user_input_parser import _load_all_env_jsons
from src.context.resolver.config_resolver import (
    create_config_root_from_dict, 
    resolve_formatted_string,
    resolve_best
)
from src.context.utils.format_utils import format_with_context


@dataclass
class EnvJsonSettings:
    """Settings extracted from env.json configuration"""
    
    # Docker settings
    mount_path: str = "/workspace"
    working_directory: str = "/workspace"
    keep_alive_command: str = "tail -f /dev/null"
    default_shell: str = "bash"
    
    # Container settings
    memory_limit: str = "1GB"
    cpu_limit: str = "1.0"
    timeout_seconds: int = 300
    
    # Error patterns
    error_patterns: Dict[str, List[str]] = None
    
    # Retry settings
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_backoff: bool = True
    
    # State management
    state_directory: str = "~/.cph/state"
    state_file_format: str = "json"
    auto_backup: bool = True
    max_history: int = 100
    
    # Naming conventions
    container_prefix: str = "cph"
    oj_container_prefix: str = "cph_ojtools"
    separator: str = "_"
    image_tag_format: str = "{language}:latest"
    
    # Path settings
    container_root_path: str = "/"
    host_current_directory: str = "."
    path_separator: str = "/"
    temp_directory: str = "/tmp"
    workspace_alias: str = "./workspace"
    
    # Docker settings
    dockerfile_hash_length: int = 12
    custom_image_prefixes: List[str] = None
    known_registries: List[str] = None
    command_wrapper: str = "bash -c"
    invalid_path_chars: List[str] = None
    
    # Timeout settings
    process_termination_timeout: int = 3
    
    # Preparation actions
    remove_stopped_container_action: str = "remove_stopped_container"
    run_new_container_action: str = "run_new_container"
    create_directory_action: str = "create_directory"
    build_or_pull_image_action: str = "build_or_pull_image"
    
    # Docker options
    force_remove_flag: str = "f"
    
    # System limits
    min_disk_space_mb: int = 100
    script_extensions: List[str] = None
    dangerous_chars: List[str] = None
    
    def __post_init__(self):
        if self.error_patterns is None:
            self.error_patterns = {}
        if self.custom_image_prefixes is None:
            self.custom_image_prefixes = ["ojtools", "cph_"]
        if self.known_registries is None:
            self.known_registries = [
                "docker.io", "gcr.io", "registry.hub.docker.com", 
                "quay.io", "ghcr.io"
            ]
        if self.invalid_path_chars is None:
            self.invalid_path_chars = ["..", " ", "\t", "\n", "\r"]
        if self.script_extensions is None:
            self.script_extensions = [".py", ".js", ".sh", ".rb", ".go"]
        if self.dangerous_chars is None:
            self.dangerous_chars = ["|", ";", "&", "$", "`", "\n", "\r", "\0"]


class EnvJsonBasedExecutionContext:
    """Execution context that eliminates hardcoded values using env.json"""
    
    def __init__(self, language: str, env_type: str = "docker", operations=None, 
                 initial_values: Dict[str, Any] = None):
        """Initialize context from env.json configuration
        
        Args:
            language: Programming language (python, cpp, rust, etc.)
            env_type: Environment type (docker, local, etc.)
            operations: Operations container for file access
            initial_values: Initial values for template resolution
        """
        self.language = language
        self.env_type = env_type
        self.operations = operations
        self.initial_values = initial_values or {}
        
        # Load env.json files
        self.env_configs = self._load_env_configs()
        
        # Create config resolver tree
        self.config_root = create_config_root_from_dict(self.env_configs)
        
        # Extract settings for the specified language and env_type
        self.settings = self._extract_settings()
        
        # Cache commonly used paths
        self._cached_docker_names = None
        self._cached_project_path = None
    
    def _load_env_configs(self) -> Dict[str, Any]:
        """Load all env.json files"""
        if self.operations:
            env_jsons = _load_all_env_jsons("contest_env", self.operations)
        else:
            # Fallback for testing - load directly
            import glob
            import json
            env_jsons = []
            pattern = os.path.join("contest_env", "*", "env.json")
            env_json_paths = glob.glob(pattern)
            
            for path in env_json_paths:
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        env_jsons.append(data)
                except Exception:
                    continue
        
        # Merge all env.json files into single config
        merged_config = {}
        for env_json in env_jsons:
            merged_config.update(env_json)
        
        return merged_config
    
    def _extract_settings(self) -> EnvJsonSettings:
        """Extract settings from env.json for current language and env_type"""
        # Get language-specific configuration
        lang_config = self.env_configs.get(self.language, {})
        env_type_config = lang_config.get("env_types", {}).get(self.env_type, {})
        
        # Extract settings with fallbacks
        settings_dict = {}
        
        # Docker settings
        settings_dict["mount_path"] = env_type_config.get("mount_path", "/workspace")
        settings_dict["working_directory"] = env_type_config.get("working_directory", "/workspace")
        settings_dict["keep_alive_command"] = env_type_config.get("keep_alive_command", "tail -f /dev/null")
        settings_dict["default_shell"] = env_type_config.get("default_shell", "bash")
        
        # Container settings
        container_settings = env_type_config.get("container_settings", {})
        settings_dict["memory_limit"] = container_settings.get("memory_limit", "1GB")
        settings_dict["cpu_limit"] = container_settings.get("cpu_limit", "1.0")
        settings_dict["timeout_seconds"] = container_settings.get("timeout_seconds", 300)
        
        # Error patterns
        settings_dict["error_patterns"] = env_type_config.get("error_patterns", {})
        
        # Retry settings
        retry_settings = env_type_config.get("retry_settings", {})
        settings_dict["max_attempts"] = retry_settings.get("max_attempts", 3)
        settings_dict["base_delay_seconds"] = retry_settings.get("base_delay_seconds", 1.0)
        settings_dict["max_delay_seconds"] = retry_settings.get("max_delay_seconds", 30.0)
        settings_dict["exponential_backoff"] = retry_settings.get("exponential_backoff", True)
        
        # State management
        state_settings = env_type_config.get("state_management", {})
        settings_dict["state_directory"] = state_settings.get("state_directory", "~/.cph/state")
        settings_dict["state_file_format"] = state_settings.get("state_file_format", "json")
        settings_dict["auto_backup"] = state_settings.get("auto_backup", True)
        settings_dict["max_history"] = state_settings.get("max_history", 100)
        
        # Naming conventions
        naming_settings = env_type_config.get("naming_conventions", {})
        settings_dict["container_prefix"] = naming_settings.get("container_prefix", "cph")
        settings_dict["oj_container_prefix"] = naming_settings.get("oj_container_prefix", "cph_ojtools")
        settings_dict["separator"] = naming_settings.get("separator", "_")
        settings_dict["image_tag_format"] = naming_settings.get("image_tag_format", "{language}:latest")
        
        # Path settings
        path_settings = env_type_config.get("path_settings", {})
        settings_dict["container_root_path"] = path_settings.get("container_root_path", "/")
        settings_dict["host_current_directory"] = path_settings.get("host_current_directory", ".")
        settings_dict["path_separator"] = path_settings.get("path_separator", "/")
        settings_dict["temp_directory"] = path_settings.get("temp_directory", "/tmp")
        settings_dict["workspace_alias"] = path_settings.get("workspace_alias", "./workspace")
        
        # Docker settings
        docker_settings = env_type_config.get("docker_settings", {})
        settings_dict["dockerfile_hash_length"] = docker_settings.get("dockerfile_hash_length", 12)
        settings_dict["custom_image_prefixes"] = docker_settings.get("custom_image_prefixes", ["ojtools", "cph_"])
        settings_dict["known_registries"] = docker_settings.get("known_registries", [
            "docker.io", "gcr.io", "registry.hub.docker.com", "quay.io", "ghcr.io"
        ])
        settings_dict["command_wrapper"] = docker_settings.get("command_wrapper", "bash -c")
        settings_dict["invalid_path_chars"] = docker_settings.get("invalid_path_chars", ["..", " ", "\t", "\n", "\r"])
        
        # Timeout settings
        timeout_settings = env_type_config.get("timeout_settings", {})
        settings_dict["process_termination_timeout"] = timeout_settings.get("process_termination_timeout", 3)
        
        # Preparation actions
        prep_actions = env_type_config.get("preparation_actions", {})
        settings_dict["remove_stopped_container_action"] = prep_actions.get("remove_stopped_container", "remove_stopped_container")
        settings_dict["run_new_container_action"] = prep_actions.get("run_new_container", "run_new_container")
        settings_dict["create_directory_action"] = prep_actions.get("create_directory", "create_directory")
        settings_dict["build_or_pull_image_action"] = prep_actions.get("build_or_pull_image", "build_or_pull_image")
        
        # Docker options
        docker_options = env_type_config.get("docker_options", {})
        settings_dict["force_remove_flag"] = docker_options.get("force_remove_flag", "f")
        
        # System limits
        system_limits = env_type_config.get("system_limits", {})
        settings_dict["min_disk_space_mb"] = system_limits.get("min_disk_space_mb", 100)
        settings_dict["script_extensions"] = system_limits.get("script_extensions", [".py", ".js", ".sh", ".rb", ".go"])
        settings_dict["dangerous_chars"] = system_limits.get("dangerous_chars", ["|", ";", "&", "$", "`", "\n", "\r", "\0"])
        
        return EnvJsonSettings(**settings_dict)
    
    def resolve_template(self, template: str) -> str:
        """Resolve template string using env.json and initial values"""
        return resolve_formatted_string(template, self.config_root, self.initial_values)
    
    def get_docker_mount_path(self) -> str:
        """Get Docker mount path from env.json"""
        return self.settings.mount_path
    
    def get_docker_working_directory(self) -> str:
        """Get Docker working directory from env.json"""
        return self.settings.working_directory
    
    def get_keep_alive_command(self) -> str:
        """Get Docker keep alive command from env.json"""
        return self.settings.keep_alive_command
    
    def get_mount_options(self, project_path: str) -> Dict[str, str]:
        """Get Docker mount options from env.json"""
        return {
            "v": f"{project_path}:{self.settings.mount_path}",
            "w": self.settings.working_directory
        }
    
    def get_container_options(self) -> Dict[str, str]:
        """Get additional container options from env.json"""
        options = {}
        if self.settings.memory_limit:
            options["m"] = self.settings.memory_limit
        # Add CPU limits if needed
        return options
    
    def get_error_patterns(self, category: str) -> List[str]:
        """Get error patterns for specific category from env.json"""
        return self.settings.error_patterns.get(category, [])
    
    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay from env.json settings"""
        if self.settings.exponential_backoff:
            delay = self.settings.base_delay_seconds * (2 ** (attempt - 1))
        else:
            delay = self.settings.base_delay_seconds
        
        return min(delay, self.settings.max_delay_seconds)
    
    def get_max_retry_attempts(self) -> int:
        """Get maximum retry attempts from env.json"""
        return self.settings.max_attempts
    
    def get_state_file_path(self, identifier: str) -> str:
        """Get state file path from env.json settings"""
        state_dir = os.path.expanduser(self.settings.state_directory)
        return os.path.join(state_dir, f"{identifier}.{self.settings.state_file_format}")
    
    def is_oj_container(self, container_name: str) -> bool:
        """Check if container is OJ container using env.json naming conventions"""
        return container_name.startswith(self.settings.oj_container_prefix)
    
    def generate_container_name(self, base_name: str, is_oj: bool = False) -> str:
        """Generate container name using env.json naming conventions"""
        prefix = self.settings.oj_container_prefix if is_oj else self.settings.container_prefix
        return f"{prefix}{self.settings.separator}{base_name}"
    
    def generate_image_name(self) -> str:
        """Generate image name using env.json template"""
        template = self.settings.image_tag_format
        context = {"language": self.language}
        return format_with_context(template, context)
    
    def get_project_path(self) -> str:
        """Get project path (cached)"""
        if self._cached_project_path is None:
            self._cached_project_path = os.getcwd()
        return self._cached_project_path
    
    def get_docker_names(self) -> Dict[str, str]:
        """Get Docker names (cached for compatibility)"""
        if self._cached_docker_names is None:
            base_name = self.language
            self._cached_docker_names = {
                "image_name": self.generate_image_name(),
                "oj_image_name": f"ojtools_{self.language}",
                "container_name": self.generate_container_name(base_name),
                "oj_container_name": self.generate_container_name(base_name, is_oj=True)
            }
        return self._cached_docker_names
    
    def resolve_container_path(self, path_components: List[str]) -> str:
        """Resolve container path using env.json path settings"""
        if not path_components:
            return self.settings.container_root_path
        return self.settings.path_separator.join(path_components)
    
    def extract_container_from_command(self, command: str) -> Optional[str]:
        """Extract container name from command using env.json patterns"""
        parts = command.split()
        if len(parts) >= 3 and parts[0] == "docker" and parts[1] == "exec":
            return parts[2]
        return None
    
    # Additional getter methods for new settings
    def get_dockerfile_hash_length(self) -> int:
        """Get Dockerfile hash length from env.json"""
        return self.settings.dockerfile_hash_length
    
    def get_custom_image_prefixes(self) -> List[str]:
        """Get custom image prefixes from env.json"""
        return self.settings.custom_image_prefixes
    
    def get_known_registries(self) -> List[str]:
        """Get known Docker registries from env.json"""
        return self.settings.known_registries
    
    def get_command_wrapper(self) -> str:
        """Get command wrapper from env.json"""
        return self.settings.command_wrapper
    
    def get_invalid_path_chars(self) -> List[str]:
        """Get invalid path characters from env.json"""
        return self.settings.invalid_path_chars
    
    def get_process_timeout(self) -> int:
        """Get process termination timeout from env.json"""
        return self.settings.process_termination_timeout
    
    def get_preparation_action(self, action_type: str) -> str:
        """Get preparation action string from env.json"""
        action_map = {
            "remove_stopped_container": self.settings.remove_stopped_container_action,
            "run_new_container": self.settings.run_new_container_action,
            "create_directory": self.settings.create_directory_action,
            "build_or_pull_image": self.settings.build_or_pull_image_action
        }
        return action_map.get(action_type, action_type)
    
    def get_docker_option(self, option: str) -> str:
        """Get Docker option from env.json"""
        if option == "force_remove":
            return self.settings.force_remove_flag
        return option
    
    def get_min_disk_space_mb(self) -> int:
        """Get minimum disk space requirement from env.json"""
        return self.settings.min_disk_space_mb
    
    def get_script_extensions(self) -> List[str]:
        """Get script file extensions from env.json"""
        return self.settings.script_extensions
    
    def get_dangerous_chars(self) -> List[str]:
        """Get dangerous characters list from env.json"""
        return self.settings.dangerous_chars
    
    def should_build_custom_image(self, image_name: str) -> bool:
        """Determine if image should be built locally using env.json settings"""
        # Check custom image prefixes from env.json
        for prefix in self.get_custom_image_prefixes():
            if image_name.startswith(prefix):
                return True
        
        # Check if it's a registry image
        if '/' in image_name:
            parts = image_name.split('/')
            registries = self.get_known_registries()
            if parts[0] in registries or '.' in parts[0]:
                return False
        
        # Standard images from Docker Hub
        if ':' in image_name and '/' not in image_name:
            return False
        
        # Default to local build for unknown patterns
        return True
    
    def validate_mount_path(self, mount_path: str) -> tuple[bool, Optional[str]]:
        """Validate mount path using env.json settings"""
        if not mount_path:
            return False, "Mount path cannot be empty"
        
        if not mount_path.startswith('/'):
            return False, "Mount path must be absolute (start with /)"
        
        if mount_path.endswith('/') and len(mount_path) > 1:
            return False, "Mount path should not end with /"
        
        # Check for invalid characters from env.json
        invalid_chars = self.get_invalid_path_chars()
        for char in invalid_chars:
            if char in mount_path:
                return False, f"Mount path contains invalid sequence: {repr(char)}"
        
        return True, None
    
    def wrap_command_with_cwd(self, command: str, cwd: Optional[str]) -> str:
        """Wrap command with working directory using env.json settings"""
        if not cwd:
            return command
        
        # Convert workspace alias if needed
        workspace_alias = self.settings.workspace_alias
        if cwd == workspace_alias:
            cwd = self.get_docker_mount_path()
        
        # Use command wrapper from env.json
        wrapper = self.get_command_wrapper()
        return f"{wrapper} 'cd {cwd} && {command}'"


def create_env_json_context(language: str, env_type: str = "docker", 
                           operations=None, **kwargs) -> EnvJsonBasedExecutionContext:
    """Factory function to create env.json based execution context
    
    Args:
        language: Programming language
        env_type: Environment type
        operations: Operations container
        **kwargs: Additional initial values for template resolution
        
    Returns:
        EnvJsonBasedExecutionContext instance
    """
    return EnvJsonBasedExecutionContext(
        language=language,
        env_type=env_type, 
        operations=operations,
        initial_values=kwargs
    )
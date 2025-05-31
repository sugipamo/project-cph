"""
Configuration file discovery and loading
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .exceptions import ConfigLoadError, ConfigDiscoveryError


class ConfigDiscovery:
    """Automatic configuration file discovery and loading"""
    
    DEFAULT_PATTERNS = [
        "contest_env/*/env.json",
        "config/*.json",
        "config/*.yaml",
        "*.config.json",
        "env.json"
    ]
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.discovered_configs = {}
    
    def discover_configs(self, patterns: Optional[List[str]] = None) -> Dict[str, Path]:
        """Discover configuration files based on patterns"""
        patterns = patterns or self.DEFAULT_PATTERNS
        discovered = {}
        
        for pattern in patterns:
            try:
                matches = list(self.project_root.glob(pattern))
                for match in matches:
                    if match.is_file():
                        # Create a unique key for this config
                        relative_path = match.relative_to(self.project_root)
                        key = self._generate_config_key(relative_path)
                        discovered[key] = match
            except Exception as e:
                # Continue with other patterns if one fails
                continue
        
        self.discovered_configs = discovered
        return discovered
    
    def _generate_config_key(self, relative_path: Path) -> str:
        """Generate a unique key for a configuration file"""
        parts = relative_path.parts
        
        # Special handling for language configs
        if len(parts) >= 2 and parts[0] == "contest_env":
            language = parts[1]
            return f"language_{language}"
        
        # For other configs, use the filename without extension
        stem = relative_path.stem
        if stem == "env":
            # For env.json files, use parent directory as key
            return f"env_{parts[-2]}" if len(parts) > 1 else "env_default"
        
        return stem.replace(".", "_")
    
    def load_config(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a single configuration file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigLoadError(
                str(file_path),
                "File does not exist"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    return json.load(f)
                elif file_path.suffix.lower() in ['.yaml', '.yml']:
                    # Optional YAML support
                    try:
                        import yaml
                        return yaml.safe_load(f)
                    except ImportError:
                        raise ConfigLoadError(
                            str(file_path),
                            "YAML support not available (install PyYAML)"
                        )
                else:
                    raise ConfigLoadError(
                        str(file_path),
                        f"Unsupported file format: {file_path.suffix}"
                    )
        
        except json.JSONDecodeError as e:
            raise ConfigLoadError(
                str(file_path),
                f"Invalid JSON: {str(e)}",
                original_exception=e
            )
        except Exception as e:
            raise ConfigLoadError(
                str(file_path),
                f"Failed to read file: {str(e)}",
                original_exception=e
            )
    
    def load_all_discovered(self) -> Dict[str, Dict[str, Any]]:
        """Load all discovered configuration files"""
        if not self.discovered_configs:
            self.discover_configs()
        
        loaded_configs = {}
        errors = []
        
        for key, file_path in self.discovered_configs.items():
            try:
                loaded_configs[key] = self.load_config(file_path)
            except ConfigLoadError as e:
                errors.append(f"{key}: {e.reason}")
        
        if errors and not loaded_configs:
            raise ConfigDiscoveryError(
                list(self.discovered_configs.values()),
                f"Failed to load all configs: {'; '.join(errors)}"
            )
        
        return loaded_configs
    
    def find_language_config(self, language: str) -> Optional[Path]:
        """Find configuration file for a specific language"""
        if not self.discovered_configs:
            self.discover_configs()
        
        # Look for exact match first
        key = f"language_{language}"
        if key in self.discovered_configs:
            return self.discovered_configs[key]
        
        # Look for partial matches
        for config_key, file_path in self.discovered_configs.items():
            if language.lower() in config_key.lower():
                return file_path
        
        return None
    
    def find_config_by_pattern(self, pattern: str) -> List[Path]:
        """Find configurations matching a specific pattern"""
        if not self.discovered_configs:
            self.discover_configs()
        
        import re
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        
        matches = []
        for key, file_path in self.discovered_configs.items():
            if compiled_pattern.search(key) or compiled_pattern.search(str(file_path)):
                matches.append(file_path)
        
        return matches
    
    def get_config_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all discovered configurations"""
        if not self.discovered_configs:
            self.discover_configs()
        
        info = {}
        for key, file_path in self.discovered_configs.items():
            try:
                stat = file_path.stat()
                info[key] = {
                    'path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.project_root)),
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'exists': file_path.exists(),
                    'readable': os.access(file_path, os.R_OK)
                }
            except Exception as e:
                info[key] = {
                    'path': str(file_path),
                    'error': str(e)
                }
        
        return info
    
    def refresh_discovery(self, patterns: Optional[List[str]] = None) -> Dict[str, Path]:
        """Refresh configuration discovery"""
        self.discovered_configs.clear()
        return self.discover_configs(patterns)
    
    def add_search_path(self, path: Union[str, Path]):
        """Add additional search path"""
        # This could be extended to support multiple search paths
        additional_root = Path(path)
        if additional_root.exists() and additional_root.is_dir():
            # For now, just update the project root
            # In the future, this could maintain a list of search paths
            self.project_root = additional_root
    
    def validate_discovered_configs(self) -> Dict[str, List[str]]:
        """Validate all discovered configurations"""
        validation_results = {}
        
        if not self.discovered_configs:
            self.discover_configs()
        
        for key, file_path in self.discovered_configs.items():
            errors = []
            try:
                config = self.load_config(file_path)
                
                # Basic validation
                if not isinstance(config, dict):
                    errors.append("Configuration must be a JSON object")
                
                # Language-specific validation
                if key.startswith("language_"):
                    if 'language_name' not in config:
                        errors.append("Missing required field: language_name")
                    if 'commands' not in config:
                        errors.append("Missing required field: commands")
                
            except ConfigLoadError as e:
                errors.append(f"Load error: {e.reason}")
            
            validation_results[key] = errors
        
        return validation_results
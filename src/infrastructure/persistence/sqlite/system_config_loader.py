"""System configuration loader that migrates from system_info.json to SQLite."""
import json
import os
from typing import Dict, Any, Optional

from src.infrastructure.di_container import DIKey


class SystemConfigLoader:
    """Loads system configuration from SQLite, with migration from JSON."""
    
    def __init__(self, container):
        """Initialize with DI container."""
        self.container = container
        self._config_repo = None
        self._migrated = False
        
    @property
    def config_repo(self):
        """Lazy load config repository."""
        if self._config_repo is None:
            self._config_repo = self.container.resolve(DIKey.SYSTEM_CONFIG_REPOSITORY)
        return self._config_repo
    
    def _migrate_from_json(self, json_path: str) -> None:
        """Migrate configuration from JSON file to SQLite."""
        if self._migrated or not os.path.exists(json_path):
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
            
            # Migrate top-level configuration
            self.config_repo.set_config("command", json_config.get("command"), "execution", "Current command type")
            self.config_repo.set_config("language", json_config.get("language"), "execution", "Current programming language")
            self.config_repo.set_config("env_type", json_config.get("env_type"), "execution", "Environment type (docker/local)")
            self.config_repo.set_config("contest_name", json_config.get("contest_name"), "contest", "Current contest name")
            self.config_repo.set_config("problem_name", json_config.get("problem_name"), "contest", "Current problem name")
            
            # Migrate language configurations
            env_json = json_config.get("env_json", {})
            for lang, lang_config in env_json.items():
                # Store entire language config as nested structure
                self.config_repo.set_config(
                    f"language.{lang}",
                    lang_config,
                    "language",
                    f"Configuration for {lang}"
                )
                
                # Also store key parts separately for easier access
                if isinstance(lang_config, dict):
                    if "language_id" in lang_config:
                        self.config_repo.set_config(
                            f"language.{lang}.language_id",
                            lang_config["language_id"],
                            "language",
                            f"AtCoder language ID for {lang}"
                        )
                    if "source_file_name" in lang_config:
                        self.config_repo.set_config(
                            f"language.{lang}.source_file_name",
                            lang_config["source_file_name"],
                            "language",
                            f"Source file name for {lang}"
                        )
            
            # Migrate Docker configuration
            docker_config = json_config.get("docker", {})
            if docker_config:
                self.config_repo.set_config("docker", docker_config, "docker", "Docker configuration")
                
                # Store naming patterns separately
                naming = docker_config.get("naming", {})
                if naming:
                    self.config_repo.set_config("docker.naming", naming, "docker", "Docker naming patterns")
            
            # Migrate output configuration
            output_config = json_config.get("output", {})
            if output_config:
                self.config_repo.set_config("output", output_config, "output", "Output formatting configuration")
            
            self._migrated = True
            
        except Exception:
            # If migration fails, we'll fall back to reading from JSON
            pass
    
    def load_config(self, json_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from SQLite, migrating from JSON if needed.
        
        Args:
            json_path: Path to system_info.json for migration
            
        Returns:
            Dictionary containing full system configuration
        """
        # Migrate from JSON if path provided
        if json_path:
            self._migrate_from_json(json_path)
        
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
        
        # If config is empty, try loading from JSON directly
        if not config.get("command") and json_path and os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
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
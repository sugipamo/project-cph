"""
Comprehensive tests for env_context module
"""
import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, mock_open
from src.env_integration.fitting.env_context import (
    EnvJsonSettings,
    EnvJsonBasedExecutionContext,
    create_env_json_context
)


class TestEnvJsonSettings:
    """Test EnvJsonSettings dataclass"""
    
    def test_settings_creation_with_defaults(self):
        """Test creating EnvJsonSettings with default values"""
        settings = EnvJsonSettings()
        
        # Check default values
        assert settings.mount_path == "/workspace"
        assert settings.working_directory == "/workspace"
        assert settings.keep_alive_command == "tail -f /dev/null"
        assert settings.default_shell == "bash"
        assert settings.memory_limit == "1GB"
        assert settings.cpu_limit == "1.0"
        assert settings.timeout_seconds == 300
        assert settings.max_attempts == 3
        assert settings.base_delay_seconds == 1.0
        assert settings.max_delay_seconds == 30.0
        assert settings.exponential_backoff is True
    
    def test_settings_creation_with_custom_values(self):
        """Test creating EnvJsonSettings with custom values"""
        settings = EnvJsonSettings(
            mount_path="/custom",
            working_directory="/work",
            max_attempts=5,
            base_delay_seconds=2.0
        )
        
        assert settings.mount_path == "/custom"
        assert settings.working_directory == "/work"
        assert settings.max_attempts == 5
        assert settings.base_delay_seconds == 2.0
        # Defaults should still apply
        assert settings.default_shell == "bash"
    
    def test_post_init_default_lists(self):
        """Test that post_init sets default list values"""
        settings = EnvJsonSettings()
        
        # These should be set by __post_init__
        assert settings.error_patterns == {}
        assert settings.custom_image_prefixes == ["ojtools", "cph_"]
        assert "docker.io" in settings.known_registries
        assert ".." in settings.invalid_path_chars
        assert ".py" in settings.script_extensions
        assert "|" in settings.dangerous_chars
    
    def test_post_init_preserves_provided_lists(self):
        """Test that post_init preserves provided list values"""
        custom_prefixes = ["custom1", "custom2"]
        settings = EnvJsonSettings(custom_image_prefixes=custom_prefixes)
        
        # Should preserve custom values
        assert settings.custom_image_prefixes == custom_prefixes


class TestEnvJsonBasedExecutionContext:
    """Test EnvJsonBasedExecutionContext class"""
    
    def test_context_initialization_basic(self):
        """Test basic context initialization"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        
        assert context.language == "python"
        assert context.env_type == "docker"
        assert context.operations is None
        assert context.initial_values == {}
    
    def test_context_initialization_with_values(self):
        """Test context initialization with initial values"""
        initial_values = {"project": "test", "env": "dev"}
        context = EnvJsonBasedExecutionContext(
            "python", 
            "docker", 
            initial_values=initial_values
        )
        
        assert context.initial_values == initial_values
    
    @patch('src.env_integration.fitting.env_context._load_all_env_jsons')
    def test_load_env_configs_with_operations(self, mock_load):
        """Test loading env configs with operations"""
        mock_load.return_value = [
            {"python": {"language_id": "5078"}},
            {"cpp": {"language_id": "5077"}}
        ]
        
        mock_operations = Mock()
        context = EnvJsonBasedExecutionContext("python", "docker", operations=mock_operations)
        
        # Should have called _load_all_env_jsons
        mock_load.assert_called_once_with("contest_env", mock_operations)
        
        # Should have merged configs
        assert "python" in context.env_configs
        assert "cpp" in context.env_configs
    
    @patch('glob.glob')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_env_configs_fallback(self, mock_file, mock_glob):
        """Test loading env configs fallback without operations"""
        # Setup mock file system
        mock_glob.return_value = ["/path/contest_env/python/env.json"]
        mock_file.return_value.read.return_value = json.dumps({
            "python": {"language_id": "5078"}
        })
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        
        # Should have used glob fallback
        mock_glob.assert_called()
        assert "python" in context.env_configs
    
    def test_extract_settings_basic(self):
        """Test basic settings extraction"""
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {
                        "mount_path": "/custom_workspace",
                        "container_settings": {
                            "timeout_seconds": 600
                        }
                    }
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        assert context.settings.mount_path == "/custom_workspace"
        assert context.settings.timeout_seconds == 600
        # Should have defaults for missing values
        assert context.settings.working_directory == "/workspace"
    
    def test_extract_settings_with_retry_config(self):
        """Test settings extraction with retry configuration"""
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {
                        "retry_settings": {
                            "max_attempts": 5,
                            "base_delay_seconds": 2.0,
                            "exponential_backoff": False
                        }
                    }
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        assert context.settings.max_attempts == 5
        assert context.settings.base_delay_seconds == 2.0
        assert context.settings.exponential_backoff is False
    
    def test_extract_settings_with_error_patterns(self):
        """Test settings extraction with error patterns"""
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {
                        "error_patterns": {
                            "daemon_connection": ["connection refused", "docker daemon"],
                            "image_not_found": ["no such image", "pull access denied"]
                        }
                    }
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        assert "daemon_connection" in context.settings.error_patterns
        assert "connection refused" in context.settings.error_patterns["daemon_connection"]
        assert "image_not_found" in context.settings.error_patterns
    
    def test_resolve_template_method(self):
        """Test template resolution method"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.initial_values = {"project": "test"}
        
        # Mock the config resolver
        with patch('src.env_integration.fitting.env_context.resolve_formatted_string') as mock_resolve:
            mock_resolve.return_value = "/test/resolved/path"
            
            result = context.resolve_template("/base/{project}/path")
            
            mock_resolve.assert_called_once()
            assert result == "/test/resolved/path"
    
    def test_docker_path_methods(self):
        """Test Docker path-related methods"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            mount_path="/custom_mount",
            working_directory="/custom_work"
        )
        
        assert context.get_docker_mount_path() == "/custom_mount"
        assert context.get_docker_working_directory() == "/custom_work"
        assert context.get_keep_alive_command() == "tail -f /dev/null"
    
    def test_mount_options_method(self):
        """Test mount options generation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            mount_path="/workspace",
            working_directory="/work"
        )
        
        options = context.get_mount_options("/host/project")
        
        assert options["v"] == "/host/project:/workspace"
        assert options["w"] == "/work"
    
    def test_container_options_method(self):
        """Test container options generation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(memory_limit="2GB")
        
        options = context.get_container_options()
        
        assert options["m"] == "2GB"
    
    def test_error_patterns_method(self):
        """Test error patterns retrieval"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            error_patterns={
                "daemon_error": ["connection refused", "daemon not running"],
                "image_error": ["no such image"]
            }
        )
        
        daemon_patterns = context.get_error_patterns("daemon_error")
        assert daemon_patterns == ["connection refused", "daemon not running"]
        
        missing_patterns = context.get_error_patterns("nonexistent")
        assert missing_patterns == []
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            exponential_backoff=True
        )
        
        # Test exponential backoff
        delay1 = context.get_retry_delay(1)
        delay2 = context.get_retry_delay(2)
        delay3 = context.get_retry_delay(3)
        
        assert delay1 == 1.0  # 1.0 * 2^(1-1) = 1.0
        assert delay2 == 2.0  # 1.0 * 2^(2-1) = 2.0
        assert delay3 == 4.0  # 1.0 * 2^(3-1) = 4.0
        
        # Test max delay cap
        delay_large = context.get_retry_delay(10)
        assert delay_large == 10.0  # Capped at max_delay_seconds
    
    def test_retry_delay_linear(self):
        """Test linear retry delay calculation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            base_delay_seconds=2.0,
            exponential_backoff=False
        )
        
        delay1 = context.get_retry_delay(1)
        delay2 = context.get_retry_delay(2)
        delay3 = context.get_retry_delay(3)
        
        # Should all be the same for linear backoff
        assert delay1 == 2.0
        assert delay2 == 2.0
        assert delay3 == 2.0
    
    def test_max_retry_attempts_method(self):
        """Test max retry attempts retrieval"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(max_attempts=7)
        
        assert context.get_max_retry_attempts() == 7
    
    def test_state_file_path_method(self):
        """Test state file path generation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            state_directory="~/.test/state",
            state_file_format="json"
        )
        
        with patch('os.path.expanduser') as mock_expand:
            mock_expand.return_value = "/home/user/.test/state"
            
            path = context.get_state_file_path("test_id")
            
            mock_expand.assert_called_once_with("~/.test/state")
            assert path == "/home/user/.test/state/test_id.json"
    
    def test_container_naming_methods(self):
        """Test container naming methods"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            container_prefix="myprefix",
            oj_container_prefix="myoj",
            separator="_"
        )
        
        # Test container name generation
        container_name = context.generate_container_name("test")
        assert container_name == "myprefix_test"
        
        oj_container_name = context.generate_container_name("test", is_oj=True)
        assert oj_container_name == "myoj_test"
        
        # Test OJ container detection
        assert context.is_oj_container("myoj_something") is True
        assert context.is_oj_container("myprefix_something") is False
    
    def test_image_name_generation(self):
        """Test image name generation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(image_tag_format="{language}:latest")
        
        with patch('src.env_integration.fitting.env_context.format_with_context') as mock_format:
            mock_format.return_value = "python:latest"
            
            image_name = context.generate_image_name()
            
            mock_format.assert_called_once_with("{language}:latest", {"language": "python"})
            assert image_name == "python:latest"
    
    def test_docker_names_caching(self):
        """Test Docker names caching"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        
        # First call should generate names
        names1 = context.get_docker_names()
        
        # Second call should return cached results
        names2 = context.get_docker_names()
        
        assert names1 is names2  # Same object reference
        assert "image_name" in names1
        assert "container_name" in names1
        assert "oj_image_name" in names1
        assert "oj_container_name" in names1
    
    def test_path_validation_method(self):
        """Test mount path validation"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            invalid_path_chars=["..", " ", "\t"]
        )
        
        # Valid path
        is_valid, error = context.validate_mount_path("/valid/path")
        assert is_valid is True
        assert error is None
        
        # Invalid paths
        is_valid, error = context.validate_mount_path("")
        assert is_valid is False
        assert "cannot be empty" in error
        
        is_valid, error = context.validate_mount_path("relative/path")
        assert is_valid is False
        assert "must be absolute" in error
        
        is_valid, error = context.validate_mount_path("/path/with/../invalid")
        assert is_valid is False
        assert "invalid sequence" in error
    
    def test_command_wrapping_method(self):
        """Test command wrapping with working directory"""
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.settings = EnvJsonSettings(
            command_wrapper="bash -c",
            workspace_alias="./workspace"
        )
        
        # Test without cwd
        result = context.wrap_command_with_cwd("ls", None)
        assert result == "ls"
        
        # Test with regular cwd
        result = context.wrap_command_with_cwd("ls", "/custom/dir")
        assert result == "bash -c 'cd /custom/dir && ls'"
        
        # Test with workspace alias
        context.settings.mount_path = "/workspace"
        result = context.wrap_command_with_cwd("ls", "./workspace")
        assert result == "bash -c 'cd /workspace && ls'"


class TestCreateEnvJsonContext:
    """Test create_env_json_context factory function"""
    
    def test_factory_function_basic(self):
        """Test basic factory function usage"""
        context = create_env_json_context("python", "docker")
        
        assert isinstance(context, EnvJsonBasedExecutionContext)
        assert context.language == "python"
        assert context.env_type == "docker"
    
    def test_factory_function_with_operations(self):
        """Test factory function with operations"""
        mock_operations = Mock()
        context = create_env_json_context("cpp", "local", operations=mock_operations)
        
        assert context.operations == mock_operations
        assert context.language == "cpp"
        assert context.env_type == "local"
    
    def test_factory_function_with_kwargs(self):
        """Test factory function with additional kwargs"""
        context = create_env_json_context(
            "rust",
            "docker",
            project="myproject",
            env="development"
        )
        
        assert context.initial_values["project"] == "myproject"
        assert context.initial_values["env"] == "development"


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_complete_docker_setup_workflow(self):
        """Test complete Docker setup workflow"""
        # Create context with typical Docker configuration
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {
                        "mount_path": "/workspace",
                        "working_directory": "/workspace",
                        "retry_settings": {
                            "max_attempts": 3,
                            "base_delay_seconds": 1.0
                        },
                        "error_patterns": {
                            "daemon_connection": ["connection refused"],
                            "image_not_found": ["no such image"]
                        },
                        "container_settings": {
                            "memory_limit": "2GB",
                            "timeout_seconds": 300
                        }
                    }
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        # Test Docker operations
        mount_options = context.get_mount_options("/host/project")
        assert mount_options["v"] == "/host/project:/workspace"
        
        # Test error handling
        daemon_errors = context.get_error_patterns("daemon_connection")
        assert "connection refused" in daemon_errors
        
        # Test retry logic
        max_attempts = context.get_max_retry_attempts()
        assert max_attempts == 3
        
        delay = context.get_retry_delay(2)
        assert delay == 2.0  # Exponential backoff: 1.0 * 2^(2-1)
    
    def test_multi_language_environment_context(self):
        """Test context with multiple language configurations"""
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {"mount_path": "/py_workspace"}
                }
            },
            "cpp": {
                "env_types": {
                    "docker": {"mount_path": "/cpp_workspace"}
                }
            }
        }
        
        # Test Python context
        py_context = EnvJsonBasedExecutionContext("python", "docker")
        py_context.env_configs = env_configs
        py_context.settings = py_context._extract_settings()
        assert py_context.get_docker_mount_path() == "/py_workspace"
        
        # Test C++ context
        cpp_context = EnvJsonBasedExecutionContext("cpp", "docker")
        cpp_context.env_configs = env_configs
        cpp_context.settings = cpp_context._extract_settings()
        assert cpp_context.get_docker_mount_path() == "/cpp_workspace"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_language_config(self):
        """Test behavior when language config is missing"""
        env_configs = {"cpp": {"env_types": {"docker": {}}}}
        
        context = EnvJsonBasedExecutionContext("python", "docker")  # Python not in config
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        # Should use defaults
        assert context.settings.mount_path == "/workspace"
        assert context.settings.max_attempts == 3
    
    def test_missing_env_type_config(self):
        """Test behavior when env_type config is missing"""
        env_configs = {
            "python": {
                "env_types": {
                    "local": {"mount_path": "/local"}
                    # Docker config missing
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")  # Docker not in config
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        # Should use defaults
        assert context.settings.mount_path == "/workspace"
    
    def test_partial_config_handling(self):
        """Test handling of partial configuration"""
        env_configs = {
            "python": {
                "env_types": {
                    "docker": {
                        "mount_path": "/custom",
                        # Other settings missing
                    }
                }
            }
        }
        
        context = EnvJsonBasedExecutionContext("python", "docker")
        context.env_configs = env_configs
        context.settings = context._extract_settings()
        
        # Should have custom value
        assert context.settings.mount_path == "/custom"
        # Should have defaults for missing values
        assert context.settings.working_directory == "/workspace"
        assert context.settings.max_attempts == 3
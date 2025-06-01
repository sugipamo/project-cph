"""
Test configuration management system
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.manager import ConfigurationManager, UnifiedConfig
from src.config.exceptions import ConfigurationError, ConfigLoadError


class TestConfigurationManager:
    """Test the core configuration manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test config files
        self.python_config = {
            "language_name": "python",
            "contest_template_path": "./contest_template/{language_name}",
            "commands": {
                "test": {
                    "steps": [
                        {"op": "shell", "cmd": ["echo", "test"]}
                    ]
                }
            }
        }
        
        # Create test directories and files
        (self.temp_path / "contest_env" / "python").mkdir(parents=True)
        with open(self.temp_path / "contest_env" / "python" / "env.json", 'w') as f:
            json.dump(self.python_config, f)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_configuration_manager_initialization(self):
        """Test basic initialization"""
        manager = ConfigurationManager(self.temp_path)
        assert manager.project_root == self.temp_path
        assert manager.enable_cache is True
        assert manager.enable_validation is True
    
    def test_load_config_basic(self):
        """Test basic configuration loading"""
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "python",
            "contest": "test_contest",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        
        assert isinstance(config, UnifiedConfig)
        assert "python" in config.list_languages()
        assert config.get_language_config("python") is not None
    
    def test_get_language_config(self):
        """Test language-specific configuration retrieval"""
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "python", 
            "contest": "test_contest",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        python_config = config.get_language_config("python")
        
        assert python_config["language_name"] == "python"
        assert "commands" in python_config
        assert "test" in python_config["commands"]
    
    def test_get_command_steps(self):
        """Test command step retrieval"""
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "python",
            "contest": "test_contest", 
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        steps = config.get_command_steps("python", "test")
        
        assert len(steps) > 0
        assert steps[0]["op"] == "shell"
        assert steps[0]["cmd"] == ["echo", "test"]
    
    def test_template_processing(self):
        """Test template processing in configuration"""
        # Add template to config
        template_config = {
            "language_name": "python",
            "workspace_path": "/tmp/{contest}/{language}",
            "commands": {
                "test": {
                    "steps": [
                        {"op": "shell", "cmd": ["echo", "{source_file_name}"]}
                    ]
                }
            }
        }
        
        with open(self.temp_path / "contest_env" / "python" / "env.json", 'w') as f:
            json.dump(template_config, f)
        
        manager = ConfigurationManager(self.temp_path)
        context = {
            "language": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        steps = config.get_command_steps("python", "test")
        
        # Template should be processed
        assert steps[0]["cmd"] == ["echo", "main.py"]
    
    def test_path_resolution(self):
        """Test configuration path resolution"""
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "python",
            "contest": "test_contest",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        
        # Test path resolution
        template_path = config.resolve_path(["contest_template_path"], "python")
        assert template_path is not None
    
    def test_config_validation(self):
        """Test configuration validation"""
        manager = ConfigurationManager(self.temp_path, enable_validation=True)
        
        context = {
            "language": "python",
            "contest": "test_contest", 
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        validation_result = manager.validate_configuration()
        
        # Should have some validation results
        assert validation_result is not None
    
    def test_missing_language_config(self):
        """Test handling of missing language configuration"""
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "nonexistent",
            "contest": "test_contest",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        
        with pytest.raises(ConfigurationError):
            manager.get_language_config("nonexistent")
    
    def test_config_info(self):
        """Test configuration information retrieval"""
        manager = ConfigurationManager(self.temp_path)
        
        info = manager.get_config_info()
        
        assert "project_root" in info
        assert "cache_enabled" in info
        assert "validation_enabled" in info
        assert info["project_root"] == str(self.temp_path)


class TestUnifiedConfig:
    """Test the unified configuration container"""
    
    def test_unified_config_creation(self):
        """Test basic unified config creation"""
        config = UnifiedConfig()
        
        assert config.language_configs == {}
        assert config.system_config == {}
        assert config.execution_context == {}
    
    def test_language_config_management(self):
        """Test language configuration management"""
        config = UnifiedConfig()
        
        python_config = {
            "language_name": "python",
            "commands": {"test": {"steps": []}}
        }
        
        config.language_configs["python"] = python_config
        
        assert config.get_language_config("python") == python_config
        assert "python" in config.list_languages()
        assert "test" in config.list_commands("python")
    
    def test_execution_context_management(self):
        """Test execution context management"""
        config = UnifiedConfig()
        
        context = {
            "language": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
        }
        
        config.set_execution_context(context)
        
        assert config.get_execution_context() == context
    
    def test_command_steps_retrieval(self):
        """Test command steps retrieval with template processing"""
        config = UnifiedConfig()
        
        # Set up test config
        config.language_configs["python"] = {
            "commands": {
                "test": {
                    "steps": [
                        {"op": "shell", "cmd": ["echo", "{source_file_name}"]}
                    ]
                }
            }
        }
        
        config.set_execution_context({
            "language": "python",
            "source_file_name": "main.py"
        })
        
        steps = config.get_command_steps("python", "test")
        
        assert len(steps) == 1
        assert steps[0]["cmd"] == ["echo", "main.py"]
    
    def test_validation_status(self):
        """Test validation status checking"""
        config = UnifiedConfig()
        
        # Initially should be valid (no validations run)
        assert config.is_valid() is True
        
        # Add mock validation results
        from src.config.validation import ConfigValidationResult
        
        valid_result = ConfigValidationResult()
        valid_result.is_valid = True
        
        invalid_result = ConfigValidationResult()
        invalid_result.is_valid = False
        invalid_result.add_error("Test error")
        
        config.validation_results["valid"] = valid_result
        config.validation_results["invalid"] = invalid_result
        
        # Should be invalid due to one invalid result
        assert config.is_valid() is False
        
        # Test validation summary
        summary = config.get_validation_summary()
        assert "INVALID" in summary
        assert "1 errors" in summary
"""Test to ensure configuration system doesn't use default values as per CLAUDE.md"""
import pytest
from unittest.mock import Mock, patch
from src.configuration.configuration_repository import ConfigurationRepository
from src.configuration.environment_manager import EnvironmentManager
from src.configuration.system_config_repository import SystemConfigRepository


class TestNoDefaultValues:
    """Verify that the configuration system adheres to the no default values policy"""
    
    def test_configuration_repository_no_defaults(self):
        """ConfigurationRepository should fail when config is missing, not use defaults"""
        mock_config_manager = Mock()
        mock_config_manager.get_config.side_effect = KeyError("Missing config")
        
        repo = ConfigurationRepository(mock_config_manager)
        
        # Should raise error, not return default
        with pytest.raises(KeyError):
            repo.get_config("nonexistent.setting")
    
    def test_environment_manager_no_defaults(self):
        """EnvironmentManager should not provide default values"""
        with patch('src.configuration.environment_manager.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            env_manager = EnvironmentManager("test_env")
            
            # Should raise error when config file doesn't exist
            with pytest.raises(Exception):
                env_manager.load_config()
    
    def test_system_config_repository_no_defaults(self):
        """SystemConfigRepository should not provide default values"""
        mock_loader = Mock()
        mock_loader.load.side_effect = FileNotFoundError("Config file not found")
        
        repo = SystemConfigRepository(mock_loader)
        
        # Should propagate error, not return default
        with pytest.raises(FileNotFoundError):
            repo.load_system_config()
    
    def test_json_config_loading_enforces_presence(self):
        """JSON config loading should enforce all required fields are present"""
        import json
        from pathlib import Path
        
        # Create a temporary JSON config missing required fields
        test_config = {
            "partial": "config"
            # Missing required fields
        }
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(test_config)
            
            # This should validate and fail if required fields are missing
            with pytest.raises(Exception) as exc_info:
                # Attempt to load incomplete config
                from src.configuration.system_config_loader import SystemConfigLoader
                loader = SystemConfigLoader()
                loader.load("test.json")
                
    def test_no_get_with_default_pattern(self):
        """Verify code doesn't use dict.get() with default values"""
        # This is a meta-test to ensure the pattern isn't used
        import ast
        import pathlib
        
        config_files = list(pathlib.Path("src/configuration").glob("*.py"))
        
        for file_path in config_files:
            if file_path.name == "__pycache__":
                continue
                
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for dict.get() with default argument
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'get' and 
                        len(node.args) > 1):
                        # Second argument to get() is a default value
                        assert False, f"Found dict.get() with default in {file_path}: line {node.lineno}"
    
    def test_required_settings_validation(self):
        """Test that missing required settings cause failures"""
        from src.configuration.execution_config import ExecutionConfig
        
        # Test with incomplete config
        incomplete_config = {
            "timeout": 30000,
            # Missing other required fields
        }
        
        # Should not silently use defaults
        with pytest.raises(Exception):
            ExecutionConfig.from_dict(incomplete_config)
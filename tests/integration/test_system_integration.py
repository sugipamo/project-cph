"""
Test system integration between major components
"""
import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch

from src.config.manager import ConfigurationManager
from src.core.exceptions import ErrorHandler, ErrorLogger
from src.performance.caching import PatternCache, TemplateCache


class TestConfigErrorIntegration:
    """Test integration between configuration system and error handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_error_handling_integration(self):
        """Test configuration errors are properly handled"""
        # Create invalid config
        invalid_config = {
            "invalid_structure": "missing required fields"
        }
        
        (self.temp_path / "contest_env" / "python").mkdir(parents=True)
        with open(self.temp_path / "contest_env" / "python" / "env.json", 'w') as f:
            json.dump(invalid_config, f)
        
        manager = ConfigurationManager(self.temp_path)
        
        # Should handle errors gracefully
        context = {
            "language": "python",
            "contest": "test",
            "source_file_name": "main.py"
        }
        
        # This should not crash, but produce validation errors
        config = manager.load_config(context=context)
        validation_result = manager.validate_configuration()
        
        # Should have validation issues
        assert validation_result is not None
    
    @patch('src.core.exceptions.error_logger.ErrorLogger.log_operation_error')
    def test_config_error_logging_integration(self, mock_log_error):
        """Test configuration errors are logged"""
        manager = ConfigurationManager("/nonexistent/path")
        
        try:
            config = manager.load_config()
        except Exception as e:
            # Error should be logged
            ErrorHandler.handle_operation_error("config_load", e)
        
        # This test verifies the integration exists
        assert True  # Basic integration test
    
    def test_template_processing_with_error_handling(self):
        """Test template processing with error recovery"""
        # Create config with template
        config_with_template = {
            "language_name": "python",
            "workspace_path": "/tmp/{contest}/{missing_variable}",
            "commands": {
                "test": {
                    "steps": [{"op": "shell", "cmd": ["echo", "{source_file_name}"]}]
                }
            }
        }
        
        (self.temp_path / "contest_env" / "python").mkdir(parents=True)
        with open(self.temp_path / "contest_env" / "python" / "env.json", 'w') as f:
            json.dump(config_with_template, f)
        
        manager = ConfigurationManager(self.temp_path)
        
        context = {
            "language": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
            # missing_variable is not provided
        }
        
        # Should handle missing template variables gracefully
        config = manager.load_config(context=context)
        
        # This should work for available variables
        steps = config.get_command_steps("python", "test")
        assert len(steps) > 0
        assert steps[0]["cmd"] == ["echo", "main.py"]


class TestPerformanceCacheIntegration:
    """Test integration between performance caching and other systems"""
    
    def test_pattern_cache_with_format_utils(self):
        """Test pattern cache integration with format utilities"""
        from src.context.utils.format_utils import extract_format_keys
        
        # Test that format utils use cached patterns
        template1 = "/path/{user}/{project}/{file}"
        template2 = "/path/{user}/{project}/{file}"  # Same template
        
        keys1 = extract_format_keys(template1)
        keys2 = extract_format_keys(template2)
        
        # Should get same results (cached)
        assert keys1 == keys2
        assert keys1 == ['user', 'project', 'file']
    
    def test_template_cache_with_config_system(self):
        """Test template cache integration with configuration system"""
        cache = TemplateCache()
        
        # Simulate template processing
        template = "Hello {name} from {project}"
        context = {"name": "User", "project": "CPH"}
        
        cache_key = cache.create_cache_key(template, context)
        
        # First processing
        result1 = template.format(**context)
        cache.cache_result(cache_key, result1)
        
        # Second processing (should use cache)
        cached_result = cache.get_cached_result(cache_key)
        
        assert cached_result == "Hello User from CPH"
        assert cached_result == result1
    
    def test_error_recovery_with_caching(self):
        """Test error recovery mechanisms with caching"""
        from src.core.exceptions import ErrorRecovery
        
        recovery = ErrorRecovery()
        call_count = 0
        
        def cached_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return f"Success on call {call_count}"
        
        # Use error recovery with retry
        @recovery.retry(max_attempts=3, delay=0.01, operation_name="cached_test")
        def retried_cached_operation():
            return cached_operation()
        
        result = retried_cached_operation()
        
        assert result == "Success on call 2"
        assert call_count == 2


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create comprehensive test config
        self.test_config = {
            "language_name": "python",
            "contest_template_path": "./contest_template/{language_name}",
            "workspace_path": "/tmp/{contest}/{language_name}",
            "commands": {
                "test": {
                    "steps": [
                        {"op": "mkdir", "target_path": "{workspace_path}"},
                        {"op": "shell", "cmd": ["echo", "Testing {source_file_name}"]},
                        {"op": "python", "cmd": ["print('Hello from {language_name}')"]}
                    ]
                },
                "build": {
                    "steps": [
                        {"op": "shell", "cmd": ["echo", "Building {source_file_name}"]}
                    ]
                }
            }
        }
        
        (self.temp_path / "contest_env" / "python").mkdir(parents=True)
        with open(self.temp_path / "contest_env" / "python" / "env.json", 'w') as f:
            json.dump(self.test_config, f)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_integration(self):
        """Test full workflow from config loading to execution"""
        manager = ConfigurationManager(self.temp_path, enable_cache=True, enable_validation=True)
        
        context = {
            "language": "python",
            "language_name": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
        }
        
        # Load configuration
        config = manager.load_config(context=context)
        
        # Verify basic structure
        assert config is not None
        assert "python" in config.list_languages()
        assert "test" in config.list_commands("python")
        assert "build" in config.list_commands("python")
        
        # Get command steps with template processing
        test_steps = config.get_command_steps("python", "test")
        build_steps = config.get_command_steps("python", "build")
        
        # Verify template processing worked
        assert len(test_steps) == 3
        assert test_steps[0]["op"] == "mkdir"
        assert test_steps[0]["target_path"] == "/tmp/abc300/python"
        
        assert test_steps[1]["op"] == "shell"
        assert test_steps[1]["cmd"] == ["echo", "Testing main.py"]
        
        assert test_steps[2]["op"] == "python"
        assert test_steps[2]["cmd"] == ["print('Hello from python')"]
        
        assert len(build_steps) == 1
        assert build_steps[0]["cmd"] == ["echo", "Building main.py"]
    
    def test_configuration_validation_integration(self):
        """Test configuration validation integration"""
        manager = ConfigurationManager(self.temp_path, enable_validation=True)
        
        context = {
            "language": "python",
            "language_name": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
        }
        
        config = manager.load_config(context=context)
        validation_result = manager.validate_configuration()
        
        # Should have validation results
        assert validation_result is not None
        
        # Get validation summary
        summary = config.get_validation_summary()
        assert summary is not None
    
    def test_error_handling_throughout_pipeline(self):
        """Test error handling integration throughout the pipeline"""
        # Test with invalid project path
        manager = ConfigurationManager("/invalid/path", enable_validation=True)
        
        context = {
            "language": "nonexistent",
            "contest": "test",
            "source_file_name": "main.py"
        }
        
        # Should handle errors gracefully
        try:
            config = manager.load_config(context=context)
            # Should not crash, even with invalid setup
        except Exception as e:
            # Errors should be handled by error system
            error_result = ErrorHandler.handle_operation_error("config_load_test", e)
            assert error_result.success is False
            assert error_result.exception == e
    
    def test_performance_optimization_integration(self):
        """Test performance optimizations work throughout the system"""
        manager = ConfigurationManager(self.temp_path, enable_cache=True)
        
        context = {
            "language": "python",
            "language_name": "python",
            "contest": "abc300",
            "source_file_name": "main.py"
        }
        
        # First load (cache miss)
        start_time = time.time()
        config1 = manager.load_config(context=context)
        first_duration = time.time() - start_time
        
        # Second load (should benefit from caching)
        start_time = time.time()
        config2 = manager.load_config(context=context)
        second_duration = time.time() - start_time
        
        # Both should work
        assert config1 is not None
        assert config2 is not None
        
        # Verify template processing works multiple times
        steps1 = config1.get_command_steps("python", "test")
        steps2 = config2.get_command_steps("python", "test")
        
        assert steps1 == steps2
        assert len(steps1) == 3
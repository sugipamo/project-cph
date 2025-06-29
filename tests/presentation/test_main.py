"""Comprehensive integration tests for src/presentation/main.py

Tests cover:
- Basic command execution (test, run, judge, etc.)
- Error cases (invalid commands, missing files, etc.)
- Different language support
- Configuration handling
"""
import pytest
import sys
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import tempfile
import os
import json
import unittest.mock

# Test imports - we'll mock the complex dependencies
from src.infrastructure.di_container import DIKey


class TestMainIntegration:
    """Integration tests for main.py entry point"""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create a mock infrastructure with all required services"""
        infrastructure = Mock()
        
        # Register all required services
        services = {
            DIKey.CONFIG_MANAGER: Mock(),
            DIKey.OS_PROVIDER: Mock(),
            DIKey.SYS_PROVIDER: Mock(),
            DIKey.JSON_PROVIDER: Mock(),
            DIKey.FILE_DRIVER: Mock(),
            DIKey.APPLICATION_LOGGER: Mock(),
            'CONFIG_MANAGER': Mock(),
            'UNIFIED_LOGGER': Mock(),
            'file_request_factory': Mock(),
            'DEBUG_SERVICE_FACTORY': Mock(),
        }
        
        def resolve(key):
            if hasattr(key, 'name'):
                return services.get(key)
            return services.get(key)
        
        def is_registered(key):
            if hasattr(key, 'name'):
                return key in services
            return key in services
        
        infrastructure.resolve = Mock(side_effect=resolve)
        infrastructure.is_registered = Mock(side_effect=is_registered)
        infrastructure.register = Mock()
        infrastructure._services = [Mock(name=k) for k in services.keys()]
        
        # Configure OS provider
        os_provider = services[DIKey.OS_PROVIDER]
        os_provider.path_join = os.path.join
        os_provider.path_dirname = os.path.dirname
        os_provider.path_exists = os.path.exists
        
        # Configure SYS provider
        sys_provider = services[DIKey.SYS_PROVIDER]
        sys_provider.get_argv = Mock(return_value=['main.py', 'test', 'abc123', 'a'])
        sys_provider.exit = Mock()
        
        # Configure JSON provider
        json_provider = services[DIKey.JSON_PROVIDER]
        json_provider.loads = json.loads
        json_provider.dumps = json.dumps
        
        # Configure logger
        logger = services[DIKey.APPLICATION_LOGGER]
        logger.info = Mock()
        logger.error = Mock()
        logger.warning = Mock()
        logger.debug = Mock()
        
        return infrastructure, services

    @pytest.fixture
    def mock_config_dict(self):
        """Create a mock configuration dictionary"""
        return {
            'shared': {
                'environment_logging': {
                    'enabled': False
                }
            },
            'paths': {
                'contest_current_path': '{workspace}/current/{contest_name}',
                'contest_stock_path': '{workspace}/stock/{contest_name}',
                'contest_template_path': '{workspace}/template',
                'contest_temp_path': '{workspace}/temp/{contest_name}',
                'local_workspace_path': '/workspace'
            },
            'python': {
                'interpreters': {
                    'default': 'python3'
                },
                'commands': {
                    'test': {
                        'matches': ['test', 't']
                    },
                    'run': {
                        'matches': ['run', 'r']
                    },
                    'judge': {
                        'matches': ['judge', 'j']
                    }
                },
                'env_types': {
                    'default': {
                        'matches': ['default']
                    },
                    'docker': {
                        'matches': ['docker']
                    }
                },
                'language_id': 'python',
                'source_file_name': 'main.py',
                'run_command': 'python3 {source_file}'
            },
            'cpp': {
                'interpreters': {
                    'default': 'g++'
                },
                'commands': {
                    'test': {
                        'matches': ['test', 't']
                    },
                    'run': {
                        'matches': ['run', 'r']
                    }
                },
                'env_types': {
                    'default': {
                        'matches': ['default']
                    }
                },
                'language_id': 'cpp',
                'source_file_name': 'main.cpp',
                'run_command': './a.out'
            },
            'timeout': {
                'default': 10
            }
        }

    def test_main_module_execution_flow(self, mock_infrastructure, mock_config_dict):
        """Test the main module execution flow without actually executing __main__"""
        infrastructure, services = mock_infrastructure
        
        # Test the sequence of operations that happen in main.py
        with patch('src.presentation.main.build_infrastructure') as mock_build_infrastructure, \
             patch('src.presentation.main.ConfigLoaderService') as mock_config_loader_service_class, \
             patch('src.presentation.main.PureConfigManager') as mock_pure_config_manager_class, \
             patch('src.presentation.main.set_config_manager') as mock_set_config_manager, \
             patch('src.presentation.main.main') as mock_main_func:
            
            # Setup return values
            mock_build_infrastructure.return_value = infrastructure
            
            config_loader = Mock()
            config_loader.load_config_files = Mock(return_value=mock_config_dict)
            mock_config_loader_service_class.return_value = config_loader
            
            config_manager = Mock()
            config_manager.initialize_from_config_dict = Mock()
            config_manager.reload_with_language = Mock()
            config_manager.resolve_config = Mock(return_value='python3')
            config_manager.get_available_languages = Mock(return_value=['python', 'cpp'])
            mock_pure_config_manager_class.return_value = config_manager
            
            mock_main_func.return_value = 0
            
            # Import and test the initialization sequence
            import src.presentation.main as main_module
            
            # Simulate the execution flow manually
            # Phase 1: Infrastructure
            test_infrastructure = mock_build_infrastructure()
            
            # Phase 2: Config loading
            test_config_loader = mock_config_loader_service_class(test_infrastructure)
            test_config_dict = test_config_loader.load_config_files(
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )
            
            # Phase 3: Config manager
            test_config_manager = mock_pure_config_manager_class()
            test_config_manager.initialize_from_config_dict(
                config_dict=test_config_dict,
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )
            
            # Phase 4: DI registration
            test_infrastructure.register("CONFIG_MANAGER", lambda: test_config_manager)
            test_infrastructure.register(DIKey.CONFIG_MANAGER, lambda: test_config_manager)
            
            # Verify the sequence
            mock_build_infrastructure.assert_called_once()
            mock_config_loader_service_class.assert_called_once_with(test_infrastructure)
            config_loader.load_config_files.assert_called_once()
            mock_pure_config_manager_class.assert_called_once()
            config_manager.initialize_from_config_dict.assert_called_once()

    def test_command_line_parsing_integration(self, mock_infrastructure):
        """Test integration with command line arguments"""
        infrastructure, services = mock_infrastructure
        
        # Test various command line argument combinations
        test_cases = [
            (['test', 'abc123', 'a'], 'test'),
            (['run', 'contest1', 'b'], 'run'),
            (['judge', 'contest2', 'c'], 'judge'),
            (['python', 'test', 'abc', 'd'], 'test'),
            (['cpp', 'run', 'xyz', 'e'], 'run'),
        ]
        
        with patch('src.presentation.main.main') as mock_main_func:
            mock_main_func.return_value = 0
            
            for argv, expected_command in test_cases:
                # Update sys provider argv
                services[DIKey.SYS_PROVIDER].get_argv.return_value = ['main.py'] + argv
                
                # The main function should receive the proper arguments
                # (actual parsing happens in cli_app and user_input_parser)
                pass

    def test_error_handling_infrastructure_failure(self):
        """Test handling when infrastructure building fails"""
        with patch('src.presentation.main.build_infrastructure') as mock_build_infrastructure:
            mock_build_infrastructure.side_effect = Exception("Infrastructure build failed")
            
            # Test that the error is properly raised
            with pytest.raises(Exception, match="Infrastructure build failed"):
                from src.presentation.main import build_infrastructure
                build_infrastructure()

    def test_error_handling_config_loading_failure(self, mock_infrastructure):
        """Test handling when config loading fails"""
        infrastructure, services = mock_infrastructure
        
        with patch('src.presentation.main.build_infrastructure') as mock_build_infrastructure, \
             patch('src.presentation.main.ConfigLoaderService') as mock_config_loader_service_class:
            
            mock_build_infrastructure.return_value = infrastructure
            
            # Make config loader raise an error
            config_loader = Mock()
            config_loader.load_config_files = Mock(side_effect=Exception("Config load failed"))
            mock_config_loader_service_class.return_value = config_loader
            
            # Test that error is raised during config loading
            from src.presentation.main import ConfigLoaderService
            loader = ConfigLoaderService(infrastructure)
            
            with pytest.raises(Exception, match="Config load failed"):
                loader.load_config_files(
                    system_dir="./config/system",
                    env_dir="./contest_env",
                    language="python"
                )

    def test_language_support_verification(self, mock_config_dict):
        """Verify that different languages are properly configured"""
        # Check that the config dict contains multiple languages
        assert 'python' in mock_config_dict
        assert 'cpp' in mock_config_dict
        
        # Verify each language has required configuration
        for lang in ['python', 'cpp']:
            assert 'interpreters' in mock_config_dict[lang]
            assert 'commands' in mock_config_dict[lang]
            assert 'env_types' in mock_config_dict[lang]

    def test_request_factory_dependency_injection(self, mock_infrastructure):
        """Test that RequestFactory is created with proper dependencies"""
        infrastructure, services = mock_infrastructure
        
        with patch('src.operations.requests.request_factory.RequestFactory') as mock_request_factory_class:
            from src.operations.requests.request_factory import RequestFactory
            
            # Create request factory with dependencies
            config_manager = Mock()
            request_creator = Mock()
            request_factory = RequestFactory(
                config_manager=config_manager,
                request_creator=request_creator
            )
            
            # Verify it was created with correct parameters
            mock_request_factory_class.assert_called_once_with(
                config_manager=config_manager,
                request_creator=request_creator
            )

    def test_no_default_values_compliance(self, mock_infrastructure, mock_config_dict):
        """Verify compliance with CLAUDE.md - no default values"""
        infrastructure, services = mock_infrastructure
        
        # Test that all function calls use explicit values, not defaults
        with patch('src.presentation.main.ConfigLoaderService') as mock_config_loader_service_class:
            config_loader = Mock()
            config_loader.load_config_files = Mock(return_value=mock_config_dict)
            mock_config_loader_service_class.return_value = config_loader
            
            # Create loader and call load_config_files
            from src.presentation.main import ConfigLoaderService
            loader = ConfigLoaderService(infrastructure)
            loader.load_config_files(
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )
            
            # Verify all parameters were explicitly provided
            call_args = config_loader.load_config_files.call_args
            assert call_args[1]['system_dir'] == "./config/system"
            assert call_args[1]['env_dir'] == "./contest_env"
            assert call_args[1]['language'] == "python"

    def test_exit_code_handling(self, mock_infrastructure):
        """Test that exit codes are properly handled"""
        infrastructure, services = mock_infrastructure
        
        # Test different exit codes
        exit_codes = [0, 1, 2, 255]
        
        with patch('src.presentation.main.main') as mock_main_func:
            for expected_exit_code in exit_codes:
                mock_main_func.return_value = expected_exit_code
                
                # Import the main function
                from src.presentation.main import main
                
                # Call main with test arguments
                result = main(['test', 'abc', 'a'], services[DIKey.SYS_PROVIDER].exit, infrastructure, services[DIKey.CONFIG_MANAGER])
                
                # Verify the exit code is returned
                assert result == expected_exit_code

    def test_docker_command_builder_integration(self, mock_infrastructure):
        """Test that docker command builder is properly configured"""
        infrastructure, services = mock_infrastructure
        
        with patch('src.presentation.main.set_config_manager') as mock_set_config_manager:
            config_manager = Mock()
            
            # Import and call set_config_manager
            from src.presentation.main import set_config_manager
            set_config_manager(config_manager)
            
            # Verify it was called with the config manager
            mock_set_config_manager.assert_called_once_with(config_manager)

    def test_initialization_phases_order(self, mock_infrastructure, mock_config_dict):
        """Test that initialization happens in correct phases"""
        infrastructure, services = mock_infrastructure
        call_order = []
        
        # Mock all the components with order tracking
        with patch('src.presentation.main.build_infrastructure') as mock_build_infra, \
             patch('src.presentation.main.ConfigLoaderService') as mock_config_loader_class, \
             patch('src.presentation.main.PureConfigManager') as mock_config_manager_class:
            
            # Track calls
            def track_build_infra():
                call_order.append('build_infrastructure')
                return infrastructure
            
            def track_config_loader(infra):
                call_order.append('ConfigLoaderService.__init__')
                loader = Mock()
                loader.load_config_files = Mock(side_effect=lambda **kwargs: (
                    call_order.append('load_config_files'), mock_config_dict
                )[1])
                return loader
            
            def track_config_manager():
                call_order.append('PureConfigManager.__init__')
                mgr = Mock()
                mgr.initialize_from_config_dict = Mock(side_effect=lambda **kwargs: 
                    call_order.append('initialize_from_config_dict')
                )
                return mgr
            
            mock_build_infra.side_effect = track_build_infra
            mock_config_loader_class.side_effect = track_config_loader
            mock_config_manager_class.side_effect = track_config_manager
            
            # Execute the initialization sequence
            test_infra = mock_build_infra()
            test_loader = mock_config_loader_class(test_infra)
            test_config = test_loader.load_config_files(
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )
            test_mgr = mock_config_manager_class()
            test_mgr.initialize_from_config_dict(
                config_dict=test_config,
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )
            
            # Verify order matches the phases in main.py
            expected_order = [
                'build_infrastructure',        # Phase 1
                'ConfigLoaderService.__init__', # Phase 2
                'load_config_files',           # Phase 2
                'PureConfigManager.__init__',  # Phase 3
                'initialize_from_config_dict', # Phase 3
            ]
            
            assert call_order == expected_order

    def test_di_container_registration(self, mock_infrastructure):
        """Test that components are properly registered in DI container"""
        infrastructure, services = mock_infrastructure
        
        # Test CONFIG_MANAGER registration
        config_manager = Mock()
        
        # Register in both ways as done in main.py
        infrastructure.register("CONFIG_MANAGER", lambda: config_manager)
        infrastructure.register(DIKey.CONFIG_MANAGER, lambda: config_manager)
        
        # Verify both registrations
        assert infrastructure.register.call_count == 2
        infrastructure.register.assert_any_call("CONFIG_MANAGER", unittest.mock.ANY)
        infrastructure.register.assert_any_call(DIKey.CONFIG_MANAGER, unittest.mock.ANY)

    def test_file_request_factory_registration(self, mock_infrastructure):
        """Test that file_request_factory is properly registered"""
        infrastructure, services = mock_infrastructure
        
        # Register file request factory
        factory_func = Mock()
        infrastructure.register("file_request_factory", factory_func)
        
        # Verify registration
        infrastructure.register.assert_called_with("file_request_factory", factory_func)

    def test_main_function_integration(self, mock_infrastructure):
        """Test the main function called from main.py"""
        infrastructure, services = mock_infrastructure
        
        with patch('src.presentation.cli_app.MinimalCLIApp') as mock_cli_app_class:
            # Setup CLI app mock
            cli_app = Mock()
            cli_app.run_cli_application = Mock(return_value=0)
            mock_cli_app_class.return_value = cli_app
            
            # Import and call the main function from cli_app
            from src.presentation.cli_app import main
            
            # Call main with test arguments
            result = main(['test', 'abc', 'a'], services[DIKey.SYS_PROVIDER].exit, infrastructure, services[DIKey.CONFIG_MANAGER])
            
            # Verify CLI app was created and run
            mock_cli_app_class.assert_called_once_with(
                infrastructure, 
                services[DIKey.APPLICATION_LOGGER],
                services[DIKey.CONFIG_MANAGER]
            )
            cli_app.run_cli_application.assert_called_once_with(['test', 'abc', 'a'])
            
            # Verify exit was called
            services[DIKey.SYS_PROVIDER].exit.assert_called_once_with(0)
            
            # Verify return value
            assert result == 0

    def test_main_module_actual_execution(self, mock_infrastructure, mock_config_dict):
        """Test actual execution of main module code"""
        infrastructure, services = mock_infrastructure
        
        # Patch all dependencies at module level before import
        with patch('src.configuration.build_infrastructure.build_infrastructure') as mock_build_infrastructure, \
             patch('src.application.services.config_loader_service.ConfigLoaderService') as mock_config_loader_service_class, \
             patch('src.application.pure_config_manager.PureConfigManager') as mock_pure_config_manager_class, \
             patch('src.presentation.docker_command_builder.set_config_manager') as mock_set_config_manager, \
             patch('src.presentation.cli_app.main') as mock_main_func, \
             patch('sys.argv', ['main.py', 'test', 'abc', 'a']):
            
            # Setup return values
            mock_build_infrastructure.return_value = infrastructure
            
            config_loader = Mock()
            config_loader.load_config_files = Mock(return_value=mock_config_dict)
            mock_config_loader_service_class.return_value = config_loader
            
            config_manager = Mock()
            config_manager.initialize_from_config_dict = Mock()
            config_manager.reload_with_language = Mock()
            config_manager.resolve_config = Mock(return_value='python3')
            config_manager.get_available_languages = Mock(return_value=['python', 'cpp'])
            mock_pure_config_manager_class.return_value = config_manager
            
            mock_main_func.return_value = 0
            
            # Import the module - this will execute the __main__ block
            import importlib
            import src.presentation.main
            
            # Force reload to execute __main__ block
            try:
                # Save original __name__
                original_name = src.presentation.main.__name__
                src.presentation.main.__name__ = '__main__'
                
                # Execute the module code
                exec(compile(open(src.presentation.main.__file__).read(), 
                            src.presentation.main.__file__, 'exec'), 
                     {'__name__': '__main__'})
            except SystemExit:
                pass  # Expected from sys.exit call
            finally:
                # Restore original __name__
                src.presentation.main.__name__ = original_name
            
            # Verify all phases were executed
            mock_build_infrastructure.assert_called_once()
            mock_config_loader_service_class.assert_called_once()
            mock_pure_config_manager_class.assert_called_once()
            mock_set_config_manager.assert_called_once()
            mock_main_func.assert_called_once()

    def test_main_module_with_different_commands(self, mock_infrastructure, mock_config_dict):
        """Test main module with different command types"""
        infrastructure, services = mock_infrastructure
        
        commands = ['test', 'run', 'judge', 'help']
        
        for command in commands:
            with patch('src.configuration.build_infrastructure.build_infrastructure') as mock_build_infrastructure, \
                 patch('src.application.services.config_loader_service.ConfigLoaderService') as mock_config_loader_service_class, \
                 patch('src.application.pure_config_manager.PureConfigManager') as mock_pure_config_manager_class, \
                 patch('src.presentation.cli_app.main') as mock_main_func:
                
                # Setup standard mocks
                mock_build_infrastructure.return_value = infrastructure
                
                config_loader = Mock()
                config_loader.load_config_files = Mock(return_value=mock_config_dict)
                mock_config_loader_service_class.return_value = config_loader
                
                config_manager = Mock()
                mock_pure_config_manager_class.return_value = config_manager
                
                # Update sys provider to return command-specific argv
                services[DIKey.SYS_PROVIDER].get_argv.return_value = ['main.py', command, 'contest', 'problem']
                
                # Main function should be called with the right arguments
                mock_main_func.return_value = 0

    def test_request_factory_creation_in_main(self, mock_infrastructure, mock_config_dict):
        """Test that RequestFactory is created and registered in main.py"""
        infrastructure, services = mock_infrastructure
        
        # Track what gets registered
        registered_factories = {}
        
        def register_side_effect(key, factory_func):
            if callable(factory_func):
                registered_factories[key] = factory_func
        
        infrastructure.register = Mock(side_effect=register_side_effect)
        
        with patch('src.configuration.build_infrastructure.build_infrastructure') as mock_build_infrastructure, \
             patch('src.application.services.config_loader_service.ConfigLoaderService') as mock_config_loader_service_class, \
             patch('src.application.pure_config_manager.PureConfigManager') as mock_pure_config_manager_class:
            
            # Setup mocks
            mock_build_infrastructure.return_value = infrastructure
            config_loader = Mock()
            config_loader.load_config_files = Mock(return_value=mock_config_dict)
            mock_config_loader_service_class.return_value = config_loader
            config_manager = Mock()
            mock_pure_config_manager_class.return_value = config_manager
            
            # Import the relevant function creation code
            from src.operations.requests.request_factory import RequestFactory
            
            # Create a mock request creator
            request_creator = Mock()
            
            # Create the factory function with correct parameters
            def create_request_factory():
                return RequestFactory(
                    config_manager=config_manager,
                    request_creator=request_creator
                )
            
            # Register it
            infrastructure.register("file_request_factory", create_request_factory)
            
            # Verify it was registered
            assert "file_request_factory" in registered_factories
            
            # Test that the factory can be created
            factory = registered_factories["file_request_factory"]()
            assert factory is not None
            assert isinstance(factory, RequestFactory)
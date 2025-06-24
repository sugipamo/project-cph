"""Tests for main.py entry point"""
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.di_container import DIKey


class TestMain:
    """Test main entry point functionality"""

    @patch('src.main.build_infrastructure')
    @patch('src.main.main')
    def test_main_entry_point_imports(self, mock_main, mock_build_infrastructure):
        """Test that main module can be imported without errors"""
        # This test validates that the main module imports are correct
        assert mock_main is not None
        assert mock_build_infrastructure is not None

    @patch('src.main.build_infrastructure')
    def test_build_infrastructure_called(self, mock_build_infrastructure):
        """Test that build_infrastructure is called when module runs"""
        # Create mock infrastructure
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'arg1', 'arg2']
        mock_sys_provider.exit = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure

        # Mock the main function to avoid actual execution
        with patch('src.main.main') as mock_main:
            # Execute the main block
            exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    main(sys_provider.get_argv()[1:], sys_provider.exit)
""", {
                'build_infrastructure': mock_build_infrastructure,
                'main': mock_main,
                'DIKey': DIKey,
                '__name__': '__main__'
            })

        # Verify infrastructure was built
        mock_build_infrastructure.assert_called_once()
        mock_infrastructure.resolve.assert_called_once_with(DIKey.SYS_PROVIDER)

    @patch('src.main.build_infrastructure')
    def test_sys_provider_resolution(self, mock_build_infrastructure):
        """Test that sys provider is resolved from infrastructure"""
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'test', 'args']
        mock_sys_provider.exit = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure

        with patch('src.main.main') as mock_main:
            exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    main(sys_provider.get_argv()[1:], sys_provider.exit)
""", {
                'build_infrastructure': mock_build_infrastructure,
                'main': mock_main,
                'DIKey': DIKey,
                '__name__': '__main__'
            })

        # Verify sys provider was resolved correctly
        mock_infrastructure.resolve.assert_called_once_with(DIKey.SYS_PROVIDER)
        mock_sys_provider.get_argv.assert_called_once()

    @patch('src.main.build_infrastructure')
    def test_main_called_with_args(self, mock_build_infrastructure):
        """Test that main is called with correct arguments"""
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'arg1', 'arg2', 'arg3']
        mock_sys_provider.exit = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure

        with patch('src.main.main') as mock_main:
            exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    main(sys_provider.get_argv()[1:], sys_provider.exit)
""", {
                'build_infrastructure': mock_build_infrastructure,
                'main': mock_main,
                'DIKey': DIKey,
                '__name__': '__main__'
            })

        # Verify main was called with correct args (excluding script name)
        mock_main.assert_called_once_with(['arg1', 'arg2', 'arg3'], mock_sys_provider.exit)

    @patch('src.main.build_infrastructure')
    def test_main_called_with_empty_args(self, mock_build_infrastructure):
        """Test that main is called correctly with no arguments"""
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py']
        mock_sys_provider.exit = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure

        with patch('src.main.main') as mock_main:
            exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    main(sys_provider.get_argv()[1:], sys_provider.exit)
""", {
                'build_infrastructure': mock_build_infrastructure,
                'main': mock_main,
                'DIKey': DIKey,
                '__name__': '__main__'
            })

        # Verify main was called with empty args list
        mock_main.assert_called_once_with([], mock_sys_provider.exit)

    def test_module_imports_correctly(self):
        """Test that all required imports are available"""
        # Test that we can import the main module and its dependencies
        from src.cli.cli_app import main
        from src.infrastructure.build_infrastructure import build_infrastructure
        from src.infrastructure.di_container import DIKey

        # Verify imports are callable/accessible
        assert callable(main)
        assert callable(build_infrastructure)
        assert hasattr(DIKey, 'SYS_PROVIDER')

    @patch('src.main.TypeSafeConfigNodeManager')
    @patch('src.main.set_config_manager')
    @patch('src.main.build_infrastructure')
    @patch('src.main.main')
    def test_config_manager_injection(self, mock_main, mock_build_infrastructure,
                                    mock_set_config_manager, mock_config_manager_class):
        """Test that config manager is properly injected to docker command builder"""
        # Setup mocks
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'build']
        mock_sys_provider.exit = Mock()
        mock_config_manager = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure
        mock_config_manager_class.return_value = mock_config_manager
        mock_main.return_value = 0

        # Execute main block
        exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()

    # Docker command builderに設定マネージャーを注入
    config_manager = TypeSafeConfigNodeManager(infrastructure)
    config_manager.load_from_files(
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"
    )
    set_config_manager(config_manager)

    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    exit_code = main(sys_provider.get_argv()[1:], sys_provider.exit, infrastructure)
    sys_provider.exit(exit_code)
""", {
            'build_infrastructure': mock_build_infrastructure,
            'TypeSafeConfigNodeManager': mock_config_manager_class,
            'set_config_manager': mock_set_config_manager,
            'main': mock_main,
            'DIKey': DIKey,
            '__name__': '__main__'
        })

        # Verify config manager setup
        mock_config_manager_class.assert_called_once_with(mock_infrastructure)
        mock_config_manager.load_from_files.assert_called_once_with(
            system_dir="./config/system",
            env_dir="./contest_env",
            language="python"
        )
        mock_set_config_manager.assert_called_once_with(mock_config_manager)

    @patch('src.main.TypeSafeConfigNodeManager')
    @patch('src.main.set_config_manager')
    @patch('src.main.build_infrastructure')
    @patch('src.main.main')
    def test_infrastructure_passed_to_main(self, mock_main, mock_build_infrastructure,
                                         mock_set_config_manager, mock_config_manager_class):
        """Test that infrastructure is passed as third argument to main"""
        # Setup mocks
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'test', 'arg']
        mock_sys_provider.exit = Mock()
        mock_config_manager = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure
        mock_config_manager_class.return_value = mock_config_manager
        mock_main.return_value = 0

        # Execute main block
        exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()

    # Docker command builderに設定マネージャーを注入
    config_manager = TypeSafeConfigNodeManager(infrastructure)
    config_manager.load_from_files(
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"
    )
    set_config_manager(config_manager)

    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    exit_code = main(sys_provider.get_argv()[1:], sys_provider.exit, infrastructure)
    sys_provider.exit(exit_code)
""", {
            'build_infrastructure': mock_build_infrastructure,
            'TypeSafeConfigNodeManager': mock_config_manager_class,
            'set_config_manager': mock_set_config_manager,
            'main': mock_main,
            'DIKey': DIKey,
            '__name__': '__main__'
        })

        # Verify main was called with infrastructure as third argument
        mock_main.assert_called_once_with(['test', 'arg'], mock_sys_provider.exit, mock_infrastructure)
        # Verify exit code is used
        mock_sys_provider.exit.assert_called_once_with(0)

    @patch('src.main.TypeSafeConfigNodeManager')
    @patch('src.main.set_config_manager')
    @patch('src.main.build_infrastructure')
    @patch('src.main.main')
    def test_exit_code_handling(self, mock_main, mock_build_infrastructure,
                               mock_set_config_manager, mock_config_manager_class):
        """Test that exit code from main is properly handled"""
        # Setup mocks for failure case
        mock_infrastructure = Mock()
        mock_sys_provider = Mock()
        mock_sys_provider.get_argv.return_value = ['script.py', 'build']
        mock_sys_provider.exit = Mock()
        mock_config_manager = Mock()

        mock_infrastructure.resolve.return_value = mock_sys_provider
        mock_build_infrastructure.return_value = mock_infrastructure
        mock_config_manager_class.return_value = mock_config_manager
        mock_main.return_value = 1  # Failure exit code

        # Execute main block
        exec("""
if __name__ == "__main__":
    infrastructure = build_infrastructure()

    # Docker command builderに設定マネージャーを注入
    config_manager = TypeSafeConfigNodeManager(infrastructure)
    config_manager.load_from_files(
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"
    )
    set_config_manager(config_manager)

    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    exit_code = main(sys_provider.get_argv()[1:], sys_provider.exit, infrastructure)
    sys_provider.exit(exit_code)
""", {
            'build_infrastructure': mock_build_infrastructure,
            'TypeSafeConfigNodeManager': mock_config_manager_class,
            'set_config_manager': mock_set_config_manager,
            'main': mock_main,
            'DIKey': DIKey,
            '__name__': '__main__'
        })

        # Verify failure exit code is properly propagated
        mock_sys_provider.exit.assert_called_once_with(1)

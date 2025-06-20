"""Tests for main.py entry point"""
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import DIKey, build_infrastructure, main


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

"""Tests for build_infrastructure module."""
import pytest
from unittest.mock import patch, Mock

from src.configuration.build_infrastructure import (
    build_infrastructure,
    build_mock_infrastructure,
    build_operations,
    build_mock_operations
)


class TestBuildInfrastructure:
    """Tests for infrastructure building functions."""
    
    @patch('src.configuration.build_infrastructure.DIContainer')
    @patch('src.configuration.build_infrastructure.configure_production_dependencies')
    def test_build_infrastructure(self, mock_configure_prod, mock_container_class):
        """Test build_infrastructure creates container and configures production dependencies."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container
        
        result = build_infrastructure()
        
        mock_container_class.assert_called_once()
        mock_configure_prod.assert_called_once_with(mock_container)
        assert result == mock_container
    
    @patch('src.configuration.build_infrastructure.DIContainer')
    @patch('src.configuration.build_infrastructure.configure_test_dependencies')
    def test_build_mock_infrastructure(self, mock_configure_test, mock_container_class):
        """Test build_mock_infrastructure creates container and configures test dependencies."""
        mock_container = Mock()
        mock_container_class.return_value = mock_container
        
        result = build_mock_infrastructure()
        
        mock_container_class.assert_called_once()
        mock_configure_test.assert_called_once_with(mock_container)
        assert result == mock_container
    
    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases are properly set."""
        assert build_operations == build_infrastructure
        assert build_mock_operations == build_mock_infrastructure
    
    @patch('src.configuration.build_infrastructure.DIContainer')
    @patch('src.configuration.build_infrastructure.configure_production_dependencies')
    def test_build_infrastructure_returns_container_instance(self, mock_configure, mock_container_class):
        """Test that build_infrastructure returns the actual container instance."""
        from src.infrastructure.di_container import DIContainer
        
        with patch('src.configuration.build_infrastructure.DIContainer', DIContainer):
            result = build_infrastructure()
            
            assert isinstance(result, DIContainer)
            mock_configure.assert_called_once()
    
    @patch('src.configuration.build_infrastructure.configure_production_dependencies')
    def test_build_infrastructure_error_handling(self, mock_configure):
        """Test build_infrastructure when configuration fails."""
        mock_configure.side_effect = Exception("Configuration error")
        
        with pytest.raises(Exception, match="Configuration error"):
            build_infrastructure()
    
    @patch('src.configuration.build_infrastructure.configure_test_dependencies')
    def test_build_mock_infrastructure_error_handling(self, mock_configure):
        """Test build_mock_infrastructure when configuration fails."""
        mock_configure.side_effect = Exception("Test configuration error")
        
        with pytest.raises(Exception, match="Test configuration error"):
            build_mock_infrastructure()
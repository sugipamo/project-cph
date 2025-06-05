"""
Comprehensive tests for build_operations module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.operations.build_operations import build_operations, build_mock_operations
from src.operations.di_container import DIContainer
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_driver import LocalDockerDriver
from src.operations.file.local_file_driver import LocalFileDriver
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class TestBuildOperations:
    """Test build_operations function"""
    
    def test_build_operations_returns_di_container(self):
        """Test that build_operations returns a DIContainer instance"""
        operations = build_operations()
        
        assert isinstance(operations, DIContainer)
    
    def test_build_operations_registers_shell_driver(self):
        """Test that shell_driver is registered correctly"""
        operations = build_operations()
        
        shell_driver = operations.resolve('shell_driver')
        assert isinstance(shell_driver, LocalShellDriver)
    
    def test_build_operations_registers_docker_driver(self):
        """Test that docker_driver is registered correctly"""
        operations = build_operations()
        
        docker_driver = operations.resolve('docker_driver')
        assert isinstance(docker_driver, LocalDockerDriver)
    
    def test_build_operations_registers_file_driver(self):
        """Test that file_driver is registered correctly"""
        operations = build_operations()
        
        file_driver = operations.resolve('file_driver')
        assert isinstance(file_driver, LocalFileDriver)
        # Check that base_dir is set to current directory
        assert file_driver.base_dir == Path('.')
    
    def test_build_operations_registers_docker_request_class(self):
        """Test that DockerRequest class is registered correctly"""
        operations = build_operations()
        
        docker_request_class = operations.resolve('DockerRequest')
        assert docker_request_class == DockerRequest
    
    def test_build_operations_registers_docker_op_type(self):
        """Test that DockerOpType is registered correctly"""
        operations = build_operations()
        
        docker_op_type = operations.resolve('DockerOpType')
        assert docker_op_type == DockerOpType
    
    def test_build_operations_multiple_calls_return_separate_instances(self):
        """Test that multiple calls to build_operations return separate instances"""
        operations1 = build_operations()
        operations2 = build_operations()
        
        # Should be different DIContainer instances
        assert operations1 is not operations2
        
        # But should have the same types of drivers
        assert type(operations1.resolve('shell_driver')) == type(operations2.resolve('shell_driver'))
        assert type(operations1.resolve('docker_driver')) == type(operations2.resolve('docker_driver'))
        assert type(operations1.resolve('file_driver')) == type(operations2.resolve('file_driver'))
    
    def test_build_operations_drivers_are_separate_instances(self):
        """Test that each resolve call returns a new driver instance"""
        operations = build_operations()
        
        # Shell drivers should be separate instances
        shell1 = operations.resolve('shell_driver')
        shell2 = operations.resolve('shell_driver')
        assert shell1 is not shell2
        assert type(shell1) == type(shell2)
        
        # Docker drivers should be separate instances
        docker1 = operations.resolve('docker_driver')
        docker2 = operations.resolve('docker_driver')
        assert docker1 is not docker2
        assert type(docker1) == type(docker2)
        
        # File drivers should be separate instances
        file1 = operations.resolve('file_driver')
        file2 = operations.resolve('file_driver')
        assert file1 is not file2
        assert type(file1) == type(file2)
    
    def test_build_operations_file_driver_base_dir(self):
        """Test that file driver is configured with correct base directory"""
        operations = build_operations()
        
        file_driver = operations.resolve('file_driver')
        assert isinstance(file_driver.base_dir, Path)
        assert str(file_driver.base_dir) == '.'


class TestBuildMockOperations:
    """Test build_mock_operations function"""
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_returns_di_container(self, mock_shell, mock_docker, mock_file):
        """Test that build_mock_operations returns a DIContainer instance"""
        mock_file_instance = Mock()
        mock_file.return_value = mock_file_instance
        
        operations = build_mock_operations()
        
        assert isinstance(operations, DIContainer)
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_registers_mock_drivers(self, mock_shell, mock_docker, mock_file):
        """Test that mock drivers are registered correctly"""
        mock_shell_instance = Mock()
        mock_docker_instance = Mock()
        mock_file_instance = Mock()
        
        mock_shell.return_value = mock_shell_instance
        mock_docker.return_value = mock_docker_instance
        mock_file.return_value = mock_file_instance
        
        operations = build_mock_operations()
        
        # Verify drivers are registered and return mock instances
        shell_driver = operations.resolve('shell_driver')
        docker_driver = operations.resolve('docker_driver')
        file_driver = operations.resolve('file_driver')
        
        assert shell_driver == mock_shell_instance
        assert docker_driver == mock_docker_instance
        assert file_driver == mock_file_instance
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver') 
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_file_driver_base_dir(self, mock_shell, mock_docker, mock_file):
        """Test that mock file driver is created with correct base directory"""
        mock_file_instance = Mock()
        mock_file.return_value = mock_file_instance
        
        operations = build_mock_operations()
        
        # Verify MockFileDriver was called with correct base_dir
        mock_file.assert_called_once_with(base_dir=Path('.'))
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_registers_docker_classes(self, mock_shell, mock_docker, mock_file):
        """Test that DockerRequest and DockerOpType classes are registered"""
        mock_file.return_value = Mock()
        
        operations = build_mock_operations()
        
        docker_request_class = operations.resolve('DockerRequest')
        docker_op_type = operations.resolve('DockerOpType')
        
        assert docker_request_class == DockerRequest
        assert docker_op_type == DockerOpType
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_file_driver_reuse(self, mock_shell, mock_docker, mock_file):
        """Test that file driver instance is reused in mock operations"""
        mock_file_instance = Mock()
        mock_file.return_value = mock_file_instance
        
        operations = build_mock_operations()
        
        # Get file driver multiple times
        file_driver1 = operations.resolve('file_driver')
        file_driver2 = operations.resolve('file_driver')
        
        # Should be the same instance (reused)
        assert file_driver1 is file_driver2
        assert file_driver1 == mock_file_instance
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_shell_docker_separate_instances(self, mock_shell, mock_docker, mock_file):
        """Test that shell and docker drivers create separate instances"""
        # Configure mocks to return new instances on each call
        mock_shell.side_effect = lambda: Mock()
        mock_docker.side_effect = lambda: Mock()
        mock_file.return_value = Mock()
        
        operations = build_mock_operations()
        
        # Shell drivers should be separate instances
        shell1 = operations.resolve('shell_driver')
        shell2 = operations.resolve('shell_driver')
        assert shell1 is not shell2
        
        # Docker drivers should be separate instances
        docker1 = operations.resolve('docker_driver')
        docker2 = operations.resolve('docker_driver')
        assert docker1 is not docker2


class TestIntegrationScenarios:
    """Test integration scenarios between build functions"""
    
    def test_operations_compatibility(self):
        """Test that both build functions create compatible DIContainer instances"""
        real_operations = build_operations()
        
        with patch('src.operations.mock.mock_file_driver.MockFileDriver') as mock_file, \
             patch('src.operations.mock.mock_docker_driver.MockDockerDriver') as mock_docker, \
             patch('src.operations.mock.mock_shell_driver.MockShellDriver') as mock_shell:
            
            mock_file.return_value = Mock()
            mock_docker.return_value = Mock()
            mock_shell.return_value = Mock()
            
            mock_operations = build_mock_operations()
        
        # Both should be DIContainer instances
        assert isinstance(real_operations, DIContainer)
        assert isinstance(mock_operations, DIContainer)
        
        # Both should have the same registered service names
        real_shell = real_operations.resolve('shell_driver')
        mock_shell_resolved = mock_operations.resolve('shell_driver')
        
        # Types should be different but both should exist
        assert real_shell is not None
        assert mock_shell_resolved is not None
        
        # Both should have Docker classes registered
        assert real_operations.resolve('DockerRequest') == DockerRequest
        assert mock_operations.resolve('DockerRequest') == DockerRequest
    
    def test_build_operations_error_handling(self):
        """Test error handling in build_operations"""
        operations = build_operations()
        
        # Should raise KeyError for unregistered services
        with pytest.raises(KeyError):
            operations.resolve('nonexistent_service')
    
    @patch('src.operations.mock.mock_file_driver.MockFileDriver')
    @patch('src.operations.mock.mock_docker_driver.MockDockerDriver')
    @patch('src.operations.mock.mock_shell_driver.MockShellDriver')
    def test_build_mock_operations_error_handling(self, mock_shell, mock_docker, mock_file):
        """Test error handling in build_mock_operations"""
        mock_file.return_value = Mock()
        
        operations = build_mock_operations()
        
        # Should raise KeyError for unregistered services
        with pytest.raises(KeyError):
            operations.resolve('nonexistent_service')
    
    def test_production_vs_test_environment_separation(self):
        """Test that production and test environments are properly separated"""
        prod_operations = build_operations()
        
        with patch('src.operations.mock.mock_file_driver.MockFileDriver') as mock_file, \
             patch('src.operations.mock.mock_docker_driver.MockDockerDriver') as mock_docker, \
             patch('src.operations.mock.mock_shell_driver.MockShellDriver') as mock_shell:
            
            mock_file.return_value = Mock()
            mock_docker.return_value = Mock()
            mock_shell.return_value = Mock()
            
            test_operations = build_mock_operations()
        
        # Production should use real drivers
        prod_shell = prod_operations.resolve('shell_driver')
        assert isinstance(prod_shell, LocalShellDriver)
        
        # Test should use mock drivers
        test_shell = test_operations.resolve('shell_driver')
        assert not isinstance(test_shell, LocalShellDriver)  # Should be mock


class TestDriverRegistration:
    """Test specific driver registration details"""
    
    def test_shell_driver_registration_factory(self):
        """Test shell driver registration uses factory pattern"""
        operations = build_operations()
        
        # Each resolution should create a new instance
        driver1 = operations.resolve('shell_driver')
        driver2 = operations.resolve('shell_driver')
        
        assert isinstance(driver1, LocalShellDriver)
        assert isinstance(driver2, LocalShellDriver)
        assert driver1 is not driver2
    
    def test_docker_driver_registration_factory(self):
        """Test docker driver registration uses factory pattern"""
        operations = build_operations()
        
        # Each resolution should create a new instance
        driver1 = operations.resolve('docker_driver')
        driver2 = operations.resolve('docker_driver')
        
        assert isinstance(driver1, LocalDockerDriver)
        assert isinstance(driver2, LocalDockerDriver)
        assert driver1 is not driver2
    
    def test_file_driver_registration_factory(self):
        """Test file driver registration uses factory pattern"""
        operations = build_operations()
        
        # Each resolution should create a new instance
        driver1 = operations.resolve('file_driver')
        driver2 = operations.resolve('file_driver')
        
        assert isinstance(driver1, LocalFileDriver)
        assert isinstance(driver2, LocalFileDriver)
        assert driver1 is not driver2
        # Both should have same base_dir configuration
        assert driver1.base_dir == driver2.base_dir == Path('.')
    
    def test_docker_class_registration_singleton(self):
        """Test that Docker classes are registered as singletons"""
        operations = build_operations()
        
        # Should return the same class object every time
        class1 = operations.resolve('DockerRequest')
        class2 = operations.resolve('DockerRequest')
        
        assert class1 is class2
        assert class1 == DockerRequest
        
        # Same for DockerOpType
        type1 = operations.resolve('DockerOpType')
        type2 = operations.resolve('DockerOpType')
        
        assert type1 is type2
        assert type1 == DockerOpType


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @patch('src.operations.build_operations.LocalShellDriver')
    def test_build_operations_with_driver_creation_failure(self, mock_shell):
        """Test build_operations when driver creation fails"""
        mock_shell.side_effect = Exception("Driver creation failed")
        
        operations = build_operations()
        
        # Should raise exception when trying to resolve failed driver
        with pytest.raises(Exception, match="Driver creation failed"):
            operations.resolve('shell_driver')
    
    def test_build_operations_with_path_creation_failure(self):
        """Test build_operations when Path creation fails"""
        with patch('src.operations.build_operations.Path') as mock_path:
            mock_path.side_effect = Exception("Path creation failed")
            
            operations = build_operations()
            
            # Should raise exception when trying to resolve file_driver
            with pytest.raises(Exception, match="Path creation failed"):
                operations.resolve('file_driver')
    
    def test_operations_isolation(self):
        """Test that operations instances are properly isolated"""
        ops1 = build_operations()
        ops2 = build_operations()
        
        # Register something in ops1
        ops1.register('test_service', lambda: "test1")
        
        # Should not affect ops2
        with pytest.raises(KeyError):
            ops2.resolve('test_service')
        
        # ops1 should still work
        assert ops1.resolve('test_service') == "test1"
"""Tests for operation interfaces."""
import pytest
from abc import ABC
from typing import Any, Optional
from unittest.mock import Mock

from src.operations.interfaces.execution_interfaces import (
    ExecutionInterface, DockerDriverInterface, ShellExecutionInterface,
    PythonExecutionInterface
)
from src.operations.interfaces.infrastructure_interfaces import (
    FileSystemInterface, PersistenceInterface, RepositoryInterface,
    TimeInterface
)
from src.operations.interfaces.utility_interfaces import (
    LoggerInterface, OutputManagerInterface, OutputInterface, RegexInterface
)


class TestExecutionInterfaces:
    """Test execution interfaces are properly defined."""
    
    def test_execution_interface_is_abstract(self):
        """Test ExecutionInterface is abstract."""
        assert issubclass(ExecutionInterface, ABC)
        
        # Verify abstract methods
        with pytest.raises(TypeError):
            ExecutionInterface()
    
    def test_shell_execution_interface_is_abstract(self):
        """Test ShellExecutionInterface is abstract."""
        assert issubclass(ShellExecutionInterface, ABC)
        
        with pytest.raises(TypeError):
            ShellExecutionInterface()
    
    def test_python_execution_interface_is_abstract(self):
        """Test PythonExecutionInterface is abstract."""
        assert issubclass(PythonExecutionInterface, ABC)
        
        with pytest.raises(TypeError):
            PythonExecutionInterface()
    
    def test_docker_driver_interface_is_abstract(self):
        """Test DockerDriverInterface is abstract."""
        assert issubclass(DockerDriverInterface, ABC)
        
        with pytest.raises(TypeError):
            DockerDriverInterface()
    


class TestInfrastructureInterfaces:
    """Test infrastructure interfaces are properly defined."""
    
    def test_file_system_interface_is_abstract(self):
        """Test FileSystemInterface is abstract."""
        assert issubclass(FileSystemInterface, ABC)
        
        with pytest.raises(TypeError):
            FileSystemInterface()
    
    def test_persistence_interface_is_abstract(self):
        """Test PersistenceInterface is abstract."""
        assert issubclass(PersistenceInterface, ABC)
        
        with pytest.raises(TypeError):
            PersistenceInterface()
    
    def test_repository_interface_is_abstract(self):
        """Test RepositoryInterface is abstract."""
        assert issubclass(RepositoryInterface, ABC)
        
        with pytest.raises(TypeError):
            RepositoryInterface()
    
    def test_time_interface_is_abstract(self):
        """Test TimeInterface is abstract."""
        assert issubclass(TimeInterface, ABC)
        
        with pytest.raises(TypeError):
            TimeInterface()


class TestUtilityInterfaces:
    """Test utility interfaces are properly defined."""
    
    def test_logger_interface_is_abstract(self):
        """Test LoggerInterface is abstract."""
        assert issubclass(LoggerInterface, ABC)
        
        with pytest.raises(TypeError):
            LoggerInterface()
    
    def test_output_manager_interface_is_abstract(self):
        """Test OutputManagerInterface is abstract."""
        assert issubclass(OutputManagerInterface, ABC)
        
        with pytest.raises(TypeError):
            OutputManagerInterface()
    
    def test_output_interface_is_abstract(self):
        """Test OutputInterface is abstract."""
        assert issubclass(OutputInterface, ABC)
        
        with pytest.raises(TypeError):
            OutputInterface()
    
    def test_regex_interface_is_abstract(self):
        """Test RegexInterface is abstract."""
        assert issubclass(RegexInterface, ABC)
        
        with pytest.raises(TypeError):
            RegexInterface()


class MockExecutionInterface(ExecutionInterface):
    """Mock implementation of ExecutionInterface for testing."""
    
    def execute_request_operation(self, request: Any, logger: Any) -> Any:
        return Mock(success=True)


class MockShellExecutionInterface(ShellExecutionInterface):
    """Mock implementation of ShellExecutionInterface for testing."""
    
    def execute_command(self, command: str, working_directory: Optional[str] = None, 
                       timeout: Optional[float] = None, environment: Optional[dict] = None, 
                       shell: Optional[bool] = None) -> dict:
        return {
            'success': True,
            'stdout': 'output',
            'stderr': '',
            'returncode': 0
        }


class MockFileSystemInterface(FileSystemInterface):
    """Mock implementation of FileSystemInterface for testing."""
    
    def exists(self, path):
        return True
    
    def is_file(self, path):
        return True
    
    def is_dir(self, path):
        return False
    
    def iterdir(self, path):
        from pathlib import Path
        return iter([Path("file1.txt"), Path("file2.txt")])
    
    def mkdir(self, path, parents, exist_ok):
        pass
    
    def create_directory(self, path):
        pass
    
    def delete_file(self, path):
        pass


class TestInterfaceImplementations:
    """Test that interfaces can be properly implemented."""
    
    def test_execution_interface_implementation(self):
        """Test ExecutionInterface can be implemented."""
        executor = MockExecutionInterface()
        
        result = executor.execute_request_operation(Mock(), Mock())
        assert result.success is True
    
    def test_shell_execution_interface_implementation(self):
        """Test ShellExecutionInterface can be implemented."""
        shell = MockShellExecutionInterface()
        
        result = shell.execute_command("echo test")
        assert result['stdout'] == "output"
        assert result['stderr'] == ""
        assert result['returncode'] == 0
    
    def test_file_system_interface_implementation(self):
        """Test FileSystemInterface can be implemented."""
        from pathlib import Path
        
        file_ops = MockFileSystemInterface()
        
        assert file_ops.exists(Path("/test.txt")) is True
        assert file_ops.is_file(Path("/test.txt")) is True
        assert file_ops.is_dir(Path("/test")) is False
        file_ops.create_directory(Path("/test"))  # Should not raise
        file_ops.delete_file(Path("/test.txt"))  # Should not raise
        file_ops.mkdir(Path("/test"), parents=True, exist_ok=True)  # Should not raise
        
        # Test iterdir
        items = list(file_ops.iterdir(Path("/")))
        assert len(items) == 2
        assert items[0].name == "file1.txt"
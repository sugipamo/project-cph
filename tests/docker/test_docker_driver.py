"""
Comprehensive tests for docker_driver module
"""
import pytest
import unittest.mock
from unittest.mock import Mock, patch, MagicMock
from tests.base.base_test import BaseTest

from src.operations.docker.docker_driver import DockerDriver, LocalDockerDriver
from src.operations.result.result import OperationResult


class TestDockerDriverInterface(BaseTest):
    """Test abstract DockerDriver interface"""
    
    def test_docker_driver_is_abstract(self):
        """Test that DockerDriver cannot be instantiated directly"""
        with pytest.raises(TypeError):
            DockerDriver()
    
    def test_abstract_methods_defined(self):
        """Test that all required abstract methods are defined"""
        abstract_methods = [
            'run_container', 'stop_container', 'remove_container',
            'exec_in_container', 'get_logs', 'build', 
            'image_ls', 'image_rm', 'ps', 'inspect', 'cp'
        ]
        
        for method in abstract_methods:
            assert hasattr(DockerDriver, method)
            assert callable(getattr(DockerDriver, method))


class TestLocalDockerDriver(BaseTest):
    """Test LocalDockerDriver implementation"""
    
    def setup_test(self):
        """Setup test data"""
        self.driver = LocalDockerDriver()
        
        # Mock successful shell result
        self.mock_success_result = Mock()
        self.mock_success_result.success = True
        self.mock_success_result.stdout = "success output"
        self.mock_success_result.stderr = ""
        self.mock_success_result.returncode = 0
        
        # Mock failed shell result
        self.mock_failure_result = Mock()
        self.mock_failure_result.success = False
        self.mock_failure_result.stdout = ""
        self.mock_failure_result.stderr = "error output"
        self.mock_failure_result.returncode = 1
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_run_container_basic(self, mock_shell_request):
        """Test basic container run operation"""
        # Setup mock
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        # Execute
        result = self.driver.run_container("test-image", "test-container")
        
        # Verify
        assert result.success is True
        assert result.stdout == "success output"
        mock_shell_request.assert_called_once()
        mock_request_instance.execute.assert_called_once()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_run_container_with_options(self, mock_shell_request):
        """Test container run with options"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        options = {"detach": True, "port_mapping": {"8080": "80"}}
        result = self.driver.run_container(
            "test-image", 
            "test-container", 
            options=options,
            show_output=False
        )
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Check that show_output=False was passed
        call_args = mock_shell_request.call_args
        assert call_args[1]['show_output'] is False
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_stop_container(self, mock_shell_request):
        """Test container stop operation"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.stop_container("test-container")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        mock_request_instance.execute.assert_called_once()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_remove_container_basic(self, mock_shell_request):
        """Test basic container removal"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.remove_container("test-container")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_remove_container_with_force(self, mock_shell_request):
        """Test container removal with force option"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.remove_container("test-container", force=True)
        
        assert result.success is True
        mock_shell_request.assert_called_once()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_exec_in_container_string_command(self, mock_shell_request):
        """Test exec with string command"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.exec_in_container("test-container", "ls -la")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Verify command was parsed correctly
        call_args = mock_shell_request.call_args[0][0]
        assert "docker" in call_args
        assert "exec" in call_args
        assert "test-container" in call_args
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_exec_in_container_list_command(self, mock_shell_request):
        """Test exec with list command"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        command = ["ls", "-la", "/tmp"]
        result = self.driver.exec_in_container("test-container", command)
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Verify command structure
        call_args = mock_shell_request.call_args[0][0]
        assert call_args[:3] == ["docker", "exec", "test-container"]
        assert call_args[3:] == command
    
    def test_exec_in_container_invalid_command_type(self):
        """Test exec with invalid command type"""
        with pytest.raises(ValueError, match="Invalid command type"):
            self.driver.exec_in_container("test-container", 123)
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_get_logs(self, mock_shell_request):
        """Test getting container logs"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.get_logs("test-container")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Verify correct docker logs command
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "logs", "test-container"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_build_success(self, mock_shell_request):
        """Test successful docker build"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        dockerfile_content = "FROM python:3.9\\nRUN pip install pytest"
        result = self.driver.build(
            dockerfile_text=dockerfile_content,
            tag="test-image:latest"
        )
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Verify inputdata was passed
        call_kwargs = mock_shell_request.call_args[1]
        assert call_kwargs['inputdata'] == dockerfile_content
    
    def test_build_without_dockerfile_text(self):
        """Test build failure when dockerfile_text is None"""
        with pytest.raises(ValueError, match="dockerfile_text is None"):
            self.driver.build(dockerfile_text=None)
        
        with pytest.raises(ValueError, match="dockerfile_text is None"):
            self.driver.build(dockerfile_text="")
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_build_with_options(self, mock_shell_request):
        """Test build with additional options"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        dockerfile_content = "FROM python:3.9"
        options = {"no_cache": True, "build_args": {"VERSION": "1.0"}}
        
        result = self.driver.build(
            dockerfile_text=dockerfile_content,
            tag="test-image",
            options=options,
            show_output=False
        )
        
        assert result.success is True
        mock_shell_request.assert_called_once()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_image_ls(self, mock_shell_request):
        """Test listing docker images"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.image_ls()
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "image", "ls"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_image_rm(self, mock_shell_request):
        """Test removing docker image"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.image_rm("test-image:latest")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "image", "rm", "test-image:latest"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_ps_basic(self, mock_shell_request):
        """Test basic docker ps"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.ps()
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "ps"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_ps_with_all_flag(self, mock_shell_request):
        """Test docker ps with all flag"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.ps(all=True)
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "ps", "-a"]
    
    @patch('src.operations.docker.docker_driver.parse_container_names_pure')
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_ps_names_only(self, mock_shell_request, mock_parse_names):
        """Test docker ps with names_only flag"""
        # Setup mocks
        mock_request_instance = Mock()
        self.mock_success_result.stdout = "container1\\ncontainer2\\n"
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        mock_parse_names.return_value = ["container1", "container2"]
        
        result = self.driver.ps(all=False, names_only=True)
        
        # Verify result is the parsed names, not the shell result
        assert result == ["container1", "container2"]
        mock_shell_request.assert_called_once()
        mock_parse_names.assert_called_once_with("container1\\ncontainer2\\n")
        
        # Verify correct command format
        call_args = mock_shell_request.call_args[0][0]
        expected_cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        assert call_args == expected_cmd
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_inspect_basic(self, mock_shell_request):
        """Test basic docker inspect"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.inspect("test-container")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "inspect", "test-container"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_inspect_with_type(self, mock_shell_request):
        """Test docker inspect with type specification"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.inspect("test-container", type_="container")
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        assert call_args == ["docker", "inspect", "--type", "container", "test-container"]
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_cp_to_container(self, mock_shell_request):
        """Test copying file to container"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.cp(
            src="/host/file.txt",
            dst="/container/file.txt", 
            container="test-container",
            to_container=True
        )
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        expected_cmd = ["docker", "cp", "/host/file.txt", "test-container:/container/file.txt"]
        assert call_args == expected_cmd
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_cp_from_container(self, mock_shell_request):
        """Test copying file from container"""
        mock_request_instance = Mock()
        mock_request_instance.execute.return_value = self.mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.cp(
            src="/container/file.txt",
            dst="/host/file.txt",
            container="test-container", 
            to_container=False
        )
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        call_args = mock_shell_request.call_args[0][0]
        expected_cmd = ["docker", "cp", "test-container:/container/file.txt", "/host/file.txt"]
        assert call_args == expected_cmd


class TestLocalDockerDriverIntegration(BaseTest):
    """Integration-style tests for LocalDockerDriver"""
    
    def setup_test(self):
        """Setup test data"""
        self.driver = LocalDockerDriver()
    
    @patch('src.operations.docker.docker_driver.LocalShellDriver')
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_full_container_lifecycle(self, mock_shell_request, mock_shell_driver):
        """Test full container lifecycle with mocked dependencies"""
        # Setup mocks
        mock_request_instance = Mock()
        mock_success_result = Mock()
        mock_success_result.success = True
        mock_success_result.stdout = "container_id"
        mock_request_instance.execute.return_value = mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        # Test run
        run_result = self.driver.run_container("test-image", "test-container")
        assert run_result.success is True
        
        # Test exec
        exec_result = self.driver.exec_in_container("test-container", ["ls", "-la"])
        assert exec_result.success is True
        
        # Test logs
        logs_result = self.driver.get_logs("test-container")
        assert logs_result.success is True
        
        # Test stop
        stop_result = self.driver.stop_container("test-container")
        assert stop_result.success is True
        
        # Test remove
        remove_result = self.driver.remove_container("test-container")
        assert remove_result.success is True
        
        # Verify all operations called ShellRequest
        assert mock_shell_request.call_count == 5


class TestDockerDriverErrorHandling(BaseTest):
    """Test error handling scenarios"""
    
    def setup_test(self):
        """Setup test data"""
        self.driver = LocalDockerDriver()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_command_execution_failure(self, mock_shell_request):
        """Test handling of command execution failures"""
        # Setup mock for failed execution
        mock_request_instance = Mock()
        mock_failure_result = Mock()
        mock_failure_result.success = False
        mock_failure_result.stderr = "Container not found"
        mock_failure_result.returncode = 1
        mock_request_instance.execute.return_value = mock_failure_result
        mock_shell_request.return_value = mock_request_instance
        
        result = self.driver.stop_container("nonexistent-container")
        
        assert result.success is False
        assert result.stderr == "Container not found"
        assert result.returncode == 1
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_shell_request_exception(self, mock_shell_request):
        """Test handling of ShellRequest exceptions"""
        # Setup mock to raise exception
        mock_shell_request.side_effect = Exception("Shell execution failed")
        
        with pytest.raises(Exception, match="Shell execution failed"):
            self.driver.run_container("test-image")


class TestDockerDriverEdgeCases(BaseTest):
    """Test edge cases and boundary conditions"""
    
    def setup_test(self):
        """Setup test data"""
        self.driver = LocalDockerDriver()
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_exec_with_complex_command(self, mock_shell_request):
        """Test exec with complex shell command containing quotes and spaces"""
        mock_request_instance = Mock()
        mock_success_result = Mock()
        mock_success_result.success = True
        mock_request_instance.execute.return_value = mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        complex_command = 'find /tmp -name "*.txt" -exec grep "pattern" {} \\;'
        result = self.driver.exec_in_container("test-container", complex_command)
        
        assert result.success is True
        mock_shell_request.assert_called_once()
        # Verify command was properly parsed
        call_args = mock_shell_request.call_args[0][0]
        assert call_args[0:3] == ["docker", "exec", "test-container"]
        assert len(call_args) > 3  # Should have parsed the complex command
    
    @patch('src.operations.docker.docker_driver.parse_container_names_pure')
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_ps_names_only_empty_output(self, mock_shell_request, mock_parse_names):
        """Test ps names_only with empty container output"""
        mock_request_instance = Mock()
        mock_empty_result = Mock()
        mock_empty_result.success = True
        mock_empty_result.stdout = ""
        mock_request_instance.execute.return_value = mock_empty_result
        mock_shell_request.return_value = mock_request_instance
        mock_parse_names.return_value = []
        
        result = self.driver.ps(names_only=True)
        
        assert result == []
        mock_parse_names.assert_called_once_with("")
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_build_with_minimal_dockerfile(self, mock_shell_request):
        """Test build with minimal Dockerfile content"""
        mock_request_instance = Mock()
        mock_success_result = Mock()
        mock_success_result.success = True
        mock_request_instance.execute.return_value = mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        minimal_dockerfile = "FROM scratch"
        result = self.driver.build(dockerfile_text=minimal_dockerfile)
        
        assert result.success is True
        call_kwargs = mock_shell_request.call_args[1]
        assert call_kwargs['inputdata'] == minimal_dockerfile
    
    @patch('src.operations.docker.docker_driver.ShellRequest')
    def test_all_operations_with_show_output_false(self, mock_shell_request):
        """Test that show_output=False is properly passed to all operations"""
        mock_request_instance = Mock()
        mock_success_result = Mock()
        mock_success_result.success = True
        mock_request_instance.execute.return_value = mock_success_result
        mock_shell_request.return_value = mock_request_instance
        
        # Test multiple operations with show_output=False
        operations = [
            (self.driver.run_container, ["test-image"], {"show_output": False}),
            (self.driver.stop_container, ["test-container"], {"show_output": False}),
            (self.driver.get_logs, ["test-container"], {"show_output": False}),
            (self.driver.image_ls, [], {"show_output": False}),
            (self.driver.ps, [], {"show_output": False}),
        ]
        
        for operation, args, kwargs in operations:
            mock_shell_request.reset_mock()
            operation(*args, **kwargs)
            
            # Verify show_output=False was passed
            call_kwargs = mock_shell_request.call_args[1]
            assert call_kwargs.get('show_output') is False
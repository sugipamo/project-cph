"""Tests for RequestFactory - creates operation requests from steps"""
import pytest
from unittest.mock import Mock, MagicMock
from src.operations.requests.request_factory import RequestFactory
from src.domain.step import StepType


class TestRequestFactory:
    """Test suite for request factory"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_config_manager = Mock()
        self.mock_request_creator = Mock()
        self.mock_env_manager = Mock()
        self.mock_context = Mock()
        self.mock_context.problem_name = "A"
        
        self.factory = RequestFactory(
            config_manager=self.mock_config_manager,
            request_creator=self.mock_request_creator
        )
    
    def test_create_file_request_mkdir(self):
        """Test creating mkdir file request"""
        step = Mock()
        step.type = StepType.MKDIR
        step.cmd = ["/test/directory"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'MKDIR'
        assert call_args['path'] == "/test/directory"
    
    def test_create_file_request_copy(self):
        """Test creating copy file request"""
        step = Mock()
        step.type = StepType.COPY
        step.cmd = ["/source/file.txt", "/dest/file.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'COPY'
        assert call_args['path'] == "/source/file.txt"
        assert call_args['dst_path'] == "/dest/file.txt"
    
    def test_create_file_request_move(self):
        """Test creating move file request"""
        step = Mock()
        step.type = StepType.MOVE
        step.cmd = ["/source/file.txt", "/dest/file.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'MOVE'
        assert call_args['path'] == "/source/file.txt"
        assert call_args['dst_path'] == "/dest/file.txt"
    
    def test_create_file_request_remove(self):
        """Test creating remove file request"""
        step = Mock()
        step.type = StepType.REMOVE
        step.cmd = ["/file/to/remove.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'REMOVE'
        assert call_args['path'] == "/file/to/remove.txt"
    
    def test_create_shell_request_run(self):
        """Test creating shell run request"""
        step = Mock()
        step.type = StepType.RUN
        step.cmd = ["echo", "Hello, World!"]
        
        mock_request = Mock()
        self.mock_request_creator.create_shell_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_shell_request.assert_called_once()
        call_args = self.mock_request_creator.create_shell_request.call_args[1]
        assert call_args['cmd'] == ["echo", "Hello, World!"]
    
    def test_create_shell_request_chmod(self):
        """Test creating chmod request (via shell)"""
        step = Mock()
        step.type = StepType.CHMOD
        step.cmd = ["chmod", "755", "/file.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_shell_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_shell_request.assert_called_once()
        call_args = self.mock_request_creator.create_shell_request.call_args[1]
        assert call_args['cmd'] == ["chmod", "755", "/file.txt"]
    
    def test_create_python_request(self):
        """Test creating Python execution request"""
        step = Mock()
        step.type = StepType.PYTHON
        step.cmd = ["print('Hello from Python')"]
        
        mock_request = Mock()
        self.mock_request_creator.create_python_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_python_request.assert_called_once()
        call_args = self.mock_request_creator.create_python_request.call_args[1]
        assert call_args['code_or_file'] == ["print('Hello from Python')"]
    
    def test_create_docker_build_request(self):
        """Test creating Docker build request"""
        step = Mock()
        step.type = StepType.DOCKER_BUILD
        step.cmd = ["docker", "build", "-t", "myapp:latest", "."]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'BUILD'
        assert call_args['image'] == "myapp:latest"
    
    def test_create_docker_run_request(self):
        """Test creating Docker run request"""
        step = Mock()
        step.type = StepType.DOCKER_RUN
        step.cmd = ["docker", "run", "--name", "test_container", "ubuntu:latest"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'RUN'
        assert call_args['image'] == "ubuntu:latest"
        assert call_args['container'] == "test_container"
    
    def test_create_docker_exec_request(self):
        """Test creating Docker exec request"""
        step = Mock()
        step.type = StepType.DOCKER_EXEC
        step.cmd = ["running_container", "ls", "-la"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'EXEC'
        assert call_args['container'] == "running_container"
        assert call_args['command'] == ["ls", "-la"]
    
    def test_unsupported_step_type(self):
        """Test handling of unsupported step type"""
        step = Mock()
        step.type = "UNSUPPORTED_TYPE"
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result is None
        # No request creator methods should be called
        self.mock_request_creator.create_file_request.assert_not_called()
        self.mock_request_creator.create_shell_request.assert_not_called()
        self.mock_request_creator.create_python_request.assert_not_called()
        self.mock_request_creator.create_docker_request.assert_not_called()
    
    def test_missing_required_parameter(self):
        """Test error handling for missing required parameters"""
        # Create factory without config_manager to test error handling
        factory_without_config = RequestFactory(
            config_manager=None,
            request_creator=self.mock_request_creator
        )
        
        step = Mock()
        step.type = StepType.MKDIR
        # Missing cmd or empty cmd
        step.cmd = []
        
        with pytest.raises(ValueError) as exc_info:
            factory_without_config.create_request_from_step(
                step, self.mock_context, self.mock_env_manager
            )
        
        assert "No command provided for mkdir" in str(exc_info.value)
    
    def test_fallback_to_config_for_missing_command(self):
        """Test that MKDIR uses config fallback for missing command"""
        step = Mock()
        step.type = StepType.MKDIR
        # Empty cmd
        step.cmd = []
        
        # Set up config manager to return a fallback path
        self.mock_config_manager.resolve_config.return_value = "/fallback/path"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['path'] == "/fallback/path"
    
    def test_debug_tag_and_name_handling(self):
        """Test debug_tag and name are generated properly"""
        step = Mock()
        step.type = StepType.TOUCH
        step.cmd = ["/test.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        # Debug tag should include problem name from context
        assert "A" in call_args['debug_tag']  # problem_name from mock context
    
    def test_create_docker_rmi_request(self):
        """Test creating Docker rmi request"""
        step = Mock()
        step.type = StepType.DOCKER_RMI
        step.cmd = ["test_image:latest"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'REMOVE'
        assert call_args['image'] == "test_image:latest"
    
    def test_create_docker_remove_request(self):
        """Test creating Docker remove request"""
        step = Mock()
        step.type = StepType.DOCKER_RM
        step.cmd = ["test_container"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'REMOVE'
        assert call_args['container'] == "test_container"
    
    def test_create_file_request_touch(self):
        """Test creating touch file request"""
        step = Mock()
        step.type = StepType.TOUCH
        step.cmd = ["/new/file.txt"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'TOUCH'
        assert call_args['path'] == "/new/file.txt"
    
    def test_create_file_request_rmtree(self):
        """Test creating rmtree file request"""
        step = Mock()
        step.type = StepType.RMTREE
        step.cmd = ["/dir/to/remove"]
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'RMTREE'
        assert call_args['path'] == "/dir/to/remove"
    
    def test_create_docker_commit_request(self):
        """Test creating Docker commit request"""
        step = Mock()
        step.type = StepType.DOCKER_COMMIT
        step.cmd = ["test_container", "new_image:latest"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'BUILD'
        assert call_args['container'] == "test_container"
        assert call_args['image'] == "new_image:latest"
    
    
    def test_create_file_request_with_fallback_paths(self):
        """Test file requests with config fallback for missing paths"""
        # Test COPY with missing destination
        step = Mock()
        step.type = StepType.COPY
        step.cmd = ["/source.txt"]  # Missing destination
        
        self.mock_config_manager.resolve_config.return_value = "/fallback/dest.txt"
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['dst_path'] == "/fallback/dest.txt"
    
    def test_create_docker_request_with_additional_options(self):
        """Test Docker requests with additional options parsing"""
        # Test Docker run with complex command
        step = Mock()
        step.type = StepType.DOCKER_RUN
        step.cmd = ["docker", "run", "-d", "-p", "8080:80", "--name", "web", "nginx:alpine", "nginx", "-g", "daemon off;"]
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['image'] == "nginx:alpine"
        assert call_args['container'] == "web"
        assert 'options' in call_args
        
    def test_create_python_request_with_file(self):
        """Test Python request with script file"""
        step = Mock()
        step.type = StepType.PYTHON
        step.cmd = ["script.py"]
        
        mock_request = Mock()
        self.mock_request_creator.create_python_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        call_args = self.mock_request_creator.create_python_request.call_args[1]
        assert call_args['code_or_file'] == ["script.py"]
    
    def test_factory_without_dependencies(self):
        """Test factory creation without optional dependencies"""
        # Create factory without config manager
        factory = RequestFactory(config_manager=None, request_creator=self.mock_request_creator)
        assert factory.config_manager is None
        assert factory._request_creator == self.mock_request_creator
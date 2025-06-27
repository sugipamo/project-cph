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
        
        self.factory = RequestFactory(
            config_manager=self.mock_config_manager,
            request_creator=self.mock_request_creator
        )
    
    def test_create_file_request_mkdir(self):
        """Test creating mkdir file request"""
        step = Mock()
        step.type = StepType.MKDIR
        step.path = "/test/directory"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'mkdir'
        assert call_args['path'] == "/test/directory"
    
    def test_create_file_request_copy(self):
        """Test creating copy file request"""
        step = Mock()
        step.type = StepType.COPY
        step.src_path = "/source/file.txt"
        step.dst_path = "/dest/file.txt"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'copy'
        assert call_args['path'] == "/source/file.txt"
        assert call_args['dst_path'] == "/dest/file.txt"
    
    def test_create_file_request_move(self):
        """Test creating move file request"""
        step = Mock()
        step.type = StepType.MOVE
        step.src_path = "/source/file.txt"
        step.dst_path = "/dest/file.txt"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'move'
        assert call_args['path'] == "/source/file.txt"
        assert call_args['dst_path'] == "/dest/file.txt"
    
    def test_create_file_request_remove(self):
        """Test creating remove file request"""
        step = Mock()
        step.type = StepType.REMOVE
        step.path = "/file/to/remove.txt"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_file_request.assert_called_once()
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['op_type'] == 'remove'
        assert call_args['path'] == "/file/to/remove.txt"
    
    def test_create_shell_request_run(self):
        """Test creating shell run request"""
        step = Mock()
        step.type = StepType.RUN
        step.command = "echo 'Hello, World!'"
        step.cwd = "/working/dir"
        
        mock_request = Mock()
        self.mock_request_creator.create_shell_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_shell_request.assert_called_once()
        call_args = self.mock_request_creator.create_shell_request.call_args[1]
        assert call_args['command'] == "echo 'Hello, World!'"
        assert call_args['cwd'] == "/working/dir"
    
    def test_create_shell_request_chmod(self):
        """Test creating chmod request (via shell)"""
        step = Mock()
        step.type = StepType.CHMOD
        step.path = "/file.txt"
        step.mode = "755"
        
        mock_request = Mock()
        self.mock_request_creator.create_shell_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_shell_request.assert_called_once()
        call_args = self.mock_request_creator.create_shell_request.call_args[1]
        assert "chmod 755" in call_args['command']
        assert "/file.txt" in call_args['command']
    
    def test_create_python_request(self):
        """Test creating Python execution request"""
        step = Mock()
        step.type = StepType.PYTHON
        step.script = "print('Hello from Python')"
        step.cwd = "/python/dir"
        
        mock_request = Mock()
        self.mock_request_creator.create_python_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_python_request.assert_called_once()
        call_args = self.mock_request_creator.create_python_request.call_args[1]
        assert call_args['script'] == "print('Hello from Python')"
        assert call_args['cwd'] == "/python/dir"
    
    def test_create_docker_build_request(self):
        """Test creating Docker build request"""
        step = Mock()
        step.type = StepType.DOCKER_BUILD
        step.dockerfile = "Dockerfile"
        step.image_tag = "myapp:latest"
        step.build_context = "/build/context"
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'build'
        assert call_args['dockerfile'] == "Dockerfile"
        assert call_args['image_tag'] == "myapp:latest"
    
    def test_create_docker_run_request(self):
        """Test creating Docker run request"""
        step = Mock()
        step.type = StepType.DOCKER_RUN
        step.image = "ubuntu:latest"
        step.container_name = "test_container"
        step.command = "bash"
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'run'
        assert call_args['image'] == "ubuntu:latest"
        assert call_args['container_name'] == "test_container"
    
    def test_create_docker_exec_request(self):
        """Test creating Docker exec request"""
        step = Mock()
        step.type = StepType.DOCKER_EXEC
        step.container = "running_container"
        step.command = "ls -la"
        
        mock_request = Mock()
        self.mock_request_creator.create_docker_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        self.mock_request_creator.create_docker_request.assert_called_once()
        call_args = self.mock_request_creator.create_docker_request.call_args[1]
        assert call_args['op_type'] == 'exec'
        assert call_args['container'] == "running_container"
        assert call_args['command'] == "ls -la"
    
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
        step = Mock()
        step.type = StepType.MKDIR
        # Missing required 'path' attribute
        del step.path
        
        with pytest.raises(ValueError) as exc_info:
            self.factory.create_request_from_step(
                step, self.mock_context, self.mock_env_manager
            )
        
        assert "Missing required parameter: path" in str(exc_info.value)
    
    def test_fallback_to_config_for_missing_command(self):
        """Test fallback to configuration for missing command"""
        step = Mock()
        step.type = StepType.RUN
        # No command attribute
        del step.command
        
        # Set up config manager to return a command
        self.mock_config_manager.get_formatted_string.return_value = "default command"
        
        mock_request = Mock()
        self.mock_request_creator.create_shell_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        assert result == mock_request
        call_args = self.mock_request_creator.create_shell_request.call_args[1]
        assert call_args['command'] == "default command"
    
    def test_debug_tag_and_name_handling(self):
        """Test debug_tag and name are passed through"""
        step = Mock()
        step.type = StepType.TOUCH
        step.path = "/test.txt"
        step.debug_tag = "test_debug"
        step.name = "test_step"
        
        mock_request = Mock()
        self.mock_request_creator.create_file_request.return_value = mock_request
        
        result = self.factory.create_request_from_step(
            step, self.mock_context, self.mock_env_manager
        )
        
        call_args = self.mock_request_creator.create_file_request.call_args[1]
        assert call_args['debug_tag'] == "test_debug"
        assert call_args['name'] == "test_step"
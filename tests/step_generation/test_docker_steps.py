"""
Test Docker step generation and request factory
"""
import pytest
from unittest.mock import MagicMock

from src.env_core.step.step import Step, StepType
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class TestDockerSteps:
    """Test Docker step types and request generation"""
    
    def test_docker_exec_step_validation(self):
        """Test docker_exec step validation"""
        # Valid step
        step = Step(
            type=StepType.DOCKER_EXEC,
            cmd=["cph_python", "python", "main.py"]
        )
        assert step.type == StepType.DOCKER_EXEC
        assert step.cmd == ["cph_python", "python", "main.py"]
        
        # Invalid step - missing command
        with pytest.raises(ValueError, match="requires at least 2 arguments"):
            Step(
                type=StepType.DOCKER_EXEC,
                cmd=["cph_python"]  # Missing command
            )
    
    def test_docker_cp_step_validation(self):
        """Test docker_cp step validation"""
        # Valid step
        step = Step(
            type=StepType.DOCKER_CP,
            cmd=["/local/file.py", "cph_python:/workspace/file.py"]
        )
        assert step.type == StepType.DOCKER_CP
        assert step.cmd == ["/local/file.py", "cph_python:/workspace/file.py"]
        
        # Invalid step - missing destination
        with pytest.raises(ValueError, match="requires at least 2 arguments"):
            Step(
                type=StepType.DOCKER_CP,
                cmd=["/local/file.py"]  # Missing destination
            )
    
    def test_docker_run_step_validation(self):
        """Test docker_run step validation"""
        # Valid step
        step = Step(
            type=StepType.DOCKER_RUN,
            cmd=["python:3.9"]
        )
        assert step.type == StepType.DOCKER_RUN
        assert step.cmd == ["python:3.9"]
        
        # Invalid step - missing image
        with pytest.raises(ValueError, match="must have non-empty cmd"):
            Step(
                type=StepType.DOCKER_RUN,
                cmd=[]  # Missing image
            )
    
    def test_create_docker_exec_request(self):
        """Test creation of docker exec request"""
        step = Step(
            type=StepType.DOCKER_EXEC,
            cmd=["cph_python", "python", "main.py"],
            show_output=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.EXEC
        assert request.container == "cph_python"
        assert request.command == "python main.py"
        assert request.show_output is True
    
    def test_create_docker_cp_request_to_container(self):
        """Test creation of docker cp request (to container)"""
        step = Step(
            type=StepType.DOCKER_CP,
            cmd=["/local/file.py", "cph_python:/workspace/file.py"],
            allow_failure=True
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.CP
        assert request.container == "cph_python"
        assert request.allow_failure is True
        
        # Check options
        assert request.options['local_path'] == "/local/file.py"
        assert request.options['remote_path'] == "/workspace/file.py"
        assert request.options['to_container'] is True
    
    def test_create_docker_cp_request_from_container(self):
        """Test creation of docker cp request (from container)"""
        step = Step(
            type=StepType.DOCKER_CP,
            cmd=["cph_python:/workspace/output.txt", "/local/output.txt"]
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.CP
        assert request.container == "cph_python"
        
        # Check options
        assert request.options['local_path'] == "/local/output.txt"
        assert request.options['remote_path'] == "/workspace/output.txt"
        assert request.options['to_container'] is False
    
    def test_create_docker_run_request(self):
        """Test creation of docker run request"""
        step = Step(
            type=StepType.DOCKER_RUN,
            cmd=["python:3.9", "--name", "test_container"]
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.RUN
        assert request.image == "python:3.9"
        
        # Check parsed options
        assert request.options['name'] == "test_container"
    
    def test_create_docker_run_request_with_context(self):
        """Test creation of docker run request with context"""
        # Mock context with docker names
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            'container_name': 'cph_python_test',
            'oj_container_name': 'cph_ojtools_test'
        }
        
        step = Step(
            type=StepType.DOCKER_RUN,
            cmd=["python:3.9"]
        )
        
        request = PureRequestFactory.create_request_from_step(step, mock_context)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.RUN
        assert request.image == "python:3.9"
        assert request.container == "cph_python_test"
    
    def test_create_docker_run_request_oj_tools(self):
        """Test creation of docker run request for OJ tools"""
        # Mock context with docker names
        mock_context = MagicMock()
        mock_context.get_docker_names.return_value = {
            'container_name': 'cph_python_test',
            'oj_container_name': 'cph_ojtools_test'
        }
        
        step = Step(
            type=StepType.DOCKER_RUN,
            cmd=["ojtools:latest"]
        )
        
        request = PureRequestFactory.create_request_from_step(step, mock_context)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.RUN
        assert request.image == "ojtools:latest"
        assert request.container == "cph_ojtools_test"  # Should use OJ container name
    
    def test_docker_cp_invalid_format(self):
        """Test docker cp with invalid format"""
        step = Step(
            type=StepType.DOCKER_CP,
            cmd=["/local/file", "/another/local/file"]  # Both local paths
        )
        
        # This should raise an error during request creation
        request = PureRequestFactory.create_request_from_step(step)
        assert request is None  # Factory returns None for invalid steps
    
    def test_docker_exec_single_word_command(self):
        """Test docker exec with single word command"""
        step = Step(
            type=StepType.DOCKER_EXEC,
            cmd=["cph_python", "ls"]
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert request.container == "cph_python"
        assert request.command == "ls"
    
    def test_docker_exec_complex_command(self):
        """Test docker exec with complex command"""
        step = Step(
            type=StepType.DOCKER_EXEC,
            cmd=["cph_python", "python", "-c", "print('hello world')"]
        )
        
        request = PureRequestFactory.create_request_from_step(step)
        
        assert request.container == "cph_python"
        assert request.command == "python -c print('hello world')"
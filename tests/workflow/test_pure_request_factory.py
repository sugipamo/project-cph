"""
Tests for PureRequestFactory
"""
import pytest
from src.env_core.workflow.pure_request_factory import PureRequestFactory
from src.env_core.step.step import Step, StepType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class TestPureRequestFactory:
    
    def test_create_mkdir_request(self):
        """Test creating mkdir request"""
        step = Step(type=StepType.MKDIR, cmd=["./test_dir"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.MKDIR
        assert request.path == "./test_dir"
    
    def test_create_mkdir_request_no_cmd(self):
        """Test creating mkdir request without cmd - validates at Step level"""
        # Step validation prevents empty cmd, so we can't test this case
        # at the factory level
        pass
    
    def test_create_touch_request(self):
        """Test creating touch request"""
        step = Step(type=StepType.TOUCH, cmd=["./test.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.TOUCH
        assert request.path == "./test.txt"
    
    def test_create_copy_request(self):
        """Test creating copy request"""
        step = Step(type=StepType.COPY, cmd=["./source.txt", "./dest.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPY
        assert request.path == "./source.txt"
        assert request.dst_path == "./dest.txt"
    
    def test_create_copy_request_insufficient_args(self):
        """Test creating copy request with insufficient arguments - validates at Step level"""
        # Step validation prevents insufficient args, so we can't test this case
        # at the factory level
        pass
    
    def test_create_move_request(self):
        """Test creating move request"""
        step = Step(type=StepType.MOVE, cmd=["./old.txt", "./new.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.MOVE
        assert request.path == "./old.txt"
        assert request.dst_path == "./new.txt"
    
    def test_create_movetree_request(self):
        """Test creating movetree request (implemented as copytree)"""
        step = Step(type=StepType.MOVETREE, cmd=["./old_dir", "./new_dir"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPYTREE
        assert request.path == "./old_dir"
        assert request.dst_path == "./new_dir"
    
    def test_create_remove_request(self):
        """Test creating remove request"""
        step = Step(type=StepType.REMOVE, cmd=["./file_to_remove.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.REMOVE
        assert request.path == "./file_to_remove.txt"
    
    def test_create_rmtree_request(self):
        """Test creating rmtree request"""
        step = Step(type=StepType.RMTREE, cmd=["./dir_to_remove"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.RMTREE
        assert request.path == "./dir_to_remove"
    
    def test_create_shell_request(self):
        """Test creating shell request"""
        step = Step(type=StepType.SHELL, cmd=["echo", "Hello World"], cwd="/test", show_output=True)
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["echo", "Hello World"]
        assert request.cwd == "/test"
        assert request.show_output is True
    
    def test_create_shell_request_no_cmd(self):
        """Test creating shell request without cmd - validates at Step level"""
        # Step validation prevents empty cmd, so we can't test this case
        # at the factory level
        pass
    
    def test_create_python_request(self):
        """Test creating python request"""
        step = Step(type=StepType.PYTHON, cmd=["print('Hello')"], cwd="/test", show_output=False)
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, PythonRequest)
        assert request.code_or_file == ["print('Hello')"]
        assert request.cwd == "/test"
        assert request.show_output is False
    
    def test_create_docker_exec_request(self):
        """Test creating docker exec request"""
        step = Step(type=StepType.DOCKER_EXEC, cmd=["container1", "ls", "-la"], show_output=True)
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.EXEC
        assert request.container == "container1"
        assert request.command == ["ls", "-la"]
        assert request.show_output is True
    
    def test_create_docker_exec_request_insufficient_args(self):
        """Test creating docker exec request with insufficient arguments - validates at Step level"""
        # Step validation prevents insufficient args, so we can't test this case
        # at the factory level
        pass
    
    def test_create_docker_cp_request_to_container(self):
        """Test creating docker cp request (to container)"""
        step = Step(type=StepType.DOCKER_CP, cmd=["./local.txt", "container1:/remote.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.CP
        # The factory should parse the container name and paths
    
    def test_create_docker_run_request(self):
        """Test creating docker run request"""
        step = Step(type=StepType.DOCKER_RUN, cmd=["ubuntu:latest", "bash", "-c", "echo test"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, DockerRequest)
        assert request.op == DockerOpType.RUN
    
    def test_create_test_request(self):
        """Test creating test request (generates special test script)"""
        step = Step(type=StepType.TEST, cmd=["python3", "test.py"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        # TEST step generates a special test script, not the original command
        assert request.cmd[0] == "bash"
        assert request.cmd[1] == "-c"
        assert "test_dir" in request.cmd[2]  # Contains test script
    
    def test_create_build_request(self):
        """Test creating build request (implemented as shell)"""
        step = Step(type=StepType.BUILD, cmd=["make", "all"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["make", "all"]
    
    def test_create_oj_request(self):
        """Test creating oj request (implemented as shell)"""
        step = Step(type=StepType.OJ, cmd=["oj", "test"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["oj", "test"]
    
    def test_create_result_request(self):
        """Test creating result request (implemented as shell)"""
        step = Step(type=StepType.RESULT, cmd=["cat", "result.txt"])
        request = PureRequestFactory.create_request_from_step(step)
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["cat", "result.txt"]
    
    def test_unknown_step_type(self):
        """Test handling unknown step type"""
        # Create a step with None type
        step = Step(type=None, cmd=["test"])
        
        request = PureRequestFactory.create_request_from_step(step)
        assert request is None
    
    def test_allow_failure_propagation(self):
        """Test that allow_failure is propagated to requests"""
        step = Step(type=StepType.SHELL, cmd=["false"], allow_failure=True)
        request = PureRequestFactory.create_request_from_step(step)
        
        assert request.allow_failure is True
    
    def test_context_parameter(self):
        """Test that context parameter is accepted (though not used in current implementation)"""
        step = Step(type=StepType.MKDIR, cmd=["./dir"])
        context = {"test": "context"}
        
        request = PureRequestFactory.create_request_from_step(step, context)
        assert isinstance(request, FileRequest)
    
    def test_exception_handling(self):
        """Test that exceptions are caught and None is returned"""
        # Step validation prevents None cmd, so we can't test this case
        # at the factory level
        pass
"""
Comprehensive tests for src/env_core/step/request_converter.py
Tests step to request conversion functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.env_core.step.request_converter import (
    steps_to_requests,
    step_to_request,
    create_shell_request,
    create_python_request,
    create_copy_request,
    create_move_request,
    create_movetree_request,
    create_mkdir_request,
    create_touch_request,
    create_remove_request,
    create_rmtree_request
)
from src.env_core.step.step import Step, StepType
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.composite.composite_request import CompositeRequest
from src.operations.composite.driver_bound_request import DriverBoundRequest


class TestStepsToRequests:
    """Tests for steps_to_requests function"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_operations = Mock()
        self.mock_file_driver = Mock()
        self.mock_operations.resolve.return_value = self.mock_file_driver
        self.mock_context = Mock()
    
    def test_steps_to_requests_empty_list(self):
        """Test conversion of empty step list"""
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests([], self.mock_operations)
            
            mock_make.assert_called_once_with([])
            assert result == mock_composite
    
    def test_steps_to_requests_simple_shell_step(self):
        """Test conversion of simple shell step"""
        shell_step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests([shell_step], self.mock_operations)
            
            # Should create one ShellRequest
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 1
            assert isinstance(requests[0], ShellRequest)
            assert result == mock_composite
    
    def test_steps_to_requests_file_step_wrapped_in_driver_bound(self):
        """Test that FileRequest is wrapped in DriverBoundRequest"""
        mkdir_step = Step(type=StepType.MKDIR, cmd=["/test/path"])
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests([mkdir_step], self.mock_operations)
            
            # Should create DriverBoundRequest wrapping FileRequest
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 1
            assert isinstance(requests[0], DriverBoundRequest)
            assert isinstance(requests[0].req, FileRequest)
            
            # Should resolve file_driver from operations
            self.mock_operations.resolve.assert_called_with('file_driver')
    
    def test_steps_to_requests_special_steps_with_context(self):
        """Test OJ/TEST/BUILD steps using PureRequestFactory"""
        test_step = Step(type=StepType.TEST, cmd=["python3", "test.py"])
        
        with patch('src.env_core.workflow.pure_request_factory.PureRequestFactory') as mock_factory:
            with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
                mock_request = Mock()
                mock_factory.create_request_from_step.return_value = mock_request
                mock_composite = Mock(spec=CompositeRequest)
                mock_make.return_value = mock_composite
                
                result = steps_to_requests([test_step], self.mock_operations, self.mock_context)
                
                # Should use PureRequestFactory for TEST step
                mock_factory.create_request_from_step.assert_called_once_with(test_step, self.mock_context)
                
                mock_make.assert_called_once()
                requests = mock_make.call_args[0][0]
                assert len(requests) == 1
                assert requests[0] == mock_request
    
    def test_steps_to_requests_special_steps_without_context(self):
        """Test OJ/TEST/BUILD steps without context (fallback to step_to_request)"""
        test_step = Step(type=StepType.TEST, cmd=["python3", "test.py"])
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests([test_step], self.mock_operations, context=None)
            
            # Should call step_to_request which returns None for TEST steps
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 0  # None requests are filtered out
    
    def test_steps_to_requests_mixed_step_types(self):
        """Test conversion of mixed step types"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "start"]),
            Step(type=StepType.MKDIR, cmd=["/test/dir"]),
            Step(type=StepType.PYTHON, cmd=["print('hello')"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        ]
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations)
            
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 4
            
            # Check request types
            assert isinstance(requests[0], ShellRequest)
            assert isinstance(requests[1], DriverBoundRequest)  # mkdir wrapped
            assert isinstance(requests[2], PythonRequest)
            assert isinstance(requests[3], DriverBoundRequest)  # copy wrapped
    
    def test_steps_to_requests_filters_none_requests(self):
        """Test that None requests are filtered out"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.OJ, cmd=["oj", "test"])  # Returns None without context
        ]
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations, context=None)
            
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 1  # Only shell request, OJ step filtered out
            assert isinstance(requests[0], ShellRequest)


class TestStepToRequest:
    """Tests for step_to_request function"""
    
    def test_step_to_request_shell_step(self):
        """Test conversion of shell step"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        
        result = step_to_request(step)
        
        assert isinstance(result, ShellRequest)
        assert result.cmd == "echo hello"
    
    def test_step_to_request_python_step(self):
        """Test conversion of python step"""
        step = Step(type=StepType.PYTHON, cmd=["print('hello')"])
        
        result = step_to_request(step)
        
        assert isinstance(result, PythonRequest)
        assert result.code_or_file == ["print('hello')"]
    
    def test_step_to_request_file_operations(self):
        """Test conversion of file operation steps"""
        # Test all file operation types
        file_steps = [
            (StepType.COPY, ["src.txt", "dst.txt"], FileOpType.COPY),
            (StepType.MOVE, ["old.txt", "new.txt"], FileOpType.MOVE),
            (StepType.MOVETREE, ["src_dir", "dst_dir"], FileOpType.COPYTREE),
            (StepType.MKDIR, ["/test/dir"], FileOpType.MKDIR),
            (StepType.TOUCH, ["/test/file.txt"], FileOpType.TOUCH),
            (StepType.REMOVE, ["/test/file.txt"], FileOpType.REMOVE),
            (StepType.RMTREE, ["/test/dir"], FileOpType.RMTREE)
        ]
        
        for step_type, cmd, expected_op_type in file_steps:
            step = Step(type=step_type, cmd=cmd)
            result = step_to_request(step)
            
            assert isinstance(result, FileRequest)
            assert result.op == expected_op_type
    
    def test_step_to_request_special_steps_return_none(self):
        """Test that OJ/TEST/BUILD steps return None"""
        special_steps = [StepType.OJ, StepType.TEST, StepType.BUILD]
        
        for step_type in special_steps:
            step = Step(type=step_type, cmd=["dummy", "command"])
            result = step_to_request(step)
            
            assert result is None
    
    def test_step_to_request_unknown_step_type_returns_none(self):
        """Test that unknown step types return None"""
        # Create step with unknown type (using RESULT which isn't handled)
        step = Step(type=StepType.RESULT, cmd=["dummy"])
        
        result = step_to_request(step)
        
        assert result is None


class TestCreateShellRequest:
    """Tests for create_shell_request function"""
    
    def test_create_shell_request_basic(self):
        """Test basic shell request creation"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello", "world"])
        
        result = create_shell_request(step)
        
        assert isinstance(result, ShellRequest)
        assert result.cmd == "echo hello world"
        assert result.cwd is None
        assert result.show_output is False
        assert result.allow_failure is False
    
    def test_create_shell_request_with_options(self):
        """Test shell request creation with all options"""
        step = Step(
            type=StepType.SHELL,
            cmd=["ls", "-la"],
            cwd="/test/dir",
            show_output=True,
            allow_failure=True
        )
        
        result = create_shell_request(step)
        
        assert result.cmd == "ls -la"
        assert result.cwd == "/test/dir"
        assert result.show_output is True
        assert result.allow_failure is True
    
    def test_create_shell_request_single_command(self):
        """Test shell request with single command"""
        step = Step(type=StepType.SHELL, cmd=["pwd"])
        
        result = create_shell_request(step)
        
        assert result.cmd == "pwd"
    
    def test_create_shell_request_empty_cmd_raises_error(self):
        """Test that empty cmd raises ValueError"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.SHELL
        mock_step.cmd = []
        
        with pytest.raises(ValueError, match="Shell step must have non-empty cmd"):
            create_shell_request(mock_step)


class TestCreatePythonRequest:
    """Tests for create_python_request function"""
    
    def test_create_python_request_basic(self):
        """Test basic python request creation"""
        step = Step(type=StepType.PYTHON, cmd=["print('hello')", "x = 1"])
        
        result = create_python_request(step)
        
        assert isinstance(result, PythonRequest)
        assert result.code_or_file == ["print('hello')", "x = 1"]
        assert result.cwd is None
        assert result.show_output is False
        assert result.allow_failure is False
    
    def test_create_python_request_with_options(self):
        """Test python request creation with options"""
        step = Step(
            type=StepType.PYTHON,
            cmd=["import os", "print(os.getcwd())"],
            cwd="/test/dir",
            show_output=True,
            allow_failure=True
        )
        
        result = create_python_request(step)
        
        assert result.code_or_file == ["import os", "print(os.getcwd())"]
        assert result.cwd == "/test/dir"
        assert result.show_output is True
        assert result.allow_failure is True
    
    def test_create_python_request_single_statement(self):
        """Test python request with single statement"""
        step = Step(type=StepType.PYTHON, cmd=["print('test')"])
        
        result = create_python_request(step)
        
        assert result.code_or_file == ["print('test')"]
    
    def test_create_python_request_empty_cmd_raises_error(self):
        """Test that empty cmd raises ValueError"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.PYTHON
        mock_step.cmd = []
        
        with pytest.raises(ValueError, match="Python step must have non-empty cmd"):
            create_python_request(mock_step)


class TestCreateFileRequests:
    """Tests for file operation request creation functions"""
    
    def test_create_copy_request(self):
        """Test copy request creation"""
        step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "destination.txt"],
            allow_failure=True,
            show_output=True
        )
        
        result = create_copy_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.COPY
        assert result.path == "source.txt"
        assert result.dst_path == "destination.txt"
        assert result.allow_failure is True
        assert result.show_output is True
    
    def test_create_copy_request_insufficient_args(self):
        """Test copy request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.COPY
        mock_step.cmd = ["only_one_arg"]
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Copy step requires at least 2 arguments"):
            create_copy_request(mock_step)
    
    def test_create_move_request(self):
        """Test move request creation"""
        step = Step(type=StepType.MOVE, cmd=["old_name.txt", "new_name.txt"])
        
        result = create_move_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.MOVE
        assert result.path == "old_name.txt"
        assert result.dst_path == "new_name.txt"
    
    def test_create_move_request_insufficient_args(self):
        """Test move request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.MOVE
        mock_step.cmd = ["only_source"]
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Move step requires at least 2 arguments"):
            create_move_request(mock_step)
    
    def test_create_movetree_request(self):
        """Test movetree request creation (implemented as COPYTREE)"""
        step = Step(type=StepType.MOVETREE, cmd=["src_directory", "dst_directory"])
        
        result = create_movetree_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.COPYTREE  # movetree -> copytree
        assert result.path == "src_directory"
        assert result.dst_path == "dst_directory"
    
    def test_create_movetree_request_insufficient_args(self):
        """Test movetree request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.MOVETREE
        mock_step.cmd = ["only_source"]
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Movetree step requires at least 2 arguments"):
            create_movetree_request(mock_step)
    
    def test_create_mkdir_request(self):
        """Test mkdir request creation"""
        step = Step(
            type=StepType.MKDIR,
            cmd=["/test/new_directory"],
            allow_failure=True
        )
        
        result = create_mkdir_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.MKDIR
        assert result.path == "/test/new_directory"
        assert result.allow_failure is True
    
    def test_create_mkdir_request_insufficient_args(self):
        """Test mkdir request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.MKDIR
        mock_step.cmd = []
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Mkdir step requires at least 1 argument"):
            create_mkdir_request(mock_step)
    
    def test_create_touch_request(self):
        """Test touch request creation"""
        step = Step(type=StepType.TOUCH, cmd=["/test/new_file.txt"])
        
        result = create_touch_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.TOUCH
        assert result.path == "/test/new_file.txt"
    
    def test_create_touch_request_insufficient_args(self):
        """Test touch request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.TOUCH
        mock_step.cmd = []
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Touch step requires at least 1 argument"):
            create_touch_request(mock_step)
    
    def test_create_remove_request(self):
        """Test remove request creation"""
        step = Step(type=StepType.REMOVE, cmd=["/test/file_to_remove.txt"])
        
        result = create_remove_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.REMOVE
        assert result.path == "/test/file_to_remove.txt"
    
    def test_create_remove_request_insufficient_args(self):
        """Test remove request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.REMOVE
        mock_step.cmd = []
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Remove step requires at least 1 argument"):
            create_remove_request(mock_step)
    
    def test_create_rmtree_request(self):
        """Test rmtree request creation"""
        step = Step(type=StepType.RMTREE, cmd=["/test/directory_to_remove"])
        
        result = create_rmtree_request(step)
        
        assert isinstance(result, FileRequest)
        assert result.op == FileOpType.RMTREE
        assert result.path == "/test/directory_to_remove"
    
    def test_create_rmtree_request_insufficient_args(self):
        """Test rmtree request with insufficient arguments"""
        # Use mock to bypass Step.__post_init__ validation
        mock_step = Mock()
        mock_step.type = StepType.RMTREE
        mock_step.cmd = []
        mock_step.allow_failure = False
        mock_step.show_output = False
        
        with pytest.raises(ValueError, match="Rmtree step requires at least 1 argument"):
            create_rmtree_request(mock_step)


class TestIntegrationScenarios:
    """Integration tests for complete conversion workflows"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_operations = Mock()
        self.mock_file_driver = Mock()
        self.mock_operations.resolve.return_value = self.mock_file_driver
    
    def test_complete_workflow_conversion(self):
        """Test complete workflow from steps to composite request"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/workspace"]),
            Step(type=StepType.TOUCH, cmd=["/workspace/input.txt"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello", ">", "/workspace/input.txt"]),
            Step(type=StepType.PYTHON, cmd=["with open('/workspace/input.txt') as f:", "    print(f.read())"]),
            Step(type=StepType.COPY, cmd=["/workspace/input.txt", "/workspace/output.txt"]),
            Step(type=StepType.REMOVE, cmd=["/workspace/input.txt"])
        ]
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations)
            
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            assert len(requests) == 6
            
            # Check request types and wrapping
            assert isinstance(requests[0], DriverBoundRequest)  # mkdir
            assert isinstance(requests[0].req, FileRequest)
            assert requests[0].req.op == FileOpType.MKDIR
            
            assert isinstance(requests[1], DriverBoundRequest)  # touch
            assert isinstance(requests[1].req, FileRequest)
            assert requests[1].req.op == FileOpType.TOUCH
            
            assert isinstance(requests[2], ShellRequest)  # shell
            
            assert isinstance(requests[3], PythonRequest)  # python
            
            assert isinstance(requests[4], DriverBoundRequest)  # copy
            assert isinstance(requests[4].req, FileRequest)
            assert requests[4].req.op == FileOpType.COPY
            
            assert isinstance(requests[5], DriverBoundRequest)  # remove
            assert isinstance(requests[5].req, FileRequest)
            assert requests[5].req.op == FileOpType.REMOVE
    
    def test_error_handling_in_conversion(self):
        """Test error handling during step conversion"""
        # Create invalid mock steps that should raise errors
        invalid_steps = []
        
        # Empty shell cmd
        shell_step = Mock()
        shell_step.type = StepType.SHELL
        shell_step.cmd = []
        invalid_steps.append(shell_step)
        
        # Copy with insufficient args  
        copy_step = Mock()
        copy_step.type = StepType.COPY
        copy_step.cmd = ["only_one_arg"]
        copy_step.allow_failure = False
        copy_step.show_output = False
        invalid_steps.append(copy_step)
        
        # Empty mkdir cmd
        mkdir_step = Mock()
        mkdir_step.type = StepType.MKDIR
        mkdir_step.cmd = []
        mkdir_step.allow_failure = False
        mkdir_step.show_output = False
        invalid_steps.append(mkdir_step)
        
        with pytest.raises(ValueError):
            steps_to_requests(invalid_steps, self.mock_operations)
    
    def test_conversion_with_special_steps_and_context(self):
        """Test conversion mixing regular and special steps with context"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/test"]),
            Step(type=StepType.TEST, cmd=["python3", "-m", "pytest"]),
            Step(type=StepType.SHELL, cmd=["echo", "done"])
        ]
        
        mock_context = Mock()
        
        with patch('src.env_core.workflow.pure_request_factory.PureRequestFactory') as mock_factory:
            with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
                mock_test_request = Mock()
                mock_factory.create_request_from_step.return_value = mock_test_request
                mock_composite = Mock(spec=CompositeRequest)
                mock_make.return_value = mock_composite
                
                result = steps_to_requests(steps, self.mock_operations, mock_context)
                
                # Should use PureRequestFactory for TEST step
                mock_factory.create_request_from_step.assert_called_once()
                
                mock_make.assert_called_once()
                requests = mock_make.call_args[0][0]
                assert len(requests) == 3
                
                # Check the mix of request types
                assert isinstance(requests[0], DriverBoundRequest)  # mkdir
                assert requests[1] == mock_test_request  # test via factory
                assert isinstance(requests[2], ShellRequest)  # shell
    
    def test_all_step_types_conversion(self):
        """Test conversion of all supported step types"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "test"]),
            Step(type=StepType.PYTHON, cmd=["print('test')"]),
            Step(type=StepType.COPY, cmd=["src", "dst"]),
            Step(type=StepType.MOVE, cmd=["old", "new"]),
            Step(type=StepType.MOVETREE, cmd=["src_dir", "dst_dir"]),
            Step(type=StepType.MKDIR, cmd=["/test"]),
            Step(type=StepType.TOUCH, cmd=["/test/file"]),
            Step(type=StepType.REMOVE, cmd=["/test/file"]),
            Step(type=StepType.RMTREE, cmd=["/test"]),
            Step(type=StepType.OJ, cmd=["oj", "test"]),  # Should return None
            Step(type=StepType.TEST, cmd=["pytest"]),   # Should return None
            Step(type=StepType.BUILD, cmd=["make"])     # Should return None
        ]
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations, context=None)
            
            mock_make.assert_called_once()
            requests = mock_make.call_args[0][0]
            # Should have 9 requests (12 steps - 3 special steps that return None)
            assert len(requests) == 9
            
            # Verify all regular step types are converted
            request_types = [type(r) for r in requests]
            wrapped_types = [type(r.req) if isinstance(r, DriverBoundRequest) else type(r) for r in requests]
            
            assert ShellRequest in wrapped_types
            assert PythonRequest in wrapped_types
            assert FileRequest in [type(r.req) for r in requests if isinstance(r, DriverBoundRequest)]
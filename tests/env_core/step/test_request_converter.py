"""
Comprehensive tests for src/env_core/step/request_converter.py
Tests step to request conversion functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.env_core.step.request_converter import (
    steps_to_requests,
    step_to_request
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
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests([], self.mock_operations)
            
            mock_create_composite.assert_called_once_with([], None, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_simple_shell_step(self):
        """Test conversion of simple shell step"""
        shell_step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests([shell_step], self.mock_operations)
            
            # Should delegate to unified factory
            mock_create_composite.assert_called_once_with([shell_step], None, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_file_step_wrapped_in_driver_bound(self):
        """Test that file steps are handled by unified factory"""
        mkdir_step = Step(type=StepType.MKDIR, cmd=["/test/path"])
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests([mkdir_step], self.mock_operations)
            
            # Should delegate to unified factory
            mock_create_composite.assert_called_once_with([mkdir_step], None, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_special_steps_with_context(self):
        """Test OJ/TEST/BUILD steps using unified factory"""
        test_step = Step(type=StepType.TEST, cmd=["python3", "test.py"])
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests([test_step], self.mock_operations, self.mock_context)
            
            # Should use unified factory for all steps including TEST
            mock_create_composite.assert_called_once_with([test_step], self.mock_context, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_special_steps_without_context(self):
        """Test OJ/TEST/BUILD steps without context"""
        test_step = Step(type=StepType.TEST, cmd=["python3", "test.py"])
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests([test_step], self.mock_operations, context=None)
            
            # Should use unified factory even without context
            mock_create_composite.assert_called_once_with([test_step], None, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_mixed_step_types(self):
        """Test conversion of mixed step types"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "start"]),
            Step(type=StepType.MKDIR, cmd=["/test/dir"]),
            Step(type=StepType.PYTHON, cmd=["print('hello')"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        ]
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations)
            
            # Should delegate to unified factory
            mock_create_composite.assert_called_once_with(steps, None, self.mock_operations)
            assert result == mock_composite
    
    def test_steps_to_requests_with_special_steps(self):
        """Test that special steps are handled by unified factory"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.OJ, cmd=["oj", "test"])
        ]
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations, context=None)
            
            # Should delegate to unified factory which handles filtering
            mock_create_composite.assert_called_once_with(steps, None, self.mock_operations)
            assert result == mock_composite


class TestStepToRequest:
    """Tests for step_to_request function"""
    
    def test_step_to_request_delegates_to_unified_factory(self):
        """Test that step_to_request delegates to unified factory"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        
        with patch('src.operations.factory.unified_request_factory.create_request') as mock_create:
            mock_request = Mock()
            mock_create.return_value = mock_request
            
            result = step_to_request(step)
            
            # Should delegate to unified factory
            mock_create.assert_called_once_with(step)
            assert result == mock_request


# The individual creation functions have been moved to the unified factory
# These tests are no longer applicable since the API has changed


class TestIntegrationScenarios:
    """Integration tests for complete conversion workflows"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_operations = Mock()
        self.mock_file_driver = Mock()
        self.mock_operations.resolve.return_value = self.mock_file_driver
    
    def test_complete_workflow_conversion(self):
        """Test complete workflow from steps to composite request using unified factory"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/workspace"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.PYTHON, cmd=["print('test')"])
        ]
        
        with patch('src.env_core.step.request_converter.create_unified_composite') as mock_create_composite:
            mock_composite = Mock(spec=CompositeRequest)
            mock_create_composite.return_value = mock_composite
            
            result = steps_to_requests(steps, self.mock_operations)
            
            # Should delegate to unified factory
            mock_create_composite.assert_called_once_with(steps, None, self.mock_operations)
            assert result == mock_composite
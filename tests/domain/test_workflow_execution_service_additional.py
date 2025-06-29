"""Additional tests for WorkflowExecutionService to improve coverage"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.domain.services.workflow_execution_service import WorkflowExecutionService
from src.domain.workflow_result import WorkflowExecutionResult
from src.domain.base_request import RequestType


class TestWorkflowExecutionServiceAdditional:
    """Additional test suite for WorkflowExecutionService to improve coverage"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_context = Mock()
        self.mock_infrastructure = Mock()
        self.service = WorkflowExecutionService(self.mock_context, self.mock_infrastructure)

    def test_should_allow_failure_without_request_attribute(self):
        """Test _should_allow_failure when result lacks request attribute"""
        mock_result = Mock(spec=[])  # No request attribute
        
        with pytest.raises(AttributeError, match="does not have required 'request' attribute"):
            self.service._should_allow_failure(mock_result)

    def test_should_allow_failure_with_none_request(self):
        """Test _should_allow_failure when request is None"""
        mock_result = Mock()
        mock_result.request = None
        
        with pytest.raises(ValueError, match="Result request is None"):
            self.service._should_allow_failure(mock_result)

    def test_should_allow_failure_without_allow_failure_attribute(self):
        """Test _should_allow_failure when request lacks allow_failure attribute"""
        mock_result = Mock()
        mock_request = Mock(spec=[])  # No allow_failure attribute
        mock_result.request = mock_request
        
        with pytest.raises(AttributeError, match="does not have required 'allow_failure' attribute"):
            self.service._should_allow_failure(mock_result)

    def test_should_allow_failure_with_temporary_workaround(self):
        """Test _should_allow_failure with temporary workaround for TEST steps"""
        mock_result = Mock()
        mock_request = Mock()
        mock_request.allow_failure = False
        mock_request.request_type = RequestType.SHELL_REQUEST
        mock_request.cmd = ["python3", "/workspace/main.py", "test"]
        mock_result.request = mock_request
        
        # Should return True due to workaround
        assert self.service._should_allow_failure(mock_result) is True

    def test_execute_workflow_with_parallel_override(self):
        """Test execute_workflow with parallel parameter override"""
        # Setup context with environment logging disabled
        self.mock_context.command_type = "test"
        self.mock_context.env_json = None  # No env_json to skip logging
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            False,  # parallel enabled = False in config
            2,      # max_workers = 2 in config
            [{"type": "shell", "cmd": ["echo", "test"]}]  # steps
        ]
        
        # Mock other services
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger,
            "unified_driver": mock_unified_driver
        }.get(key)
        
        # Mock workflow generation
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_parallel.return_value = [mock_result]
        
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (mock_composite, [], [])
            
            # Execute with parallel=True override (config says False)
            result = self.service.execute_workflow(parallel=True, max_workers=8)
            
            # Should use parallel execution with max_workers=8
            mock_composite.execute_parallel.assert_called_once()
            assert result.success is True

    def test_execute_workflow_with_max_workers_override(self):
        """Test execute_workflow with max_workers parameter override"""
        # Setup context
        self.mock_context.command_type = "test"
        self.mock_context.env_json = None  # No env_json
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,   # parallel enabled
            4,      # max_workers = 4 in config
            [{"type": "shell", "cmd": ["echo", "test"]}]  # steps
        ]
        
        # Mock other services
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger,
            "unified_driver": mock_unified_driver
        }.get(key)
        
        # Mock workflow generation
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_parallel.return_value = [mock_result]
        
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (mock_composite, [], [])
            
            # Execute with max_workers=16 override (config says 4)
            result = self.service.execute_workflow(parallel=None, max_workers=16)
            
            # Should use max_workers=16
            mock_composite.execute_parallel.assert_called_once_with(
                mock_unified_driver,
                max_workers=16,
                logger=mock_unified_logger
            )
            assert result.success is True

    def test_execute_main_workflow_without_parallel_attribute(self):
        """Test _execute_main_workflow when composite lacks execute_parallel"""
        # Setup mocks
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        mock_config_manager = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "unified_driver": mock_unified_driver,
            "unified_logger": mock_unified_logger,
            "config_manager": mock_config_manager
        }.get(key)
        
        # Mock composite without execute_parallel method
        mock_composite = Mock(spec=['execute_operation'])
        
        # Execute with parallel=True should raise error
        with pytest.raises(AttributeError, match="does not support parallel execution"):
            self.service._execute_main_workflow(mock_composite, use_parallel=True, max_workers=4)

    def test_execute_main_workflow_returns_single_result(self):
        """Test _execute_main_workflow when composite returns single result"""
        # Setup mocks
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        mock_config_manager = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "unified_driver": mock_unified_driver,
            "unified_logger": mock_unified_logger,
            "config_manager": mock_config_manager
        }.get(key)
        
        mock_composite = Mock()
        mock_result = Mock(success=True)
        # Return single result instead of list
        mock_composite.execute_operation.return_value = mock_result
        
        # Execute
        results = self.service._execute_main_workflow(mock_composite, use_parallel=False, max_workers=1)
        
        # Should wrap single result in list
        assert results == [mock_result]

    def test_prepare_workflow_steps_no_steps(self):
        """Test _prepare_workflow_steps when no steps are found"""
        # Mock config manager to return empty steps
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.return_value = []
        
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger
        }.get(key)
        
        # Execute
        composite, errors, warnings = self.service._prepare_workflow_steps()
        
        # Should return None and error
        assert composite is None
        assert errors == ["No workflow steps found for command"]
        assert warnings == []

    def test_prepare_workflow_steps_with_errors(self):
        """Test _prepare_workflow_steps when workflow generation has errors"""
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.return_value = [
            {"type": "invalid", "cmd": ["bad"]}
        ]
        
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger
        }.get(key)
        
        # Mock workflow generation with errors
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (None, ["Invalid step type"], ["Warning"])
            
            # Execute
            composite, errors, warnings = self.service._prepare_workflow_steps()
            
            # Should return errors
            assert composite is None
            assert errors == ["Invalid step type"]
            assert warnings == ["Warning"]

    def test_log_environment_info_with_merged_config(self):
        """Test _log_environment_info with merged config structure"""
        # Setup context with merged config (shared settings at root)
        self.mock_context.command_type = "test"
        self.mock_context.language = "python"
        self.mock_context.contest_name = "abc"
        self.mock_context.problem_name = "a"
        self.mock_context.env_type = "local"
        self.mock_context.env_json = {
            "environment_logging": {
                "enabled": True,
                "fields": ["language", "contest", "problem"]
            }
        }
        
        mock_unified_logger = Mock()
        self.mock_infrastructure.resolve.return_value = mock_unified_logger
        
        # Execute
        self.service._log_environment_info()
        
        # Should call log_environment_info
        mock_unified_logger.log_environment_info.assert_called_once_with(
            language_name="python",
            contest_name="abc",
            problem_name="a",
            env_type="local",
            env_logging_config={
                "enabled": True,
                "fields": ["language", "contest", "problem"]
            }
        )

    def test_execute_workflow_with_preparation_errors(self):
        """Test execute_workflow when preparation phase has errors"""
        # Setup context
        self.mock_context.command_type = "test"
        self.mock_context.env_json = None
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,  # parallel enabled
            4,     # max_workers
            []     # No steps - will cause error
        ]
        
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger
        }.get(key)
        
        # Execute
        result = self.service.execute_workflow(parallel=None, max_workers=None)
        
        # Should return error result
        assert result.success is False
        assert result.errors == ["No workflow steps found for command"]
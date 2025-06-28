"""Tests for WorkflowExecutionService - critical domain layer component"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.domain.services.workflow_execution_service import WorkflowExecutionService
from src.domain.workflow_result import WorkflowExecutionResult


class TestWorkflowExecutionService:
    """Test suite for WorkflowExecutionService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_context = Mock()
        self.mock_infrastructure = Mock()
        self.service = WorkflowExecutionService(self.mock_context, self.mock_infrastructure)

    def test_execute_workflow_success(self):
        """Test successful workflow execution"""
        # Setup mocks
        self.mock_context.command_type = "test"
        self.mock_context.env_json = {"shared": {"environment_logging": {"enabled": False}}}
        self.mock_context.language = "python"
        self.mock_context.contest_name = "test_contest"
        self.mock_context.problem_name = "test_problem"
        self.mock_context.env_type = "test"
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,  # parallel enabled
            4,     # max_workers
            [{"type": "shell", "cmd": ["echo", "test"]}]  # steps
        ]
        
        # Mock unified driver and logger
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        
        # Mock infrastructure resolver
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger,
            "unified_driver": mock_unified_driver
        }.get(key)
        
        # Mock composite request
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_operation.return_value = [mock_result]
        
        # Mock workflow generation
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (mock_composite, [], [])
            
            # Execute
            result = self.service.execute_workflow(parallel=False, max_workers=None)
            
            # Assert
            assert isinstance(result, WorkflowExecutionResult)
            assert result.success is True
            assert len(result.results) == 1
            assert result.errors == []

    def test_execute_workflow_with_errors(self):
        """Test workflow execution with errors"""
        # Setup mocks
        self.mock_context.command_type = "test"
        self.mock_context.env_json = {"shared": {"environment_logging": {"enabled": False}}}
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            False,  # parallel enabled
            1,      # max_workers
            [{"type": "shell", "cmd": ["false"]}]  # steps that will fail
        ]
        
        # Mock infrastructure
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": Mock(),
            "unified_driver": Mock()
        }.get(key)
        
        # Mock workflow generation with errors
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (None, ["Step generation failed"], ["Warning"])
            
            # Execute
            result = self.service.execute_workflow(parallel=None, max_workers=None)
            
            # Assert
            assert isinstance(result, WorkflowExecutionResult)
            assert result.success is False
            assert "Step generation failed" in result.errors
            assert "Warning" in result.warnings

    def test_get_parallel_config_raises_on_missing_config(self):
        """Test that missing parallel config raises appropriate error"""
        # Setup mocks
        self.mock_context.command_type = "test"
        
        # Mock config manager that raises KeyError
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = KeyError("Config not found")
        
        self.mock_infrastructure.resolve.return_value = mock_config_manager
        
        # Execute and assert
        with pytest.raises(KeyError):
            self.service._get_parallel_config()

    def test_analyze_execution_results_with_critical_failure(self):
        """Test analyzing results with critical failures"""
        # Create mock results
        mock_request = Mock(allow_failure=False)
        mock_result = Mock(
            success=False,
            request=mock_request,
            get_error_output=Mock(return_value="Critical error")
        )
        
        # Execute
        success, errors = self.service._analyze_execution_results([mock_result])
        
        # Assert
        assert success is False
        assert len(errors) == 1
        assert "Critical error" in errors[0]

    def test_analyze_execution_results_with_allowed_failure(self):
        """Test analyzing results with allowed failures"""
        # Create mock results
        mock_request = Mock(allow_failure=True)
        mock_result = Mock(
            success=False,
            request=mock_request,
            get_error_output=Mock(return_value="Allowed error")
        )
        
        # Execute
        success, errors = self.service._analyze_execution_results([mock_result])
        
        # Assert
        assert success is True  # Success despite failure because it's allowed
        assert len(errors) == 1
        assert "allowed" in errors[0]
        assert "Allowed error" in errors[0]
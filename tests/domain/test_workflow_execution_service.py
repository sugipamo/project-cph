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

    def test_log_environment_info_enabled(self):
        """Test environment logging when enabled"""
        # Setup mocks
        self.mock_context.env_json = {
            "shared": {
                "environment_logging": {
                    "enabled": True
                }
            }
        }
        self.mock_context.language = "python"
        self.mock_context.contest_name = "test_contest"
        self.mock_context.problem_name = "test_problem"
        self.mock_context.env_type = "test"
        
        mock_unified_logger = Mock()
        self.mock_infrastructure.resolve.return_value = mock_unified_logger
        
        # Execute
        self.service._log_environment_info()
        
        # Assert
        mock_unified_logger.log_environment_info.assert_called_once_with(
            language_name="python",
            contest_name="test_contest",
            problem_name="test_problem",
            env_type="test",
            env_logging_config={"enabled": True}
        )

    def test_log_environment_info_disabled(self):
        """Test environment logging when disabled"""
        # Setup mocks
        self.mock_context.env_json = {
            "shared": {
                "environment_logging": {
                    "enabled": False
                }
            }
        }
        
        mock_unified_logger = Mock()
        self.mock_infrastructure.resolve.return_value = mock_unified_logger
        
        # Execute
        self.service._log_environment_info()
        
        # Assert - logger should not be resolved
        self.mock_infrastructure.resolve.assert_not_called()

    def test_log_environment_info_missing_config(self):
        """Test environment logging with missing config raises error"""
        # Setup mocks with missing environment_logging
        self.mock_context.env_json = {
            "shared": {}
        }
        
        # Execute and assert
        with pytest.raises(KeyError, match="Required environment_logging configuration not found"):
            self.service._log_environment_info()

    def test_log_environment_info_no_env_json(self):
        """Test environment logging with no env_json"""
        # Setup mocks
        self.mock_context.env_json = None
        
        # Execute - should return early
        self.service._log_environment_info()
        
        # Assert - infrastructure should not be accessed
        self.mock_infrastructure.resolve.assert_not_called()

    def test_execute_preparation_phase_success(self):
        """Test successful preparation phase execution"""
        # Create mock composite request
        mock_composite = Mock()
        
        # Execute
        results, errors = self.service._execute_preparation_phase(mock_composite)
        
        # Assert - preparation phase is currently stubbed
        assert results == []
        assert errors == []


    def test_execute_main_workflow_sequential(self):
        """Test sequential workflow execution"""
        # Setup mocks
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        mock_config_manager = Mock()
        
        def mock_resolve(key):
            mapping = {
                "unified_driver": mock_unified_driver,
                "unified_logger": mock_unified_logger,
                "config_manager": mock_config_manager
            }
            return mapping.get(key)
        
        self.mock_infrastructure.resolve.side_effect = mock_resolve
        
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_operation.return_value = [mock_result]
        
        # Execute
        results = self.service._execute_main_workflow(mock_composite, use_parallel=False, max_workers=1)
        
        # Assert
        assert results == [mock_result]
        mock_composite.execute_operation.assert_called_once_with(
            mock_unified_driver,
            logger=mock_unified_logger
        )

    def test_execute_main_workflow_parallel(self):
        """Test parallel workflow execution"""
        # Setup mocks
        mock_unified_driver = Mock()
        mock_unified_logger = Mock()
        mock_config_manager = Mock()
        
        def mock_resolve(key):
            mapping = {
                "unified_driver": mock_unified_driver,
                "unified_logger": mock_unified_logger,
                "config_manager": mock_config_manager
            }
            return mapping.get(key)
        
        self.mock_infrastructure.resolve.side_effect = mock_resolve
        
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_parallel.return_value = [mock_result]
        
        # Execute
        results = self.service._execute_main_workflow(mock_composite, use_parallel=True, max_workers=4)
        
        # Assert
        assert results == [mock_result]
        mock_composite.execute_parallel.assert_called_once_with(
            mock_unified_driver,
            max_workers=4,
            logger=mock_unified_logger
        )

    def test_get_workflow_steps_missing_config(self):
        """Test get_workflow_steps with missing configuration"""
        # Setup mocks
        self.mock_context.command_type = "test"
        
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = KeyError("Config not found")
        self.mock_infrastructure.resolve.return_value = mock_config_manager
        
        # Execute and assert
        with pytest.raises(KeyError):
            self.service._get_workflow_steps()

    def test_prepare_workflow_steps_success(self):
        """Test successful workflow step preparation"""
        # Setup mocks
        self.mock_context.command_type = "test"
        
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.return_value = [
            {"type": "shell", "cmd": ["echo", "test"]}
        ]
        
        mock_unified_logger = Mock()
        
        self.mock_infrastructure.resolve.side_effect = lambda key: {
            "config_manager": mock_config_manager,
            "unified_logger": mock_unified_logger
        }.get(key)
        
        # Mock workflow generation
        mock_composite = Mock()
        with patch('src.domain.services.workflow_execution_service.generate_workflow_from_json') as mock_generate:
            mock_generate.return_value = (mock_composite, [], [])
            
            # Execute
            composite, errors, warnings = self.service._prepare_workflow_steps()
            
            # Assert
            assert composite == mock_composite
            assert errors == []
            assert warnings == []
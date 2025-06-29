"""Tests for minimal CLI application."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.presentation.cli_app import MinimalCLIApp, main
from src.domain.workflow_result import WorkflowExecutionResult
from src.domain.composite_step_failure import CompositeStepFailureError
from src.operations.error_codes import ErrorCode


class TestMinimalCLIApp:
    """Test cases for MinimalCLIApp class."""

    def test_init_with_infrastructure(self):
        """Test initialization with infrastructure."""
        infrastructure = Mock()
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        config_manager = Mock()
        
        app = MinimalCLIApp(infrastructure, logger, config_manager)
        
        assert app.infrastructure is infrastructure
        assert app.logger is logger
        assert app.config_manager is config_manager
        assert app.context is None

    def test_init_without_infrastructure(self):
        """Test initialization fails without infrastructure."""
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        
        with pytest.raises(ValueError, match="Infrastructure must be injected"):
            MinimalCLIApp(None, logger)

    def test_run_cli_application_without_infrastructure(self):
        """Test run fails without infrastructure."""
        app = MinimalCLIApp(Mock(), Mock())
        app.infrastructure = None
        
        with pytest.raises(RuntimeError, match="Infrastructure not injected"):
            app.run_cli_application(["test"])

    @patch('src.presentation.cli_app.parse_user_input')
    def test_run_cli_application_success(self, mock_parse):
        """Test successful CLI application run."""
        # Setup mocks
        infrastructure = Mock()
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        config_manager = Mock()
        
        # Mock context
        mock_context = Mock()
        mock_context.debug_mode = False
        mock_context.language = "python"
        mock_parse.return_value = mock_context
        
        # Mock workflow execution result
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        
        app = MinimalCLIApp(infrastructure, logger, config_manager)
        
        # Mock the workflow execution
        with patch.object(app, '_execute_workflow', return_value=mock_result):
            exit_code = app.run_cli_application(["test", "command"])
        
        assert exit_code == 0
        logger.info.assert_any_call("CLI実行開始: test command")
        logger.info.assert_any_call("CLI実行完了")
        config_manager.reload_with_language.assert_called_once_with("python")

    @patch('src.presentation.cli_app.parse_user_input')
    def test_run_cli_application_failure(self, mock_parse):
        """Test failed CLI application run."""
        # Setup mocks
        infrastructure = Mock()
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        
        # Mock context
        mock_context = Mock()
        mock_context.debug_mode = False
        mock_parse.return_value = mock_context
        
        # Mock workflow execution result
        mock_result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["Test error"],
            warnings=[]
        )
        
        app = MinimalCLIApp(infrastructure, logger)
        
        # Mock the workflow execution
        with patch.object(app, '_execute_workflow', return_value=mock_result):
            exit_code = app.run_cli_application(["test", "command"])
        
        assert exit_code == 1
        logger.error.assert_any_call("CLI実行失敗")

    def test_initialize_logger_success(self):
        """Test successful logger initialization."""
        infrastructure = Mock()
        # Create mock service with name attribute
        mock_service = Mock()
        mock_service.name = 'UNIFIED_LOGGER'
        infrastructure._services = [mock_service]
        infrastructure.resolve.return_value = Mock()
        
        app = MinimalCLIApp(infrastructure, None)
        result = app._initialize_logger()
        
        assert result is True
        assert app.logger is not None
        infrastructure.resolve.assert_called_once_with('UNIFIED_LOGGER')

    def test_initialize_logger_not_registered(self):
        """Test logger initialization when not registered."""
        infrastructure = Mock()
        infrastructure._services = []
        
        app = MinimalCLIApp(infrastructure, None)
        
        with pytest.raises(RuntimeError, match="Logger dependency not registered"):
            app._initialize_logger()

    def test_initialize_logger_resolution_failure(self):
        """Test logger initialization when resolution fails."""
        infrastructure = Mock()
        # Create mock service with name attribute
        mock_service = Mock()
        mock_service.name = 'UNIFIED_LOGGER'
        infrastructure._services = [mock_service]
        infrastructure.resolve.return_value = None
        
        app = MinimalCLIApp(infrastructure, None)
        
        with pytest.raises(RuntimeError, match="Logger initialization failed"):
            app._initialize_logger()

    @patch('src.presentation.cli_app.WorkflowExecutionService')
    def test_execute_workflow(self, mock_service_class):
        """Test workflow execution."""
        infrastructure = Mock()
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        context = Mock()
        
        # Mock workflow service
        mock_service = Mock()
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result
        mock_service_class.return_value = mock_service
        
        app = MinimalCLIApp(infrastructure, logger)
        app.context = context
        
        result = app._execute_workflow()
        
        assert result == mock_result
        mock_service_class.assert_called_once_with(context, infrastructure)
        mock_service.execute_workflow.assert_called_once_with(parallel=None, max_workers=None)

    def test_present_results_with_errors_and_warnings(self):
        """Test presenting results with errors and warnings."""
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        
        result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        
        app = MinimalCLIApp(Mock(), logger)
        app._present_results(result)
        
        logger.error.assert_any_call("ワークフローエラー: Error 1")
        logger.error.assert_any_call("ワークフローエラー: Error 2")
        logger.warning.assert_called_once_with("ワークフロー警告: Warning 1")

    def test_present_results_no_errors_or_warnings(self):
        """Test presenting results with no errors or warnings."""
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        
        result = WorkflowExecutionResult(
            success=True,
            results=[],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        
        app = MinimalCLIApp(Mock(), logger)
        app._present_results(result)
        
        logger.error.assert_not_called()
        logger.warning.assert_not_called()

    def test_handle_debug_mode_with_service(self):
        """Test debug mode handling with debug service."""
        infrastructure = Mock()
        infrastructure.is_registered.return_value = True
        debug_service = Mock()
        infrastructure.resolve.return_value = debug_service
        
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        context = Mock()
        context.__dict__ = {"test": "data"}
        
        app = MinimalCLIApp(infrastructure, logger)
        app.context = context
        
        app._handle_debug_mode()
        
        infrastructure.is_registered.assert_called_once_with("debug_service")
        infrastructure.resolve.assert_called_once_with("debug_service")
        debug_service.log_debug_context.assert_called_once_with({"test": "data"})

    def test_handle_debug_mode_without_service(self):
        """Test debug mode handling without debug service."""
        infrastructure = Mock()
        infrastructure.is_registered.return_value = False
        
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        context = Mock()
        context.__dict__ = {"test": "data"}
        
        app = MinimalCLIApp(infrastructure, logger)
        app.context = context
        
        app._handle_debug_mode()
        
        logger.debug.assert_any_call("🔍 デバッグモードが有効化されました")
        logger.debug.assert_any_call("🔍 実行コンテキスト: {'test': 'data'}")

    def test_handle_debug_mode_exception(self):
        """Test debug mode handling with exception."""
        infrastructure = Mock()
        infrastructure.is_registered.side_effect = Exception("Test error")
        
        logger = Mock()
        logger.output_manager = Mock()
        logger.output_manager.flush = Mock()
        context = Mock()
        
        app = MinimalCLIApp(infrastructure, logger)
        app.context = context
        
        with pytest.raises(RuntimeError, match="デバッグ処理に失敗"):
            app._handle_debug_mode()

    def test_get_error_output_safely_with_output(self):
        """Test getting error output when available."""
        result = Mock()
        result.get_error_output.return_value = "Error output"
        
        app = MinimalCLIApp(Mock(), Mock())
        output = app._get_error_output_safely(result)
        
        assert output == "Error output"

    def test_get_error_output_safely_without_method(self):
        """Test getting error output when method not available."""
        result = Mock(spec=[])  # No get_error_output method
        
        app = MinimalCLIApp(Mock(), Mock())
        output = app._get_error_output_safely(result)
        
        assert output is None

    def test_get_error_output_safely_returns_none(self):
        """Test getting error output when method returns None."""
        result = Mock()
        result.get_error_output.return_value = None
        
        app = MinimalCLIApp(Mock(), Mock())
        output = app._get_error_output_safely(result)
        
        assert output is None


class TestMainFunction:
    """Test cases for main function."""

    def test_main_success(self):
        """Test successful main execution."""
        infrastructure = Mock()
        infrastructure.resolve.return_value = Mock()
        
        exit_func = Mock()
        
        with patch('src.presentation.cli_app.MinimalCLIApp') as mock_app_class:
            mock_app = Mock()
            mock_app.run_cli_application.return_value = 0
            mock_app_class.return_value = mock_app
            
            exit_code = main(["test"], exit_func, infrastructure)
        
        assert exit_code == 0
        exit_func.assert_called_once_with(0)

    def test_main_without_infrastructure(self):
        """Test main fails without infrastructure."""
        with pytest.raises(ValueError, match="Infrastructure must be injected"):
            main(["test"], Mock(), None)

    def test_main_without_argv(self):
        """Test main fails without argv."""
        infrastructure = Mock()
        infrastructure.resolve.return_value = Mock()
        
        with pytest.raises(ValueError, match="argv must be provided"):
            main(None, Mock(), infrastructure)

    def test_main_with_config_manager(self):
        """Test main with config manager."""
        infrastructure = Mock()
        infrastructure.resolve.return_value = Mock()
        config_manager = Mock()
        
        exit_func = Mock()
        
        with patch('src.presentation.cli_app.MinimalCLIApp') as mock_app_class:
            mock_app = Mock()
            mock_app.run_cli_application.return_value = 0
            mock_app_class.return_value = mock_app
            
            exit_code = main(["test"], exit_func, infrastructure, config_manager)
        
        assert exit_code == 0
        mock_app_class.assert_called_once_with(
            infrastructure, 
            infrastructure.resolve.return_value,
            config_manager
        )
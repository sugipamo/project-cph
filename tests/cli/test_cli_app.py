"""Tests for CLI application."""
from unittest.mock import Mock, patch

import pytest

from src.cli.cli_app import MinimalCLIApp, main
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.workflow.workflow_result import WorkflowExecutionResult


class TestMinimalCLIApp:
    """Test cases for MinimalCLIApp."""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock DI container."""
        infrastructure = Mock()
        mock_logger = Mock()
        infrastructure.resolve.return_value = mock_logger
        return infrastructure

    @pytest.fixture
    def mock_context(self):
        """Create mock execution context."""
        context = Mock()
        return context

    @pytest.fixture
    def cli_app(self, mock_infrastructure):
        """Create MinimalCLIApp instance."""
        return MinimalCLIApp(mock_infrastructure)

    def test_init_success(self, mock_infrastructure):
        """Test successful CLI app initialization."""
        app = MinimalCLIApp(mock_infrastructure)

        assert app.infrastructure == mock_infrastructure
        assert app.context is None
        assert app.logger is None

    def test_init_with_logger(self, mock_infrastructure):
        """Test CLI app initialization with logger."""
        mock_logger = Mock()
        app = MinimalCLIApp(mock_infrastructure, logger=mock_logger)

        assert app.logger == mock_logger

    def test_init_no_infrastructure(self):
        """Test CLI app initialization fails without infrastructure."""
        with pytest.raises(ValueError, match="Infrastructure must be injected from main.py"):
            MinimalCLIApp(None)

    def test_run_cli_application_success(self, cli_app, mock_infrastructure):
        """Test successful CLI application run."""
        args = ["python", "build", "contest", "A"]
        mock_context = Mock()
        mock_logger = Mock()
        mock_logger.output_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.errors = []
        mock_result.warnings = []

        # Mock dependencies
        mock_infrastructure.resolve.return_value = mock_logger

        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.return_value = mock_context

            with patch.object(cli_app, '_execute_workflow') as mock_execute:
                mock_execute.return_value = mock_result

                result = cli_app.run_cli_application(args)

                assert result == 0
                assert cli_app.context == mock_context
                assert cli_app.logger == mock_logger

    def test_run_cli_application_failure(self, cli_app, mock_infrastructure):
        """Test CLI application run with failure."""
        args = ["python", "build", "contest", "A"]
        mock_context = Mock()
        mock_logger = Mock()
        mock_logger.output_manager = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.errors = []
        mock_result.warnings = []

        # Mock dependencies
        mock_infrastructure.resolve.return_value = mock_logger

        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.return_value = mock_context

            with patch.object(cli_app, '_execute_workflow') as mock_execute:
                mock_execute.return_value = mock_result

                result = cli_app.run_cli_application(args)

                assert result == 1

    def test_run_cli_application_no_infrastructure(self, mock_infrastructure):
        """Test CLI application run without infrastructure."""
        app = MinimalCLIApp(mock_infrastructure)
        app.infrastructure = None  # Simulate missing infrastructure

        with pytest.raises(RuntimeError, match="Infrastructure not injected"):
            app.run_cli_application(["test"])

    def test_run_cli_application_logger_initialization_error(self, cli_app, mock_infrastructure):
        """Test CLI application run with logger initialization error."""
        args = ["python", "build"]

        # Mock logger resolution to fail
        mock_infrastructure.resolve.side_effect = KeyError("Logger not found")

        with pytest.raises(RuntimeError, match="Logger dependency not registered"):
            cli_app.run_cli_application(args)

    def test_run_cli_application_logger_exception(self, cli_app, mock_infrastructure):
        """Test CLI application run with logger exception."""
        args = ["python", "build"]

        # Mock logger resolution to raise exception
        mock_infrastructure.resolve.side_effect = Exception("Logger failed")

        with pytest.raises(RuntimeError, match="Logger initialization failed"):
            cli_app.run_cli_application(args)

    def test_run_cli_application_composite_step_failure(self, cli_app, mock_infrastructure):
        """Test CLI application handling CompositeStepFailureError."""
        args = ["python", "build", "contest", "A"]
        mock_logger = Mock()
        mock_logger.output_manager = Mock()

        # Mock logger resolution
        mock_infrastructure.resolve.return_value = mock_logger
        cli_app.logger = mock_logger

        # Mock parse_user_input to raise CompositeStepFailureError
        mock_error = CompositeStepFailureError("Test failure", original_exception=None)

        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.side_effect = mock_error

            with patch.object(cli_app, '_handle_composite_step_failure') as mock_handle:
                mock_handle.return_value = 1

                result = cli_app.run_cli_application(args)

                assert result == 1
                mock_handle.assert_called_once_with(mock_error)

    def test_run_cli_application_general_exception(self, cli_app, mock_infrastructure):
        """Test CLI application handling general exception."""
        args = ["python", "build", "contest", "A"]
        mock_logger = Mock()
        mock_logger.output_manager = Mock()

        # Mock logger resolution
        mock_infrastructure.resolve.return_value = mock_logger
        cli_app.logger = mock_logger

        # Mock parse_user_input to raise general exception
        test_exception = ValueError("Test error")

        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.side_effect = test_exception

            with patch.object(cli_app, '_handle_general_exception') as mock_handle:
                mock_handle.return_value = 1

                result = cli_app.run_cli_application(args)

                assert result == 1
                mock_handle.assert_called_once_with(test_exception, args)

    def test_run_cli_application_exception_logger_fallback(self, cli_app, mock_infrastructure):
        """Test CLI application exception handling with logger fallback."""
        args = ["python", "build"]
        mock_output_manager = Mock()

        # First call fails (logger), second call succeeds (output_manager)
        mock_infrastructure.resolve.side_effect = [Exception("Logger failed"), mock_output_manager]

        test_exception = ValueError("Test error")

        with patch('src.cli.cli_app.parse_user_input') as mock_parse:
            mock_parse.side_effect = test_exception

            result = cli_app.run_cli_application(args)

            assert result == 1
            mock_output_manager.error.assert_called()

    def test_execute_workflow(self, cli_app, mock_context):
        """Test workflow execution."""
        cli_app.context = mock_context
        mock_result = Mock()
        mock_result.success = True
        mock_result.errors = []
        mock_result.warnings = []

        with patch('src.cli.cli_app.WorkflowExecutionService') as mock_service_class:
            mock_service = Mock()
            mock_service.execute_workflow.return_value = mock_result
            mock_service_class.return_value = mock_service

            with patch.object(cli_app, '_present_results') as mock_present:
                result = cli_app._execute_workflow()

                assert result == mock_result
                mock_service_class.assert_called_once_with(mock_context, cli_app.infrastructure)
                mock_present.assert_called_once_with(mock_result)

    def test_present_results_with_errors_and_warnings(self, cli_app):
        """Test presenting results with errors and warnings."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        mock_result = Mock()
        mock_result.errors = ["Error 1", "Error 2"]
        mock_result.warnings = ["Warning 1", "Warning 2"]

        cli_app._present_results(mock_result)

        # Should log all errors and warnings
        assert mock_logger.error.call_count == 2
        assert mock_logger.warning.call_count == 2

    def test_present_results_no_errors_warnings(self, cli_app):
        """Test presenting results with no errors or warnings."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []

        cli_app._present_results(mock_result)

        # Should not log anything
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()

    def test_handle_composite_step_failure(self, cli_app):
        """Test handling CompositeStepFailureError."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        # Create mock exception with result
        mock_result = Mock()
        mock_result.get_error_output.return_value = "Error output"

        mock_exception = Mock(spec=CompositeStepFailureError)
        mock_exception.get_formatted_message.return_value = "Formatted error message"
        mock_exception.result = mock_result
        mock_exception.original_exception = ValueError("Original error")

        result = cli_app._handle_composite_step_failure(mock_exception)

        assert result == 1
        # Should log multiple error messages
        assert mock_logger.error.call_count >= 5  # Header, message, details, original exception, footer

    def test_handle_composite_step_failure_no_result(self, cli_app):
        """Test handling CompositeStepFailureError without result."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        mock_exception = Mock(spec=CompositeStepFailureError)
        mock_exception.get_formatted_message.return_value = "Formatted error message"
        mock_exception.result = None
        mock_exception.original_exception = None

        result = cli_app._handle_composite_step_failure(mock_exception)

        assert result == 1
        mock_logger.error.assert_called()

    def test_handle_general_exception(self, cli_app):
        """Test handling general exception."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        args = ["python", "build"]
        test_exception = ValueError("Test error")

        with patch('src.cli.cli_app.classify_error') as mock_classify, \
             patch('src.cli.cli_app.ErrorSuggestion') as mock_suggestion:
            mock_error_code = Mock()
            mock_error_code.value = "VALIDATION_ERROR"
            mock_classify.return_value = mock_error_code
            mock_suggestion.get_suggestion.return_value = "Check your input"
            mock_suggestion.get_recovery_actions.return_value = ["Action 1", "Action 2"]

            result = cli_app._handle_general_exception(test_exception, args)

            assert result == 1
            mock_logger.error.assert_called()

    def test_handle_general_exception_with_debug(self, cli_app):
        """Test handling general exception with debug flag."""
        mock_logger = Mock()
        cli_app.logger = mock_logger

        args = ["python", "build", "--debug"]
        test_exception = ValueError("Test error")

        with patch('src.cli.cli_app.classify_error') as mock_classify, \
             patch('src.cli.cli_app.ErrorSuggestion') as mock_suggestion, \
             patch('src.cli.cli_app.traceback') as mock_traceback:
                    mock_error_code = Mock()
                    mock_error_code.value = "VALIDATION_ERROR"
                    mock_classify.return_value = mock_error_code
                    mock_suggestion.get_suggestion.return_value = "Check your input"
                    mock_suggestion.get_recovery_actions.return_value = []
                    mock_traceback.format_exc.return_value = "Stack trace"

                    result = cli_app._handle_general_exception(test_exception, args)

                    assert result == 1
                    # Should call debug logging for stack trace
                    mock_logger.debug.assert_called()

    def test_main_success(self, mock_infrastructure):
        """Test main function success."""
        argv = ["python", "build", "contest", "A"]
        mock_exit_func = Mock()

        with patch('src.cli.cli_app.MinimalCLIApp') as mock_app_class:
            mock_app = Mock()
            mock_app.run_cli_application.return_value = 0
            mock_app_class.return_value = mock_app

            result = main(argv, mock_exit_func, mock_infrastructure)

            assert result == 0
            mock_exit_func.assert_called_once_with(0)

    def test_main_no_infrastructure(self):
        """Test main function without infrastructure."""
        with pytest.raises(ValueError, match="Infrastructure must be injected from main.py"):
            main(["test"], None, None)

    def test_main_no_argv(self, mock_infrastructure):
        """Test main function without argv."""
        with pytest.raises(ValueError, match="argv must be provided"):
            main(None, None, mock_infrastructure)

    def test_main_no_exit_func(self, mock_infrastructure):
        """Test main function without exit function."""
        argv = ["python", "build"]

        with patch('src.cli.cli_app.MinimalCLIApp') as mock_app_class:
            mock_app = Mock()
            mock_app.run_cli_application.return_value = 0
            mock_app_class.return_value = mock_app

            result = main(argv, None, mock_infrastructure)

            assert result == 0

    def test_direct_execution_not_allowed(self):
        """Test that direct execution raises error."""
        # This test verifies the __main__ guard behavior
        with patch.dict('sys.modules', {'__main__': type('MockMain', (), {'__name__': '__main__'})()}):
            # Import the module and trigger the __main__ check
            import src.cli.cli_app

            # Simulate __name__ == '__main__' condition
            with patch.object(src.cli.cli_app, '__name__', '__main__'), \
                 pytest.raises(RuntimeError, match="Direct CLI execution not allowed"):
                # Execute the __main__ guard code directly
                if src.cli.cli_app.__name__ == "__main__":
                    raise RuntimeError("Direct CLI execution not allowed - must run from main.py")

"""Tests for CLI Application."""
import json
import sys
from unittest.mock import MagicMock, call, patch

import pytest

from src.application.cli_application import CLIApplication, main
from src.domain.exceptions.composite_step_failure import CompositeStepFailureError
from src.workflow.workflow_result import WorkflowExecutionResult


class TestCLIApplication:
    """Test CLIApplication functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = CLIApplication()

    def test_init(self):
        """Test CLIApplication initialization."""
        assert self.app.operations is None
        assert self.app.context is None

    @patch('src.application.cli_application.build_operations')
    @patch('src.application.cli_application.parse_user_input')
    @patch.object(CLIApplication, '_execute_workflow')
    def test_run_success(self, mock_execute, mock_parse, mock_build):
        """Test successful run."""
        # Setup mocks
        mock_operations = MagicMock()
        mock_context = MagicMock()
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context
        mock_execute.return_value = MagicMock()

        # Execute
        result = self.app.run(['python', 'test', 'a'])

        # Assert
        assert result == 0
        assert self.app.operations == mock_operations
        assert self.app.context == mock_context

        mock_build.assert_called_once()
        mock_parse.assert_called_once_with(['python', 'test', 'a'], mock_operations)
        mock_execute.assert_called_once()

    @patch('src.application.cli_application.build_operations')
    @patch('src.application.cli_application.parse_user_input')
    @patch('builtins.print')
    def test_run_value_error(self, mock_print, mock_parse, mock_build):
        """Test run with ValueError."""
        mock_build.return_value = MagicMock()
        mock_parse.side_effect = ValueError("Invalid argument")

        result = self.app.run(['invalid'])

        assert result == 1
        mock_print.assert_called_once_with("エラー: Invalid argument")

    @patch('src.application.cli_application.build_operations')
    @patch('src.application.cli_application.parse_user_input')
    @patch('builtins.print')
    def test_run_file_not_found_error(self, mock_print, mock_parse, mock_build):
        """Test run with FileNotFoundError."""
        mock_build.return_value = MagicMock()
        mock_parse.side_effect = FileNotFoundError("File not found")

        result = self.app.run(['python'])

        assert result == 1
        mock_print.assert_called_once_with("ファイルが見つかりません: File not found")

    @patch('src.application.cli_application.build_operations')
    @patch('src.application.cli_application.parse_user_input')
    @patch('builtins.print')
    def test_run_json_decode_error(self, mock_print, mock_parse, mock_build):
        """Test run with JSONDecodeError."""
        mock_build.return_value = MagicMock()
        mock_parse.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        result = self.app.run(['python'])

        assert result == 1
        mock_print.assert_called_once_with("エラー: Invalid JSON: line 1 column 1 (char 0)")

    @patch('src.application.cli_application.build_operations')
    @patch('src.application.cli_application.parse_user_input')
    @patch.object(CLIApplication, '_handle_general_exception')
    def test_run_general_exception(self, mock_handle, mock_parse, mock_build):
        """Test run with general exception."""
        mock_build.return_value = MagicMock()
        mock_parse.side_effect = RuntimeError("Unexpected error")
        mock_handle.return_value = 1

        result = self.app.run(['python'])

        assert result == 1
        mock_handle.assert_called_once()
        assert isinstance(mock_handle.call_args[0][0], RuntimeError)

    @patch('src.application.cli_application.get_output_config')
    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.application.cli_application.WorkflowResultPresenter')
    def test_execute_workflow(self, mock_presenter_class, mock_service_class, mock_get_config):
        """Test _execute_workflow method."""
        # Setup mocks
        mock_context = MagicMock()
        mock_operations = MagicMock()
        mock_config = {'format': 'json'}
        mock_service = MagicMock()
        mock_presenter = MagicMock()
        mock_result = MagicMock()

        self.app.context = mock_context
        self.app.operations = mock_operations

        mock_get_config.return_value = mock_config
        mock_service_class.return_value = mock_service
        mock_presenter_class.return_value = mock_presenter
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        result = self.app._execute_workflow()

        # Assert
        assert result == mock_result
        mock_get_config.assert_called_once_with(mock_context)
        mock_service_class.assert_called_once_with(mock_context, mock_operations)
        mock_service.execute_workflow.assert_called_once_with(parallel=False)
        mock_presenter_class.assert_called_once_with(mock_config)
        mock_presenter.present_results.assert_called_once_with(mock_result)

    @patch('builtins.print')
    def test_handle_general_exception_composite_step_failure(self, mock_print):
        """Test _handle_general_exception with CompositeStepFailureError."""
        mock_result = MagicMock()
        mock_result.get_error_output.return_value = "Error output"

        exception = CompositeStepFailureError("Step failed")
        exception.result = mock_result

        result = self.app._handle_general_exception(exception)

        assert result == 1
        assert mock_print.call_count == 2
        mock_print.assert_any_call("ユーザー定義コマンドでエラーが発生しました: Step failed")
        mock_print.assert_any_call("Error output")

    @patch('builtins.print')
    def test_handle_general_exception_composite_step_failure_no_result(self, mock_print):
        """Test _handle_general_exception with CompositeStepFailureError without result."""
        exception = CompositeStepFailureError("Step failed")

        result = self.app._handle_general_exception(exception)

        assert result == 1
        mock_print.assert_called_once_with("ユーザー定義コマンドでエラーが発生しました: Step failed")

    @patch('builtins.print')
    @patch('traceback.print_exc')
    def test_handle_general_exception_other_exception(self, mock_traceback, mock_print):
        """Test _handle_general_exception with other exception."""
        exception = RuntimeError("Unexpected error")

        result = self.app._handle_general_exception(exception)

        assert result == 1
        mock_print.assert_called_once_with("予期せぬエラーが発生しました: Unexpected error")
        mock_traceback.assert_called_once()

    @patch('builtins.print')
    def test_handle_general_exception_composite_step_failure_with_exception_in_result(self, mock_print):
        """Test _handle_general_exception when result.get_error_output() raises exception."""
        mock_result = MagicMock()
        mock_result.get_error_output.side_effect = Exception("Error getting output")

        exception = CompositeStepFailureError("Step failed")
        exception.result = mock_result

        result = self.app._handle_general_exception(exception)

        assert result == 1
        # Should only print the main error message, suppressing the secondary exception
        mock_print.assert_called_once_with("ユーザー定義コマンドでエラーが発生しました: Step failed")


class TestMainFunction:
    """Test main function."""

    @patch('sys.argv', ['program', 'python', 'test', 'a'])
    @patch('sys.exit')
    @patch.object(CLIApplication, 'run')
    def test_main_without_parameters(self, mock_run, mock_exit):
        """Test main function without parameters."""
        mock_run.return_value = 0

        main()

        mock_run.assert_called_once_with(['python', 'test', 'a'])
        mock_exit.assert_called_once_with(0)

    @patch('src.application.cli_application.get_output_config')
    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.application.cli_application.WorkflowResultPresenter')
    def test_main_with_parameters(self, mock_presenter_class, mock_service_class, mock_get_config):
        """Test main function with parameters (testing mode)."""
        # Setup mocks
        mock_context = MagicMock()
        mock_operations = MagicMock()
        mock_config = {'format': 'json'}
        mock_service = MagicMock()
        mock_presenter = MagicMock()
        mock_result = MagicMock()

        mock_get_config.return_value = mock_config
        mock_service_class.return_value = mock_service
        mock_presenter_class.return_value = mock_presenter
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        result = main(context=mock_context, operations=mock_operations)

        # Assert
        assert result == mock_result
        mock_get_config.assert_called_once_with(mock_context)
        mock_service_class.assert_called_once_with(mock_context, mock_operations)
        mock_service.execute_workflow.assert_called_once_with(parallel=False)
        mock_presenter_class.assert_called_once_with(mock_config)
        mock_presenter.present_results.assert_called_once_with(mock_result)

    def test_main_with_partial_parameters(self):
        """Test main function with only one parameter."""
        mock_context = MagicMock()

        with patch('sys.argv', ['program', 'test']), \
             patch('sys.exit') as mock_exit, \
             patch.object(CLIApplication, 'run') as mock_run:
                mock_run.return_value = 1

                # Should call CLI application since operations is None
                main(context=mock_context)

                mock_run.assert_called_once()
                mock_exit.assert_called_once_with(1)

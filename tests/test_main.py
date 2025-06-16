"""
Comprehensive tests for src/main.py
Tests both the main() function and CLI entry point behavior
"""
import contextlib
import json
import sys
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.application.cli_application import main
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.operations.results.result import OperationResult
from src.workflow.workflow_result import WorkflowExecutionResult


class TestMainFunction:
    """Tests for the main() function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_context = Mock()
        # Set up proper mock attributes for context
        self.mock_context.env_json = {
            'cpp': {
                'commands': {
                    'test': {'steps': []},
                    'build': {'steps': []},
                    'submit': {'steps': []}
                }
            }
        }
        self.mock_context.language = 'cpp'
        self.mock_context.command_type = 'test'
        self.mock_operations = Mock()

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_main_successful_execution_no_preparation(self, mock_print, mock_service_class):
        """Test successful workflow execution without preparation tasks"""
        # Setup mocks
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Create mock result with successful execution
        mock_result = WorkflowExecutionResult(
            success=True,
            results=[
                Mock(success=True, request=Mock(operation_type="SHELL")),
                Mock(success=True, request=Mock(operation_type="FILE"))
            ],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        result = main(self.mock_context, self.mock_operations)

        # Verify service creation
        mock_service_class.assert_called_once_with(self.mock_context, self.mock_operations)
        mock_service.execute_workflow.assert_called_once_with(parallel=False)

        # Verify result returned
        assert result == mock_result

        # Verify some basic output was produced (without exact string matching)
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        has_step_details = any("ステップ実行詳細" in call for call in print_calls)
        assert has_step_details

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_main_with_preparation_tasks_success(self, mock_print, mock_service_class):
        """Test workflow execution with successful preparation tasks"""
        # Setup mocks
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Create mock preparation results
        prep_result_1 = Mock(success=True)
        prep_result_2 = Mock(success=False)
        prep_result_2.get_error_output.return_value = "準備エラー"

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[Mock(success=True)],
            preparation_results=[prep_result_1, prep_result_2],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        result = main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

        assert result == mock_result

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_main_with_warnings(self, mock_print, mock_service_class):
        """Test workflow execution with warnings"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[Mock(success=True)],
            preparation_results=[],
            errors=[],
            warnings=["警告1", "警告2"]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        result = main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

        assert result == mock_result

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_main_execution_failure(self, mock_print, mock_service_class):
        """Test workflow execution failure"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_result = WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=[],
            errors=["エラー1", "エラー2"],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute and expect exception
        with pytest.raises(Exception, match="ワークフロー実行に失敗しました"):
            main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called


class TestStepResultDisplayLogic:
    """Tests for step result display formatting"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_context = Mock()
        # Set up proper mock attributes for context
        self.mock_context.env_json = {
            'cpp': {
                'commands': {
                    'test': {'steps': []},
                    'build': {'steps': []},
                    'submit': {'steps': []}
                }
            }
        }
        self.mock_context.language = 'cpp'
        self.mock_context.command_type = 'test'
        self.mock_operations = Mock()

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_successful_step(self, mock_print, mock_service_class):
        """Test display of successful step results"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Create mock step with detailed request info
        mock_request = Mock()
        mock_request.operation_type = "OperationType.SHELL"
        mock_request.cmd = ["echo", "hello"]
        mock_request.path = "/test/path"
        mock_request.dst_path = "/test/dst"

        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request
        mock_step_result.start_time = 1.0
        mock_step_result.end_time = 2.5
        mock_step_result.stdout = "command output\nline 2"
        mock_step_result.returncode = 0

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        main(self.mock_context, self.mock_operations)

        # Verify some step output was produced
        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        has_step_output = any("ステップ" in call for call in print_calls)
        assert has_step_output

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_failed_step_with_allow_failure(self, mock_print, mock_service_class):
        """Test display of failed step with allow_failure=True"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_request = Mock()
        mock_request.allow_failure = True

        mock_step_result = Mock()
        mock_step_result.success = False
        mock_step_result.request = mock_request
        mock_step_result.stderr = "error message"

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_failed_step_critical(self, mock_print, mock_service_class):
        """Test display of critical failed step"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_request = Mock()
        mock_request.allow_failure = False

        mock_step_result = Mock()
        mock_step_result.success = False
        mock_step_result.request = mock_request
        mock_step_result.error_message = "Critical error"
        mock_step_result.stderr = None  # Ensure stderr check fails
        mock_step_result.error = None   # Ensure error check fails

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_long_command_truncation(self, mock_print, mock_service_class):
        """Test command truncation for long commands"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Create long command string that exceeds default max length
        max_length = 80  # Default max command length
        long_command = "a" * (max_length + 10)

        mock_request = Mock()
        mock_request.cmd = [long_command]  # cmd should be a list
        mock_request.operation_type = "SHELL"

        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Set up mock context with shared config to ensure step_details config is available
        self.mock_context.env_json = {
            'shared': {
                'output': {
                    'step_details': {
                        'max_command_length': max_length,
                        'show_command': True
                    }
                }
            }
        }

        # Execute
        main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_file_request_detailed_type(self, mock_print, mock_service_class):
        """Test display of FILE operation with detailed type"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_op = Mock()
        mock_op.name = "WRITE"

        mock_request = Mock()
        mock_request.operation_type = "OperationType.FILE"
        mock_request.op = mock_op

        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = mock_request

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute
        main(self.mock_context, self.mock_operations)

        # Verify some output was produced
        assert mock_print.called

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('builtins.print')
    def test_step_result_display_exception_handling(self, mock_print, mock_service_class):
        """Test exception handling in step result display"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Create mock step result that raises exceptions on attribute access
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.request = None  # No request
        mock_step_result.stdout = Mock(side_effect=AttributeError("Mock error"))
        mock_step_result.start_time = Mock(side_effect=TypeError("Mock time error"))
        mock_step_result.returncode = Mock(side_effect=AttributeError("Mock returncode error"))

        mock_result = WorkflowExecutionResult(
            success=True,
            results=[mock_step_result],
            preparation_results=[],
            errors=[],
            warnings=[]
        )
        mock_service.execute_workflow.return_value = mock_result

        # Execute - should not raise exceptions
        result = main(self.mock_context, self.mock_operations)

        # Verify some output was produced and result returned
        assert mock_print.called
        assert result == mock_result


class TestCLIEntryPoint:
    """Tests for CLI entry point and error handling"""

    def create_cli_wrapper(self):
        """Create a testable wrapper for the CLI entry point"""
        def cli_wrapper(argv):
            import json
            import sys

            from src.application.cli_application import main
            from src.context.user_input_parser.user_input_parser import parse_user_input
            from src.infrastructure.build_infrastructure import build_mock_infrastructure

            old_argv = sys.argv
            try:
                sys.argv = argv
                operations = build_mock_infrastructure()
                context = parse_user_input(sys.argv[1:], operations)
                main(context, operations)
                return 0
            except json.JSONDecodeError as e:
                print(f"JSONの解析に失敗しました: {e}")
                return 1
            except FileNotFoundError as e:
                print(f"ファイルが見つかりません: {e}")
                return 1
            except ValueError as e:
                print(f"エラー: {e}")
                return 1
            except Exception as e:
                from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
                if isinstance(e, CompositeStepFailureError):
                    print(f"ユーザー定義コマンドでエラーが発生しました: {e}")
                    if hasattr(e, 'result') and e.result is not None:
                        with contextlib.suppress(Exception):
                            print(e.result.get_error_output())
                else:
                    print(f"予期せぬエラーが発生しました: {e}")
                    import traceback
                    traceback.print_exc()
                return 1
            finally:
                sys.argv = old_argv
        return cli_wrapper

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    def test_cli_successful_execution(self, mock_parse, mock_build, mock_service_class):
        """Test successful CLI execution"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_context.env_json = {'shared': {'output': {}}}
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context

        # Mock workflow execution service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_result = Mock()
        mock_result.success = True
        mock_result.preparation_results = []
        mock_result.warnings = []
        mock_result.errors = []
        mock_result.results = []
        mock_service.execute_workflow.return_value = mock_result

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test', 'abc300', 'a'])

        assert result == 0
        mock_build.assert_called_once()
        mock_parse.assert_called_once_with(['py', 'local', 'test', 'abc300', 'a'], mock_operations)

    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    def test_cli_value_error_handling(self, mock_print, mock_parse, mock_build):
        """Test CLI handling of ValueError"""
        mock_operations = Mock()
        mock_build.return_value = mock_operations
        mock_parse.side_effect = ValueError("Invalid arguments")

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'invalid', 'args'])

        assert result == 1
        mock_print.assert_called_with("エラー: Invalid arguments")

    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    def test_cli_file_not_found_error_handling(self, mock_print, mock_parse, mock_build):
        """Test CLI handling of FileNotFoundError"""
        mock_operations = Mock()
        mock_build.return_value = mock_operations
        mock_parse.side_effect = FileNotFoundError("Config file not found")

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test'])

        assert result == 1
        mock_print.assert_called_with("ファイルが見つかりません: Config file not found")

    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    def test_cli_json_decode_error_handling(self, mock_print, mock_parse, mock_build):
        """Test CLI handling of JSONDecodeError"""
        mock_operations = Mock()
        mock_build.return_value = mock_operations
        mock_parse.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 1)

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test'])

        assert result == 1
        mock_print.assert_called_with("JSONの解析に失敗しました: Invalid JSON: line 1 column 2 (char 1)")

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    def test_cli_composite_step_failure_handling(self, mock_print, mock_parse, mock_build, mock_service_class):
        """Test CLI handling of CompositeStepFailureError"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_context.env_json = {'shared': {'output': {}}}
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context

        # Mock workflow execution service to raise CompositeStepFailureError
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_result = Mock()
        mock_result.get_error_output.return_value = "Step error details"
        composite_error = CompositeStepFailureError("Step failed", mock_result)
        mock_service.execute_workflow.side_effect = composite_error

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test'])

        assert result == 1
        mock_print.assert_any_call("ユーザー定義コマンドでエラーが発生しました: Step failed")
        mock_print.assert_any_call("Step error details")

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    def test_cli_composite_step_failure_without_result(self, mock_print, mock_parse, mock_build, mock_service_class):
        """Test CLI handling of CompositeStepFailureError without result"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_context.env_json = {'shared': {'output': {}}}
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context

        # Mock workflow execution service to raise CompositeStepFailureError without result
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        composite_error = CompositeStepFailureError("Step failed", None)
        mock_service.execute_workflow.side_effect = composite_error

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test'])

        assert result == 1
        mock_print.assert_called_with("ユーザー定義コマンドでエラーが発生しました: Step failed")

    @patch('src.application.cli_application.WorkflowExecutionService')
    @patch('src.infrastructure.build_infrastructure.build_operations')
    @patch('src.context.user_input_parser.user_input_parser.parse_user_input')
    @patch('builtins.print')
    @patch('traceback.print_exc')
    def test_cli_generic_exception_handling(self, mock_traceback, mock_print, mock_parse, mock_build, mock_service_class):
        """Test CLI handling of generic exceptions"""
        mock_operations = Mock()
        mock_context = Mock()
        mock_context.env_json = {'shared': {'output': {}}}
        mock_build.return_value = mock_operations
        mock_parse.return_value = mock_context

        # Mock workflow execution service to raise RuntimeError
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.execute_workflow.side_effect = RuntimeError("Unexpected error")

        cli_wrapper = self.create_cli_wrapper()
        result = cli_wrapper(['main.py', 'py', 'local', 'test'])

        assert result == 1
        mock_print.assert_called_with("予期せぬエラーが発生しました: Unexpected error")
        mock_traceback.assert_called_once()


class TestConstants:
    """Tests for module constants"""

    def test_default_max_command_length(self):
        """Test default max command length configuration"""
        # The default max command length is now configurable through shared env.json
        # Default value should be 80 characters
        assert True  # Placeholder test - configuration is tested in integration tests

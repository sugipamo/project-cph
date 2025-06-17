"""CLI Application controller for managing command-line interface interactions
"""
import contextlib
import json
import sys
import traceback
from typing import Optional

from src.application.orchestration.workflow_result_presenter import WorkflowResultPresenter, get_output_config
from src.context.user_input_parser.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_infrastructure
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.workflow.workflow_execution_service import WorkflowExecutionService
from src.workflow.workflow_result import WorkflowExecutionResult


class CLIApplication:
    """Main CLI application controller"""

    def __init__(self):
        """Initialize CLI application"""
        self.infrastructure = None
        self.context = None

    def execute_cli_application(self, args: list[str]) -> int:
        """Run the CLI application with given arguments

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            # Initialize infrastructure
            self.infrastructure = build_infrastructure()
            self.context = parse_user_input(args, self.infrastructure)

            # Execute main workflow
            self._execute_workflow()

            return 0  # Success

        except ValueError as e:
            print(f"エラー: {e}")
            return 1
        except FileNotFoundError as e:
            print(f"ファイルが見つかりません: {e}")
            return 1
        except json.JSONDecodeError as e:
            print(f"JSONの解析に失敗しました: {e}")
            return 1
        except Exception as e:
            return self._handle_general_exception(e)

    def _execute_workflow(self) -> WorkflowExecutionResult:
        """Execute the main workflow

        Returns:
            Workflow execution result
        """
        # Get output configuration
        output_config = get_output_config(self.context)

        # Create workflow execution service
        service = WorkflowExecutionService(self.context, self.infrastructure)

        # Execute workflow
        result = service.execute_workflow()

        # Present results
        presenter = WorkflowResultPresenter(output_config, self.context)
        presenter.present_results(result)

        return result

    def _handle_general_exception(self, exception: Exception) -> int:
        """Handle general exceptions with appropriate error reporting

        Args:
            exception: The exception that occurred

        Returns:
            Exit code (1 for failure)
        """
        if isinstance(exception, CompositeStepFailureError):
            # Use the enhanced error formatting
            print("=" * 60)
            print("🚨 実行エラーが発生しました")
            print("=" * 60)
            print(exception.get_formatted_message())

            if hasattr(exception, 'result') and exception.result is not None:
                with contextlib.suppress(Exception):
                    print("\n詳細:")
                    print(exception.result.get_error_output())

            if exception.original_exception:
                print(f"\n元の例外: {type(exception.original_exception).__name__}")

            print("=" * 60)
        else:
            print("=" * 60)
            print("🚨 予期せぬエラーが発生しました")
            print("=" * 60)
            print(f"エラー内容: {exception}")

            # Try to provide some context-based suggestions
            from src.operations.exceptions.error_codes import ErrorSuggestion, classify_error
            error_code = classify_error(exception)
            suggestion = ErrorSuggestion.get_suggestion(error_code)
            print(f"分類: {error_code.value}")
            print(f"提案: {suggestion}")
            print("=" * 60)

            # Show traceback for debugging
            if "--debug" in sys.argv:
                print("\nデバッグ情報:")
                traceback.print_exc()

        return 1


def main(context=None, infrastructure=None) -> Optional[WorkflowExecutionResult]:
    """Main entry point (for backward compatibility and testing)

    Args:
        context: Execution context (optional, for testing)
        infrastructure: Infrastructure container (optional, for testing)

    Returns:
        Workflow execution result
    """
    if context is None or infrastructure is None:
        # Called without parameters - run CLI application
        app = CLIApplication()
        exit_code = app.execute_cli_application(sys.argv[1:])
        sys.exit(exit_code)
    else:
        # Called with parameters - execute workflow directly (for testing)
        output_config = get_output_config(context)
        service = WorkflowExecutionService(context, infrastructure)
        result = service.execute_workflow()

        presenter = WorkflowResultPresenter(output_config, context)
        presenter.present_results(result)

        return result


if __name__ == "__main__":
    main()

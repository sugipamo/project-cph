"""CLI Application controller for managing command-line interface interactions
"""
import contextlib
import json
import sys
import traceback
from typing import Optional

from src.application.orchestration.workflow_result_presenter import WorkflowResultPresenter, get_output_config
from src.context.user_input_parser import parse_user_input
from src.domain.exceptions.composite_step_failure import CompositeStepFailure
from src.infrastructure.build_infrastructure import build_operations
from src.workflow.workflow_execution_service import WorkflowExecutionService
from src.workflow.workflow_result import WorkflowExecutionResult


class CLIApplication:
    """Main CLI application controller"""

    def __init__(self):
        """Initialize CLI application"""
        self.operations = None
        self.context = None

    def run(self, args: list[str]) -> int:
        """Run the CLI application with given arguments

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            # Initialize infrastructure
            self.operations = build_operations()
            self.context = parse_user_input(args, self.operations)

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
        service = WorkflowExecutionService(self.context, self.operations)

        # Execute workflow
        result = service.execute_workflow(parallel=False)

        # Present results
        presenter = WorkflowResultPresenter(output_config)
        presenter.present_results(result)

        return result

    def _handle_general_exception(self, exception: Exception) -> int:
        """Handle general exceptions with appropriate error reporting

        Args:
            exception: The exception that occurred

        Returns:
            Exit code (1 for failure)
        """
        if isinstance(exception, CompositeStepFailure):
            print(f"ユーザー定義コマンドでエラーが発生しました: {exception}")
            if hasattr(exception, 'result') and exception.result is not None:
                with contextlib.suppress(Exception):
                    print(exception.result.get_error_output())
        else:
            print(f"予期せぬエラーが発生しました: {exception}")
            traceback.print_exc()

        return 1


def main(context=None, operations=None) -> Optional[WorkflowExecutionResult]:
    """Main entry point (for backward compatibility and testing)

    Args:
        context: Execution context (optional, for testing)
        operations: Operations container (optional, for testing)

    Returns:
        Workflow execution result
    """
    if context is None or operations is None:
        # Called without parameters - run CLI application
        app = CLIApplication()
        exit_code = app.run(sys.argv[1:])
        sys.exit(exit_code)
    else:
        # Called with parameters - execute workflow directly (for testing)
        output_config = get_output_config(context)
        service = WorkflowExecutionService(context, operations)
        result = service.execute_workflow(parallel=False)

        presenter = WorkflowResultPresenter(output_config)
        presenter.present_results(result)

        return result


if __name__ == "__main__":
    main()

"""Minimal CLI application with DI container injection and workflow construction"""
import traceback
from typing import Optional

from src.context.user_input_parser.user_input_parser import parse_user_input
from src.infrastructure.di_container import DIContainer, DIKey
from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.operations.exceptions.error_codes import ErrorSuggestion, classify_error
from src.workflow.workflow_execution_service import WorkflowExecutionService
from src.workflow.workflow_result import WorkflowExecutionResult


class MinimalCLIApp:
    """Minimal CLI application with essential features"""

    def __init__(self, infrastructure: DIContainer, logger):
        """Initialize minimal CLI application

        Args:
            infrastructure: DI container (must be injected from main.py)
            logger: Logger instance (optional, for testing)
        """
        if infrastructure is None:
            raise ValueError("Infrastructure must be injected from main.py - no direct initialization allowed")
        self.infrastructure = infrastructure
        self.context = None
        self.logger = logger

    def run_cli_application(self, args: list[str]) -> int:
        """Run the CLI application with dependency injection

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Infrastructure must be injected from main.py - no direct initialization
        if self.infrastructure is None:
            raise RuntimeError("Infrastructure not injected - must be provided by main.py")

        # Initialize logger if not provided
        if self.logger is None:
            logger_result = self._initialize_logger()
            if not logger_result:
                return 1

        # Parse user input with infrastructure context
        self.context = parse_user_input(args, self.infrastructure)

        # Log application start
        self.logger.info(f"CLI実行開始: {' '.join(args)}")

        # Construct and execute workflow
        result = self._execute_workflow()

        # Log application end
        if result.success:
            self.logger.info("CLI実行完了")
        else:
            self.logger.error("CLI実行失敗")

        # ログ出力をフラッシュして表示
        if self.logger and hasattr(self.logger, 'output_manager'):
            self.logger.output_manager.flush()

        # 互換性維持: 成功時は0、失敗時は1を返す
        if result.success:
            return 0
        return 1

    def _initialize_logger(self) -> bool:
        """Initialize logger using dependency injection

        Returns:
            bool: True if successful, False if failed
        """
        # Logger dependency resolution
        if 'UNIFIED_LOGGER' not in [key.name for key in self.infrastructure._services]:
            # Logger initialization failure - infrastructure available but logger failed
            # 互換性維持: CLIではロガー初期化失敗時にエラーコードを返すのが正しい動作
            raise RuntimeError("Logger dependency not registered")

        resolved_logger = self.infrastructure.resolve(DIKey.UNIFIED_LOGGER)
        if resolved_logger is None:
            # 互換性維持: CLIではロガー初期化失敗時にエラーコードを返すのが正しい動作
            raise RuntimeError("Logger initialization failed")

        self.logger = resolved_logger
        return True

    def _execute_workflow(self) -> WorkflowExecutionResult:
        """Construct and execute workflow using infrastructure dependencies

        Returns:
            WorkflowExecutionResult
        """
        # Create workflow execution service with DI-injected dependencies
        service = WorkflowExecutionService(self.context, self.infrastructure)

        # Execute workflow
        result = service.execute_workflow()

        # Present results if needed
        self._present_results(result)

        return result

    def _present_results(self, result: WorkflowExecutionResult) -> None:
        """Present workflow execution results

        Args:
            result: Workflow execution result
        """
        if result.errors:
            for error in result.errors:
                self.logger.error(f"ワークフローエラー: {error}")

        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(f"ワークフロー警告: {warning}")

    def _handle_composite_step_failure(self, exception: CompositeStepFailureError) -> int:
        """Handle CompositeStepFailureError with enhanced formatting

        Args:
            exception: The CompositeStepFailureError that occurred

        Returns:
            Exit code (1 for failure)
        """
        # Log the error
        self.logger.error(f"CompositeStepFailure: {exception}")

        # Log formatted error details
        self.logger.error("=" * 60)
        self.logger.error("🚨 実行エラーが発生しました")
        self.logger.error("=" * 60)
        self.logger.error(exception.get_formatted_message())

        if hasattr(exception, 'result') and exception.result is not None:
            # エラー出力取得を安全に実行
            error_output = self._get_error_output_safely(exception.result)
            if error_output:
                self.logger.error("詳細:")
                self.logger.error(error_output)

        if exception.original_exception:
            self.logger.error(f"元の例外: {type(exception.original_exception).__name__}")

        self.logger.error("=" * 60)

        return 1

    def _handle_general_exception(self, exception: Exception, args: list[str]) -> int:
        """Handle general exceptions with error classification

        Args:
            exception: The exception that occurred
            args: Command line arguments for context

        Returns:
            Exit code (1 for failure)
        """
        # Error classification and suggestions
        error_code = classify_error(exception)
        suggestion = ErrorSuggestion.get_suggestion(error_code)
        recovery_actions = ErrorSuggestion.get_recovery_actions(error_code)

        # Log the error
        self.logger.error(f"一般例外: {exception}")
        if "--debug" in args:
            self.logger.debug(f"スタックトレース: {traceback.format_exc()}")

        # Log formatted error details
        self.logger.error("=" * 60)
        self.logger.error("🚨 予期せぬエラーが発生しました")
        self.logger.error("=" * 60)
        self.logger.error(f"エラー内容: {exception}")
        self.logger.error(f"分類: {error_code.value}")
        self.logger.error(f"提案: {suggestion}")

        if recovery_actions:
            self.logger.error("回復手順:")
            for i, action in enumerate(recovery_actions, 1):
                self.logger.error(f"  {i}. {action}")

        self.logger.error("=" * 60)

        if "--debug" in args:
            self.logger.debug("デバッグ情報:")
            self.logger.debug(traceback.format_exc())

        return 1

    def _get_error_output_safely(self, result) -> Optional[str]:
        """Safely get error output from result object

        Args:
            result: Result object that may have get_error_output method

        Returns:
            str: Error output if available, None otherwise
        """
        if hasattr(result, 'get_error_output'):
            error_output = result.get_error_output()
            if error_output:
                return error_output
        return None


def main(argv: Optional[list[str]], exit_func, infrastructure: Optional[DIContainer]) -> int:
    """Main entry point for minimal CLI

    Args:
        argv: Command line arguments (injected for testability)
        exit_func: Exit function (injected for testability)
        infrastructure: DI container (must be injected from main.py)

    Returns:
        Exit code
    """
    if infrastructure is None:
        raise ValueError("Infrastructure must be injected from main.py - no direct initialization allowed")

    app = MinimalCLIApp(infrastructure)

    # デフォルト引数の処理は呼び出し元で行う
    if argv is None:
        raise ValueError("argv must be provided - no default values allowed")

    exit_code = app.run_cli_application(argv)

    if exit_func is not None:
        exit_func(exit_code)

    return exit_code


if __name__ == "__main__":
    # エントリーポイントでのテストのみ - 実際の実行はmain.pyから
    # Note: This requires infrastructure injection - testing only
    raise RuntimeError("Direct CLI execution not allowed - must run from main.py")

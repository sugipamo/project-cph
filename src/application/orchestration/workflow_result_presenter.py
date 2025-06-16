"""Workflow execution result presentation and formatting
"""
from typing import Any, Optional

from src.domain.results.result import OperationResult
from src.workflow.workflow_result import WorkflowExecutionResult


class WorkflowResultPresenter:
    """Handles presentation of workflow execution results"""

    def __init__(self, output_config: Optional[dict[str, Any]] = None, execution_context: Optional[Any] = None):
        """Initialize result presenter

        Args:
            output_config: Output configuration dictionary
            execution_context: Execution context with settings information
        """
        self.output_config = output_config or {}
        self.execution_context = execution_context

    def present_results(self, result: WorkflowExecutionResult) -> None:
        """Present complete workflow execution results

        Args:
            result: Workflow execution result to present
        """
        # Show execution settings if enabled
        if self.output_config.get('show_execution_settings', True):
            self._present_execution_settings()

        # Handle errors
        if not result.success:
            self._present_errors(result.errors)
            raise Exception("ワークフロー実行に失敗しました")

        # Show detailed step information
        self._present_step_details(result.results)

    def _present_execution_settings(self) -> None:
        """Present execution settings information"""
        if not self.execution_context:
            return
        
        settings = []
        if hasattr(self.execution_context, 'language'):
            settings.append(f"language: {self.execution_context.language}")
        if hasattr(self.execution_context, 'contest_name'):
            settings.append(f"contest: {self.execution_context.contest_name}")
        if hasattr(self.execution_context, 'problem_name'):
            settings.append(f"problem: {self.execution_context.problem_name}")
        
        if settings:
            print(f"⚙️  実行設定: {', '.join(settings)}")
            print()

    def _present_preparation_results(self, prep_results: list[OperationResult]) -> None:
        """Present preparation task results"""
        print(f"準備タスク実行: {len(prep_results)} 件")
        for i, prep_result in enumerate(prep_results):
            if prep_result.success:
                print(f"  ✓ 準備タスク {i+1}: 成功")
            else:
                print(f"  ✗ 準備タスク {i+1}: 失敗 - {prep_result.get_error_output()}")

    def _present_warnings(self, warnings: list[str]) -> None:
        """Present warnings"""
        for warning in warnings:
            print(f"警告: {warning}")

    def _present_errors(self, errors: list[str]) -> None:
        """Present errors"""
        for error in errors:
            print(f"エラー: {error}")

    def _present_workflow_summary(self, results: list[OperationResult]) -> None:
        """Present workflow execution summary"""
        successful_steps = sum(1 for r in results if r.success)
        print(f"\nワークフロー実行完了: {successful_steps}/{len(results)} ステップ成功")

    def _present_step_details(self, results: list[OperationResult]) -> None:
        """Present detailed step execution information"""
        print("\n=== ステップ実行詳細 ===")
        step_details_config = self.output_config.get('step_details', {})
        max_command_length = step_details_config.get('max_command_length', 80)

        for i, step_result in enumerate(results):
            self._present_single_step(i, step_result, step_details_config, max_command_length)

    def _present_single_step(
        self,
        step_index: int,
        step_result: OperationResult,
        config: dict[str, Any],
        max_command_length: int
    ) -> None:
        """Present details for a single step"""
        # Determine step status
        status = self._get_step_status(step_result)
        print(f"\nステップ {step_index + 1}: {status}")

        # Show step type and command if available
        if hasattr(step_result, 'request') and step_result.request:
            self._present_step_request_info(step_result.request, config, max_command_length)

        # Show execution time if available
        if config.get('show_execution_time', True):
            self._present_execution_time(step_result)

        # Show output
        if config.get('show_stdout', True):
            self._present_stdout(step_result)

        # Show errors
        if config.get('show_stderr', True) and not step_result.success:
            self._present_stderr(step_result)

        # Show return code if available
        if config.get('show_return_code', True):
            self._present_return_code(step_result)

    def _get_step_status(self, step_result: OperationResult) -> str:
        """Get formatted step status string"""
        if step_result.success:
            return "✓ 成功"
        # Check if failure is allowed
        request = step_result.request if hasattr(step_result, 'request') else None
        allow_failure = getattr(request, 'allow_failure', False) if request else False
        if allow_failure:
            return "⚠️ 失敗 (許可済み)"
        return "✗ 失敗"

    def _present_step_request_info(
        self,
        request: Any,
        config: dict[str, Any],
        max_command_length: int
    ) -> None:
        """Present request information for a step"""
        # Show request type
        if config.get('show_type', True) and hasattr(request, 'operation_type'):
            # FileRequestの場合はより具体的なfile operation typeを表示
            if str(request.operation_type) == "OperationType.FILE" and hasattr(request, 'op'):
                print(f"  タイプ: FILE.{request.op.name}")
            else:
                print(f"  タイプ: {request.operation_type}")

        # Show command
        if config.get('show_command', True) and hasattr(request, 'cmd') and request.cmd:
            cmd_str = str(request.cmd)
            try:
                if len(cmd_str) > max_command_length:
                    cmd_str = cmd_str[:max_command_length-3] + "..."
            except (TypeError, ValueError):
                # Handle cases where max_command_length might be a Mock
                pass
            print(f"  コマンド: {cmd_str}")

        # Show paths
        if config.get('show_path', True):
            if hasattr(request, 'path') and request.path:
                print(f"  パス: {request.path}")
            if hasattr(request, 'dst_path') and request.dst_path:
                print(f"  送信先: {request.dst_path}")
        
        # Show Python code for OperationType.PYTHON
        if str(request.operation_type) == "OperationType.PYTHON" and hasattr(request, 'cmd'):
            print(f"  コード:")
            for line in str(request.cmd).split('\n'):
                print(f"    {line}")

    def _present_execution_time(self, step_result: OperationResult) -> None:
        """Present execution time if available"""
        if (hasattr(step_result, 'start_time') and hasattr(step_result, 'end_time') and
            step_result.start_time is not None and step_result.end_time is not None):
            try:
                duration = step_result.end_time - step_result.start_time
                print(f"  実行時間: {duration:.3f}秒")
            except (TypeError, ValueError):
                # Handle mock objects or invalid time values
                pass

    def _present_stdout(self, step_result: OperationResult) -> None:
        """Present stdout if available"""
        try:
            if step_result.stdout and step_result.stdout.strip():
                print("  標準出力:")
                for line in step_result.stdout.strip().split('\n'):
                    print(f"    {line}")
        except (AttributeError, TypeError):
            # Handle mock objects
            pass

    def _present_stderr(self, step_result: OperationResult) -> None:
        """Present stderr and error information"""
        try:
            if step_result.stderr and step_result.stderr.strip():
                print("  標準エラー:")
                for line in step_result.stderr.strip().split('\n'):
                    print(f"    {line}")
            elif hasattr(step_result, 'error_message') and step_result.error_message:
                print(f"  エラー: {step_result.error_message}")
            elif hasattr(step_result, 'error') and step_result.error:
                print(f"  エラー: {step_result.error}")
        except (AttributeError, TypeError):
            # Handle mock objects
            pass

    def _present_return_code(self, step_result: OperationResult) -> None:
        """Present return code if available"""
        try:
            if hasattr(step_result, 'returncode') and step_result.returncode is not None:
                print(f"  終了コード: {step_result.returncode}")
        except (AttributeError, TypeError):
            # Handle mock objects
            pass


def get_output_config(context) -> dict[str, Any]:
    """Get output configuration from context

    Args:
        context: Execution context

    Returns:
        Output configuration dictionary
    """
    try:
        shared_config = context.env_json.get('shared', {})
        return shared_config.get('output', {})
    except (AttributeError, TypeError):
        return {}

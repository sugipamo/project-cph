"""Workflow Logger Adapter - bridges src/logging with workflow-specific logging."""

from typing import Any, Optional

from ..format_info import FormatInfo
from ..interfaces.output_manager_interface import OutputManagerInterface
from ..types import LogLevel


class WorkflowLoggerAdapter:
    """Adapter that provides workflow-specific logging using src/logging OutputManager."""

    # アイコン設定（DebugLoggerから移行）
    DEFAULT_ICONS = {
        "start": "🚀",
        "success": "✅",
        "failure": "❌",
        "warning": "⚠️",
        "executing": "⏱️",
        "info": "ℹ️",
        "debug": "🔍",
        "error": "💥"
    }

    def __init__(self, output_manager: OutputManagerInterface,
                 logger_config: Optional[dict[str, Any]] = None):
        """Initialize workflow logger adapter.

        Args:
            output_manager: The underlying output manager
            logger_config: Debug configuration (compatible with DebugLogger)
        """
        self.output_manager = output_manager
        self.config = logger_config or {}
        self.enabled = self.config.get("enabled", True)

        # Merge user icons with defaults
        format_config = self.config.get("format", {})
        user_icons = format_config.get("icons", {})
        self.icons = {**self.DEFAULT_ICONS, **user_icons}

    def debug(self, message: str, **kwargs) -> None:
        """デバッグメッセージ出力"""
        if self.enabled:
            icon = self.icons.get("debug", "🔍")
            formatted_message = f"{icon} DEBUG: {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.DEBUG,
                formatinfo=FormatInfo(color="gray")
            )

    def info(self, message: str, **kwargs) -> None:
        """情報メッセージ出力"""
        if self.enabled:
            icon = self.icons.get("info", "ℹ️")
            formatted_message = f"{icon} {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="cyan")
            )

    def warning(self, message: str, **kwargs) -> None:
        """警告メッセージ出力"""
        if self.enabled:
            icon = self.icons.get("warning", "⚠️")
            formatted_message = f"{icon} WARNING: {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.WARNING,
                formatinfo=FormatInfo(color="yellow", bold=True)
            )

    def error(self, message: str, **kwargs) -> None:
        """エラーメッセージ出力"""
        if self.enabled:
            icon = self.icons.get("error", "💥")
            formatted_message = f"{icon} ERROR: {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.ERROR,
                formatinfo=FormatInfo(color="red", bold=True)
            )

    def step_start(self, step_name: str, **kwargs) -> None:
        """ステップ開始ログ"""
        if not self.enabled:
            return

        icon = self.icons.get("start", "🚀")
        start_message = f"\n{icon} 実行開始: {step_name}"
        self.output_manager.add(
            start_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

        executing_icon = self.icons.get("executing", "⏱️")
        executing_message = f"  {executing_icon} 実行中..."
        self.output_manager.add(
            executing_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def step_success(self, step_name: str, message: str = "") -> None:
        """ステップ成功ログ"""
        if not self.enabled:
            return

        icon = self.icons.get("success", "✅")
        success_message = f"{icon} 完了: {step_name}"
        if message:
            success_message += f" - {message}"

        self.output_manager.add(
            success_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def step_failure(self, step_name: str, error: str, allow_failure: bool = False) -> None:
        """ステップ失敗ログ"""
        if not self.enabled:
            return

        if allow_failure:
            icon = self.icons.get("warning", "⚠️")
            status = "失敗許可"
            color = "yellow"
        else:
            icon = self.icons.get("failure", "❌")
            status = "失敗"
            color = "red"

        failure_message = f"{icon} {status}: {step_name}"
        self.output_manager.add(
            failure_message,
            LogLevel.WARNING if allow_failure else LogLevel.ERROR,
            formatinfo=FormatInfo(color=color, bold=True)
        )

        if error:
            error_message = f"  エラー: {error}"
            self.output_manager.add(
                error_message,
                LogLevel.WARNING if allow_failure else LogLevel.ERROR,
                formatinfo=FormatInfo(color=color, indent=1)
            )

    def log_preparation_start(self, task_count: int) -> None:
        """環境準備開始ログ"""
        if self.enabled:
            icon = self.icons.get("start", "🚀")
            message = f"\n{icon} 環境準備開始: {task_count}タスク"
            self.output_manager.add(
                message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="blue", bold=True)
            )

    def log_workflow_start(self, step_count: int, parallel: bool = False) -> None:
        """ワークフロー実行開始ログ"""
        if self.enabled:
            icon = self.icons.get("start", "🚀")
            mode = "並列" if parallel else "順次"
            message = f"\n{icon} ワークフロー実行開始: {step_count}ステップ ({mode}実行)"
            self.output_manager.add(
                message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="blue", bold=True)
            )

    def config_load_warning(self, file_path: str, error: str) -> None:
        """設定ファイル読み込み警告"""
        self.warning(f"Failed to load {file_path}: {error}")

    def is_enabled(self) -> bool:
        """デバッグログが有効かチェック"""
        return self.enabled

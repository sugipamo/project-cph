"""Unified logger that combines all logging functionality."""

import uuid
from typing import Any, ClassVar, Optional

from src.operations.interfaces.logger_interface import LoggerInterface

from .format_info import FormatInfo
from .interfaces.output_manager_interface import OutputManagerInterface
from .types import LogLevel


class UnifiedLogger(LoggerInterface):
    """Unified logger that provides all infrastructure/drivers/logging functionality."""

    # アイコン設定（DebugLoggerから移行）
    DEFAULT_ICONS: ClassVar[dict[str, str]] = {
        "start": "🚀",
        "success": "✅",
        "failure": "❌",
        "warning": "⚠️",
        "executing": "⏱️",
        "info": "ℹ️",
        "debug": "🔍",
        "error": "💥",
        "critical": "🔥"
    }

    def __init__(self, output_manager: OutputManagerInterface,
                 name: str = __name__, logger_config: Optional[dict[str, Any]] = None):
        """Initialize unified logger.

        Args:
            output_manager: The underlying output manager
            name: Logger name for session tracking
            logger_config: Configuration for workflow-specific features
        """
        self.output_manager = output_manager
        self.name = name
        self.session_id = str(uuid.uuid4())[:8]

        # Workflow configuration (backward compatible with DebugLogger)
        self.config = logger_config or {}
        self.enabled = self.config.get("enabled", True)

        # Merge user icons with defaults
        format_config = self.config.get("format", {})
        user_icons = format_config.get("icons", {})
        self.icons = {**self.DEFAULT_ICONS, **user_icons}

    # LoggerInterface implementation
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons.get("debug", "🔍")
        display_message = f"{icon} DEBUG: {formatted_message}"

        self.output_manager.add(
            display_message,
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons.get("info", "ℹ️")
        display_message = f"{icon} {formatted_message}"

        self.output_manager.add(
            display_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons.get("warning", "⚠️")
        display_message = f"{icon} WARNING: {formatted_message}"

        self.output_manager.add(
            display_message,
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons.get("error", "💥")
        display_message = f"{icon} ERROR: {formatted_message}"

        self.output_manager.add(
            display_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons.get("critical", "🔥")
        display_message = f"{icon} CRITICAL: {formatted_message}"

        self.output_manager.add(
            display_message,
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    # PythonLogger compatibility methods
    def log_error_with_correlation(self, error_id: str, error_code: str,
                                  message: str, context: Optional[dict] = None) -> None:
        """Log an error with correlation ID and structured context."""
        formatted_message = (
            f"[ERROR#{error_id}] [{error_code}] {message} "
            f"(session: {self.session_id})"
        )

        if context:
            formatted_message += f" Context: {context}"

        self.output_manager.add(
            formatted_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def log_operation_start(self, operation_id: str, operation_type: str,
                           details: Optional[dict] = None) -> None:
        """Log the start of an operation with correlation tracking."""
        message = f"[OP#{operation_id}] {operation_type} started (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        self.output_manager.add(
            message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def log_operation_end(self, operation_id: str, operation_type: str,
                         success: bool, details: Optional[dict] = None) -> None:
        """Log the end of an operation with correlation tracking."""
        status = "completed" if success else "failed"
        message = f"[OP#{operation_id}] {operation_type} {status} (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        level = LogLevel.INFO if success else LogLevel.ERROR
        color = "green" if success else "red"

        self.output_manager.add(
            message,
            level,
            formatinfo=FormatInfo(color=color, bold=bool(not success))
        )

    # ConsoleLogger/DebugLogger compatibility methods
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
            level = LogLevel.WARNING
        else:
            icon = self.icons.get("failure", "❌")
            status = "失敗"
            color = "red"
            level = LogLevel.ERROR

        failure_message = f"{icon} {status}: {step_name}"
        self.output_manager.add(
            failure_message,
            level,
            formatinfo=FormatInfo(color=color, bold=True)
        )

        if error:
            error_message = f"  エラー: {error}"
            self.output_manager.add(
                error_message,
                level,
                formatinfo=FormatInfo(color=color, indent=1)
            )

    def config_load_warning(self, file_path: str, error: str) -> None:
        """設定ファイル読み込み警告（重複していたprint文を統合）"""
        self.warning(f"Failed to load {file_path}: {error}")

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

    def log_environment_info(self, language_name: Optional[str] = None, contest_name: Optional[str] = None,
                           problem_name: Optional[str] = None, env_type: Optional[str] = None,
                           env_logging_config: Optional[dict] = None) -> None:
        """Log environment information if enabled in configuration"""
        if not env_logging_config:
            return

        enabled = env_logging_config.get("enabled", False)
        if not enabled:
            return

        # Check configuration flags
        show_language = env_logging_config.get("show_language_name", True)
        show_contest = env_logging_config.get("show_contest_name", True)
        show_problem = env_logging_config.get("show_problem_name", True)
        show_env_type = env_logging_config.get("show_env_type", True)

        if not any([show_language, show_contest, show_problem, show_env_type]):
            return

        icon = self.icons.get("start", "🚀")
        env_info_parts = []

        if show_language and language_name:
            env_info_parts.append(f"Language: {language_name}")
        if show_contest and contest_name:
            env_info_parts.append(f"Contest: {contest_name}")
        if show_problem and problem_name:
            env_info_parts.append(f"Problem: {problem_name}")
        if show_env_type and env_type:
            env_info_parts.append(f"Environment: {env_type}")

        if env_info_parts:
            env_info = " | ".join(env_info_parts)
            message = f"{icon} 実行環境: {env_info}"
            self.output_manager.add(
                message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="cyan")
            )

    def is_enabled(self) -> bool:
        """Check if debug logging is enabled"""
        return self.enabled

    def _format_message(self, message: str, args: tuple) -> str:
        """Format message with arguments (Python logging style)."""
        if args:
            try:
                return message % args
            except (TypeError, ValueError):
                # Fallback if formatting fails
                return f"{message} {args}"
        return message

"""Workflow Logger Adapter - bridges src/logging with workflow-specific logging."""

import contextlib
from typing import Any, ClassVar, Optional

from src.infrastructure.di_container import DIContainer

from ..format_info import FormatInfo
from ..interfaces.output_manager_interface import OutputManagerInterface
from ..types import LogLevel


class WorkflowLoggerAdapter:
    """Adapter that provides workflow-specific logging using src/logging OutputManager."""

    # アイコン設定（DebugLoggerから移行）
    DEFAULT_ICONS: ClassVar[dict[str, str]] = {
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
                 logger_config: Optional[dict[str, Any]]):
        """Initialize workflow logger adapter.

        Args:
            output_manager: The underlying output manager
            logger_config: Debug configuration (compatible with DebugLogger)
        """
        self.output_manager = output_manager
        self._config_manager = None

        # Get configuration through DI container
        with contextlib.suppress(Exception):
            self._config_manager = DIContainer.resolve("config_manager")

        if logger_config is not None:
            self.config = logger_config
        else:
            self.config = {}

        # Get enabled status from configuration
        try:
            if self._config_manager:
                self.enabled = self._config_manager.resolve_config(
                    ['logging_config', 'adapters', 'workflow', 'default_enabled'], bool
                )
            else:
                raise KeyError("Config manager not available")
        except (KeyError, Exception) as e:
            raise ValueError(f"Workflow logger enabled status configuration not available: {e}") from e

        # Get icon configuration
        try:
            if self._config_manager:
                config_icons = self._config_manager.resolve_config(
                    ['logging_config', 'adapters', 'workflow', 'default_format', 'icons'], dict
                )
            else:
                raise KeyError("Config manager not available")
        except (KeyError, Exception) as e:
            raise ValueError(f"Workflow logger icon configuration not available: {e}") from e

        # Merge user icons with defaults
        try:
            format_config = self.config["format"]
            user_icons = format_config["icons"]
        except KeyError as e:
            raise ValueError(f"User icon configuration not found in format config: {e}") from e
        self.icons = {**self.DEFAULT_ICONS, **config_icons, **user_icons}

    def debug(self, message: str, **kwargs) -> None:
        """デバッグメッセージ出力"""
        if self.enabled:
            icon = self.icons["debug"]
            formatted_message = f"{icon} DEBUG: {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.DEBUG,
                formatinfo=FormatInfo(color="gray")
            )

    def info(self, message: str, **kwargs) -> None:
        """情報メッセージ出力"""
        if self.enabled:
            icon = self.icons["info"]
            formatted_message = f"{icon} {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="cyan")
            )

    def warning(self, message: str, **kwargs) -> None:
        """警告メッセージ出力"""
        if self.enabled:
            icon = self.icons["warning"]
            formatted_message = f"{icon} WARNING: {message}"
            self.output_manager.add(
                formatted_message,
                LogLevel.WARNING,
                formatinfo=FormatInfo(color="yellow", bold=True)
            )

    def error(self, message: str, **kwargs) -> None:
        """エラーメッセージ出力"""
        if self.enabled:
            icon = self.icons["error"]
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

        icon = self.icons["start"]
        start_message = f"\n{icon} 実行開始: {step_name}"
        self.output_manager.add(
            start_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

        executing_icon = self.icons["executing"]
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

        icon = self.icons["success"]
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
            icon = self.icons["warning"]
            status = "失敗許可"
            color = "yellow"
        else:
            icon = self.icons["failure"]
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
            icon = self.icons["start"]
            message = f"\n{icon} 環境準備開始: {task_count}タスク"
            self.output_manager.add(
                message,
                LogLevel.INFO,
                formatinfo=FormatInfo(color="blue", bold=True)
            )

    def log_workflow_start(self, step_count: int, parallel: bool = False) -> None:
        """ワークフロー実行開始ログ"""
        if self.enabled:
            icon = self.icons["start"]
            # Get execution mode from configuration
            try:
                if self._config_manager:
                    mode_parallel = self._config_manager.resolve_config(
                        ['workflow', 'execution_modes', 'parallel'], str
                    )
                    mode_sequential = self._config_manager.resolve_config(
                        ['workflow', 'execution_modes', 'sequential'], str
                    )
                else:
                    raise KeyError("Config manager not available")
            except (KeyError, Exception) as e:
                raise ValueError("Workflow execution mode configuration not found") from e

            mode = mode_parallel if parallel else mode_sequential
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

    def set_level(self, level_name: str) -> None:
        """ログレベルを動的に変更する

        Args:
            level_name: ログレベル名（"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"）
        """
        from src.infrastructure.drivers.logging.types import LogLevel
        level_mapping = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL
        }

        if level_name not in level_mapping:
            raise ValueError(f"Invalid log level: {level_name}")

        self.output_manager.set_level(level_mapping[level_name])

    def get_level(self) -> str:
        """現在のログレベルを取得する

        Returns:
            現在のログレベル名
        """
        from src.infrastructure.drivers.logging.types import LogLevel
        level_name_mapping = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.WARNING: "WARNING",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRITICAL"
        }
        return level_name_mapping[self.output_manager.get_level(], "INFO")

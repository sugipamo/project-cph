"""Unified logger that combines all logging functionality."""
import re
import uuid
from typing import Any, ClassVar, Optional

from src.infrastructure.di_container import DIContainer
from src.operations.interfaces.utility_interfaces import LoggerInterface, OutputManagerInterface
from src.utils.format_info import FormatInfo
from src.utils.types import LogLevel


class UnifiedLogger(LoggerInterface):
    """Unified logger that provides all infrastructure/drivers/logging functionality."""
    DEFAULT_ICONS: ClassVar[dict[str, str]] = {'start': '🚀', 'success': '✅', 'failure': '❌', 'warning': '⚠️', 'executing': '⏱️', 'info': 'ℹ️', 'debug': '🔍', 'error': '💥', 'critical': '🔥'}

    def __init__(self, output_manager: OutputManagerInterface, name: str, logger_config: Optional[dict[str, Any]], di_container: Optional[DIContainer]):
        """Initialize unified logger.

        Args:
            output_manager: The underlying output manager
            name: Logger name for session tracking
            logger_config: Configuration for workflow-specific features
        """
        self.output_manager = output_manager
        self.name = name
        self.session_id = str(uuid.uuid4())[:8]
        self._config_manager = None
        self._di_container = di_container
        if logger_config is not None:
            self.config = logger_config
        else:
            self.config = {}
        try:
            if self._di_container:
                self._config_manager = self._di_container.resolve('config_manager')
            else:
                raise KeyError('DI container not available')
            self.enabled = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'default_enabled'], bool)
        except (KeyError, Exception) as e:
            raise ValueError(f'Logger enabled status configuration not available: {e}') from e
        if not self._config_manager:
            raise ValueError('Config manager is required for unified logger initialization')
        config_icons = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'default_format', 'icons'], dict)
        if 'format' not in self.config:
            raise ValueError('Format configuration is required')
        format_config = self.config['format']
        if 'icons' not in format_config:
            raise ValueError('Icons configuration is required in format config')
        user_icons = format_config['icons']
        self.icons = {**self.DEFAULT_ICONS, **config_icons, **user_icons}

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons['debug']
        display_message = f'{icon} DEBUG: {formatted_message}'
        self.output_manager.add(display_message, LogLevel.DEBUG, formatinfo=FormatInfo(color='gray'), realtime=False)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons['info']
        display_message = f'{icon} {formatted_message}'
        self.output_manager.add(display_message, LogLevel.INFO, formatinfo=FormatInfo(color='cyan'), realtime=False)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons['warning']
        display_message = f'{icon} WARNING: {formatted_message}'
        self.output_manager.add(display_message, LogLevel.WARNING, formatinfo=FormatInfo(color='yellow', bold=True), realtime=False)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons['error']
        display_message = f'{icon} ERROR: {formatted_message}'
        self.output_manager.add(display_message, LogLevel.ERROR, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        formatted_message = self._format_message(message, args)
        icon = self.icons['critical']
        display_message = f'{icon} CRITICAL: {formatted_message}'
        self.output_manager.add(display_message, LogLevel.CRITICAL, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def log_error_with_correlation(self, error_id: str, error_code: str, message: str, context: Optional[dict]) -> None:
        """Log an error with correlation ID and structured context."""
        formatted_message = f'[ERROR#{error_id}] [{error_code}] {message} (session: {self.session_id})'
        if context:
            formatted_message += f' Context: {context}'
        self.output_manager.add(formatted_message, LogLevel.ERROR, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def log_operation_start(self, operation_id: str, operation_type: str, details: Optional[dict]) -> None:
        """Log the start of an operation with correlation tracking."""
        message = f'[OP#{operation_id}] {operation_type} started (session: {self.session_id})'
        if details:
            message += f' Details: {details}'
        self.output_manager.add(message, LogLevel.INFO, formatinfo=FormatInfo(color='blue'), realtime=False)

    def log_operation_end(self, operation_id: str, operation_type: str, success: bool, details: Optional[dict]) -> None:
        """Log the end of an operation with correlation tracking."""
        try:
            if self._config_manager:
                status_success = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'defaults', 'status_success'], str)
                status_failure = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'defaults', 'status_failure'], str)
                color_success = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'defaults', 'color_success'], str)
                color_failure = self._config_manager.resolve_config(['logging_config', 'unified_logger', 'defaults', 'color_failure'], str)
            else:
                raise KeyError('Config manager not available')
        except (KeyError, Exception) as e:
            raise ValueError('Operation status configuration not found') from e
        status = status_success if success else status_failure
        message = f'[OP#{operation_id}] {operation_type} {status} (session: {self.session_id})'
        if details:
            message += f' Details: {details}'
        level = LogLevel.INFO if success else LogLevel.ERROR
        color = color_success if success else color_failure
        self.output_manager.add(message, level, formatinfo=FormatInfo(color=color, bold=bool(not success)), realtime=False)

    def step_start(self, step_name: str, **kwargs) -> None:
        """ステップ開始ログ"""
        if not self.enabled:
            return
        icon = self.icons['start']
        start_message = f'\n{icon} 実行開始: {step_name}'
        self.output_manager.add(start_message, LogLevel.INFO, formatinfo=FormatInfo(color='blue', bold=True), realtime=False)
        executing_icon = self.icons['executing']
        executing_message = f'  {executing_icon} 実行中...'
        self.output_manager.add(executing_message, LogLevel.INFO, formatinfo=FormatInfo(color='blue'), realtime=False)

    def step_success(self, step_name: str, message: str) -> None:
        """ステップ成功ログ"""
        if not self.enabled:
            return
        icon = self.icons['success']
        success_message = f'{icon} 完了: {step_name}'
        if message:
            success_message += f' - {message}'
        self.output_manager.add(success_message, LogLevel.INFO, formatinfo=FormatInfo(color='green', bold=True), realtime=False)

    def step_failure(self, step_name: str, error: str, allow_failure: bool) -> None:
        """ステップ失敗ログ"""
        if not self.enabled:
            return
        if allow_failure:
            icon = self.icons['warning']
            status = '失敗許可'
            color = 'yellow'
            level = LogLevel.WARNING
        else:
            icon = self.icons['failure']
            status = '失敗'
            color = 'red'
            level = LogLevel.ERROR
        failure_message = f'{icon} {status}: {step_name}'
        self.output_manager.add(failure_message, level, formatinfo=FormatInfo(color=color, bold=True), realtime=False)
        if error:
            error_message = f'  エラー: {error}'
            self.output_manager.add(error_message, level, formatinfo=FormatInfo(color=color, indent=1), realtime=False)

    def config_load_warning(self, file_path: str, error: str) -> None:
        """設定ファイル読み込み警告（重複していたprint文を統合）"""
        self.warning(f'Failed to load {file_path}: {error}')

    def log_preparation_start(self, task_count: int) -> None:
        """環境準備開始ログ"""
        if self.enabled:
            icon = self.icons['start']
            message = f'\n{icon} 環境準備開始: {task_count}タスク'
            self.output_manager.add(message, LogLevel.INFO, formatinfo=FormatInfo(color='blue', bold=True), realtime=False)

    def log_workflow_start(self, step_count: int, parallel: bool) -> None:
        """ワークフロー実行開始ログ"""
        if self.enabled:
            icon = self.icons['start']
            try:
                if self._config_manager:
                    mode_parallel = self._config_manager.resolve_config(['workflow', 'execution_modes', 'parallel'], str)
                    mode_sequential = self._config_manager.resolve_config(['workflow', 'execution_modes', 'sequential'], str)
                else:
                    raise KeyError('Config manager not available')
            except (KeyError, Exception) as e:
                raise ValueError('Workflow execution mode configuration not found') from e
            mode = mode_parallel if parallel else mode_sequential
            message = f'\n{icon} ワークフロー実行開始: {step_count}ステップ ({mode}実行)'
            self.output_manager.add(message, LogLevel.INFO, formatinfo=FormatInfo(color='blue', bold=True), realtime=False)

    def log_environment_info(self, language_name: Optional[str], contest_name: Optional[str], problem_name: Optional[str], env_type: Optional[str], env_logging_config: Optional[dict]) -> None:
        """Log environment information if enabled in configuration"""
        if not env_logging_config:
            return
        enabled = env_logging_config['enabled']
        if not enabled:
            return
        show_language = env_logging_config['show_language_name']
        show_contest = env_logging_config['show_contest_name']
        show_problem = env_logging_config['show_problem_name']
        show_env_type = env_logging_config['show_env_type']
        if not any([show_language, show_contest, show_problem, show_env_type]):
            return
        icon = self.icons['start']
        env_info_parts = []
        if show_language and language_name:
            env_info_parts.append(f'Language: {language_name}')
        if show_contest and contest_name:
            env_info_parts.append(f'Contest: {contest_name}')
        if show_problem and problem_name:
            env_info_parts.append(f'Problem: {problem_name}')
        if show_env_type and env_type:
            env_info_parts.append(f'Environment: {env_type}')
        if env_info_parts:
            env_info = ' | '.join(env_info_parts)
            message = f'{icon} 実行環境: {env_info}'
            self.output_manager.add(message, LogLevel.INFO, formatinfo=FormatInfo(color='cyan'), realtime=False)

    def is_enabled(self) -> bool:
        """Check if debug logging is enabled"""
        return self.enabled

    def _format_message(self, message: str, args: tuple) -> str:
        """Format message with arguments (Python logging style)."""
        if args:
            if not self._validate_format_args(message, args):
                raise ValueError(f"Message formatting validation failed. Message: '{message}', Args: {args}")
            return message % args
        return message

    def _validate_format_args(self, message: str, args: tuple) -> bool:
        """Validate format string and arguments compatibility."""
        if not isinstance(message, str):
            return False
        if not isinstance(args, tuple):
            return False
        format_specs = re.findall('%[sdifgGeEcrxa%]', message)
        literal_percents = message.count('%%')
        expected_args = len(format_specs) - literal_percents
        return len(args) == expected_args

    def set_level(self, level_name: str) -> None:
        """ログレベルを動的に変更する

        Args:
            level_name: ログレベル名（"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"）
        """
        level_mapping = {'DEBUG': LogLevel.DEBUG, 'INFO': LogLevel.INFO, 'WARNING': LogLevel.WARNING, 'ERROR': LogLevel.ERROR, 'CRITICAL': LogLevel.CRITICAL}
        if level_name not in level_mapping:
            raise ValueError(f'Invalid log level: {level_name}')
        self.output_manager.set_level(level_mapping[level_name])

    def get_level(self) -> str:
        """現在のログレベルを取得する

        Returns:
            現在のログレベル名
        """
        level_name_mapping = {LogLevel.DEBUG: 'DEBUG', LogLevel.INFO: 'INFO', LogLevel.WARNING: 'WARNING', LogLevel.ERROR: 'ERROR', LogLevel.CRITICAL: 'CRITICAL'}
        current_level = self.output_manager.get_level()
        if current_level in level_name_mapping:
            return level_name_mapping[current_level]
        return 'INFO'

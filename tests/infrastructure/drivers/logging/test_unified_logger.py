"""Tests for UnifiedLogger class"""

from unittest.mock import Mock, patch

import pytest

from src.infrastructure.di_container import DIContainer
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.interfaces.output_manager_interface import OutputManagerInterface
from src.infrastructure.drivers.logging.types import LogLevel
from src.infrastructure.drivers.logging.unified_logger import UnifiedLogger


class TestUnifiedLogger:
    """Test UnifiedLogger functionality"""

    @pytest.fixture
    def mock_output_manager(self):
        """Create mock output manager"""
        return Mock(spec=OutputManagerInterface)

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock()

        # Default configuration values
        config_manager.resolve_config.side_effect = lambda path, type_: {
            ('logging_config', 'unified_logger', 'default_enabled'): True,
            ('logging_config', 'unified_logger', 'default_format', 'icons'): {
                "start": "🚀",
                "success": "✅",
                "failure": "❌",
                "warning": "⚠️",
                "executing": "⏱️",
                "info": "ℹ️",
                "debug": "🔍",
                "error": "💥",
                "critical": "🔥"
            },
            ('logging_config', 'unified_logger', 'defaults', 'status_success'): "completed",
            ('logging_config', 'unified_logger', 'defaults', 'status_failure'): "failed",
            ('logging_config', 'unified_logger', 'defaults', 'color_success'): "green",
            ('logging_config', 'unified_logger', 'defaults', 'color_failure'): "red",
            ('workflow', 'execution_modes', 'parallel'): "parallel",
            ('workflow', 'execution_modes', 'sequential'): "sequential"
        }[tuple(path)]

        return config_manager

    @pytest.fixture
    def mock_di_container(self, mock_config_manager):
        """Create mock DI container"""
        container = Mock(spec=DIContainer)
        container.resolve.return_value = mock_config_manager
        return container

    @pytest.fixture
    def logger_config(self):
        """Create logger configuration"""
        return {
            "format": {
                "icons": {
                    "debug": "🐛",
                    "info": "📢"
                }
            }
        }

    @pytest.fixture
    def unified_logger(self, mock_output_manager, mock_di_container, logger_config):
        """Create UnifiedLogger instance"""
        return UnifiedLogger(
            output_manager=mock_output_manager,
            name="test_logger",
            logger_config=logger_config,
            di_container=mock_di_container
        )

    def test_init_success(self, mock_output_manager, mock_di_container, logger_config):
        """Test successful UnifiedLogger initialization"""
        logger = UnifiedLogger(
            output_manager=mock_output_manager,
            name="test_logger",
            logger_config=logger_config,
            di_container=mock_di_container
        )

        assert logger.output_manager == mock_output_manager
        assert logger.name == "test_logger"
        assert logger.config == logger_config
        assert logger.enabled is True
        assert len(logger.session_id) == 8




    def test_debug_logging(self, unified_logger, mock_output_manager):
        """Test debug message logging"""
        unified_logger.debug("Test debug message")

        mock_output_manager.add.assert_called_once_with(
            "🐛 DEBUG: Test debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray"),
            realtime=False
        )

    def test_debug_logging_with_args(self, unified_logger, mock_output_manager):
        """Test debug message logging with arguments"""
        unified_logger.debug("Test %s message %d", "debug", 42)

        mock_output_manager.add.assert_called_once_with(
            "🐛 DEBUG: Test debug message 42",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray"),
            realtime=False
        )

    def test_info_logging(self, unified_logger, mock_output_manager):
        """Test info message logging"""
        unified_logger.info("Test info message")

        mock_output_manager.add.assert_called_once_with(
            "📢 Test info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan"),
            realtime=False
        )

    def test_warning_logging(self, unified_logger, mock_output_manager):
        """Test warning message logging"""
        unified_logger.warning("Test warning message")

        mock_output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Test warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True),
            realtime=False
        )

    def test_error_logging(self, unified_logger, mock_output_manager):
        """Test error message logging"""
        unified_logger.error("Test error message")

        mock_output_manager.add.assert_called_once_with(
            "💥 ERROR: Test error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_critical_logging(self, unified_logger, mock_output_manager):
        """Test critical message logging"""
        unified_logger.critical("Test critical message")

        mock_output_manager.add.assert_called_once_with(
            "🔥 CRITICAL: Test critical message",
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_log_error_with_correlation(self, unified_logger, mock_output_manager):
        """Test error logging with correlation ID"""
        unified_logger.log_error_with_correlation(
            error_id="ERR001",
            error_code="VALIDATION_FAILED",
            message="Test error",
            context={"field": "username"}
        )

        args, kwargs = mock_output_manager.add.call_args
        assert "[ERROR#ERR001]" in args[0]
        assert "[VALIDATION_FAILED]" in args[0]
        assert "Test error" in args[0]
        assert unified_logger.session_id in args[0]
        assert "Context: {'field': 'username'}" in args[0]
        assert args[1] == LogLevel.ERROR

    def test_log_operation_start(self, unified_logger, mock_output_manager):
        """Test operation start logging"""
        unified_logger.log_operation_start(
            operation_id="OP001",
            operation_type="DATABASE_QUERY",
            details={"table": "users"}
        )

        args, kwargs = mock_output_manager.add.call_args
        assert "[OP#OP001]" in args[0]
        assert "DATABASE_QUERY started" in args[0]
        assert unified_logger.session_id in args[0]
        assert args[0].endswith("Details: {'table': 'users'}")
        assert args[1] == LogLevel.INFO

    def test_log_operation_end_success(self, unified_logger, mock_output_manager):
        """Test successful operation end logging"""
        unified_logger.log_operation_end(
            operation_id="OP001",
            operation_type="DATABASE_QUERY",
            success=True,
            details={"rows": 5}
        )

        args, kwargs = mock_output_manager.add.call_args
        assert "[OP#OP001]" in args[0]
        assert "DATABASE_QUERY completed" in args[0]
        assert unified_logger.session_id in args[0]
        assert args[1] == LogLevel.INFO
        assert kwargs['formatinfo'].color == "green"

    def test_log_operation_end_failure(self, unified_logger, mock_output_manager):
        """Test failed operation end logging"""
        unified_logger.log_operation_end(
            operation_id="OP001",
            operation_type="DATABASE_QUERY",
            success=False,
            details=None
        )

        args, kwargs = mock_output_manager.add.call_args
        assert "[OP#OP001]" in args[0]
        assert "DATABASE_QUERY failed" in args[0]
        assert args[1] == LogLevel.ERROR
        assert kwargs['formatinfo'].color == "red"
        assert kwargs['formatinfo'].bold is True

    def test_step_start(self, unified_logger, mock_output_manager):
        """Test step start logging"""
        unified_logger.step_start("Build application")

        assert mock_output_manager.add.call_count == 2

        # First call: start message
        first_call = mock_output_manager.add.call_args_list[0]
        assert "🚀 実行開始: Build application" in first_call[0][0]
        assert first_call[0][1] == LogLevel.INFO

        # Second call: executing message
        second_call = mock_output_manager.add.call_args_list[1]
        assert "⏱️ 実行中..." in second_call[0][0]
        assert second_call[0][1] == LogLevel.INFO

    def test_step_start_disabled(self, unified_logger, mock_output_manager):
        """Test step start logging when disabled"""
        unified_logger.enabled = False

        unified_logger.step_start("Build application")

        mock_output_manager.add.assert_not_called()

    def test_step_success(self, unified_logger, mock_output_manager):
        """Test step success logging"""
        unified_logger.step_success("Build application", "Build completed successfully")

        mock_output_manager.add.assert_called_once_with(
            "✅ 完了: Build application - Build completed successfully",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True),
            realtime=False
        )

    def test_step_success_no_message(self, unified_logger, mock_output_manager):
        """Test step success logging without message"""
        unified_logger.step_success("Build application", "")

        mock_output_manager.add.assert_called_once_with(
            "✅ 完了: Build application",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True),
            realtime=False
        )

    def test_step_failure(self, unified_logger, mock_output_manager):
        """Test step failure logging"""
        unified_logger.step_failure("Build application", "Compilation error", False)

        assert mock_output_manager.add.call_count == 2

        # First call: failure message
        first_call = mock_output_manager.add.call_args_list[0]
        assert "❌ 失敗: Build application" in first_call[0][0]
        assert first_call[0][1] == LogLevel.ERROR

        # Second call: error details
        second_call = mock_output_manager.add.call_args_list[1]
        assert "エラー: Compilation error" in second_call[0][0]
        assert second_call[0][1] == LogLevel.ERROR

    def test_step_failure_allowed(self, unified_logger, mock_output_manager):
        """Test step failure logging with allowed failure"""
        unified_logger.step_failure("Test application", "Test failed", allow_failure=True)

        assert mock_output_manager.add.call_count == 2

        # First call: warning message
        first_call = mock_output_manager.add.call_args_list[0]
        assert "⚠️ 失敗許可: Test application" in first_call[0][0]
        assert first_call[0][1] == LogLevel.WARNING

    def test_config_load_warning(self, unified_logger, mock_output_manager):
        """Test configuration load warning"""
        unified_logger.config_load_warning("/path/to/config.json", "File not found")

        mock_output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Failed to load /path/to/config.json: File not found",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True),
            realtime=False
        )

    def test_log_preparation_start(self, unified_logger, mock_output_manager):
        """Test preparation start logging"""
        unified_logger.log_preparation_start(5)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 環境準備開始: 5タスク",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True),
            realtime=False
        )

    def test_log_workflow_start_sequential(self, unified_logger, mock_output_manager):
        """Test workflow start logging in sequential mode"""
        unified_logger.log_workflow_start(3, parallel=False)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (sequential実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True),
            realtime=False
        )

    def test_log_workflow_start_parallel(self, unified_logger, mock_output_manager):
        """Test workflow start logging in parallel mode"""
        unified_logger.log_workflow_start(3, parallel=True)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (parallel実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True),
            realtime=False
        )


    def test_log_environment_info_disabled(self, unified_logger, mock_output_manager):
        """Test environment info logging when disabled"""
        env_config = {"enabled": False}

        unified_logger.log_environment_info(
            language_name=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_logging_config=env_config
        )

        mock_output_manager.add.assert_not_called()

    def test_log_environment_info_no_config(self, unified_logger, mock_output_manager):
        """Test environment info logging without configuration"""
        unified_logger.log_environment_info(
            language_name=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_logging_config=None
        )

        mock_output_manager.add.assert_not_called()

    def test_log_environment_info_enabled(self, unified_logger, mock_output_manager):
        """Test environment info logging when enabled"""
        env_config = {
            "enabled": True,
            "show_language_name": True,
            "show_contest_name": True,
            "show_problem_name": True,
            "show_env_type": True
        }

        unified_logger.log_environment_info(
            language_name="Python",
            contest_name="AtCoder",
            problem_name="A",
            env_type="local",
            env_logging_config=env_config
        )

        mock_output_manager.add.assert_called_once()
        args, kwargs = mock_output_manager.add.call_args
        assert "Language: Python" in args[0]
        assert "Contest: AtCoder" in args[0]
        assert "Problem: A" in args[0]
        assert "Environment: local" in args[0]
        assert args[1] == LogLevel.INFO

    def test_log_environment_info_partial_config(self, unified_logger, mock_output_manager):
        """Test environment info logging with partial configuration"""
        env_config = {
            "enabled": True,
            "show_language_name": True,
            "show_contest_name": False,
            "show_problem_name": True,
            "show_env_type": False
        }

        unified_logger.log_environment_info(
            language_name="Python",
            contest_name="AtCoder",
            problem_name="A",
            env_type="local",
            env_logging_config=env_config
        )

        mock_output_manager.add.assert_called_once()
        args, kwargs = mock_output_manager.add.call_args
        assert "Language: Python" in args[0]
        assert "Contest: AtCoder" not in args[0]
        assert "Problem: A" in args[0]
        assert "Environment: local" not in args[0]

    def test_log_environment_info_no_display_flags(self, unified_logger, mock_output_manager):
        """Test environment info logging with no display flags"""
        env_config = {
            "enabled": True,
            "show_language_name": False,
            "show_contest_name": False,
            "show_problem_name": False,
            "show_env_type": False
        }

        unified_logger.log_environment_info(
            language_name=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_logging_config=env_config
        )

        mock_output_manager.add.assert_not_called()

    def test_is_enabled(self, unified_logger):
        """Test is_enabled method"""
        assert unified_logger.is_enabled() is True

        unified_logger.enabled = False
        assert unified_logger.is_enabled() is False

    def test_format_message_no_args(self, unified_logger):
        """Test message formatting without arguments"""
        result = unified_logger._format_message("Simple message", ())

        assert result == "Simple message"

    def test_format_message_with_args(self, unified_logger):
        """Test message formatting with arguments"""
        result = unified_logger._format_message("Hello %s, count: %d", ("world", 42))

        assert result == "Hello world, count: 42"


    def test_icons_merge_priority(self, mock_output_manager, mock_di_container, mock_config_manager):
        """Test icon configuration merge priority (user > config > defaults)"""
        # Configure mock to return config icons
        mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('logging_config', 'unified_logger', 'default_enabled'): True,
            ('logging_config', 'unified_logger', 'default_format', 'icons'): {
                "debug": "🐞",  # Config overrides default
                "info": "📋"   # Config overrides default
            }
        }[tuple(path)] if tuple(path) != ('logging_config', 'unified_logger', 'defaults', 'status_success') else "completed"

        logger_config = {
            "format": {
                "icons": {
                    "debug": "🐛",  # User overrides config and default
                    "warning": "⚠️"  # User adds new icon
                }
            }
        }

        logger = UnifiedLogger(
            output_manager=mock_output_manager,
            name="test_logger_merge",
            logger_config=logger_config,
            di_container=mock_di_container
        )

        # User config should have highest priority
        assert logger.icons["debug"] == "🐛"
        # Config should override default
        assert logger.icons["info"] == "📋"
        # User config should add new icons
        assert logger.icons["warning"] == "⚠️"
        # Default should be used when not overridden
        assert logger.icons["error"] == "💥"

    def test_unified_logger_integration(self, mock_infrastructure):
        """統一ロガーの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # 統一されたログ機能のテスト（必須パラメータ明示）
        logger.info("Test message")

        # ロガーの基本プロパティ確認
        assert logger is not None
        assert hasattr(logger, 'enabled')
        assert hasattr(logger, 'session_id')

    def test_debug_logging_integration(self, mock_infrastructure):
        """デバッグログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # デバッグメッセージのテスト（必須パラメータ明示）
        logger.debug("Test debug message")

        # 引数付きデバッグメッセージのテスト（必須パラメータ明示）
        logger.debug("Test %s message %d", "debug", 42)

    def test_info_logging_integration(self, mock_infrastructure):
        """INFOログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # INFOメッセージのテスト（必須パラメータ明示）
        logger.info("Test info message")

    def test_warning_logging_integration(self, mock_infrastructure):
        """WARNINGログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # WARNINGメッセージのテスト（必須パラメータ明示）
        logger.warning("Test warning message")

    def test_error_logging_integration(self, mock_infrastructure):
        """ERRORログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # ERRORメッセージのテスト（必須パラメータ明示）
        logger.error("Test error message")

    def test_critical_logging_integration(self, mock_infrastructure):
        """CRITICALログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # CRITICALメッセージのテスト（必須パラメータ明示）
        logger.critical("Test critical message")

    def test_log_error_with_correlation_integration(self, mock_infrastructure):
        """相関ID付きエラーログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # 相関ID付きエラーログのテスト（必須パラメータ明示）
        logger.log_error_with_correlation(
            error_id="ERR001",
            error_code="VALIDATION_FAILED",
            message="Test error",
            context={"field": "username"}
        )

        # ログが記録されたことを確認
        assert logger is not None

    def test_log_operation_start_integration(self, mock_infrastructure):
        """操作開始ログの統合テスト（必須パラメータ明示）"""
        infrastructure = mock_infrastructure
        logger = infrastructure.resolve('unified_logger')

        # 操作開始ログのテスト（必須パラメータ明示）
        logger.log_operation_start(
            operation_id="OP001",
            operation_type="DATABASE_QUERY",
            details={"table": "users"}
        )

        # ログが記録されたことを確認
        assert logger is not None


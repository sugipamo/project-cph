"""
Debug logger のテストケース
"""
from unittest.mock import patch

import pytest

from src.utils.debug_logger import MAX_COMMAND_LENGTH, DebugLevel, DebugLogger


class TestDebugLevel:
    """DebugLevel enum のテスト"""

    def test_debug_level_values(self):
        """DebugLevel の値確認"""
        assert DebugLevel.NONE.value == "none"
        assert DebugLevel.MINIMAL.value == "minimal"
        assert DebugLevel.DETAILED.value == "detailed"


class TestDebugLogger:
    """DebugLogger クラスのテスト"""

    def test_init_default_config(self):
        """デフォルト設定での初期化テスト"""
        logger = DebugLogger()

        assert logger.config == {}
        assert logger.enabled is False
        assert logger.level == DebugLevel.MINIMAL
        assert logger.format_config == {}
        assert "start" in logger.icons
        assert logger.icons["start"] == "🚀"

    def test_init_with_config(self):
        """設定ありでの初期化テスト"""
        config = {
            "enabled": True,
            "level": "detailed",
            "format": {
                "icons": {
                    "start": "▶️",
                    "custom": "⭐"
                }
            }
        }

        logger = DebugLogger(config)

        assert logger.config == config
        assert logger.enabled is True
        assert logger.level == DebugLevel.DETAILED
        assert logger.format_config == config["format"]
        assert logger.icons["start"] == "▶️"
        assert logger.icons["custom"] == "⭐"
        assert logger.icons["success"] == "✅"  # Default icon should still exist

    def test_init_invalid_level(self):
        """無効なレベルでの初期化テスト"""
        config = {"level": "invalid"}

        with pytest.raises(ValueError):
            DebugLogger(config)

    def test_log_step_start_disabled(self):
        """無効時のlog_step_startテスト"""
        logger = DebugLogger({"enabled": False})

        with patch('builtins.print') as mock_print:
            logger.log_step_start("test", "shell")
            mock_print.assert_not_called()

    def test_log_step_start_enabled_minimal(self):
        """有効・minimal レベルでのlog_step_startテスト"""
        logger = DebugLogger({
            "enabled": True,
            "level": "minimal"
        })

        with patch('builtins.print') as mock_print:
            logger.log_step_start("test step", "shell", cmd=["echo", "hello"])

            # 呼び出し回数の確認
            assert mock_print.call_count >= 2

            # 最初の呼び出しで実行開始ログ
            first_call = mock_print.call_args_list[0][0][0]
            assert "実行開始: test step" in first_call
            assert "🚀" in first_call

    def test_log_step_start_enabled_detailed(self):
        """有効・detailed レベルでのlog_step_startテスト"""
        logger = DebugLogger({
            "enabled": True,
            "level": "detailed"
        })

        with patch('builtins.print') as mock_print:
            logger.log_step_start("test step", "OperationType.SHELL",
                                cmd=["echo", "hello"], allow_failure=True)

            assert mock_print.call_count >= 3

            # 詳細情報が出力されることを確認
            all_output = ' '.join([call[0][0] for call in mock_print.call_args_list])
            assert "タイプ: OperationType.SHELL" in all_output
            assert "コマンド:" in all_output
            assert "失敗許可: True" in all_output

    def test_log_step_success_disabled(self):
        """無効時のlog_step_successテスト"""
        logger = DebugLogger({"enabled": False})

        with patch('builtins.print') as mock_print:
            logger.log_step_success("test", "success message")
            mock_print.assert_not_called()

    def test_log_step_success_enabled(self):
        """有効時のlog_step_successテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_step_success("test step", "all good")

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "完了: test step - all good" in output
            assert "✅" in output

    def test_log_step_success_no_message(self):
        """メッセージなしのlog_step_successテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_step_success("test step")

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "完了: test step" in output
            assert " - " not in output  # No message suffix

    def test_log_step_failure_disabled(self):
        """無効時のlog_step_failureテスト"""
        logger = DebugLogger({"enabled": False})

        with patch('builtins.print') as mock_print:
            logger.log_step_failure("test", "error occurred")
            mock_print.assert_not_called()

    def test_log_step_failure_enabled_not_allowed(self):
        """有効時・失敗許可なしのlog_step_failureテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_step_failure("test step", "error occurred", allow_failure=False)

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "失敗: test step" in output
            assert "❌" in output

    def test_log_step_failure_enabled_allowed(self):
        """有効時・失敗許可ありのlog_step_failureテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_step_failure("test step", "error occurred", allow_failure=True)

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "失敗許可: test step" in output
            assert "⚠️" in output

    def test_log_step_failure_detailed_level(self):
        """detailed レベルでのlog_step_failureテスト"""
        logger = DebugLogger({
            "enabled": True,
            "level": "detailed"
        })

        with patch('builtins.print') as mock_print:
            logger.log_step_failure("test step", "detailed error", allow_failure=False)

            assert mock_print.call_count == 2
            # Error details should be printed
            error_output = mock_print.call_args_list[1][0][0]
            assert "エラー: detailed error" in error_output

    def test_log_preparation_start_disabled(self):
        """無効時のlog_preparation_startテスト"""
        logger = DebugLogger({"enabled": False})

        with patch('builtins.print') as mock_print:
            logger.log_preparation_start(5)
            mock_print.assert_not_called()

    def test_log_preparation_start_enabled(self):
        """有効時のlog_preparation_startテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_preparation_start(5)

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "環境準備開始: 5タスク" in output
            assert "🚀" in output

    def test_log_workflow_start_disabled(self):
        """無効時のlog_workflow_startテスト"""
        logger = DebugLogger({"enabled": False})

        with patch('builtins.print') as mock_print:
            logger.log_workflow_start(10, parallel=True)
            mock_print.assert_not_called()

    def test_log_workflow_start_enabled_sequential(self):
        """有効時・順次実行のlog_workflow_startテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_workflow_start(10, parallel=False)

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "ワークフロー実行開始: 10ステップ (順次実行)" in output

    def test_log_workflow_start_enabled_parallel(self):
        """有効時・並列実行のlog_workflow_startテスト"""
        logger = DebugLogger({"enabled": True})

        with patch('builtins.print') as mock_print:
            logger.log_workflow_start(10, parallel=True)

            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "ワークフロー実行開始: 10ステップ (並列実行)" in output

    def test_log_step_details_file_operations(self):
        """ファイル操作のステップ詳細ログテスト"""
        logger = DebugLogger({"enabled": True, "level": "detailed"})

        # mkdir operation
        with patch('builtins.print') as mock_print:
            logger._log_step_details("FILE.MKDIR", path="/test/path")

            assert mock_print.call_count >= 2
            all_output = ' '.join([call[0][0] for call in mock_print.call_args_list])
            assert "タイプ: FILE.MKDIR" in all_output
            assert "パス: /test/path" in all_output

        # copy operation
        with patch('builtins.print') as mock_print:
            logger._log_step_details("FILE.COPY", source="/src", dest="/dst")

            all_output = ' '.join([call[0][0] for call in mock_print.call_args_list])
            assert "タイプ: FILE.COPY" in all_output
            assert "パス: /src" in all_output
            assert "送信先: /dst" in all_output

    def test_log_step_details_operation_type(self):
        """OperationType のステップ詳細ログテスト"""
        logger = DebugLogger({"enabled": True, "level": "detailed"})

        with patch('builtins.print') as mock_print:
            logger._log_step_details("OperationType.SHELL",
                                   cmd=["echo", "test"],
                                   allow_failure=True,
                                   show_output=False)

            all_output = ' '.join([call[0][0] for call in mock_print.call_args_list])
            assert "タイプ: OperationType.SHELL" in all_output
            assert "コマンド:" in all_output
            assert "失敗許可: True" in all_output
            assert "出力表示: False" in all_output

    def test_get_type_icon(self):
        """_get_type_icon メソッドのテスト"""
        logger = DebugLogger()

        # File operations
        assert logger._get_type_icon("FILE.MKDIR") == "📁"
        assert logger._get_type_icon("FILE.COPY") == "📋"
        assert logger._get_type_icon("FILE.UNKNOWN") == "📁"  # Default file icon

        # Other operation types
        assert logger._get_type_icon("OperationType.SHELL") == "🔧"
        assert logger._get_type_icon("OperationType.PYTHON") == "🐍"
        assert logger._get_type_icon("OperationType.DOCKER") == "🐳"
        assert logger._get_type_icon("TEST") == "🧪"
        assert logger._get_type_icon("BUILD") == "🔨"
        assert logger._get_type_icon("RESULT") == "📊"
        assert logger._get_type_icon("UNKNOWN") == "🔧"  # Default icon

    def test_is_enabled(self):
        """is_enabled メソッドのテスト"""
        logger_disabled = DebugLogger({"enabled": False})
        logger_enabled = DebugLogger({"enabled": True})

        assert logger_disabled.is_enabled() is False
        assert logger_enabled.is_enabled() is True

    def test_get_level(self):
        """get_level メソッドのテスト"""
        logger_minimal = DebugLogger({"level": "minimal"})
        logger_detailed = DebugLogger({"level": "detailed"})

        assert logger_minimal.get_level() == DebugLevel.MINIMAL
        assert logger_detailed.get_level() == DebugLevel.DETAILED

    def test_format_command_string(self):
        """_format_command メソッドのテスト（文字列）"""
        logger = DebugLogger()

        # Short command
        result = logger._format_command("echo hello")
        assert result == "echo hello"

        # Long command
        long_cmd = "a" * (MAX_COMMAND_LENGTH + 10)
        result = logger._format_command(long_cmd)
        assert len(result) <= MAX_COMMAND_LENGTH + 3  # +3 for "..."
        assert result.endswith("...")

    def test_format_command_list(self):
        """_format_command メソッドのテスト（リスト）"""
        logger = DebugLogger()

        # Short command list
        result = logger._format_command(["echo", "hello", "world"])
        assert "echo" in result
        assert "hello" in result
        assert "world" in result

        # Long command list
        long_parts = ["part" + str(i) for i in range(50)]
        result = logger._format_command(long_parts)
        assert "..." in result
        assert len(result) <= MAX_COMMAND_LENGTH + 50  # More tolerance for list formatting

        # Command list with very long individual parts
        long_part = "a" * (MAX_COMMAND_LENGTH // 2 + 10)
        result = logger._format_command([long_part, "short"])
        assert "..." in result

    def test_format_command_edge_cases(self):
        """_format_command メソッドのエッジケーステスト"""
        logger = DebugLogger()

        # Empty list
        result = logger._format_command([])
        assert result == "[]"

        # Non-string types
        result = logger._format_command(123)
        assert result == "123"

        # Mixed types in list
        result = logger._format_command([1, "hello", 3.14])
        assert "1" in result
        assert "hello" in result
        assert "3.14" in result


class TestConstants:
    """定数のテスト"""

    def test_max_command_length(self):
        """MAX_COMMAND_LENGTH 定数のテスト"""
        assert MAX_COMMAND_LENGTH == 80
        assert isinstance(MAX_COMMAND_LENGTH, int)
        assert MAX_COMMAND_LENGTH > 0

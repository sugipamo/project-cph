"""Debug logger with configurable output formats
"""
from enum import Enum
from typing import Any, Optional

# コマンド表示の最大文字数
MAX_COMMAND_LENGTH = 80


class DebugLevel(Enum):
    """Debug output levels"""
    NONE = "none"
    MINIMAL = "minimal"
    DETAILED = "detailed"


class DebugLogger:
    """Configurable debug output logger for workflow execution
    """

    def __init__(self, logger_config: Optional[dict[str, Any]] = None):
        """Initialize debug logger with configuration

        Args:
            logger_config: Debug configuration from env.json
        """
        self.config = logger_config or {}
        self.enabled = "enabled" in self.config and self.config["enabled"] or False
        self.level = DebugLevel(self.config["level"] if "level" in self.config else "minimal")
        self.format_config = self.config["format"] if "format" in self.config else {}

        # Default emoji/icon mappings
        self.default_icons = {
            "start": "🚀",
            "file_mkdir": "📁",
            "file_copy": "📋",
            "file_move": "🔄",
            "file_remove": "🗑️",
            "shell": "🔧",
            "python": "🐍",
            "docker": "🐳",
            "test": "🧪",
            "build": "🔨",
            "result": "📊",
            "success": "✅",
            "failure": "❌",
            "warning": "⚠️",
            "executing": "⏱️"
        }

        # Merge with user-provided icons
        self.icons = {**self.default_icons, **(self.format_config["icons"] if "icons" in self.format_config else {})}

    def log_step_start(self, step_name: str, step_type: str, **kwargs):
        """Log step execution start"""
        if not self.enabled:
            return

        icon = self.icons["start"] if "start" in self.icons else "🚀"
        print(f"\n{icon} 実行開始: {step_name}")

        # Log step details based on level
        if self.level in [DebugLevel.MINIMAL, DebugLevel.DETAILED]:
            self._log_step_details(step_type, **kwargs)

        executing_icon = self.icons["executing"] if "executing" in self.icons else "⏱️"
        print(f"  {executing_icon}  実行中...")

    def log_step_success(self, step_name: str, message: str = ""):
        """Log step success"""
        if not self.enabled:
            return

        icon = self.icons["success"] if "success" in self.icons else "✅"
        success_message = f"{icon} 完了: {step_name}"
        if message:
            success_message += f" - {message}"
        print(success_message)

    def log_step_failure(self, step_name: str, error: str, allow_failure: bool = False):
        """Log step failure"""
        if not self.enabled:
            return

        if allow_failure:
            icon = self.icons["warning"] if "warning" in self.icons else "⚠️"
            status = "失敗許可"
        else:
            icon = self.icons["failure"] if "failure" in self.icons else "❌"
            status = "失敗"

        print(f"{icon} {status}: {step_name}")
        if self.level == DebugLevel.DETAILED and error:
            print(f"  エラー: {error}")

    def log_preparation_start(self, task_count: int):
        """Log preparation phase start"""
        if not self.enabled:
            return

        icon = self.icons["start"] if "start" in self.icons else "🚀"
        print(f"\n{icon} 環境準備開始: {task_count}タスク")

    def log_workflow_start(self, step_count: int, parallel: bool = False):
        """Log workflow execution start"""
        if not self.enabled:
            return

        icon = self.icons["start"] if "start" in self.icons else "🚀"
        mode = "並列" if parallel else "順次"
        print(f"\n{icon} ワークフロー実行開始: {step_count}ステップ ({mode}実行)")

    def log_environment_info(self, language_name: Optional[str] = None, contest_name: Optional[str] = None,
                           problem_name: Optional[str] = None, env_type: Optional[str] = None,
                           env_logging_config: Optional[dict] = None):
        """Log environment information if enabled in configuration"""
        if not env_logging_config:
            return

        enabled = "enabled" in env_logging_config and env_logging_config["enabled"] or False
        if not enabled:
            return

        # Check if all required flags are False
        show_language = "show_language_name" in env_logging_config and env_logging_config["show_language_name"] or True
        show_contest = "show_contest_name" in env_logging_config and env_logging_config["show_contest_name"] or True
        show_problem = "show_problem_name" in env_logging_config and env_logging_config["show_problem_name"] or True
        show_env_type = "show_env_type" in env_logging_config and env_logging_config["show_env_type"] or True

        if not any([show_language, show_contest, show_problem, show_env_type]):
            return

        icon = self.icons["start"] if "start" in self.icons else "🚀"
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
            print(f"{icon} 実行環境: {env_info}")

    def _log_step_details(self, step_type: str, **kwargs):
        """Log detailed step information"""
        # Determine appropriate icon based on step type
        type_icon = self._get_type_icon(step_type)

        if step_type.startswith("FILE."):
            file_op = step_type.split(".", 1)[1].lower()
            print(f"  {type_icon} タイプ: {step_type}")

            if file_op in ["mkdir", "touch", "remove", "rmtree"]:
                if "path" in kwargs:
                    print(f"  📂 パス: {kwargs['path']}")
            elif file_op in ["copy", "move"]:
                if "source" in kwargs:
                    print(f"  📂 パス: {kwargs['source']}")
                if "dest" in kwargs:
                    print(f"  📋 送信先: {kwargs['dest']}")

        elif step_type.startswith("OperationType."):
            print(f"  {type_icon} タイプ: {step_type}")
            if "cmd" in kwargs:
                cmd_str = self._format_command(kwargs["cmd"])
                print(f"  ⚡ コマンド: {cmd_str}")

        # Common properties
        if "allow_failure" in kwargs:
            failure_icon = self.icons["warning"] if "warning" in self.icons else "⚠️"
            print(f"  {failure_icon}  失敗許可: {kwargs['allow_failure']}")

        if "show_output" in kwargs:
            print(f"  📺 出力表示: {kwargs['show_output']}")

    def _get_type_icon(self, step_type: str) -> str:
        """Get appropriate icon for step type"""
        if step_type.startswith("FILE."):
            file_op = step_type.split(".", 1)[1].lower()
            return self.icons[f"file_{file_op}"] if f"file_{file_op}" in self.icons else (self.icons["file_mkdir"] if "file_mkdir" in self.icons else "📁")
        if "SHELL" in step_type:
            return self.icons["shell"] if "shell" in self.icons else "🔧"
        if "PYTHON" in step_type:
            return self.icons["python"] if "python" in self.icons else "🐍"
        if "DOCKER" in step_type:
            return self.icons["docker"] if "docker" in self.icons else "🐳"
        if "TEST" in step_type:
            return self.icons["test"] if "test" in self.icons else "🧪"
        if "BUILD" in step_type:
            return self.icons["build"] if "build" in self.icons else "🔨"
        if "RESULT" in step_type:
            return self.icons["result"] if "result" in self.icons else "📊"
        return "🔧"

    def is_enabled(self) -> bool:
        """Check if debug logging is enabled"""
        return self.enabled

    def get_level(self) -> DebugLevel:
        """Get current debug level"""
        return self.level

    def _format_command(self, cmd) -> str:
        """Format command for display with length limit"""
        if isinstance(cmd, list):
            # リストの場合は各要素を処理
            formatted_parts = []
            total_length = 0

            for part in cmd:
                part_str = str(part)
                # 各パートが長すぎる場合は個別に短縮
                if len(part_str) > MAX_COMMAND_LENGTH // 2:
                    part_str = part_str[:MAX_COMMAND_LENGTH // 2] + "..."

                # 全体の長さをチェック
                if total_length + len(part_str) + 4 > MAX_COMMAND_LENGTH:  # +4 for "[]", spaces
                    formatted_parts.append("...")
                    break

                formatted_parts.append(part_str)
                total_length += len(part_str) + 2  # +2 for quotes/spaces

            return str(formatted_parts)
        # 文字列の場合
        cmd_str = str(cmd)
        if len(cmd_str) > MAX_COMMAND_LENGTH:
            return cmd_str[:MAX_COMMAND_LENGTH] + "..."
        return cmd_str

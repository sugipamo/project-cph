"""Abstract base class for shell command execution."""
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Union

from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface


class ShellDriver(ExecutionDriverInterface):
    """Abstract base class for shell command execution."""

    def __init__(self):
        """Initialize ShellDriver with infrastructure defaults."""
        # 互換性維持: 設定システムでgetattr()デフォルト値を管理
        self._infrastructure_defaults = self._load_infrastructure_defaults()

    def _load_infrastructure_defaults(self) -> dict[str, Any]:
        """Load infrastructure defaults from config file."""
        try:
            config_path = Path(__file__).parents[4] / "config" / "system" / "infrastructure_defaults.json"
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # フォールバック: デフォルト値をハードコード
            return {
                "infrastructure_defaults": {
                    "shell": {"cwd": None, "env": {}, "inputdata": None, "timeout": 30}
                }
            }

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        for key in path:
            current = current[key]
        if isinstance(current, default_type):
            return current
        # 型が不一致の場合のフォールバック
        if default_type is dict:
            return {}
        if default_type is int:
            return 30
        return None

    @abstractmethod
    def execute_shell_command(self, cmd: Union[str, list[str]], cwd: str,
                            env: dict[str, str], inputdata: str,
                            timeout: int) -> Any:
        """Execute a shell command.

        Args:
            cmd: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables
            inputdata: Input data to pass to the command
            timeout: Command timeout in seconds

        Returns:
            Command execution result
        """


    def execute_command(self, request: Any) -> Any:
        """Execute a shell request."""
        # Delegate to execute_shell_command method
        if hasattr(request, 'cmd'):
            # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
            return self.execute_shell_command(
                cmd=request.cmd,
                cwd=request.cwd if hasattr(request, 'cwd') else self._get_default_value(['infrastructure_defaults', 'shell', 'cwd'], type(None)),
                env=request.env if hasattr(request, 'env') else self._get_default_value(['infrastructure_defaults', 'shell', 'env'], dict),
                inputdata=request.inputdata if hasattr(request, 'inputdata') else self._get_default_value(['infrastructure_defaults', 'shell', 'inputdata'], type(None)),
                timeout=request.timeout if hasattr(request, 'timeout') else self._get_default_value(['infrastructure_defaults', 'shell', 'timeout'], int)
            )
        raise ValueError("Invalid request type for ShellDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'cmd')

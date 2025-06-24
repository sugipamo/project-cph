"""Python code execution driver."""
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional

# 互換性維持: config_managerは注入されるべき
from src.infrastructure.drivers.base.base_driver import ExecutionDriverInterface
from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


class PythonDriver(ExecutionDriverInterface):
    """Abstract base class for Python code execution."""

    def __init__(self, config_manager: Any):
        """Initialize PythonDriver with configuration manager."""
        self.config_manager = config_manager
        self.python_utils = PythonUtils(self.config_manager)
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
                    "python": {"cwd": None}
                }
            }

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        for key in path:
            current = current[key]
        if isinstance(current, default_type):
            return current
        return None

    @abstractmethod
    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string.

        Args:
            code: Python code to execute
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    @abstractmethod
    def run_script_file(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file.

        Args:
            file_path: Path to Python script
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    def execute_command(self, request: Any) -> Any:
        """Execute a Python request."""
        if hasattr(request, 'code_or_file'):
            if self.python_utils.is_script_file(request.code_or_file):
                return self.run_script_file(
                    request.code_or_file[0],
                    # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
                    cwd=request.cwd if hasattr(request, 'cwd') else self._get_default_value(['infrastructure_defaults', 'python', 'cwd'], type(None))
                )
            if isinstance(request.code_or_file, list):
                code = "\n".join(request.code_or_file)
            else:
                code = request.code_or_file
            return self.run_code_string(
                code,
                # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
                cwd=request.cwd if hasattr(request, 'cwd') else self._get_default_value(['infrastructure_defaults', 'python', 'cwd'], type(None))
            )
        raise ValueError("Invalid request type for PythonDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'code_or_file')


class LocalPythonDriver(PythonDriver):
    """Local Python execution driver using subprocess."""

    def __init__(self, config_manager: Any):
        """Initialize LocalPythonDriver with configuration manager."""
        super().__init__(config_manager)

    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string using subprocess."""
        return self.python_utils.run_code_string(code, cwd)

    def run_script_file(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file using subprocess."""
        return self.python_utils.run_script_file(file_path, cwd)

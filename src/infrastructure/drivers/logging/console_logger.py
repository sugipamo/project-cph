"""コンソールログ統合 - print文とDebugLoggerを統合"""
from abc import ABC, abstractmethod
from enum import Enum


class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ConsoleLogger(ABC):
    """コンソール出力の抽象インターフェース"""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """デバッグメッセージ出力"""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """情報メッセージ出力"""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """警告メッセージ出力"""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """エラーメッセージ出力"""
        pass

    @abstractmethod
    def step_start(self, step_name: str, **kwargs) -> None:
        """ステップ開始ログ"""
        pass

    @abstractmethod
    def step_success(self, step_name: str, message: str = "") -> None:
        """ステップ成功ログ"""
        pass

    @abstractmethod
    def step_failure(self, step_name: str, error: str, allow_failure: bool = False) -> None:
        """ステップ失敗ログ"""
        pass


class SystemConsoleLogger(ConsoleLogger):
    """システムコンソール出力実装 - 副作用はここに集約"""

    def __init__(self, enabled: bool = True, level: LogLevel = LogLevel.INFO):
        self.enabled = enabled
        self.level = level

        # アイコン設定（DebugLoggerから移行）
        self.icons = {
            "start": "🚀",
            "success": "✅",
            "failure": "❌",
            "warning": "⚠️",
            "executing": "⏱️",
            "info": "ℹ️",
            "debug": "🔍",
            "error": "💥"
        }

    def debug(self, message: str, **kwargs) -> None:
        """デバッグメッセージ出力（副作用）"""
        if self.enabled and self._should_log(LogLevel.DEBUG):
            icon = self.icons.get("debug", "🔍")
            print(f"{icon} DEBUG: {message}")

    def info(self, message: str, **kwargs) -> None:
        """情報メッセージ出力（副作用）"""
        if self.enabled and self._should_log(LogLevel.INFO):
            icon = self.icons.get("info", "ℹ️")
            print(f"{icon} {message}")

    def warning(self, message: str, **kwargs) -> None:
        """警告メッセージ出力（副作用）"""
        if self.enabled and self._should_log(LogLevel.WARNING):
            icon = self.icons.get("warning", "⚠️")
            print(f"{icon} WARNING: {message}")

    def error(self, message: str, **kwargs) -> None:
        """エラーメッセージ出力（副作用）"""
        if self.enabled and self._should_log(LogLevel.ERROR):
            icon = self.icons.get("error", "💥")
            print(f"{icon} ERROR: {message}")

    def step_start(self, step_name: str, **kwargs) -> None:
        """ステップ開始ログ（副作用）"""
        if not self.enabled:
            return

        icon = self.icons.get("start", "🚀")
        print(f"\n{icon} 実行開始: {step_name}")

        executing_icon = self.icons.get("executing", "⏱️")
        print(f"  {executing_icon} 実行中...")

    def step_success(self, step_name: str, message: str = "") -> None:
        """ステップ成功ログ（副作用）"""
        if not self.enabled:
            return

        icon = self.icons.get("success", "✅")
        success_message = f"{icon} 完了: {step_name}"
        if message:
            success_message += f" - {message}"
        print(success_message)

    def step_failure(self, step_name: str, error: str, allow_failure: bool = False) -> None:
        """ステップ失敗ログ（副作用）"""
        if not self.enabled:
            return

        if allow_failure:
            icon = self.icons.get("warning", "⚠️")
            status = "失敗許可"
        else:
            icon = self.icons.get("failure", "❌")
            status = "失敗"

        print(f"{icon} {status}: {step_name}")
        if error:
            print(f"  エラー: {error}")

    def config_load_warning(self, file_path: str, error: str) -> None:
        """設定ファイル読み込み警告（重複していたprint文を統合）"""
        self.warning(f"Failed to load {file_path}: {error}")

    def _should_log(self, message_level: LogLevel) -> bool:
        """ログレベルチェック（純粋関数）"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3
        }
        return level_order[message_level] >= level_order[self.level]


class MockConsoleLogger(ConsoleLogger):
    """テスト用モックコンソールログ - 副作用なし"""

    def __init__(self):
        self.messages = []

    def debug(self, message: str, **kwargs) -> None:
        """モックデバッグ出力（副作用なし）"""
        self.messages.append(("DEBUG", message))

    def info(self, message: str, **kwargs) -> None:
        """モック情報出力（副作用なし）"""
        self.messages.append(("INFO", message))

    def warning(self, message: str, **kwargs) -> None:
        """モック警告出力（副作用なし）"""
        self.messages.append(("WARNING", message))

    def error(self, message: str, **kwargs) -> None:
        """モックエラー出力（副作用なし）"""
        self.messages.append(("ERROR", message))

    def step_start(self, step_name: str, **kwargs) -> None:
        """モックステップ開始（副作用なし）"""
        self.messages.append(("STEP_START", step_name))

    def step_success(self, step_name: str, message: str = "") -> None:
        """モックステップ成功（副作用なし）"""
        self.messages.append(("STEP_SUCCESS", f"{step_name}: {message}"))

    def step_failure(self, step_name: str, error: str, allow_failure: bool = False) -> None:
        """モックステップ失敗（副作用なし）"""
        status = "FAILURE_ALLOWED" if allow_failure else "FAILURE"
        self.messages.append((status, f"{step_name}: {error}"))

    def config_load_warning(self, file_path: str, error: str) -> None:
        """モック設定警告（副作用なし）"""
        self.warning(f"Failed to load {file_path}: {error}")

    def get_messages(self) -> list:
        """テスト用メッセージ取得"""
        return self.messages.copy()

    def clear_messages(self) -> None:
        """テスト用メッセージクリア"""
        self.messages.clear()

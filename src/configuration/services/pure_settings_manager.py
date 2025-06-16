"""純粋な設定管理システム

runtime状態管理から分離された3層設定システム（system/shared/language）
"""
from typing import Any, Dict, Optional

from ..expansion.template_expander import TemplateExpander
from ..interfaces.execution_settings import IExecutionSettings
from ..interfaces.runtime_settings import IRuntimeSettings
from ..interfaces.settings_manager import ISettingsManager
from ..loaders.configuration_loader import ConfigurationLoader
from ..registries.language_registry import LanguageRegistry


class PureExecutionSettings(IExecutionSettings):
    """純粋な実行設定実装"""

    def __init__(self, contest_name: str, problem_name: str, language: str,
                 env_type: str, command_type: str, old_contest_name: str = "",
                 old_problem_name: str = "", paths: Optional[Dict[str, str]] = None,
                 file_patterns: Optional[Dict[str, list]] = None):
        self._contest_name = contest_name
        self._problem_name = problem_name
        self._language = language
        self._env_type = env_type
        self._command_type = command_type
        self._old_contest_name = old_contest_name
        self._old_problem_name = old_problem_name
        self._paths = paths or {}
        self._file_patterns = file_patterns or {}

    def get_contest_name(self) -> str:
        return self._contest_name

    def get_problem_name(self) -> str:
        return self._problem_name

    def get_language(self) -> str:
        return self._language

    def get_env_type(self) -> str:
        return self._env_type

    def get_command_type(self) -> str:
        return self._command_type

    def get_old_contest_name(self) -> str:
        return self._old_contest_name

    def get_old_problem_name(self) -> str:
        return self._old_problem_name

    def get_paths(self) -> Dict[str, str]:
        return self._paths.copy()

    def get_file_patterns(self) -> Dict[str, list]:
        return self._file_patterns.copy()

    def to_template_dict(self) -> Dict[str, str]:
        """テンプレート展開用辞書の生成"""
        template_dict = {
            "contest_name": self._contest_name,
            "problem_name": self._problem_name,
            "old_contest_name": self._old_contest_name,
            "old_problem_name": self._old_problem_name,
            "language": self._language,
            "language_name": self._language,  # エイリアス
            "env_type": self._env_type,
            "command_type": self._command_type,
        }

        # パス変数の追加
        for key, value in self._paths.items():
            template_dict[key] = str(value)
            # _pathサフィックス付きのエイリアス
            if not key.endswith("_path"):
                template_dict[f"{key}_path"] = str(value)

        return template_dict


class PureRuntimeSettings(IRuntimeSettings):
    """純粋なRuntime設定実装"""

    def __init__(self, language_id: str, source_file_name: str, run_command: str,
                 timeout_seconds: int = 300, retry_settings: Optional[Dict[str, Any]] = None):
        self._language_id = language_id
        self._source_file_name = source_file_name
        self._run_command = run_command
        self._timeout_seconds = timeout_seconds
        self._retry_settings = retry_settings or {}

    def get_language_id(self) -> str:
        return self._language_id

    def get_source_file_name(self) -> str:
        return self._source_file_name

    def get_run_command(self) -> str:
        return self._run_command

    def get_timeout_seconds(self) -> int:
        return self._timeout_seconds

    def get_retry_settings(self) -> Dict[str, Any]:
        return self._retry_settings.copy()

    def to_runtime_dict(self) -> Dict[str, str]:
        """Runtime用辞書の生成"""
        return {
            "language_id": self._language_id,
            "source_file_name": self._source_file_name,
            "run_command": self._run_command,
            "timeout_seconds": str(self._timeout_seconds),
        }


class PureSettingsManager(ISettingsManager):
    """純粋な設定管理実装

    runtime状態管理から完全に分離された設定システム
    """

    def __init__(self, config_loader: ConfigurationLoader, language_registry: LanguageRegistry):
        self.config_loader = config_loader
        self.language_registry = language_registry
        self._current_execution_settings: Optional[PureExecutionSettings] = None
        self._template_expander: Optional[TemplateExpander] = None

    def get_execution_settings(self) -> IExecutionSettings:
        """実行設定の取得"""
        if self._current_execution_settings is None:
            raise RuntimeError("Execution settings not initialized. Call initialize() first.")
        return self._current_execution_settings

    def get_runtime_settings(self, language: str) -> IRuntimeSettings:
        """Runtime設定の取得"""
        language_config = self.language_registry.get_language_config(language)

        return PureRuntimeSettings(
            language_id=language_config.get("language_id", ""),
            source_file_name=language_config.get("source_file_name", "main.py"),
            run_command=language_config.get("run_command", "python3"),
            timeout_seconds=language_config.get("timeout_seconds", 300),
            retry_settings=language_config.get("retry_settings", {})
        )

    def save_execution_context(self, context: Dict[str, Any]) -> None:
        """実行コンテキストの保存

        Note: 純粋な設定システムでは状態保存は行わない
        状態管理は別のStateManagerで行う
        """
        # 設定システムでは状態保存は責務外
        pass

    def load_execution_context(self) -> Optional[Dict[str, Any]]:
        """実行コンテキストの読み込み

        Note: 純粋な設定システムでは状態読み込みは行わない
        """
        # 設定システムでは状態読み込みは責務外
        return None

    def expand_template(self, template: str, context: Dict[str, str]) -> str:
        """テンプレート展開"""
        # シンプルな展開実装
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def initialize(self, contest_name: str, problem_name: str, language: str,
                   env_type: str = "local", command_type: str = "open",
                   old_contest_name: str = "", old_problem_name: str = "") -> None:
        """設定の初期化

        Args:
            contest_name: コンテスト名
            problem_name: 問題名
            language: 言語名
            env_type: 環境タイプ
            command_type: コマンドタイプ
            old_contest_name: 前回のコンテスト名
            old_problem_name: 前回の問題名
        """
        # 3層設定（system/shared/language）の読み込み
        config_source = self.config_loader.load_configuration(
            language=language,
            env_type=env_type
        )

        # パス設定とファイルパターンの抽出
        paths = config_source.get_paths()
        file_patterns = config_source.get_file_patterns()

        # 実行設定の作成
        self._current_execution_settings = PureExecutionSettings(
            contest_name=contest_name,
            problem_name=problem_name,
            language=language,
            env_type=env_type,
            command_type=command_type,
            old_contest_name=old_contest_name,
            old_problem_name=old_problem_name,
            paths=paths,
            file_patterns=file_patterns
        )

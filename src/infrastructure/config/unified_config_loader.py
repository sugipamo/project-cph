"""統合設定読み込み - 重複する設定読み込み機能を統合"""
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..providers.file_provider import FileProvider


class UnifiedConfigLoader:
    """設定読み込みの一元化 - 副作用をinfrastructureに集約

    既存の以下2つの実装を統合:
    - configuration/loaders/configuration_loader.py
    - infrastructure/config/json_config_loader.py
    """

    def __init__(self,
                 contest_env_dir: Path,
                 system_config_dir: Path,
                 file_provider: FileProvider = None):
        self.contest_env_dir = contest_env_dir
        self.system_config_dir = system_config_dir
        self.file_provider = file_provider or FileProvider()

    def load_unified_source(self, language: str, runtime_args: Dict[str, Any]) -> Dict[str, Any]:
        """統合設定ソースを読み込み（新ConfigurationSource形式）

        Args:
            language: 対象言語
            runtime_args: 実行時引数

        Returns:
            統合設定辞書
        """
        system_config = self.load_system_configs()
        shared_config, language_config = self.load_env_configs(language)

        return {
            "system": system_config,
            "shared": shared_config,
            "language": language_config,
            "runtime": runtime_args
        }

    def load_system_configs(self) -> Dict[str, Any]:
        """システム設定の読み込み（副作用をfileProviderに委譲）

        Returns:
            システム設定辞書
        """
        system_config = {}

        if not self.system_config_dir.exists():
            return system_config

        # 読み込むシステム設定ファイル
        system_files = [
            "docker_security.json",
            "docker_defaults.json",
            "system_constants.json",
            "dev_config.json"
        ]

        for config_file in system_files:
            file_path = self.system_config_dir / config_file
            config_data = self._load_json_file(file_path)
            if config_data:
                system_config.update(config_data)

        return system_config

    def load_env_configs(self, language: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """環境設定（共有・言語固有）の読み込み

        Args:
            language: 対象言語

        Returns:
            (shared_config, language_config): 共有設定と言語固有設定のタプル
        """
        shared_config = {}
        language_config = {}

        if not self.contest_env_dir.exists():
            return shared_config, language_config

        # 共有設定を読み込み
        shared_file = self.contest_env_dir / "shared" / "env.json"
        shared_data = self._load_json_file(shared_file)
        if shared_data:
            shared_config = shared_data.get("shared", {})

        # 言語固有設定を読み込み
        language_file = self.contest_env_dir / language / "env.json"
        language_data = self._load_json_file(language_file)
        if language_data:
            language_config = language_data.get(language, {})

        return shared_config, language_config

    def get_env_config(self) -> Dict[str, Any]:
        """環境設定全体を読み込み（JsonConfigLoader互換）

        Returns:
            マージされた環境設定辞書
        """
        config = {}

        # システム設定読み込み（最低優先度）
        system_config = self.load_system_configs()
        if system_config:
            config = self._deep_merge(config, {"shared": system_config})

        if not self.contest_env_dir.exists():
            return config

        # 共有設定読み込み
        shared_data = self._load_json_file(self.contest_env_dir / "shared" / "env.json")
        if shared_data:
            config = self._deep_merge(config, shared_data)

        # 言語固有設定読み込み（最高優先度）
        try:
            for lang_dir in self.contest_env_dir.iterdir():
                if lang_dir.is_dir() and lang_dir.name != "shared":
                    lang_data = self._load_json_file(lang_dir / "env.json")
                    if lang_data:
                        config = self._deep_merge(config, lang_data)
        except (OSError, PermissionError):
            pass

        return config

    def get_language_config(self, language: str) -> Dict[str, Any]:
        """言語固有設定を取得（JsonConfigLoader互換）

        Args:
            language: 言語名

        Returns:
            言語設定辞書（共有設定 + 言語固有設定）
        """
        shared_config = self.get_shared_config()

        config = self.get_env_config()
        language_config = config.get(language, {})

        return self._deep_merge(shared_config, language_config)

    def get_shared_config(self) -> Dict[str, Any]:
        """共有設定を取得（JsonConfigLoader互換）

        Returns:
            共有設定辞書
        """
        shared_data = self._load_json_file(self.contest_env_dir / "shared" / "env.json")
        return shared_data.get("shared", {}) if shared_data else {}

    def get_file_patterns(self, language: str) -> Dict[str, Dict[str, List[str]]]:
        """ファイルパターン設定を取得（JsonConfigLoader互換）"""
        lang_config = self.get_language_config(language)
        return lang_config.get("file_patterns", {})

    def get_supported_languages(self) -> List[str]:
        """サポート言語一覧を取得（JsonConfigLoader互換）"""
        supported = []

        if not self.contest_env_dir.exists():
            return supported

        try:
            for lang_dir in self.contest_env_dir.iterdir():
                if (lang_dir.is_dir() and
                    lang_dir.name != "shared" and
                    self._has_file_patterns_support(lang_dir.name)):
                    supported.append(lang_dir.name)
        except (OSError, PermissionError):
            pass

        return supported

    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """JSONファイル読み込み（副作用をfileProviderに委譲）

        Args:
            file_path: ファイルパス

        Returns:
            JSONデータ辞書（読み込み失敗時は空辞書）
        """
        if not file_path.exists():
            return {}

        try:
            content = self.file_provider.read_text_file(str(file_path))
            return json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            # ログ出力は後でconsole_loggerに置き換え
            print(f"Warning: Failed to load {file_path}: {e}")
            return {}

    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """辞書の深いマージ（純粋関数）

        Args:
            base_dict: ベース辞書
            update_dict: 更新辞書（優先）

        Returns:
            マージされた新しい辞書
        """
        result = base_dict.copy()

        for key, value in update_dict.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _has_file_patterns_support(self, language: str) -> bool:
        """言語がファイルパターンをサポートしているかチェック（純粋関数）"""
        patterns = self.get_file_patterns(language)
        return len(patterns) > 0

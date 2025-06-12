"""設定読み込みの一元化"""
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from ..core.configuration_source import ConfigurationSource


class ConfigurationLoader:
    """設定読み込みの一元化"""

    def __init__(self, contest_env_dir: Path, system_config_dir: Path):
        self.contest_env_dir = contest_env_dir
        self.system_config_dir = system_config_dir

    def load_source(self, language: str, runtime_args: Dict[str, Any]) -> ConfigurationSource:
        """すべての設定ソースを読み込み

        Args:
            language: 対象言語
            runtime_args: 実行時引数

        Returns:
            ConfigurationSource: 統一設定ソース
        """
        system_config = self.load_system_configs()
        shared_config, language_config = self.load_env_configs(language)

        return ConfigurationSource(
            system=system_config,
            shared=shared_config,
            language=language_config,
            runtime=runtime_args
        )

    def load_system_configs(self) -> Dict[str, Any]:
        """システム設定の読み込み

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
            if file_path.exists():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        config_data = json.load(f)
                        system_config.update(config_data)
                except (OSError, json.JSONDecodeError) as e:
                    print(f"Warning: Failed to load system config {file_path}: {e}")

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
        if shared_file.exists():
            try:
                with open(shared_file, encoding='utf-8') as f:
                    data = json.load(f)
                    shared_config = data.get("shared", {})
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to load shared config {shared_file}: {e}")

        # 言語固有設定を読み込み
        language_file = self.contest_env_dir / language / "env.json"
        if language_file.exists():
            try:
                with open(language_file, encoding='utf-8') as f:
                    data = json.load(f)
                    language_config = data.get(language, {})
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to load language config {language_file}: {e}")

        return shared_config, language_config

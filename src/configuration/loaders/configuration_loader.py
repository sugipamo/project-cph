"""設定読み込みの一元化"""
from pathlib import Path
from typing import Any, Dict

from ..core.configuration_source import ConfigurationSource
from .config_merger import ConfigMerger
from .env_config_loader import EnvConfigLoader
from .system_config_loader import SystemConfigLoader


class ConfigurationLoader:
    """設定読み込みの一元化 - 責任分離後のメインクラス"""

    def __init__(self, contest_env_dir: Path, system_config_dir: Path):
        self.system_loader = SystemConfigLoader(system_config_dir)
        self.env_loader = EnvConfigLoader(contest_env_dir)
        self.merger = ConfigMerger()

    def load_source(self, language: str, runtime_args: Dict[str, Any]) -> ConfigurationSource:
        """すべての設定ソースを読み込み

        Args:
            language: 対象言語
            runtime_args: 実行時引数

        Returns:
            ConfigurationSource: 統一設定ソース
        """
        # 各設定を分離されたローダーで読み込み
        system_config = self.system_loader.load_system_configs()
        shared_config, language_config = self.env_loader.load_env_configs(language)

        # 共有設定の正規化
        normalized_shared = self.merger.extract_shared_config(shared_config)

        return ConfigurationSource(
            system=system_config,
            shared=normalized_shared,
            language=language_config,
            runtime=runtime_args
        )

    def load_merged_config(self, language: str, runtime_args: Dict[str, Any]) -> Dict[str, Any]:
        """マージされた設定を取得

        Args:
            language: 対象言語
            runtime_args: 実行時引数

        Returns:
            Dict[str, Any]: マージされた設定辞書
        """
        # 各設定を読み込み
        system_config = self.system_loader.load_system_configs()
        shared_config, language_config = self.env_loader.load_env_configs(language)

        # 共有設定の正規化
        normalized_shared = self.merger.extract_shared_config(shared_config)

        # マージ実行
        return self.merger.merge_configs(
            system_config=system_config,
            shared_config=normalized_shared,
            language_config=language_config,
            runtime_config=runtime_args
        )

    def get_available_languages(self) -> list[str]:
        """利用可能な言語一覧を取得

        Returns:
            list[str]: 言語名のリスト
        """
        return self.env_loader.get_available_languages()

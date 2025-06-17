"""既存システムとの互換性レイヤー"""
from typing import Any, Dict

from .config_manager import TypedExecutionConfiguration


class BackwardCompatibilityLayer:
    """既存システムとの互換性のみに特化"""

    def __init__(self, config: TypedExecutionConfiguration):
        self.config = config
        self._resolver = None  # 既存システムとの互換性のため
        self._env_json = None  # env_json の mutable 状態
        self._dockerfile_resolver = None  # dockerfile_resolver の mutable 状態
        # TypeSafeConfigNodeManagerは直接使用可能

    @property
    def resolver(self):
        return self._resolver

    @resolver.setter
    def resolver(self, value):
        self._resolver = value

        # TypeSafeConfigNodeManagerは初期化不要

    @property
    def env_json(self) -> Dict[str, Any]:
        """env_jsonプロパティの互換実装"""
        if self._env_json is not None:
            return self._env_json

        # ファイルパターンとその他の設定を統合した形で返す
        result = {}
        if self.config.language:
            result[self.config.language] = {
                'file_patterns': self.config.file_patterns,
                'language_id': self.config.runtime_config.language_id,
                'source_file_name': self.config.runtime_config.source_file_name,
                'run_command': self.config.runtime_config.run_command,
            }
        return result

    @env_json.setter
    def env_json(self, value: Dict[str, Any]):
        """env_jsonのsetter（既存システムとの互換性のため）"""
        self._env_json = value

        # TypeSafeConfigNodeManagerでは初期化不要

    @property
    def dockerfile_resolver(self):
        """dockerfile_resolverプロパティの互換実装"""
        return self._dockerfile_resolver

    @dockerfile_resolver.setter
    def dockerfile_resolver(self, value):
        """dockerfile_resolverのsetter"""
        self._dockerfile_resolver = value

    def get_config_resolver(self):
        """新設定解決器を取得（テスト・デバッグ用）"""
        return  # TypeSafeConfigNodeManagerでは直接使用

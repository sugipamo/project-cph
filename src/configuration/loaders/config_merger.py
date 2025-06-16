"""設定マージ専用クラス"""
from typing import Any, Dict


class ConfigMerger:
    """設定マージ専用クラス

    責任:
    - 複数の設定辞書を優先度に従ってマージ
    - deep_merge ロジックの提供
    - マージルールの一元化
    """

    @staticmethod
    def merge_configs(
        system_config: Dict[str, Any],
        shared_config: Dict[str, Any],
        language_config: Dict[str, Any],
        runtime_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """設定をマージ（優先度: runtime > language > shared > system）

        Args:
            system_config: システム設定（最低優先度）
            shared_config: 共有設定
            language_config: 言語固有設定
            runtime_config: 実行時設定（最高優先度）

        Returns:
            Dict[str, Any]: マージされた設定辞書
        """
        result = {}

        # 低優先度から順番にマージ
        configs = [system_config, shared_config, language_config, runtime_config]

        for config in configs:
            if config:
                result = ConfigMerger._deep_merge(result, config)

        return result

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """辞書を再帰的にマージ

        Args:
            target: マージ対象辞書
            source: マージ元辞書

        Returns:
            Dict[str, Any]: マージ結果
        """
        # targetのコピーを作成
        result = target.copy()

        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 両方が辞書の場合は再帰的にマージ
                result[key] = ConfigMerger._deep_merge(result[key], value)
            else:
                # そうでなければ上書き
                result[key] = value

        return result

    @staticmethod
    def extract_shared_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """shared設定の正規化

        shared/env.jsonの形式:
        {
          "shared": {
            "paths": {...},
            "commands": {...}
          }
        }

        Args:
            config: 設定辞書

        Returns:
            Dict[str, Any]: 正規化された設定辞書
        """
        if "shared" in config:
            return config["shared"]
        return config

    @staticmethod
    def flatten_file_patterns(patterns: Dict[str, Any]) -> Dict[str, Any]:
        """ファイルパターンの正規化

        複雑な形式:
        {
          "pattern_name": {
            "workspace": ["*.cpp"],
            "contest_current": ["*.cpp"],
            "contest_stock": ["*.cpp"]
          }
        }

        シンプルな形式:
        {
          "pattern_name": ["*.cpp"]
        }

        Args:
            patterns: パターン辞書

        Returns:
            Dict[str, Any]: 正規化されたパターン辞書
        """
        if not patterns:
            return {}

        result = {}

        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, dict):
                # 複雑な形式の場合
                for location in ['workspace', 'contest_current', 'contest_stock']:
                    if pattern_data.get(location):
                        result[pattern_name] = pattern_data[location]
                        break
            else:
                # シンプルな形式の場合
                result[pattern_name] = pattern_data

        return result

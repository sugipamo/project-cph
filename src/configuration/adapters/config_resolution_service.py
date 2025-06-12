"""設定解決機能の提供"""
from typing import Any, List

from ..core.execution_configuration import ExecutionConfiguration
from .compatibility_layer import BackwardCompatibilityLayer


class ConfigResolutionService:
    """設定解決機能を提供するサービス"""

    def __init__(self, config: ExecutionConfiguration, compatibility_layer: BackwardCompatibilityLayer):
        self.config = config
        self.compatibility_layer = compatibility_layer

    def resolve_config_value(self, path: List[str], default: Any = None) -> Any:
        """設定値をパスで解決（ConfigNode機能の統合）

        Args:
            path: 設定パス（例: ['python', 'language_id']）
            default: デフォルト値

        Returns:
            解決された設定値
        """
        config_resolver = self.compatibility_layer.get_config_resolver()
        if config_resolver:
            return config_resolver.resolve_value(path, default)

        # フォールバック：従来の解決方法
        current = self.compatibility_layer.env_json or {}
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def resolve_config_values(self, path: List[str]) -> List[Any]:
        """設定値のリストをパスで解決

        Args:
            path: 設定パス

        Returns:
            解決された設定値のリスト
        """
        config_resolver = self.compatibility_layer.get_config_resolver()
        if config_resolver:
            return config_resolver.resolve_values(path)

        # フォールバック
        value = self.resolve_config_value(path)
        return [value] if value is not None else []

    def resolve_with_fallback(self, primary_path: List[str], fallback_path: List[str], default: Any = None) -> Any:
        """プライマリパスでの解決を試行し、失敗時にフォールバックパスを使用

        Args:
            primary_path: 第一優先の設定パス
            fallback_path: フォールバック用の設定パス
            default: 最終的なデフォルト値

        Returns:
            解決された設定値
        """
        value = self.resolve_config_value(primary_path)
        if value is not None:
            return value

        value = self.resolve_config_value(fallback_path)
        if value is not None:
            return value

        return default

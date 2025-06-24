"""純粋なConfiguration層の実装

副作用を排除し、設定データの解析とアクセスのみに責務を限定した
Configuration層の実装です。
"""
from typing import Any, Dict, List, Optional, Type, TypeVar

# 遅延インポートで循環依存を回避
ConfigNode = None
create_config_root_from_dict = None

T = TypeVar('T')


def _ensure_imports():
    """必要なモジュールの遅延インポート"""
    global ConfigNode, create_config_root_from_dict
    if ConfigNode is None:
        from src.context.resolver.config_resolver import ConfigNode as ConfigNodeClass
        from src.context.resolver.config_resolver import create_config_root_from_dict as create_func
        ConfigNode = ConfigNodeClass
        create_config_root_from_dict = create_func


class PureConfigManager:
    """純粋な設定管理（副作用なし）

    設定データの解析とアクセスのみを担当し、
    ファイル読み込み等の副作用はInfrastructure層に委譲します。
    """

    def __init__(self):
        """純粋な初期化（依存性なし）"""
        _ensure_imports()
        self.root_node: Optional[ConfigNode] = None
        self._system_dir: Optional[str] = None
        self._env_dir: Optional[str] = None
        self._language: Optional[str] = None

    def initialize_from_config_dict(self, config_dict: Dict[str, Any],
                                   system_dir: str, env_dir: str, language: str):
        """設定辞書から初期化（純粋関数）

        Args:
            config_dict: 設定データ辞書
            system_dir: システム設定ディレクトリ（記録用）
            env_dir: 環境設定ディレクトリ（記録用）
            language: 言語設定（記録用）
        """
        self._system_dir = system_dir
        self._env_dir = env_dir
        self._language = language
        self.root_node = create_config_root_from_dict(config_dict)

    def resolve_config(self, path: List[str], expected_type: Type[T]) -> T:
        """型安全な設定値解決

        Args:
            path: 設定パス
            expected_type: 期待する型

        Returns:
            解決された設定値

        Raises:
            KeyError: 設定が見つからない場合
            TypeError: 型が一致しない場合
        """
        if self.root_node is None:
            raise RuntimeError("ConfigManager has not been initialized")

        from src.context.resolver.config_resolver import resolve_best

        try:
            value = resolve_best(self.root_node, path)
            if not isinstance(value, expected_type):
                if expected_type == str and not isinstance(value, str):
                    value = str(value)
                elif expected_type == int and isinstance(value, str):
                    value = int(value)
                elif expected_type == bool and isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
            return value
        except KeyError:
            raise KeyError(f"Config path {path} not found")

    def resolve_template_typed(self, template: str, context: Dict[str, Any],
                              expected_type: Type[T]) -> T:
        """型安全なテンプレート展開

        Args:
            template: テンプレート文字列
            context: 展開コンテキスト
            expected_type: 期待する型

        Returns:
            展開された値
        """
        if self.root_node is None:
            raise RuntimeError("ConfigManager has not been initialized")

        from src.context.resolver.config_resolver import resolve_formatted_string

        result = resolve_formatted_string(self.root_node, template, context)

        if not isinstance(result, expected_type):
            if expected_type == str:
                result = str(result)
            else:
                raise TypeError(f"Template result type mismatch: expected {expected_type.__name__}")

        return result

    def get_language(self) -> Optional[str]:
        """現在の言語設定を取得"""
        return self._language

    def get_system_dir(self) -> Optional[str]:
        """システム設定ディレクトリを取得"""
        return self._system_dir

    def get_env_dir(self) -> Optional[str]:
        """環境設定ディレクトリを取得"""
        return self._env_dir

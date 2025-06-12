"""レジストリプロバイダー - グローバル状態管理の副作用を集約"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T')


class RegistryProvider(ABC, Generic[T]):
    """レジストリの抽象インターフェース"""

    @abstractmethod
    def get_registry(self, registry_name: str) -> Optional[T]:
        """レジストリを取得"""
        pass

    @abstractmethod
    def set_registry(self, registry_name: str, registry: T) -> None:
        """レジストリを設定"""
        pass

    @abstractmethod
    def has_registry(self, registry_name: str) -> bool:
        """レジストリが存在するかチェック"""
        pass

    @abstractmethod
    def clear_registry(self, registry_name: str) -> None:
        """レジストリを削除"""
        pass


class SystemRegistryProvider(RegistryProvider):
    """システムレジストリプロバイダー - 副作用はここに集約"""

    def __init__(self):
        self._registries: Dict[str, Any] = {}

    def get_registry(self, registry_name: str) -> Optional[Any]:
        """レジストリを取得（副作用）"""
        return self._registries.get(registry_name)

    def set_registry(self, registry_name: str, registry: Any) -> None:
        """レジストリを設定（副作用）"""
        self._registries[registry_name] = registry

    def has_registry(self, registry_name: str) -> bool:
        """レジストリが存在するかチェック（副作用なし）"""
        return registry_name in self._registries

    def clear_registry(self, registry_name: str) -> None:
        """レジストリを削除（副作用）"""
        self._registries.pop(registry_name, None)

    def get_all_registries(self) -> Dict[str, Any]:
        """全レジストリを取得（副作用なし）"""
        return self._registries.copy()

    def clear_all_registries(self) -> None:
        """全レジストリを削除（副作用）"""
        self._registries.clear()


class MockRegistryProvider(RegistryProvider):
    """テスト用モックレジストリプロバイダー - 副作用なし"""

    def __init__(self):
        self._registries: Dict[str, Any] = {}
        self._access_log: list = []

    def get_registry(self, registry_name: str) -> Optional[Any]:
        """モックレジストリ取得（副作用なし）"""
        self._access_log.append(("GET", registry_name))
        return self._registries.get(registry_name)

    def set_registry(self, registry_name: str, registry: Any) -> None:
        """モックレジストリ設定（副作用なし）"""
        self._access_log.append(("SET", registry_name))
        self._registries[registry_name] = registry

    def has_registry(self, registry_name: str) -> bool:
        """モックレジストリ存在チェック（副作用なし）"""
        self._access_log.append(("HAS", registry_name))
        return registry_name in self._registries

    def clear_registry(self, registry_name: str) -> None:
        """モックレジストリ削除（副作用なし）"""
        self._access_log.append(("CLEAR", registry_name))
        self._registries.pop(registry_name, None)

    def get_access_log(self) -> list:
        """テスト用アクセスログ取得"""
        return self._access_log.copy()

    def clear_access_log(self) -> None:
        """テスト用アクセスログクリア"""
        self._access_log.clear()


class LanguageRegistryProvider:
    """言語レジストリ専用プロバイダー（既存LanguageRegistryの副作用を集約）"""

    def __init__(self, registry_provider: RegistryProvider):
        self.registry_provider = registry_provider
        self._registry_name = "language_registry"

    def get_language_registry(self):
        """言語レジストリを取得（副作用をプロバイダーに委譲）"""
        registry = self.registry_provider.get_registry(self._registry_name)
        if registry is None:
            # 遅延初期化
            from ..config.language_registry_factory import create_default_language_registry
            registry = create_default_language_registry()
            self.registry_provider.set_registry(self._registry_name, registry)
        return registry

    def register_custom_language(self, name: str, extension: str, run_command: str,
                                compile_command: Optional[str] = None,
                                aliases: Optional[list] = None) -> None:
        """カスタム言語を登録（副作用をプロバイダーに委譲）"""
        registry = self.get_language_registry()
        from src.configuration.registries.language_registry import LanguageConfig
        
        config = LanguageConfig(
            extension=extension,
            run_command=run_command,
            compile_command=compile_command,
            aliases=aliases or []
        )
        registry.register_language(name, config)

    def get_language_config(self, language: str):
        """言語設定を取得（副作用をプロバイダーに委譲）"""
        registry = self.get_language_registry()
        return registry.get_language_config(language)


# ユーティリティ関数（純粋関数）
def validate_registry_name(name: str) -> bool:
    """レジストリ名をバリデーション（純粋関数）
    
    Args:
        name: レジストリ名
        
    Returns:
        有効な名前かどうか
    """
    if not name or not isinstance(name, str):
        return False
    
    # 英数字、アンダースコア、ハイフンのみ許可
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


def create_registry_key(prefix: str, identifier: str) -> str:
    """レジストリキーを生成（純粋関数）
    
    Args:
        prefix: プレフィックス
        identifier: 識別子
        
    Returns:
        レジストリキー
    """
    return f"{prefix}:{identifier}"


def parse_registry_key(key: str) -> tuple:
    """レジストリキーをパース（純粋関数）
    
    Args:
        key: レジストリキー
        
    Returns:
        (prefix, identifier)のタプル
    """
    if ':' not in key:
        return (key, '')
    
    parts = key.split(':', 1)
    return (parts[0], parts[1])
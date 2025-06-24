"""
シンプルな依存性注入コンテナ
"""
from typing import Any, Dict, Callable
import logging


class DIContainer:
    """辞書ベースのシンプルなDIコンテナ"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._setup_default_services()
    
    def _setup_default_services(self) -> None:
        """デフォルトサービスの設定"""
        self._factories["logger"] = lambda: logging.getLogger(__name__)
    
    def register(self, name: str, service: Any) -> None:
        """サービスインスタンスを登録"""
        self._services[name] = service
    
    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """サービスファクトリを登録"""
        self._factories[name] = factory
    
    def resolve(self, name: str) -> Any:
        """サービスを解決して取得"""
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service  # シングルトンとして保存
            return service
        
        raise KeyError(f"Service '{name}' not found in container")
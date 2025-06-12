"""リファクタリングされた ExecutionContextAdapter"""
from typing import Any, Dict

from ..core.execution_configuration import ExecutionConfiguration
from ..expansion.template_expander import TemplateExpander
from .property_provider import ConfigurationPropertyProvider
from .compatibility_layer import BackwardCompatibilityLayer
from .validation_service import ConfigurationValidationService
from .config_resolution_service import ConfigResolutionService


class ExecutionContextAdapterV2:
    """責務分離されたExecutionContextAdapter
    
    既存のExecutionContextと同一のAPIを提供しながら、
    内部的には責務ごとに分離されたコンポーネントを使用
    """
    
    def __init__(self, config: ExecutionConfiguration, expander: TemplateExpander):
        self.config = config
        self.expander = expander
        
        # 責務ごとに分離されたコンポーネント
        self._property_provider = ConfigurationPropertyProvider(config)
        self._compatibility_layer = BackwardCompatibilityLayer(config)
        self._validation_service = ConfigurationValidationService(config)
        self._config_resolution_service = ConfigResolutionService(config, self._compatibility_layer)
    
    # === テンプレート展開機能 ===
    def format_string(self, template: str) -> str:
        """既存のformat_stringメソッドの互換実装"""
        return self.expander.expand_all(template)
    
    def to_dict(self) -> Dict[str, str]:
        """既存のto_dictメソッドの互換実装"""
        return self.config.to_template_dict()
    
    # === プロパティアクセス（委譲） ===
    @property
    def command_type(self) -> str:
        return self._property_provider.command_type
    
    @property
    def language(self) -> str:
        return self._property_provider.language
    
    @property
    def contest_name(self) -> str:
        return self._property_provider.contest_name
    
    @property
    def problem_name(self) -> str:
        return self._property_provider.problem_name
    
    @property
    def env_type(self) -> str:
        return self._property_provider.env_type
    
    @property
    def workspace_path(self) -> str:
        return self._property_provider.workspace_path
    
    @property
    def contest_current_path(self) -> str:
        return self._property_provider.contest_current_path
    
    @property
    def contest_stock_path(self) -> str:
        return self._property_provider.contest_stock_path
    
    @property
    def contest_template_path(self) -> str:
        return self._property_provider.contest_template_path
    
    @property
    def contest_temp_path(self) -> str:
        return self._property_provider.contest_temp_path
    
    # === 互換性レイヤー（委譲） ===
    @property
    def resolver(self):
        return self._compatibility_layer.resolver
    
    @resolver.setter
    def resolver(self, value):
        self._compatibility_layer.resolver = value
    
    @property
    def env_json(self) -> Dict[str, Any]:
        return self._compatibility_layer.env_json
    
    @env_json.setter
    def env_json(self, value: Dict[str, Any]):
        self._compatibility_layer.env_json = value
    
    @property
    def dockerfile_resolver(self):
        return self._compatibility_layer.dockerfile_resolver
    
    @dockerfile_resolver.setter
    def dockerfile_resolver(self, value):
        self._compatibility_layer.dockerfile_resolver = value
    
    # === バリデーション機能（委譲） ===
    def validate_execution_data(self) -> tuple[bool, str]:
        """既存のvalidate_execution_dataメソッドの互換実装"""
        return self._validation_service.validate_execution_data()
    
    # === 設定解決機能（委譲） ===
    def resolve_config_value(self, path: list, default: Any = None) -> Any:
        """設定値をパスで解決"""
        return self._config_resolution_service.resolve_config_value(path, default)
    
    def resolve_config_values(self, path: list) -> list[Any]:
        """設定値のリストをパスで解決"""
        return self._config_resolution_service.resolve_config_values(path)
    
    def get_config_resolver(self):
        """新設定解決器を取得（テスト・デバッグ用）"""
        return self._compatibility_layer.get_config_resolver()


# 既存システムとの完全互換性のためのエイリアス
class ExecutionContextAdapter(ExecutionContextAdapterV2):
    """既存システムとの完全互換性を保つエイリアス
    
    段階的移行期間中は既存の名前でも利用可能
    """
    pass
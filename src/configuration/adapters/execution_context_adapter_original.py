"""既存ExecutionContextとの互換性を保つアダプター"""
from typing import Any, Dict, Optional

from ..core.execution_configuration import ExecutionConfiguration
from ..expansion.template_expander import TemplateExpander
from ..resolvers.config_resolver import ConfigurationResolver, create_config_resolver


class ExecutionContextAdapter:
    """既存ExecutionContextとの互換性を保つアダプター"""
    
    def __init__(self, config: ExecutionConfiguration, expander: TemplateExpander):
        self.config = config
        self.expander = expander
        self._resolver = None  # 既存システムとの互換性のため
        self._env_json = None  # env_json の mutable 状態
        self._dockerfile_resolver = None  # dockerfile_resolver の mutable 状態
        self._config_resolver: Optional[ConfigurationResolver] = None  # 新設定解決器
    
    def format_string(self, template: str) -> str:
        """既存のformat_stringメソッドの互換実装
        
        Args:
            template: テンプレート文字列
            
        Returns:
            展開された文字列
        """
        return self.expander.expand_all(template)
    
    def to_dict(self) -> Dict[str, str]:
        """既存のto_dictメソッドの互換実装
        
        Returns:
            テンプレート変数辞書
        """
        return self.config.to_template_dict()
    
    # 既存ExecutionContextプロパティの互換実装
    @property
    def command_type(self) -> str:
        return self.config.command_type
    
    @property
    def language(self) -> str:
        return self.config.language
    
    @property
    def contest_name(self) -> str:
        return self.config.contest_name
    
    @property
    def problem_name(self) -> str:
        return self.config.problem_name
    
    @property
    def env_type(self) -> str:
        return self.config.env_type
    
    @property
    def workspace_path(self) -> str:
        return str(self.config.paths.workspace)
    
    @property
    def contest_current_path(self) -> str:
        return str(self.config.paths.contest_current)
    
    @property
    def contest_stock_path(self) -> str:
        return str(self.config.paths.contest_stock)
    
    @property
    def contest_template_path(self) -> str:
        return str(self.config.paths.contest_template)
    
    @property
    def contest_temp_path(self) -> str:
        return str(self.config.paths.contest_temp)
    
    # 既存システムとの互換性のためのプロパティ
    @property
    def resolver(self):
        return self._resolver
    
    @resolver.setter
    def resolver(self, value):
        self._resolver = value
        
        # env_jsonが利用可能な場合、新設定解決器を初期化
        if self._env_json and self._config_resolver is None:
            self._config_resolver = create_config_resolver(self.config, self._env_json)
    
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
        
        # 新設定解決器を初期化
        if value:
            self._config_resolver = create_config_resolver(self.config, value)
    
    @property
    def dockerfile_resolver(self):
        """dockerfile_resolverプロパティの互換実装"""
        return self._dockerfile_resolver
    
    @dockerfile_resolver.setter
    def dockerfile_resolver(self, value):
        """dockerfile_resolverのsetter"""
        self._dockerfile_resolver = value
    
    def validate_execution_data(self) -> tuple[bool, str]:
        """既存のvalidate_execution_dataメソッドの互換実装"""
        # 基本的な検証
        if not self.config.language:
            return False, "Language is required"
        if not self.config.contest_name:
            return False, "Contest name is required"
        if not self.config.problem_name:
            return False, "Problem name is required"
        return True, ""
    
    # ConfigNode 統合機能
    def resolve_config_value(self, path: list, default: Any = None) -> Any:
        """設定値をパスで解決（ConfigNode機能の統合）
        
        Args:
            path: 設定パス（例: ['python', 'language_id']）
            default: デフォルト値
            
        Returns:
            解決された設定値
        """
        if self._config_resolver:
            return self._config_resolver.resolve_value(path, default)
        
        # フォールバック：従来の解決方法
        current = self._env_json or {}
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def resolve_config_values(self, path: list) -> list[Any]:
        """設定値のリストをパスで解決
        
        Args:
            path: 設定パス
            
        Returns:
            解決された設定値のリスト
        """
        if self._config_resolver:
            return self._config_resolver.resolve_values(path)
        
        # フォールバック
        value = self.resolve_config_value(path)
        return [value] if value is not None else []
    
    def get_config_resolver(self) -> Optional[ConfigurationResolver]:
        """新設定解決器を取得（テスト・デバッグ用）"""
        return self._config_resolver
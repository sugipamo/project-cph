"""TemplateExpander生成"""
from ..core.execution_configuration import ExecutionConfiguration
from ..expansion.template_expander import TemplateExpander


class TemplateExpanderFactory:
    """TemplateExpander生成"""
    
    @staticmethod
    def create(config: ExecutionConfiguration) -> TemplateExpander:
        """設定に応じたTemplateExpanderを生成
        
        Args:
            config: 実行設定
            
        Returns:
            TemplateExpander: 生成されたテンプレート展開器
        """
        return TemplateExpander(config)
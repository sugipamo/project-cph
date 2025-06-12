"""新設定管理システム - 統一された設定管理とテンプレート展開

このモジュールは既存の分散した設定管理システムを統一し、
5つのコンテキストクラスと32個の変数展開関数を統合します。

主要コンポーネント:
- ConfigurationSource: 設定ソースの統合
- ExecutionConfiguration: 統一された実行設定（不変）
- TemplateExpander: 変数展開の一元化
- ExecutionConfigurationFactory: 設定生成
- ExecutionContextAdapter: 既存システムとの互換性
"""

from .adapters.execution_context_adapter import ExecutionContextAdapter
from .core.configuration_source import ConfigurationSource
from .core.execution_configuration import ExecutionConfiguration
from .core.execution_paths import ExecutionPaths
from .core.output_config import OutputConfig
from .core.runtime_config import RuntimeConfig
from .expansion.template_expander import TemplateExpander, TemplateValidator
from .factories.configuration_factory import ExecutionConfigurationFactory
from .factories.expander_factory import TemplateExpanderFactory
from .loaders.configuration_loader import ConfigurationLoader
from .resolvers.config_resolver import ConfigNode, ConfigurationResolver, create_config_resolver

__all__ = [
    'ConfigNode',
    'ConfigurationLoader',
    'ConfigurationResolver',
    'ConfigurationSource',
    'ExecutionConfiguration',
    'ExecutionConfigurationFactory',
    'ExecutionContextAdapter',
    'ExecutionPaths',
    'OutputConfig',
    'RuntimeConfig',
    'TemplateExpander',
    'TemplateExpanderFactory',
    'TemplateValidator',
    'create_config_resolver',
]

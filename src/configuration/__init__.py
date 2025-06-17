"""新設定管理システム - 統一された設定管理とテンプレート展開

このモジュールは既存の分散した設定管理システムを統一し、
TypeSafeConfigNodeManagerを中心とした簡潔な設定管理を提供します。

主要コンポーネント:
- TypeSafeConfigNodeManager: 型安全な統一設定管理
- ExecutionPaths: 実行パス設定
- OutputConfig: 出力設定
- CompatibilityLayer: 既存システムとの互換性
"""

from .core.execution_paths import ExecutionPaths
from .core.output_config import OutputConfig
from .registries.language_registry import LanguageRegistry
from .typed_config_node_manager import (
    FileLoader,
    TypedExecutionConfiguration,
    TypeSafeConfigNodeManager,
)

__all__ = [
    'ExecutionPaths',
    'FileLoader',
    'LanguageRegistry',
    'OutputConfig',
    'TypeSafeConfigNodeManager',
    'TypedExecutionConfiguration',
]

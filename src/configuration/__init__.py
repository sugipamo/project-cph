"""洗練された設定管理システム - シンプルで直感的な設定管理

このモジュールは統一された設定管理システムを提供し、
名前から責務が直接わかる構造を実現しています。

主要コンポーネント:
- ConfigManager: 設定管理の中核（型安全・高性能）
- ExecutionConfig: 実行設定とパス管理
- OutputConfig: 出力設定

移行完了により、レガシーアダプターは削除されました。
"""

from .config_manager import (
    FileLoader,
    TypedExecutionConfiguration,
    TypeSafeConfigNodeManager,
)
from .models.execution_config import ExecutionPaths
from .models.output_config import OutputConfig

__all__ = [
    'ExecutionPaths',
    'FileLoader',
    'OutputConfig',
    'TypeSafeConfigNodeManager',
    'TypedExecutionConfiguration',
]

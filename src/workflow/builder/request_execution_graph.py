"""リクエスト実行グラフ

依存関係を持つリクエストのグラフ構造と実行戦略を提供
"""
from concurrent.futures import ThreadPoolExecutor

from src.domain.results.result import OperationResult

from .execution.execution_core import DependencyEdge, DependencyType, NodeExecutionResult, RequestNode

# モジュール化された実行コンポーネントをインポート
from .execution.execution_core import RequestExecutionGraph as CoreRequestExecutionGraph
from .execution.execution_parallel import ParallelExecutor
from .execution.execution_sequential import SequentialExecutor


class RequestExecutionGraph(CoreRequestExecutionGraph):
    """リクエスト実行グラフ - モジュール化されたコアを拡張"""

    # コア機能はベースクラスから継承

    def execute_sequential(self, driver=None) -> list[OperationResult]:
        """順次実行 - モジュール化されたExecutorを使用"""
        executor = SequentialExecutor(self)
        return executor.execute_sequential_workflow(driver)

    def execute_parallel(self, driver=None, max_workers: int = 4,
                        executor_class: type = ThreadPoolExecutor) -> list[OperationResult]:
        """並行実行 - モジュール化されたExecutorを使用"""
        executor = ParallelExecutor(self)
        return executor.execute_parallel_workflow(driver, max_workers, executor_class)


# 後方互換性のためのエクスポート
__all__ = [
    'DependencyEdge',
    'DependencyType',
    'NodeExecutionResult',
    'RequestExecutionGraph',
    'RequestNode'
]

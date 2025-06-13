"""実行オーケストレーションの純粋関数 - RequestExecutionGraphから分離"""
import traceback
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ExecutionContext:
    """実行コンテキスト（不変データ構造）"""
    nodes: Dict[str, Any]
    dependencies: Dict[str, Set[str]]
    max_workers: int
    timeout: int = 300  # 5分のデフォルトタイムアウト

    @property
    def node_count(self) -> int:
        """ノード数（純粋関数）"""
        return len(self.nodes)

    @property
    def dependency_count(self) -> int:
        """依存関係数（純粋関数）"""
        return sum(len(deps) for deps in self.dependencies.values())


@dataclass(frozen=True)
class BatchResult:
    """バッチ実行結果（不変データ構造）"""
    node_id: str
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None

    @classmethod
    def success_result(cls, node_id: str, result: Any, execution_time: float) -> 'BatchResult':
        """成功結果を作成（純粋関数）"""
        return cls(
            node_id=node_id,
            success=True,
            result=result,
            execution_time=execution_time
        )

    @classmethod
    def error_result(cls, node_id: str, error_message: str, execution_time: float) -> 'BatchResult':
        """エラー結果を作成（純粋関数）"""
        return cls(
            node_id=node_id,
            success=False,
            result=None,
            execution_time=execution_time,
            error_message=error_message
        )


def create_execution_context(nodes: Dict[str, Any],
                           dependencies: Dict[str, Set[str]],
                           max_workers: int = 4,
                           timeout: int = 300) -> ExecutionContext:
    """実行コンテキストを作成（純粋関数）

    Args:
        nodes: ノード辞書
        dependencies: 依存関係辞書
        max_workers: 最大ワーカー数
        timeout: タイムアウト秒数

    Returns:
        実行コンテキスト
    """
    return ExecutionContext(
        nodes=nodes.copy(),
        dependencies={k: v.copy() for k, v in dependencies.items()},
        max_workers=max_workers,
        timeout=timeout
    )


def prepare_batch_execution(executable_nodes: List[str],
                           context: ExecutionContext) -> Dict[str, Any]:
    """バッチ実行の準備（純粋関数）

    Args:
        executable_nodes: 実行可能ノードリスト
        context: 実行コンテキスト

    Returns:
        バッチ実行メタデータ
    """
    return {
        'batch_id': f"batch_{hash(tuple(executable_nodes)) % 10000}",
        'node_count': len(executable_nodes),
        'max_workers': context.max_workers,
        'timeout': context.timeout,
        'nodes': executable_nodes.copy()
    }


def collect_execution_results(futures: List[Tuple[Future, str]],
                             execution_order: List[str],
                             timeout: int = 300) -> Dict[str, Any]:
    """実行結果を収集（副作用を含む）

    Args:
        futures: Futureとノードのペアリスト
        execution_order: 実行順序
        timeout: タイムアウト秒数

    Returns:
        実行結果辞書
    """
    all_results = {}

    for future, node_id in futures:
        try:
            result = future.result(timeout=timeout)
            all_results[node_id] = result
        except Exception as e:
            # エラー結果を作成
            from src.domain.results.result import OperationResult
            error_result = OperationResult(success=False, error_message=str(e))
            all_results[node_id] = error_result

    return all_results


def handle_execution_failure(failed_node_id: str,
                           adjacency_list: Dict[str, Set[str]],
                           node_states: Dict[str, str]) -> Dict[str, str]:
    """実行失敗の処理（純粋関数）

    Args:
        failed_node_id: 失敗ノードID
        adjacency_list: 隣接リスト
        node_states: ノード状態辞書

    Returns:
        更新されたノード状態辞書
    """
    updated_states = node_states.copy()

    # 失敗ノードに依存するノードを再帰的にスキップ
    def mark_skipped_recursive(current_failed_id: str):
        dependents = adjacency_list.get(current_failed_id, set())

        for dependent_id in dependents:
            if dependent_id in updated_states and updated_states[dependent_id] == "pending":
                updated_states[dependent_id] = "skipped"
                # 再帰的に依存ノードもスキップ
                mark_skipped_recursive(dependent_id)

    mark_skipped_recursive(failed_node_id)
    return updated_states


def calculate_execution_progress(completed_nodes: Set[str],
                               failed_nodes: Set[str],
                               skipped_nodes: Set[str],
                               total_nodes: int) -> Dict[str, Any]:
    """実行進捗を計算（純粋関数）

    Args:
        completed_nodes: 完了ノード集合
        failed_nodes: 失敗ノード集合
        skipped_nodes: スキップノード集合
        total_nodes: 総ノード数

    Returns:
        進捗情報辞書
    """
    processed_nodes = len(completed_nodes | failed_nodes | skipped_nodes)

    return {
        'total_nodes': total_nodes,
        'completed': len(completed_nodes),
        'failed': len(failed_nodes),
        'skipped': len(skipped_nodes),
        'remaining': total_nodes - processed_nodes,
        'progress_percentage': (processed_nodes / total_nodes * 100) if total_nodes > 0 else 0,
        'success_rate': (len(completed_nodes) / processed_nodes * 100) if processed_nodes > 0 else 0
    }


def validate_execution_readiness(context: ExecutionContext) -> List[str]:
    """実行準備状態を検証（純粋関数）

    Args:
        context: 実行コンテキスト

    Returns:
        エラーメッセージリスト
    """
    errors = []

    # ノードが存在するかチェック
    if not context.nodes:
        errors.append("No nodes to execute")

    # 最大ワーカー数のチェック
    if context.max_workers <= 0:
        errors.append(f"Invalid max_workers: {context.max_workers}")

    # タイムアウトのチェック
    if context.timeout <= 0:
        errors.append(f"Invalid timeout: {context.timeout}")

    # 依存関係の整合性チェック
    for node_id, deps in context.dependencies.items():
        if node_id not in context.nodes:
            errors.append(f"Node {node_id} has dependencies but doesn't exist in nodes")

        for dep_id in deps:
            if dep_id not in context.nodes:
                errors.append(f"Dependency {dep_id} for node {node_id} doesn't exist")

    return errors


def create_execution_plan_summary(context: ExecutionContext,
                                parallel_groups: List[List[str]]) -> Dict[str, Any]:
    """実行計画サマリーを作成（純粋関数）

    Args:
        context: 実行コンテキスト
        parallel_groups: 並列グループ

    Returns:
        実行計画サマリー
    """
    return {
        'total_nodes': context.node_count,
        'total_dependencies': context.dependency_count,
        'max_workers': context.max_workers,
        'timeout': context.timeout,
        'execution_groups': len(parallel_groups),
        'max_parallelism': max(len(group) for group in parallel_groups) if parallel_groups else 0,
        'estimated_execution_time': len(parallel_groups) * 30,  # 概算：グループあたり30秒
        'groups': [
            {
                'group_index': i,
                'node_count': len(group),
                'nodes': group
            }
            for i, group in enumerate(parallel_groups)
        ]
    }


def safe_execute_node(node: Any, driver: Any) -> Any:
    """ノードを安全に実行（例外ハンドリング付き）

    Args:
        node: 実行するノード
        driver: 実行ドライバー

    Returns:
        実行結果（成功またはエラー）
    """
    try:
        return node.request.execute(driver=driver)
    except Exception as e:
        # 例外をキャッチしてエラー結果を返す
        from src.domain.results.result import OperationResult
        error_msg = f"{e!s}\n{traceback.format_exc()}"
        return OperationResult(success=False, error_message=error_msg)


def optimize_worker_allocation(parallel_groups: List[List[str]],
                             max_workers: int) -> List[int]:
    """並列グループごとの最適ワーカー数を計算（純粋関数）

    Args:
        parallel_groups: 並列グループリスト
        max_workers: 最大ワーカー数

    Returns:
        グループごとの推奨ワーカー数リスト
    """
    if not parallel_groups:
        return []

    worker_allocations = []

    for group in parallel_groups:
        group_size = len(group)
        # グループサイズと最大ワーカー数の小さい方を使用
        optimal_workers = min(group_size, max_workers)
        worker_allocations.append(optimal_workers)

    return worker_allocations


def calculate_resource_usage(context: ExecutionContext,
                           current_running: Set[str]) -> Dict[str, Any]:
    """リソース使用量を計算（純粋関数）

    Args:
        context: 実行コンテキスト
        current_running: 現在実行中のノード集合

    Returns:
        リソース使用量情報
    """
    return {
        'total_nodes': context.node_count,
        'max_workers': context.max_workers,
        'current_running': len(current_running),
        'worker_utilization': (len(current_running) / context.max_workers * 100) if context.max_workers > 0 else 0,
        'available_workers': max(0, context.max_workers - len(current_running)),
        'running_nodes': list(current_running)
    }


def estimate_remaining_time(completed_groups: int,
                          total_groups: int,
                          elapsed_time: float) -> float:
    """残り実行時間を推定（純粋関数）

    Args:
        completed_groups: 完了済みグループ数
        total_groups: 総グループ数
        elapsed_time: 経過時間（秒）

    Returns:
        推定残り時間（秒）
    """
    if completed_groups == 0 or total_groups <= completed_groups:
        return 0.0

    # 完了済みグループの平均実行時間を基に推定
    avg_time_per_group = elapsed_time / completed_groups
    remaining_groups = total_groups - completed_groups

    return avg_time_per_group * remaining_groups

"""結果処理の純粋関数 - RequestExecutionGraphから分離"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .functional_utils import filter_data_collection


@dataclass(frozen=True)
class ExecutionResult:
    """実行結果（不変データ構造）"""
    node_id: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

    @property
    def failed(self) -> bool:
        """失敗判定（純粋関数）"""
        return not self.success


@dataclass(frozen=True)
class WorkflowResult:
    """ワークフロー実行結果（不変データ構造）"""
    results: List[ExecutionResult]
    success: bool
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    skipped_nodes: int

    @property
    def success_rate(self) -> float:
        """成功率（純粋関数）"""
        if self.total_nodes == 0:
            return 0.0
        return self.completed_nodes / self.total_nodes

    @property
    def failure_rate(self) -> float:
        """失敗率（純粋関数）"""
        if self.total_nodes == 0:
            return 0.0
        return self.failed_nodes / self.total_nodes


def collect_workflow_result(execution_results: Dict[str, Any],
                           execution_plan: Any,
                           node_statuses: Dict[str, str]) -> WorkflowResult:
    """実行結果と計画から最終結果を構築（純粋関数）

    Args:
        execution_results: 実行結果辞書
        execution_plan: 実行計画
        node_statuses: ノード状態辞書

    Returns:
        ワークフロー実行結果
    """
    # 実行結果を変換
    results = []
    for node_id in execution_plan.execution_order:
        if node_id in execution_results:
            op_result = execution_results[node_id]
            exec_result = ExecutionResult(
                node_id=node_id,
                success=op_result.success,
                result=op_result,
                error_message=getattr(op_result, 'error_message', None),
                execution_time=getattr(op_result, 'execution_time', None)
            )
            results.append(exec_result)

    # 統計情報を計算
    stats = calculate_execution_statistics(results, node_statuses)

    return WorkflowResult(
        results=results,
        success=stats['overall_success'],
        total_nodes=stats['total_nodes'],
        completed_nodes=stats['completed_nodes'],
        failed_nodes=stats['failed_nodes'],
        skipped_nodes=stats['skipped_nodes']
    )


def calculate_execution_statistics(results: List[ExecutionResult],
                                 node_statuses: Dict[str, str]) -> Dict[str, Any]:
    """実行統計を計算（純粋関数）

    Args:
        results: 実行結果リスト
        node_statuses: ノード状態辞書

    Returns:
        統計情報辞書
    """
    total_nodes = len(node_statuses)
    completed_nodes = sum(1 for r in results if r.success)
    failed_nodes = sum(1 for r in results if r.failed)

    # ステータスからスキップ数を計算
    skipped_nodes = sum(1 for status in node_statuses.values() if status == "skipped")

    # 全体成功判定：失敗許可されていないノードが失敗していない
    overall_success = failed_nodes == 0

    return {
        'total_nodes': total_nodes,
        'completed_nodes': completed_nodes,
        'failed_nodes': failed_nodes,
        'skipped_nodes': skipped_nodes,
        'overall_success': overall_success
    }


def sort_results_by_execution_order(results: List[ExecutionResult],
                                   execution_order: List[str]) -> List[ExecutionResult]:
    """実行順序に従って結果をソート（純粋関数）

    Args:
        results: 実行結果リスト
        execution_order: 実行順序

    Returns:
        ソートされた結果リスト
    """
    # 実行順序のインデックスマップを作成
    order_map = {node_id: i for i, node_id in enumerate(execution_order)}

    # 結果をソート
    return sorted(results, key=lambda r: order_map.get(r.node_id, len(execution_order)))


def filter_results_by_status(results: List[ExecutionResult],
                             status_filter: str) -> List[ExecutionResult]:
    """ステータスで結果をフィルタ（純粋関数）

    Args:
        results: 実行結果リスト
        status_filter: フィルタ条件 ("success", "failed", "all")

    Returns:
        フィルタされた結果リスト
    """
    if status_filter == "success":
        return filter_data_collection(lambda r: r.success, results)
    if status_filter == "failed":
        return filter_data_collection(lambda r: r.failed, results)
    # "all"
    return results.copy()


def group_results_by_group(results: List[ExecutionResult],
                          parallel_groups: List[List[str]]) -> Dict[int, List[ExecutionResult]]:
    """並列グループ別に結果をグループ化（純粋関数）

    Args:
        results: 実行結果リスト
        parallel_groups: 並列グループリスト

    Returns:
        グループ別結果辞書
    """
    # ノードIDからグループインデックスへのマップを作成
    node_to_group = {}
    for group_idx, group in enumerate(parallel_groups):
        for node_id in group:
            node_to_group[node_id] = group_idx

    # 結果をグループ化
    grouped = {}
    for result in results:
        group_idx = node_to_group.get(result.node_id, -1)
        if group_idx not in grouped:
            grouped[group_idx] = []
        grouped[group_idx].append(result)

    return grouped


def calculate_group_statistics(grouped_results: Dict[int, List[ExecutionResult]]) -> Dict[int, Dict[str, Any]]:
    """グループ別統計を計算（純粋関数）

    Args:
        grouped_results: グループ別結果辞書

    Returns:
        グループ別統計辞書
    """
    group_stats = {}

    for group_idx, results in grouped_results.items():
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        group_stats[group_idx] = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0.0
        }

    return group_stats


def format_execution_summary(workflow_result: WorkflowResult) -> Dict[str, Any]:
    """実行サマリーをフォーマット（純粋関数）

    Args:
        workflow_result: ワークフロー結果

    Returns:
        フォーマット済みサマリー
    """
    return {
        'status': 'SUCCESS' if workflow_result.success else 'FAILED',
        'summary': {
            'total_nodes': workflow_result.total_nodes,
            'completed': workflow_result.completed_nodes,
            'failed': workflow_result.failed_nodes,
            'skipped': workflow_result.skipped_nodes,
            'success_rate': f"{workflow_result.success_rate:.1%}",
            'failure_rate': f"{workflow_result.failure_rate:.1%}"
        },
        'details': [
            {
                'node_id': result.node_id,
                'success': result.success,
                'error': result.error_message,
                'execution_time': result.execution_time
            }
            for result in workflow_result.results
        ]
    }


def create_legacy_operation_results(workflow_result: WorkflowResult) -> List[Any]:
    """レガシーOperationResultリストを作成（純粋関数）

    既存のAPIとの互換性のため

    Args:
        workflow_result: ワークフロー結果

    Returns:
        レガシーOperationResultリスト
    """
    return [result.result for result in workflow_result.results if result.result is not None]


def merge_execution_results(results1: List[ExecutionResult],
                           results2: List[ExecutionResult]) -> List[ExecutionResult]:
    """実行結果をマージ（純粋関数）

    Args:
        results1: 結果リスト1
        results2: 結果リスト2

    Returns:
        マージされた結果リスト（重複除去済み）
    """
    seen_nodes = set()
    merged = []

    # 最初のリストを追加
    for result in results1:
        if result.node_id not in seen_nodes:
            merged.append(result)
            seen_nodes.add(result.node_id)

    # 2番目のリストから重複していないものを追加
    for result in results2:
        if result.node_id not in seen_nodes:
            merged.append(result)
            seen_nodes.add(result.node_id)

    return merged

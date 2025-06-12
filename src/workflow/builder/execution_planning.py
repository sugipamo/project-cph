"""実行計画データ構造と純粋関数 - RequestExecutionGraphから分離"""
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Any
from enum import Enum

from .functional_utils import group_by, filter_pure, map_pure


@dataclass(frozen=True)
class ExecutionPlan:
    """実行計画（不変データ構造）"""
    parallel_groups: List[List[str]]
    node_dependencies: Dict[str, Set[str]] 
    execution_order: List[str]
    max_workers: int
    
    @property
    def total_nodes(self) -> int:
        """総ノード数（純粋関数）"""
        return sum(len(group) for group in self.parallel_groups)
    
    @property 
    def parallelism_factor(self) -> float:
        """並列化度（純粋関数）"""
        if not self.parallel_groups:
            return 0.0
        return self.total_nodes / len(self.parallel_groups)


@dataclass(frozen=True)
class NodeExecutionStatus:
    """ノード実行状態（不変データ構造）"""
    node_id: str
    status: str  # "pending", "running", "completed", "failed", "skipped"
    allow_failure: bool = False
    
    def is_executable(self, failed_nodes: Set[str], dependencies: Set[str]) -> bool:
        """実行可能判定（純粋関数）"""
        if self.status != "pending":
            return False
        return not dependencies.intersection(failed_nodes)
    
    def with_status(self, new_status: str) -> 'NodeExecutionStatus':
        """ステータス変更した新インスタンス（純粋関数）"""
        return NodeExecutionStatus(self.node_id, new_status, self.allow_failure)


def create_execution_plan(nodes: Dict[str, Any], dependencies: Dict[str, Set[str]], 
                         max_workers: int = 4) -> ExecutionPlan:
    """実行計画を生成（純粋関数）
    
    Args:
        nodes: ノード辞書
        dependencies: 依存関係辞書
        max_workers: 最大ワーカー数
        
    Returns:
        実行計画
    """
    parallel_groups = group_nodes_by_level(list(nodes.keys()), dependencies)
    execution_order = flatten_groups(parallel_groups)
    
    return ExecutionPlan(
        parallel_groups=parallel_groups,
        node_dependencies=dependencies,
        execution_order=execution_order,
        max_workers=max_workers
    )


def group_nodes_by_level(node_ids: List[str], dependencies: Dict[str, Set[str]]) -> List[List[str]]:
    """依存関係を基にノードを実行レベル別にグループ化（純粋関数）
    
    Args:
        node_ids: ノードIDリスト
        dependencies: 依存関係辞書
        
    Returns:
        レベル別グループリスト
    """
    # トポロジカルソートベースのレベリング
    in_degree = {node_id: 0 for node_id in node_ids}
    
    # 入次数を計算
    for node_id in node_ids:
        deps = dependencies.get(node_id, set())
        in_degree[node_id] = len(deps.intersection(set(node_ids)))
    
    levels = []
    remaining_nodes = set(node_ids)
    
    while remaining_nodes:
        # 入次数0のノードを現在レベルに
        current_level = [
            node_id for node_id in remaining_nodes 
            if in_degree[node_id] == 0
        ]
        
        if not current_level:
            # 循環依存がある場合、残りをすべて現在レベルに
            current_level = list(remaining_nodes)
        
        levels.append(current_level)
        
        # 現在レベルのノードを除去し、入次数を更新
        for node_id in current_level:
            remaining_nodes.remove(node_id)
            # このノードに依存していた他ノードの入次数を減らす
            for other_id in remaining_nodes:
                deps = dependencies.get(other_id, set())
                if node_id in deps:
                    in_degree[other_id] -= 1
    
    return levels


def flatten_groups(parallel_groups: List[List[str]]) -> List[str]:
    """並列グループを平坦化して実行順序を作成（純粋関数）
    
    Args:
        parallel_groups: 並列グループリスト
        
    Returns:
        平坦化された実行順序
    """
    execution_order = []
    for group in parallel_groups:
        execution_order.extend(sorted(group))  # グループ内は辞書順でソート
    return execution_order


def calculate_optimal_workers(max_workers: int, cpu_count: Optional[int] = None) -> int:
    """最適ワーカー数を計算（純粋関数）
    
    Args:
        max_workers: 最大ワーカー数
        cpu_count: CPUコア数（Noneの場合は1とみなす）
        
    Returns:
        最適ワーカー数
    """
    cpu_count = cpu_count or 1
    optimal_workers = min(max_workers, cpu_count * 2)  # CPUコア数の2倍まで
    return max(1, optimal_workers)  # 最低1ワーカー


def filter_executable_nodes(node_statuses: List[NodeExecutionStatus], 
                           failed_nodes: Set[str],
                           dependencies: Dict[str, Set[str]]) -> List[str]:
    """実行可能ノードをフィルタ（純粋関数）
    
    Args:
        node_statuses: ノード状態リスト
        failed_nodes: 失敗ノード集合
        dependencies: 依存関係辞書
        
    Returns:
        実行可能ノードIDリスト
    """
    executable = []
    for status in node_statuses:
        node_deps = dependencies.get(status.node_id, set())
        if status.is_executable(failed_nodes, node_deps):
            executable.append(status.node_id)
    return executable


def update_execution_statuses(statuses: List[NodeExecutionStatus], 
                             results: Dict[str, Any],
                             failed_nodes: Set[str]) -> List[NodeExecutionStatus]:
    """実行状態を更新（純粋関数）
    
    Args:
        statuses: 現在の状態リスト
        results: 実行結果辞書
        failed_nodes: 失敗ノード集合
        
    Returns:
        更新された状態リスト
    """
    updated_statuses = []
    
    for status in statuses:
        if status.node_id in results:
            result = results[status.node_id]
            new_status = "completed" if result.success else "failed"
            updated_statuses.append(status.with_status(new_status))
        elif status.node_id in failed_nodes and status.status == "pending":
            # 失敗依存によりスキップ
            updated_statuses.append(status.with_status("skipped"))
        else:
            updated_statuses.append(status)
    
    return updated_statuses


def create_batch_metadata(group: List[str], max_workers: int) -> Dict[str, Any]:
    """バッチ実行メタデータを作成（純粋関数）
    
    Args:
        group: 実行グループ
        max_workers: 最大ワーカー数
        
    Returns:
        バッチメタデータ
    """
    return {
        "group_size": len(group),
        "max_workers": max_workers,
        "batch_id": f"batch_{hash(tuple(group)) % 10000}",
        "nodes": group.copy()
    }


def validate_execution_plan(plan: ExecutionPlan, total_nodes: int) -> List[str]:
    """実行計画をバリデーション（純粋関数）
    
    Args:
        plan: 実行計画
        total_nodes: 期待される総ノード数
        
    Returns:
        バリデーションエラーリスト
    """
    errors = []
    
    if plan.total_nodes != total_nodes:
        errors.append(f"Node count mismatch: expected {total_nodes}, got {plan.total_nodes}")
    
    if plan.max_workers <= 0:
        errors.append(f"Invalid max_workers: {plan.max_workers}")
    
    if not plan.parallel_groups:
        errors.append("No parallel groups defined")
    
    # 重複ノードチェック
    all_planned_nodes = set()
    for group in plan.parallel_groups:
        for node_id in group:
            if node_id in all_planned_nodes:
                errors.append(f"Duplicate node in plan: {node_id}")
            all_planned_nodes.add(node_id)
    
    return errors
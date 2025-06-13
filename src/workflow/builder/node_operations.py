"""ノード操作の純粋関数 - RequestExecutionGraphから分離"""
from dataclasses import dataclass, replace
from typing import Dict, Set, List, Any, Optional


@dataclass(frozen=True)
class NodeState:
    """ノード状態（不変データ構造）"""
    node_id: str
    status: str
    allow_failure: bool = False
    result: Any = None
    
    def with_status(self, new_status: str) -> 'NodeState':
        """ステータスを変更した新インスタンス（純粋関数）"""
        return replace(self, status=new_status)
    
    def with_result(self, result: Any) -> 'NodeState':
        """結果を設定した新インスタンス（純粋関数）"""
        return replace(self, result=result)


@dataclass(frozen=True)
class NodeInfo:
    """ノード情報（不変データ構造）"""
    id: str
    creates_files: Set[str]
    creates_dirs: Set[str]
    reads_files: Set[str]
    requires_dirs: Set[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def from_request_node(cls, node: Any) -> 'NodeInfo':
        """RequestNodeからNodeInfoを作成（純粋関数）"""
        return cls(
            id=node.id,
            creates_files=node.creates_files.copy() if hasattr(node, 'creates_files') else set(),
            creates_dirs=node.creates_dirs.copy() if hasattr(node, 'creates_dirs') else set(),
            reads_files=node.reads_files.copy() if hasattr(node, 'reads_files') else set(),
            requires_dirs=node.requires_dirs.copy() if hasattr(node, 'requires_dirs') else set(),
            metadata=node.metadata.copy() if hasattr(node, 'metadata') else {}
        )


def create_node_state(node_id: str, status: str = "pending", 
                     allow_failure: bool = False, result: Any = None) -> NodeState:
    """ノード状態を作成（純粋関数）
    
    Args:
        node_id: ノードID
        status: 初期ステータス
        allow_failure: 失敗許可フラグ
        result: 実行結果
        
    Returns:
        新しいノード状態
    """
    return NodeState(
        node_id=node_id,
        status=status,
        allow_failure=allow_failure,
        result=result
    )


def update_node_status(node_state: NodeState, new_status: str, 
                      result: Any = None) -> NodeState:
    """ノードステータスを更新（純粋関数）
    
    Args:
        node_state: 現在のノード状態
        new_status: 新しいステータス
        result: 実行結果（オプション）
        
    Returns:
        更新されたノード状態
    """
    updated = node_state.with_status(new_status)
    if result is not None:
        updated = updated.with_result(result)
    return updated


def is_node_executable(node_state: NodeState, failed_nodes: Set[str], 
                      dependencies: Set[str]) -> bool:
    """ノードが実行可能かどうかを判定（純粋関数）
    
    Args:
        node_state: ノード状態
        failed_nodes: 失敗ノード集合
        dependencies: 依存ノード集合
        
    Returns:
        実行可能な場合True
    """
    if node_state.status != "pending":
        return False
    
    # 依存ノードに失敗があるかチェック
    return not dependencies.intersection(failed_nodes)


def mark_dependent_nodes_skipped(node_states: Dict[str, NodeState],
                                adjacency_list: Dict[str, Set[str]],
                                failed_node_id: str) -> Dict[str, NodeState]:
    """失敗ノードに依存するノードをスキップ状態にマーク（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        adjacency_list: 隣接リスト
        failed_node_id: 失敗ノードID
        
    Returns:
        更新されたノード状態辞書
    """
    updated_states = node_states.copy()
    
    # 失敗ノードに依存するノードを再帰的に探索
    def mark_recursive(current_failed_id: str):
        dependents = adjacency_list.get(current_failed_id, set())
        
        for dependent_id in dependents:
            if dependent_id in updated_states:
                current_state = updated_states[dependent_id]
                if current_state.status == "pending":
                    updated_states[dependent_id] = current_state.with_status("skipped")
                    # 再帰的に依存ノードもスキップ
                    mark_recursive(dependent_id)
    
    mark_recursive(failed_node_id)
    return updated_states


def filter_executable_nodes(node_states: Dict[str, NodeState],
                           failed_nodes: Set[str],
                           reverse_adjacency_list: Dict[str, Set[str]]) -> List[str]:
    """実行可能ノードをフィルタ（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        failed_nodes: 失敗ノード集合
        reverse_adjacency_list: 逆隣接リスト
        
    Returns:
        実行可能ノードIDリスト
    """
    executable = []
    
    for node_id, state in node_states.items():
        dependencies = reverse_adjacency_list.get(node_id, set())
        if is_node_executable(state, failed_nodes, dependencies):
            executable.append(node_id)
    
    return executable


def calculate_node_priority(node_info: NodeInfo, 
                          dependents_count: int, 
                          critical_path_member: bool = False) -> int:
    """ノードの実行優先度を計算（純粋関数）
    
    Args:
        node_info: ノード情報
        dependents_count: 被依存ノード数
        critical_path_member: クリティカルパス上のノードかどうか
        
    Returns:
        優先度スコア（高いほど優先）
    """
    priority = 0
    
    # 被依存ノード数に基づく優先度
    priority += dependents_count * 10
    
    # クリティカルパス上のノードは高優先度
    if critical_path_member:
        priority += 100
    
    # リソース作成ノードは優先度を上げる
    if node_info.creates_files or node_info.creates_dirs:
        priority += 50
    
    # ファイル読み込みノードは優先度を下げる
    if node_info.reads_files and not node_info.creates_files:
        priority -= 20
    
    return priority


def group_nodes_by_status(node_states: Dict[str, NodeState]) -> Dict[str, List[str]]:
    """ステータス別にノードをグループ化（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        
    Returns:
        ステータス -> ノードIDリストの辞書
    """
    groups = {}
    
    for node_id, state in node_states.items():
        status = state.status
        if status not in groups:
            groups[status] = []
        groups[status].append(node_id)
    
    return groups


def calculate_completion_statistics(node_states: Dict[str, NodeState]) -> Dict[str, int]:
    """完了統計を計算（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        
    Returns:
        統計情報辞書
    """
    status_groups = group_nodes_by_status(node_states)
    
    return {
        'total': len(node_states),
        'pending': len(status_groups.get('pending', [])),
        'running': len(status_groups.get('running', [])),
        'completed': len(status_groups.get('completed', [])),
        'failed': len(status_groups.get('failed', [])),
        'skipped': len(status_groups.get('skipped', []))
    }


def validate_node_states(node_states: Dict[str, NodeState],
                        all_node_ids: Set[str]) -> List[str]:
    """ノード状態の妥当性をチェック（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        all_node_ids: 全ノードID集合
        
    Returns:
        エラーメッセージリスト
    """
    errors = []
    
    # 欠落ノードチェック
    missing_nodes = all_node_ids - set(node_states.keys())
    if missing_nodes:
        errors.append(f"Missing node states: {missing_nodes}")
    
    # 余分ノードチェック
    extra_nodes = set(node_states.keys()) - all_node_ids
    if extra_nodes:
        errors.append(f"Extra node states: {extra_nodes}")
    
    # 不正ステータスチェック
    valid_statuses = {"pending", "running", "completed", "failed", "skipped"}
    for node_id, state in node_states.items():
        if state.status not in valid_statuses:
            errors.append(f"Invalid status for {node_id}: {state.status}")
    
    return errors


def create_node_batch(node_states: Dict[str, NodeState],
                     batch_nodes: List[str],
                     max_batch_size: int = 10) -> List[List[str]]:
    """ノードをバッチに分割（純粋関数）
    
    Args:
        node_states: ノード状態辞書
        batch_nodes: バッチ対象ノードリスト
        max_batch_size: 最大バッチサイズ
        
    Returns:
        バッチ分割されたノードIDリストのリスト
    """
    if not batch_nodes:
        return []
    
    # 実行可能ノードのみを抽出
    executable_nodes = [
        node_id for node_id in batch_nodes
        if node_id in node_states and node_states[node_id].status == "pending"
    ]
    
    # バッチに分割
    batches = []
    for i in range(0, len(executable_nodes), max_batch_size):
        batch = executable_nodes[i:i + max_batch_size]
        batches.append(batch)
    
    return batches
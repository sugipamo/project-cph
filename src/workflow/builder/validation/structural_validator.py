"""構造バリデーター

グラフ構造の整合性を検証する純粋関数群
"""
from typing import Any, Dict, List, Set, Tuple

from ..builder_validation import ValidationResult


def validate_graph_structure(nodes: Dict[str, Any], edges: List[Any]) -> ValidationResult:
    """グラフ構造を検証（純粋関数）

    Args:
        nodes: ノード辞書
        edges: エッジリスト

    Returns:
        検証結果
    """
    # 各種検証を実行
    node_errors = _validate_nodes(nodes)
    edge_errors, edge_warnings = _validate_edges(edges, set(nodes.keys()))
    structural_warnings, structural_suggestions = _check_structural_issues(nodes, edges)

    # 統計情報を計算
    statistics = _calculate_validation_statistics(nodes, edges)

    # 結果をマージ
    all_errors = node_errors + edge_errors
    all_warnings = edge_warnings + structural_warnings

    if all_errors:
        return ValidationResult.failure(all_errors, all_warnings, structural_suggestions, statistics)
    return ValidationResult.success(all_warnings, structural_suggestions, statistics)


def _validate_nodes(nodes: Dict[str, Any]) -> List[str]:
    """ノードの検証"""
    errors = []

    if not nodes:
        errors.append("No nodes found in graph")
        return errors

    for node_id, node_data in nodes.items():
        if not node_id:
            errors.append("Empty node ID found")

        if node_data is None:
            errors.append(f"Node {node_id} has no data")
            continue

        if hasattr(node_data, 'request') and node_data.request is None:
            errors.append(f"Node {node_id} has no request")

    return errors


def _validate_edges(edges: List[Any], valid_node_ids: Set[str]) -> Tuple[List[str], List[str]]:
    """エッジの検証"""
    errors = []
    warnings = []

    if not edges:
        warnings.append("No edges found - all nodes will run independently")
        return errors, warnings

    for i, edge in enumerate(edges):
        if not hasattr(edge, 'from_node') or not hasattr(edge, 'to_node'):
            errors.append(f"Edge {i} is missing from_node or to_node")
            continue

        from_node = getattr(edge, 'from_node', None)
        to_node = getattr(edge, 'to_node', None)

        if from_node not in valid_node_ids:
            errors.append(f"Edge {i} references invalid from_node: {from_node}")

        if to_node not in valid_node_ids:
            errors.append(f"Edge {i} references invalid to_node: {to_node}")

        if from_node == to_node:
            errors.append(f"Edge {i} creates self-loop: {from_node}")

        if hasattr(edge, 'dependency_type') and not _is_valid_dependency_type(edge.dependency_type):
            warnings.append(f"Edge {i} has unknown dependency type: {edge.dependency_type}")

    return errors, warnings


def _is_valid_dependency_type(dependency_type: Any) -> bool:
    """依存関係タイプの妥当性確認"""
    valid_types = ["FILE_CREATION", "DIRECTORY_CREATION", "RESOURCE_ACCESS", "EXECUTION_ORDER"]
    return str(dependency_type) in valid_types


def _check_structural_issues(nodes: Dict[str, Any], edges: List[Any]) -> Tuple[List[str], List[str]]:
    """構造的な問題をチェック（純粋関数）"""
    adjacency_list, reverse_adjacency_list = _build_adjacency_lists(nodes, edges)

    warnings = []
    suggestions = []

    # 各種構造問題をチェック
    isolated_warnings, isolated_suggestions = _check_isolated_nodes(nodes, adjacency_list, reverse_adjacency_list)
    sink_warnings, sink_suggestions = _check_sink_nodes(adjacency_list)
    source_warnings, source_suggestions = _check_source_nodes(reverse_adjacency_list)

    warnings.extend(isolated_warnings)
    warnings.extend(sink_warnings)
    warnings.extend(source_warnings)
    suggestions.extend(isolated_suggestions)
    suggestions.extend(sink_suggestions)
    suggestions.extend(source_suggestions)

    return warnings, suggestions


def _build_adjacency_lists(nodes: Dict[str, Any], edges: List[Any]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """隣接リストを構築"""
    adjacency_list = {node_id: set() for node_id in nodes}
    reverse_adjacency_list = {node_id: set() for node_id in nodes}

    for edge in edges:
        if hasattr(edge, 'from_node') and hasattr(edge, 'to_node'):
            from_node = edge.from_node
            to_node = edge.to_node

            if from_node in adjacency_list and to_node in reverse_adjacency_list:
                adjacency_list[from_node].add(to_node)
                reverse_adjacency_list[to_node].add(from_node)

    return adjacency_list, reverse_adjacency_list


def _check_isolated_nodes(nodes: Dict[str, Any], adjacency_list: Dict[str, Set[str]],
                         reverse_adjacency_list: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """孤立ノードのチェック"""
    isolated_nodes = []
    for node_id in nodes:
        has_incoming = bool(reverse_adjacency_list[node_id])
        has_outgoing = bool(adjacency_list[node_id])

        if not has_incoming and not has_outgoing:
            isolated_nodes.append(node_id)

    warnings = []
    suggestions = []

    if isolated_nodes:
        warnings.append(f"Isolated nodes detected: {isolated_nodes}")
        suggestions.append("Consider connecting isolated nodes or removing them")

    return warnings, suggestions


def _check_sink_nodes(adjacency_list: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """終端ノードのチェック"""
    sink_nodes = [node_id for node_id, neighbors in adjacency_list.items() if not neighbors]

    warnings = []
    suggestions = []

    if len(sink_nodes) > 3:
        warnings.append(f"Many sink nodes detected ({len(sink_nodes)})")
        suggestions.append("Consider consolidating final steps")

    return warnings, suggestions


def _check_source_nodes(reverse_adjacency_list: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """開始ノードのチェック"""
    source_nodes = [node_id for node_id, predecessors in reverse_adjacency_list.items() if not predecessors]

    warnings = []
    suggestions = []

    if len(source_nodes) > 5:
        warnings.append(f"Many source nodes detected ({len(source_nodes)})")
        suggestions.append("Consider consolidating initial steps")

    return warnings, suggestions


def _calculate_validation_statistics(nodes: Dict[str, Any], edges: List[Any]) -> Dict[str, Any]:
    """検証統計の計算"""
    return {
        'node_count': len(nodes),
        'edge_count': len(edges),
        'average_degree': len(edges) * 2 / len(nodes) if nodes else 0,
        'has_nodes': len(nodes) > 0,
        'has_edges': len(edges) > 0
    }

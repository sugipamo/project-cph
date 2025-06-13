"""接続性分析器

グラフの連結性を分析する純粋関数群
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass(frozen=True)
class ValidationResult:
    """検証結果を表現する不変データ構造"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    statistics: Dict[str, Any]

    @classmethod
    def success(cls, warnings: Optional[List[str]] = None, suggestions: Optional[List[str]] = None,
                statistics: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """成功結果を作成"""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )

    @classmethod
    def failure(cls, errors: List[str], warnings: Optional[List[str]] = None,
                suggestions: Optional[List[str]] = None, statistics: Optional[Dict[str, Any]] = None) -> 'ValidationResult':
        """失敗結果を作成"""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )


def check_graph_connectivity(adjacency_list: Dict[str, Set[str]]) -> ValidationResult:
    """グラフの連結性をチェック（純粋関数）

    Args:
        adjacency_list: 隣接リスト

    Returns:
        検証結果
    """
    if not adjacency_list:
        return ValidationResult.failure(["Empty adjacency list"])

    # 連結性分析を実行
    components = _analyze_connectivity(adjacency_list)
    warnings, suggestions = _analyze_component_structure(components, len(adjacency_list))
    statistics = _calculate_connectivity_statistics(components, len(adjacency_list))

    return ValidationResult.success(warnings, suggestions, statistics)


def _analyze_connectivity(adjacency_list: Dict[str, Set[str]]) -> List[Set[str]]:
    """グラフの連結成分を分析"""
    undirected_adj = _create_undirected_adjacency(adjacency_list)
    return _find_connected_components(undirected_adj)


def _analyze_component_structure(components: List[Set[str]], total_nodes: int) -> tuple[List[str], List[str]]:
    """連結成分の構造を分析"""
    warnings = []
    suggestions = []

    if len(components) > 1:
        warnings.append(f"Graph has {len(components)} disconnected components")
        suggestions.append("Consider adding connections between components")

    component_sizes = [len(comp) for comp in components]
    max_component_size = max(component_sizes) if component_sizes else 0
    min_component_size = min(component_sizes) if component_sizes else 0

    if max_component_size > total_nodes * 0.8:
        suggestions.append("Large connected component detected - consider splitting")

    if min_component_size == 1:
        isolated_count = component_sizes.count(1)
        warnings.append(f"{isolated_count} isolated nodes detected")

    return warnings, suggestions


def _calculate_connectivity_statistics(components: List[Set[str]], total_nodes: int) -> Dict[str, any]:
    """接続性統計を計算"""
    component_sizes = [len(comp) for comp in components]
    max_component_size = max(component_sizes) if component_sizes else 0
    min_component_size = min(component_sizes) if component_sizes else 0

    return {
        'connected_components': len(components),
        'largest_component_size': max_component_size,
        'smallest_component_size': min_component_size,
        'connectivity_ratio': max_component_size / total_nodes if total_nodes else 0
    }


def _create_undirected_adjacency(directed_adj: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """有向グラフから無向グラフの隣接リストを作成"""
    undirected = {node: set() for node in directed_adj}

    for node, neighbors in directed_adj.items():
        for neighbor in neighbors:
            undirected[node].add(neighbor)
            if neighbor in undirected:
                undirected[neighbor].add(node)

    return undirected


def _find_connected_components(adjacency_list: Dict[str, Set[str]]) -> List[Set[str]]:
    """連結成分を検出（DFS使用）"""
    visited = set()
    components = []

    for node in adjacency_list:
        if node not in visited:
            component = _dfs_component(node, adjacency_list, visited)
            components.append(component)

    return components


def _dfs_component(start_node: str, adjacency_list: Dict[str, Set[str]], visited: Set[str]) -> Set[str]:
    """深さ優先探索で連結成分を取得"""
    component = set()
    stack = [start_node]

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            component.add(node)

            for neighbor in adjacency_list.get(node, set()):
                if neighbor not in visited:
                    stack.append(neighbor)

    return component
